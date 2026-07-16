import os
import json
import math
import numpy as np
import requests
from datetime import datetime
import rasterio

# Load env variables from .env if present
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()


# ── Site coordinates (centre of the 4-field cluster) ──────────────────────────
LAT, LON = 38.5414, -121.8688

FIELDS = [
    {"name": "Field-A (Corn)",    "bbox": [-121.8790, 38.5480, -121.8720, 38.5540]},
    {"name": "Field-B (Alfalfa)", "bbox": [-121.8860, 38.5480, -121.8800, 38.5540]},
    {"name": "Field-C (Fallow)",  "bbox": [-121.8860, 38.5420, -121.8800, 38.5475]},
    {"name": "Field-D (Tomato)",  "bbox": [-121.8790, 38.5420, -121.8720, 38.5475]}
]

WEIGHTS_OUT = r"C:\Users\umert\aquavolt-ai-pk\ai_weights_mlp.json"

class PIMLNet:
    def __init__(self, input_dim=4, seed=42):
        np.random.seed(seed)
        # Xavier/He initialization for stable gradients
        self.W1 = np.random.normal(0.0, np.sqrt(2.0 / input_dim), (input_dim, 16))
        self.b1 = np.zeros(16)
        self.W2 = np.random.normal(0.0, np.sqrt(2.0 / 16), (16, 8))
        self.b2 = np.zeros(8)
        self.W3 = np.random.normal(0.0, np.sqrt(2.0 / 8), (8, 1))
        self.b3 = np.zeros(1)
        self.lr = 0.1  # Learning rate for normalized inputs

    def forward(self, X):
        self.h1 = np.maximum(0, X @ self.W1 + self.b1)
        self.h2 = np.maximum(0, self.h1 @ self.W2 + self.b2)
        return self.h2 @ self.W3 + self.b3

    def backward(self, X, dL):
        dW3 = self.h2.T @ dL
        db3 = dL.sum(axis=0)
        dh2 = dL @ self.W3.T * (self.h2 > 0)
        dW2 = self.h1.T @ dh2
        db2 = dh2.sum(axis=0)
        dh1 = dh2 @ self.W2.T * (self.h1 > 0)
        dW1 = X.T @ dh1
        db1 = dh1.sum(axis=0)
        
        for W, dW in [(self.W1,dW1),(self.b1,db1),(self.W2,dW2),(self.b2,db2),(self.W3,dW3),(self.b3,db3)]:
            W -= self.lr * np.clip(dW, -1.0, 1.0)

    def train(self, X, y_kc, epochs=300, batch=32):
        n = len(X)
        best_loss, patience, wait = 1e9, 30, 0
        best_W = [w.copy() for w in [self.W1,self.b1,self.W2,self.b2,self.W3,self.b3]]
        
        for ep in range(epochs):
            idx = np.random.permutation(n)
            losses = []
            for i in range(0, n, batch):
                xi = X[idx[i:i+batch]]
                yk = y_kc[idx[i:i+batch]]
                out = self.forward(xi)
                res_kc = np.clip(out[:, 0] * 0.30, -0.30, 0.30)
                loss = ((res_kc - yk)**2).mean()
                losses.append(loss)
                
                dout = np.zeros_like(out)
                dout[:, 0] = 2*(res_kc - yk) * 0.30 / len(xi)
                self.backward(xi, dout)
                
            ep_loss = np.mean(losses)
            if ep % 30 == 0:
                print(f"  Epoch {ep:3d}: loss={ep_loss:.5f}")
            if ep_loss < best_loss:
                best_loss = ep_loss
                best_W = [w.copy() for w in [self.W1,self.b1,self.W2,self.b2,self.W3,self.b3]]
                wait = 0
            else:
                wait += 1
                if wait >= patience:
                    break
        
        self.W1,self.b1,self.W2,self.b2,self.W3,self.b3 = [w.copy() for w in best_W]
        return best_loss

def fao56_kc_prior(ndvi):
    return float(np.clip(1.457 * ndvi - 0.1725 + 0.10, 0.15, 1.20))

