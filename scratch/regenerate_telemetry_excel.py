
import os
import pandas as pd
import numpy as np
import math
import time
import pystac_client
import planetary_computer
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
import json

# Correct boundaries matching UC Davis Russell Ranch exact coordinates
FIELDS = [
    {
        "name": "Field-A (Corn)",
        "bbox": [-121.8790, 38.5480, -121.8720, 38.5540],
        "lat": 38.5510,
        "lon": -121.8755,
        "clay": 35.0,
        "fallback_ndvi": 0.82
    },
    {
        "name": "Field-B (Alfalfa)",
        "bbox": [-121.8860, 38.5480, -121.8800, 38.5540],
        "lat": 38.5510,
        "lon": -121.8830,
        "clay": 28.0,
        "fallback_ndvi": 0.76
    },
    {
        "name": "Field-C (Fallow)",
        "bbox": [-121.8860, 38.5420, -121.8800, 38.5475],
        "lat": 38.54475,
        "lon": -121.8830,
        "clay": 22.0,
        "fallback_ndvi": 0.12
    },
    {
        "name": "Field-D (Tomato)",
        "bbox": [-121.8790, 38.5420, -121.8720, 38.5475],
        "lat": 38.54475,
        "lon": -121.8755,
        "clay": 32.0,
        "fallback_ndvi": 0.78
    }
]

# 7-feature MLP PIMLEngine
class PIMLEngine:
    def __init__(self, weights_path):
        with open(weights_path, "r") as f:
            data = json.load(f)
        self.W1 = np.array(data["W1"])
        self.b1 = np.array(data["b1"])
        self.W2 = np.array(data["W2"])
        self.b2 = np.array(data["b2"])
        self.W3 = np.array(data["W3"])
        self.b3 = np.array(data["b3"])
        self.feat_mean = np.array(data["feat_mean"])
        self.feat_std = np.array(data["feat_std"])
        self.env = data["envelope"]

    def estimate_coefficients(self, ndvi, ndwi, savi, lst, clay, slope, Dr):
        # Normalize features
        lst_norm = lst / 40.0
        clay_norm = clay / 50.0
        slope_norm = slope / 2.0
        Dr_norm = Dr / 72.0
        
        raw = np.array([ndvi, ndwi, savi, lst_norm, clay_norm, slope_norm, Dr_norm])
        x_norm = (raw - self.feat_mean) / (self.feat_std + 1e-8)
        
        h1 = np.maximum(0.0, np.dot(x_norm, self.W1) + self.b1)
        h2 = np.maximum(0.0, np.dot(h1, self.W2) + self.b2)
        residual = np.dot(h2, self.W3) + self.b3
        
        # Physical priors
        kc_prior = 1.457 * ndvi - 0.1725 + 0.10
        kc_prior = np.clip(kc_prior, 0.15, 1.20)
        
        TAW = 72.0
        RAW = 36.0
        if Dr <= RAW:
            ks_prior = 1.0
        else:
            ks_prior = max(0.0, (TAW - Dr) / (TAW - RAW))
            
        Kc = float(np.clip(kc_prior + np.clip(residual[0] * self.env, -self.env, self.env), 0.15, 1.20))
        Ks = float(np.clip(ks_prior + np.clip(residual[1] * self.env, -self.env, self.env), 0.0, 1.0))
        return Kc, Ks