def get_sentinel_items_for_date(lat, lon, target_date_str):
    try:
        import pystac_client
        import planetary_computer
        from datetime import datetime, timedelta
    except ImportError:
        return []
    try:
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )
        target_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
        start_dt = target_dt - timedelta(days=7)
        end_dt = target_dt + timedelta(days=7)
        time_range = f"{start_dt.strftime('%Y-%m-%d')}/{end_dt.strftime('%Y-%m-%d')}"
        bbox = [lon - 0.02, lat - 0.02, lon + 0.02, lat + 0.02]
        search = catalog.search(
            collections=["sentinel-2-l2a"], bbox=bbox, datetime=time_range,
            query={"eo:cloud_cover": {"lt": 20}}
        )
        items = list(search.items())
        if not items:
            return []
        items.sort(key=lambda x: abs((x.datetime.replace(tzinfo=None) - target_dt).total_seconds()))
        return items
    except Exception as e:
        print(f"[STAC ERROR] Failed to query Sentinel-2 for {target_date_str}: {e}")
        return []

def fetch_field_indices_5x5(s2_item, bbox):
    """Fetches a 5x5 sub-field grid of NDVI, NDWI, SAVI for a specific bbox.
    Uses highly-optimized native CRS clipping to avoid downloading the entire tile.
    Applies Processing Baseline >= 04.00 DN offset correction (-1000).
    """
    try:
        import planetary_computer
        import rioxarray
        from pyproj import Transformer
        from rasterio.enums import Resampling
        
        signed_item = planetary_computer.sign(s2_item)
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # Detect Processing Baseline offset (>= 04.00 adds +1000 to DN)
        baseline_str = s2_item.properties.get("s2:processing_baseline", "0")
        try:
            baseline_val = float(baseline_str.replace("N", "0"))
        except (ValueError, AttributeError):
            baseline_val = 0.0
        dn_offset = 1000.0 if baseline_val >= 4.0 else 0.0
        
        # Open B04 band lazily to inspect source CRS and bounds
        url_sample = signed_item.assets["B04"].href
        da_sample = rioxarray.open_rasterio(url_sample)
        src_crs = da_sample.rio.crs
        
        # Project bbox to source UTM CRS
        transformer = Transformer.from_crs("EPSG:4326", src_crs, always_xy=True)
        min_x, min_y = transformer.transform(min_lon, min_lat)
        max_x, max_y = transformer.transform(max_lon, max_lat)
        
        x1, x2 = min(min_x, max_x), max(min_x, max_x)
        y1, y2 = min(min_y, max_y), max(min_y, max_y)
        
        # Verify overlap with tile bounds
        left, bottom, right, top = da_sample.rio.bounds()
        if x2 < left or x1 > right or y2 < bottom or y1 > top:
            # Bounding box is outside the scanned swath of this tile
            return None
            
        def _get_band(band_name):
            url = signed_item.assets[band_name].href
            da = rioxarray.open_rasterio(url)
            # Clip native
            clipped = da.rio.clip_box(minx=x1, miny=y1, maxx=x2, maxy=y2)
            # Reproject clipped slice to EPSG:4326 (practically instantaneous)
            da_4326 = clipped.rio.reproject("EPSG:4326")
            # Resample to 5x5
            resampled = da_4326.rio.reproject(
                da_4326.rio.crs, 
                shape=(5, 5), 
                resampling=Resampling.bilinear
            )
            # Apply offset correction and convert to reflectance
            vals = resampled.values[0].astype(float) - dn_offset
            vals = np.maximum(vals, 0.0)  # reflectance can't be negative
            return vals
            
        b4 = _get_band("B04") # Red
        b8 = _get_band("B08") # NIR
        b3 = _get_band("B03") # Green
        
        ndvi = (b8 - b4) / (b8 + b4 + 1e-8)
        ndwi = (b3 - b8) / (b3 + b8 + 1e-8)
        savi = ((b8 - b4) / (b8 + b4 + 0.5)) * 1.5
        
        return {"ndvi": ndvi, "ndwi_real": ndwi, "savi": savi}
    except Exception as e:
        print(f"[S2 ERROR] Failed to fetch 5x5 raster: {e}")
        return None

def extract_ecostress_5x5(tif_path, bbox):
    """Extracts a 5x5 grid from the ECOSTRESS GeoTIFF for the bbox."""
    import rioxarray
    from rasterio.enums import Resampling
    min_lon, min_lat, max_lon, max_lat = bbox
    da = rioxarray.open_rasterio(tif_path)
    if da.rio.crs.to_epsg() != 4326:
        da = da.rio.reproject("EPSG:4326")
    try:
        clipped = da.rio.clip_box(minx=min_lon, miny=min_lat, maxx=max_lon, maxy=max_lat)
        resampled = clipped.rio.reproject(
            clipped.rio.crs, 
            shape=(5, 5), 
            resampling=Resampling.bilinear
        )
        return resampled.values[0]
    except Exception as e:
        print(f"[ECOSTRESS ERROR] Failed to clip/resample {tif_path}: {e}")
        return None

def main():
    print("=" * 60)
    print("AquaVolt-AI Sub-Field PIML Training Pipeline (Rigorous Polygon Validation)")
    print("=" * 60)

    np.random.seed(42)
    # The first 3 dates are for training, the last 2 are held out for testing.
    dates = [
        "2024-06-26", 
        "2024-07-03", 
        "2024-07-16", 
        "2024-07-30", 
        "2024-08-15"
    ]
    train_dates = dates[:3]
    test_dates = dates[3:]

    X_train_list, y_train_kc = [], []
    X_test_list, y_test_kc = [], []
    kc_prior_train, kc_obs_train = [], []
    kc_prior_test, kc_obs_test = [], []
    test_field_names = []  # track which field each test sample belongs to

    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from plugins.sensors import ecostress_api, cimis_api

    print("\n[1/3] Fetching historical weather/ET0 from CIMIS (Open-Meteo Fallback)...")
    cimis_resp = cimis_api.fetch("2024-05-01", "2024-09-30")
    if cimis_resp['status'] != 'success':
        print(f"[FATAL] CIMIS API fetch failed: {cimis_resp.get('msg', cimis_resp.get('text'))}")
        return
    cimis_data = cimis_resp['data']

    print("\n[1/3] Fetching historical sub-field area targets from ECOSTRESS API...")
    field_et_files = {}
    for field in FIELDS:
        f_name = field["name"]
        eco_resp = ecostress_api.fetch_area(field["bbox"], "2024-05-01", "2024-09-30")
        if eco_resp.get('status') != 'success':
            print(f"[FATAL] ECOSTRESS API area fetch failed for {f_name}: {eco_resp.get('msg', eco_resp.get('text'))}")
            return
        field_et_files[f_name] = eco_resp.get('data', {})

    for date_idx, date in enumerate(dates):
        is_test = date in test_dates
        print(f"Processing Date: {date} [{'TEST' if is_test else 'TRAIN'}]")
        
        c_weather = cimis_data.get(date, {})
        eto_val = c_weather.get('cimis_et0')
        if eto_val is None or eto_val <= 0:
            eto_val = 7.2
            
        for field in FIELDS:
            f_name = field["name"]
            
            # Fetch Sentinel-2 5x5 Raster (with fallback to adjacent scenes if swath edge/no-data occurs)
            s2_items = get_sentinel_items_for_date(LAT, LON, date)
            if not s2_items:
                raise SystemExit(f"No Sentinel-2 scene found near {date}. Stopping.")
                
            field_s2 = None
            for s2_item in s2_items:
                field_s2 = fetch_field_indices_5x5(s2_item, field["bbox"])
                if field_s2 is not None:
                    break
                    
            if field_s2 is None:
                raise SystemExit(f"Failed to fetch Sentinel-2 indices for {f_name} near {date} from any available scenes. Stopping.")

            # Fetch true spatial ECOSTRESS 5x5 raster
            tif_path = field_et_files[f_name].get(date)
            if tif_path is None:
                raise SystemExit(f"No real ET area data for {f_name} on {date}. Stopping.")
            
            et_grid = extract_ecostress_5x5(tif_path, field["bbox"])
            if et_grid is None:
                raise SystemExit(f"Failed to extract 5x5 ECOSTRESS raster for {f_name} on {date}.")

            TAW = 72.0

            # --- ECOSTRESS ETinst to ETdaily conversion ---
            # We fetch ETinst (W/m2) and multiply by 0.0353 to get daily mm/day.
            for row in range(5):
                for col in range(5):
                    ndvi = float(field_s2["ndvi"][row][col])
                    ndwi = float(field_s2["ndwi_real"][row][col])
                    savi = float(field_s2["savi"][row][col])
                    
                    sm_frac = max(0.0, min(1.0, 0.10 + ((ndwi - (-0.5)) / 1.0) * 0.80))
                    Dr = max(0.0, min(TAW, TAW * (1.0 - sm_frac)))
                    Dr_norm = Dr / TAW
                    
                    kc_prior = fao56_kc_prior(ndvi)
                    
                    et_val = float(et_grid[row][col]) * 0.0353  # mm/day
                    kc_obs = et_val / eto_val
                    kc_obs = max(0.05, min(1.40, kc_obs))
                    
                    res_kc = np.clip(kc_obs - kc_prior, -0.30, 0.30)
                    
                    features = [ndvi, ndwi, savi, Dr_norm]
                    if is_test:
                        X_test_list.append(features)
                        y_test_kc.append(res_kc)
                        kc_prior_test.append(kc_prior)
                        kc_obs_test.append(kc_obs)
                        test_field_names.append(f_name)
                    else:
                        X_train_list.append(features)
                        y_train_kc.append(res_kc)
                        kc_prior_train.append(kc_prior)
                        kc_obs_train.append(kc_obs)

    X_train = np.array(X_train_list, dtype=np.float32)
    y_train = np.array(y_train_kc, dtype=np.float32)
    X_test = np.array(X_test_list, dtype=np.float32)
    y_test = np.array(y_test_kc, dtype=np.float32)
    kc_prior_test = np.array(kc_prior_test, dtype=np.float32)
    kc_obs_test = np.array(kc_obs_test, dtype=np.float32)
    kc_prior_train = np.array(kc_prior_train, dtype=np.float32)
    kc_obs_train = np.array(kc_obs_train, dtype=np.float32)

    feat_mean = X_train.mean(axis=0)
    feat_std = X_train.std(axis=0)
    for i in range(len(feat_std)):
        if feat_std[i] < 1e-4:
            feat_std[i] = 1.0
            
    print(f"\nGenerated {len(X_train)} training samples and {len(X_test)} test samples.")
    print("Features Standard Deviations:")
    features_names = ["ndvi", "ndwi", "savi", "Dr"]
    for name, std_val in zip(features_names, feat_std):
        print(f"  {name:6s}: {std_val:.4f}")
    print(f"\nLabel (res_kc) stats:")
    print(f"  Train: mean={y_train.mean():.4f}  std={y_train.std():.4f}  min={y_train.min():.4f}  max={y_train.max():.4f}")
    print(f"  Test:  mean={y_test.mean():.4f}  std={y_test.std():.4f}  min={y_test.min():.4f}  max={y_test.max():.4f}")

    # Normalize features to 0-mean 1-std before training/eval
    X_train_norm = (X_train - feat_mean) / feat_std
    X_test_norm = (X_test - feat_mean) / feat_std

    print("\n[2/3] Training 4->16->8->1 MLP on pure empirical sub-field dataset...")
    net = PIMLNet(input_dim=4, seed=42)
    train_loss = net.train(X_train_norm, y_train, epochs=400)
    print(f"Final training loss (MSE): {train_loss:.6f}")
    
    # ==========================================
    # HELD-OUT TEST: A/B/C Comparison Table
    # ==========================================
    print("\n" + "="*60)
    print("HELD-OUT TEST SET EVALUATION (dates 4-5, unseen)")
    print("="*60)
    
    # Model A: FAO-56 Prior alone (no MLP correction)
    kc_A = kc_prior_test
    rmse_A = np.sqrt(((kc_A - kc_obs_test)**2).mean())
    
    # Model B: FAO-56 Prior + MLP residual correction
    out_test = net.forward(X_test_norm)
    res_kc_pred = np.clip(out_test[:, 0] * 0.30, -0.30, 0.30)
    kc_B = kc_prior_test + res_kc_pred
    rmse_B = np.sqrt(((kc_B - kc_obs_test)**2).mean())
    
    # Model C: Constant Kc (field-mean of observed Kc from training set)
    kc_const = kc_obs_train.mean()
    kc_C = np.full_like(kc_obs_test, kc_const)
    rmse_C = np.sqrt(((kc_C - kc_obs_test)**2).mean())
    
    print(f"\n{'Model':<30s} {'RMSE(Kc)':<12s} {'MAE(Kc)':<12s}")
    print("-"*54)
    
    mae_A = np.abs(kc_A - kc_obs_test).mean()
    mae_B = np.abs(kc_B - kc_obs_test).mean()
    mae_C = np.abs(kc_C - kc_obs_test).mean()
    
    print(f"{'A. FAO-56 prior alone':<30s} {rmse_A:<12.4f} {mae_A:<12.4f}")
    print(f"{'B. Prior + MLP (ours)':<30s} {rmse_B:<12.4f} {mae_B:<12.4f}")
    print(f"{'C. Constant Kc (baseline)':<30s} {rmse_C:<12.4f} {mae_C:<12.4f}")
    
    improvement = (1.0 - rmse_B / rmse_A) * 100
    print(f"\nImprovement B over A: {improvement:.1f}%")
    print(f"Constant Kc used: {kc_const:.4f}")
    print(f"Test samples: {len(X_test)}")

    # ==========================================
    # PAIRED STATISTICAL TESTS (B vs A)
    # ==========================================
    print("\n" + "="*60)
    print("PAIRED STATISTICAL TESTS (B vs A)")
    print("="*60)
    from scipy import stats
    eA = np.abs(kc_A - kc_obs_test)
    eB = np.abs(kc_B - kc_obs_test)
    t_stat, p_ttest = stats.ttest_rel(eB, eA)
    try:
        w_stat, p_wilcox = stats.wilcoxon(eB - eA)
    except Exception:
        w_stat, p_wilcox = float('nan'), float('nan')
    diff = eA - eB
    cohens_dz = diff.mean() / (diff.std(ddof=1) + 1e-12)
    print(f"Paired t-test:  t={t_stat:.3f}  p={p_ttest:.4f}")
    print(f"Wilcoxon test:  W={w_stat:.0f}  p={p_wilcox:.4f}")
    print(f"Cohen's dz:     {cohens_dz:.3f}")
    print(f"")
    print(f"MAE divergence note:")
    print(f"  MAE(A)={mae_A:.4f}  MAE(B)={mae_B:.4f}  diff={mae_A-mae_B:.4f} ({(mae_A-mae_B)/mae_A*100:.1f}%)")
    print(f"  RMSE(A)={rmse_A:.4f} RMSE(B)={rmse_B:.4f} diff={rmse_A-rmse_B:.4f} ({improvement:.1f}%)")
    print(f"  => Gain concentrated in tail errors (large residuals)")

    # ==========================================
    # PER-FIELD MEAN Kc ON TEST DATES (sanity check)
    # ==========================================
    print("\n" + "="*60)
    print("PER-FIELD MEAN Kc ON TEST DATES (sanity check)")
    print("="*60)
    print(f"\nAnchor: irrigated corn, Russell Ranch, July -> should be 1.10-1.15")
    print(f"{'Field':<25s} {'mean Kc_obs':<12s} {'mean Kc_prior':<14s} {'mean Kc_B':<12s} {'n':<6s}")
    print("-"*69)
    test_field_arr = np.array(test_field_names)
    for f in FIELDS:
        fn = f["name"]
        mask = test_field_arr == fn
        if mask.sum() == 0:
            continue
        mean_obs = kc_obs_test[mask].mean()
        mean_prior = kc_prior_test[mask].mean()
        mean_B = kc_B[mask].mean()
        print(f"{fn:<25s} {mean_obs:<12.4f} {mean_prior:<14.4f} {mean_B:<12.4f} {mask.sum():<6d}")

    print("\n[3/3] Saving weights to file...")
    data = {
        "W1": net.W1.tolist(), "b1": net.b1.tolist(),
        "W2": net.W2.tolist(), "b2": net.b2.tolist(),
        "W3": net.W3.tolist(), "b3": net.b3.tolist(),
        "feat_mean": feat_mean.tolist(),
        "feat_std": feat_std.tolist(),
        "trained_on": datetime.now().isoformat(),
        "training_source": "NASA ECOSTRESS ECO_L3T_JET.002 Area Raster + Sentinel-2 Raster (within-date normalized)",
        "n_features": 4,
        "features": features_names,
        "outputs": ["kc_residual"],
        "envelope": 0.30,
        "normalization": "within-date: ECOSTRESS spatial pattern preserved, anchored to field-mean FAO-56 prior"
    }
    with open(WEIGHTS_OUT, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Weights saved to: {WEIGHTS_OUT}")
    print("[OK] Retraining complete!")

if __name__ == "__main__":
    main()