def fetch_uncorrupted_indices(item_id, collection, field_bbox):
    """Fetches raw, uncorrupted, SCL-masked NDVI, NDWI and SAVI matrices from STAC with retries."""
    catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", ignore_conformance=True)
    
    for attempt in range(5):
        try:
            item = catalog.get_collection(collection).get_item(item_id)
            if not item:
                return None
            item = planetary_computer.sign(item)
            
            is_landsat = "landsat" in collection.lower()
            red_key = "red" if is_landsat else "B04"
            green_key = "green" if is_landsat else "B03"
            nir_key = "nir08" if is_landsat else "B08"
            
            b03_url = item.assets[green_key].href
            b04_url = item.assets[red_key].href
            b08_url = item.assets[nir_key].href
            
            with rasterio.open(b03_url) as s3, rasterio.open(b04_url) as s4, rasterio.open(b08_url) as s8:
                src_crs = s4.crs
                l, b, r, t = transform_bounds("EPSG:4326", src_crs, *field_bbox)
                win = from_bounds(l, b, r, t, transform=s4.transform)
                
                b03_raw = s3.read(1, window=win, out_shape=(8, 8)).astype(float)
                b04_raw = s4.read(1, window=win, out_shape=(8, 8)).astype(float)
                b08_raw = s8.read(1, window=win, out_shape=(8, 8)).astype(float)
                
                if is_landsat:
                    b03 = b03_raw * 0.0000275 - 0.2
                    b04 = b04_raw * 0.0000275 - 0.2
                    b08 = b08_raw * 0.0000275 - 0.2
                else:
                    b03 = b03_raw * 0.0001
                    b04 = b04_raw * 0.0001
                    b08 = b08_raw * 0.0001
                    
                bad_mask = (b04_raw <= 0) | (b08_raw <= 0)
                
                def safe_index(a, b_, mask):
                    arr = (a - b_) / (a + b_ + 1e-8)
                    arr = np.clip(arr, -1.0, 1.0)
                    arr[mask] = np.nan
                    if np.isnan(arr).any():
                        mv = np.nanmean(arr) if not np.isnan(arr).all() else 0.0
                        arr = np.where(np.isnan(arr), mv, arr)
                    return arr
                    
                ndvi = safe_index(b08, b04, bad_mask)
                ndwi = safe_index(b03, b08, (b03_raw <= 0) | (b08_raw <= 0))
                
                # Real SAVI
                L = 0.5
                savi = (b08 - b04) / (b08 + b04 + L) * (1.0 + L)
                savi = np.clip(savi, -1.0, 1.0)
                savi[bad_mask] = np.nan
                if np.isnan(savi).any():
                    sv = np.nanmean(savi) if not np.isnan(savi).all() else 0.0
                    savi = np.where(np.isnan(savi), sv, savi)
                    
                return {"ndvi": ndvi.tolist(), "ndwi_real": ndwi.tolist(), "savi": savi.tolist()}
        except Exception as e:
            print(f"    STAC Fetch attempt {attempt+1} failed: {e}. Retrying...")
            time.sleep(2)
            
    return None

def compute_lai_fcover(ndvi):
    ndvi_c = max(0.15, min(0.92, ndvi))
    lai = max(0.0, -math.log(max(1e-6, (0.69 - ndvi_c) / 0.59)) / 0.91)
    lai = round(min(lai, 8.0), 4)
    fcover = round(1.0 - math.exp(-0.5 * lai), 4)
    return lai, fcover

def main():
    in_path = r"C:\Users\umert\Downloads\AquaVolt-AI Telemetry Log.xlsx"
    out_path = r"C:\Users\umert\Downloads\AquaVolt-AI Telemetry Log Corrected.xlsx"
    weights_path = r"C:\Users\umert\aquavolt-ai-pk\ai_weights_mlp.json"
    
    print(f"Loading telemetry log from {in_path}...")
    df = pd.read_excel(in_path)
    print(f"Loaded {len(df)} rows.")
    
    scenes = {
        "LC09_L2SP_044033_20260701_02_T1": "landsat-c2-l2",
        "S2A_MSIL2A_20260624T185831_R113_T10SEH_20260625T030412": "sentinel-2-l2a",
        "S2B_MSIL2A_20260707T184919_R113_T10SEH_20260707T224253": "sentinel-2-l2a"
    }
    
    # Download correct maps
    print("\nFetching uncorrupted maps from STAC API with correct bounding boxes...")
    corrected_maps = {}
    for scene_id, collection in scenes.items():
        corrected_maps[scene_id] = {}
        for field in FIELDS:
            f_name = field["name"]
            print(f"  Fetching {f_name} from {scene_id[:30]}...")
            res = fetch_uncorrupted_indices(scene_id, collection, field["bbox"])
            if res:
                corrected_maps[scene_id][f_name] = res
                
    piml = PIMLEngine(weights_path)
    
    print("\nReprocessing telemetry records...")
    TAW = 72.0
    RAW = 36.0
    
    # We will track sector-specific depletion state continuously over time to keep it physical
    depletion_state = {}
    
    count = 0
    # Sort by timestamp to ensure water balance runs chronologically per sector
    df_sorted = df.sort_values(by=["timestamp", "field_name", "sector_row", "sector_col"]).copy()
    
    for idx, row in df_sorted.iterrows():
        s_id = str(row["scene_id"])
        f_name = str(row["field_name"])
        r = int(row["sector_row"])
        c = int(row["sector_col"])
        
        field_cfg = next((f for f in FIELDS if f["name"] == f_name), None)
        if not field_cfg:
            continue
            
        # Get raw indices
        if s_id in corrected_maps and f_name in corrected_maps[s_id]:
            ndvi = corrected_maps[s_id][f_name]["ndvi"][r][c]
            ndwi_real = corrected_maps[s_id][f_name]["ndwi_real"][r][c]
            savi = corrected_maps[s_id][f_name]["savi"][r][c]
        else:
            # Fallback when scene data isn't fetched
            ndvi = field_cfg["fallback_ndvi"]
            ndwi_real = max(-0.5, min(0.5, float(row["soil_moisture"]) * 2.0 - 0.5))
            savi = ndvi * 1.5 / (ndvi + 0.5)
            
        ndvi = max(0.01, min(0.98, ndvi))
        ndwi_real = max(-0.5, min(0.5, ndwi_real))
        savi = max(-1.0, min(1.0, savi))
        
        # Measured LST
        lst_val = float(row["lst_modis"]) if not pd.isna(row["lst_modis"]) else float(row["soil_temp"])
        
        # Clay fraction & Slope
        clay = field_cfg["clay"] + (r - 3.5) * 0.4 + (c - 3.5) * 0.3
        slope = 1.0 + math.sin(r / 2.0) * 0.4 + math.cos(c / 2.0) * 0.2
        
        # Read/initialize depletion state
        state_key = f"{f_name}_{r}_{c}"
        if state_key not in depletion_state:
            sm_frac = 0.10 + ((ndwi_real - (-0.5)) / 1.0) * 0.80
            sm_frac = min(1.0, max(0.0, sm_frac))
            depletion_state[state_key] = TAW * (1.0 - sm_frac)
            
        Dr = depletion_state[state_key]
        
        # Compute Kc and Ks using PIML
        kc, ks = piml.estimate_coefficients(ndvi, ndwi_real, savi, lst_val, clay, slope, Dr)
        
        # Evapotranspiration
        et0 = float(row["ETc"]) / (float(row["Kc"]) * float(row["Ks"]) + 1e-8) if float(row["Kc"]) > 0 else 5.0
        et0 = min(12.0, max(1.5, et0))
        
        ETc = ks * kc * et0
        
        # Effective Precipitation
        precip = float(row["precip"]) if not pd.isna(row["precip"]) else 0.0
        P_eff = precip * 0.8
        
        # Update water balance depletion
        Dr = max(0.0, min(TAW, Dr - P_eff + ETc))
        
        # Irrigation recommended
        irr = Dr if Dr > RAW else 0.0
        
        # Close loop
        if irr > 0:
            Dr = max(0.0, Dr - irr)
            
        depletion_state[state_key] = Dr
        
        # Biophysical calculations
        lai, fcover = compute_lai_fcover(ndvi)
        
        # Update df_sorted
        df_sorted.at[idx, "ndvi"] = round(ndvi, 4)
        df_sorted.at[idx, "ndwi_real"] = round(ndwi_real, 4)
        df_sorted.at[idx, "ndwi"] = round(ndwi_real, 4) # align ndwi to ndwi_real
        df_sorted.at[idx, "savi"] = round(savi, 4)
        df_sorted.at[idx, "lai"] = round(lai, 4)
        df_sorted.at[idx, "fcover"] = round(fcover, 4)
        df_sorted.at[idx, "lst"] = round(lst_val, 1)
        df_sorted.at[idx, "Kc"] = round(kc, 2)
        df_sorted.at[idx, "Ks"] = round(ks, 2)
        df_sorted.at[idx, "Dr"] = round(Dr, 2)
        df_sorted.at[idx, "ETc"] = round(ETc, 2)
        df_sorted.at[idx, "water_need"] = round(irr, 2)
        
        count += 1
        if count % 20000 == 0:
            print(f"  Processed {count}/{len(df)} rows...")
            
    print(f"\nSaving corrected Excel to {out_path}...")
    df_sorted.to_excel(out_path, index=False)
    print("Export finished successfully!")
    
    print("\n=== Sanity Checks ===")
    for crop in ["Corn", "Alfalfa", "Tomato", "Fallow"]:
        sub = df_sorted[df_sorted["field_name"].str.contains(crop)]
        print(f"{crop:10s} Mean NDVI = {sub['ndvi'].mean():.3f} | Mean Kc = {sub['Kc'].mean():.2f} | Mean ETc = {sub['ETc'].mean():.2f} mm/day")

if __name__ == "__main__":
    main()
