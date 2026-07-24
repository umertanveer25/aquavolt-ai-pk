"""
AquaVolt-AI — SQLite Hourly Data Logger (Multi-Field Upgrade)
=================================================================
Tier 1 Real-Time Integrations:
  1. Sentinel-2 NDVI + Real NDWI (B03/B08) per field
  2. MODIS Daily LST via Microsoft Planetary Computer
  3. Open-Meteo 16-Day Irrigation Forecast
  4. Multi-Field 8x8 Grid Telemetry (256 rows/hour)
"""

import os
import sys
import math
import numpy as np
import json
import sqlite3
import time
import requests
import socket
import urllib.request
import ssl
from datetime import datetime, timedelta, timezone
try:
    from gibs_viirs_integration import fill_gap_with_gibs as _gibs_fill
    _GIBS_AVAILABLE = True
except ImportError:
    _GIBS_AVAILABLE = False

# --- DoH Monkeypatch for robust DNS resolution ---
original_getaddrinfo = socket.getaddrinfo

def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return original_getaddrinfo(host, port, family, type, proto, flags)
    except socket.gaierror:
        try:
            url = f"https://8.8.8.8/resolve?name={host}&type=A"
            req = urllib.request.Request(url)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                res_data = json.loads(response.read().decode())
                for ans in res_data.get("Answer", []):
                    if ans.get("type") == 1:
                        ip = ans.get("data")
                        return original_getaddrinfo(ip, port, family, type, proto, flags)
        except Exception:
            pass
        raise

socket.getaddrinfo = custom_getaddrinfo
# -------------------------------------------------

# True farm center coordinates for Russell Ranch
LAT  = float(os.environ.get("AQUAVOLT_LAT",  38.5480))
LON  = float(os.environ.get("AQUAVOLT_LON",  -121.8780))
FARM = os.environ.get("AQUAVOLT_FARM", "UC Davis Russell Ranch, CA")

# Define database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aquavolt_telemetry.db")
INTERVAL_SECONDS = 3600  # 1 hour

# Define 4 distinct fields with their crop types — matches UC_Davis_Russell_Ranch_EXACT_FIELDS.png
FIELDS = [
    {
        "name": "Field-A (Corn)",
        "bbox": [-121.8790, 38.5480, -121.8720, 38.5540],
        "lat": 38.5510,
        "lon": -121.8755,
        "clay": 35.0
    },
    {
        "name": "Field-B (Alfalfa)",
        "bbox": [-121.8860, 38.5480, -121.8800, 38.5540],
        "lat": 38.5510,
        "lon": -121.8830,
        "clay": 28.0
    },
    {
        "name": "Field-C (Fallow)",
        "bbox": [-121.8860, 38.5420, -121.8800, 38.5475],
        "lat": 38.54475,
        "lon": -121.8830,
        "clay": 22.0
    },
    {
        "name": "Field-D (Tomato)",
        "bbox": [-121.8790, 38.5420, -121.8720, 38.5475],
        "lat": 38.54475,
        "lon": -121.8755,
        "clay": 32.0
    }
]


# TIER 1 — Sentinel-2 STAC Search (Once per run)
def get_latest_sentinel_item(lat, lon):
    print("[SATELLITE] Connecting to Planetary Computer STAC API...")
    try:
        import pystac_client
        import planetary_computer
        import certifi
    except ImportError as e:
        print(f"[SATELLITE WARNING] Missing deps: {e}. Falling back.")
        return None

    os.environ["CURL_CA_BUNDLE"] = certifi.where()

    try:
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        bbox = [lon - 0.02, lat - 0.02, lon + 0.02, lat + 0.02]

        search = catalog.search(
            collections=["sentinel-2-l2a"], bbox=bbox, datetime=time_range,
            query={"eo:cloud_cover": {"lt": 30}}
        )
        items = search.item_collection()
        if not items:
            start_date = end_date - timedelta(days=60)
            time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            search = catalog.search(
                collections=["sentinel-2-l2a"], bbox=bbox, datetime=time_range,
                query={"eo:cloud_cover": {"lt": 40}}
            )
            items = search.item_collection()
            if not items:
                print("[SATELLITE WARNING] No cloud-free scenes found. Falling back.")
                return None

        latest_item = items[0]
        print(f"[SATELLITE] Found Scene: {latest_item.id} | {latest_item.datetime.date()}")
        return latest_item

    except Exception as e:
        print(f"[SATELLITE WARNING] STAC Search failed: {e}. Falling back.")
        return None


# Extract 8x8 crop indices for a specific field's bbox
def fetch_field_indices(latest_item, field_bbox):
    try:
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.warp import transform_bounds
        import numpy as np
    except ImportError:
        return None

    try:
        b03_url = latest_item.assets["B03"].href
        b04_url = latest_item.assets["B04"].href
        b08_url = latest_item.assets["B08"].href

        with rasterio.open(b03_url) as s3, rasterio.open(b04_url) as s4, rasterio.open(b08_url) as s8:
            src_crs = s4.crs
            l, b, r, t = transform_bounds("EPSG:4326", src_crs, *field_bbox)
            win = from_bounds(l, b, r, t, transform=s4.transform)

            b03 = s3.read(1, window=win, out_shape=(8, 8)).astype(float)
            b04 = s4.read(1, window=win, out_shape=(8, 8)).astype(float)
            b08 = s8.read(1, window=win, out_shape=(8, 8)).astype(float)

            # Convert DN to reflectance (Sentinel-2 L2A scale = 0.0001)
            b04_refl = b04 * 0.0001
            b08_refl = b08 * 0.0001

            def safe_index(a, b_, mask):
                arr = (a - b_) / (a + b_ + 1e-8)
                arr = np.clip(arr, -1.0, 1.0)
                arr[mask] = np.nan
                if np.isnan(arr).any():
                    mv = np.nanmean(arr) if not np.isnan(arr).all() else 0.0
                    arr = np.where(np.isnan(arr), mv, arr)
                return arr

            bad_mask = (b04 == 0) | (b08 == 0)
            ndvi = safe_index(b08, b04, bad_mask)
            ndwi_real = safe_index(b03, b08, (b03 == 0) | (b08 == 0))

            # Real SAVI: (NIR - RED) / (NIR + RED + L) * (1 + L), L=0.5
            L = 0.5
            savi = (b08_refl - b04_refl) / (b08_refl + b04_refl + L) * (1.0 + L)
            savi = np.clip(savi, -1.0, 1.0)
            savi[bad_mask] = np.nan
            if np.isnan(savi).any():
                sv = np.nanmean(savi) if not np.isnan(savi).all() else 0.0
                savi = np.where(np.isnan(savi), sv, savi)

            return {
                "ndvi": ndvi.tolist(),
                "ndwi_real": ndwi_real.tolist(),
                "savi": savi.tolist(),
                "b04_refl": b04_refl.tolist(),
                "b08_refl": b08_refl.tolist()
            }

    except Exception as e:
        print(f"[SATELLITE WARNING] Error reading field window: {e}.")
        return None


# TIER 1 — MODIS Daily LST
def fetch_modis_lst(lat, lon):
    print("[MODIS] Fetching daily Land Surface Temperature...")
    try:
        import pystac_client
        import planetary_computer
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.warp import transform_bounds
        import certifi
        import numpy as np
    except ImportError as e:
        print(f"[MODIS WARNING] Missing deps: {e}.")
        return None

    os.environ["CURL_CA_BUNDLE"] = certifi.where()

    try:
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )

        end_date = datetime.now()
        start_date = end_date - timedelta(days=12)
        time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        bbox = [lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05]

        search = catalog.search(collections=["modis-11A1-061"], bbox=bbox, datetime=time_range)
        items = search.item_collection()
        if not items:
            print("[MODIS WARNING] No MODIS LST data found.")
            return None

        latest_item = items[0]
        start_dt = latest_item.properties.get("start_datetime")
        date_str = start_dt.split("T")[0] if start_dt else "Unknown"
        print(f"[MODIS] LST scene: {latest_item.id} | {date_str}")

        lst_url = latest_item.assets["LST_Day_1km"].href

        lat_deg = 500.0 / 111000.0
        lon_deg = 500.0 / (111000.0 * math.cos(math.radians(lat)))
        crop_bbox = [lon - lon_deg, lat - lat_deg, lon + lon_deg, lat + lat_deg]

        with rasterio.open(lst_url) as src:
            src_crs = src.crs
            l, b, r, t = transform_bounds("EPSG:4326", src_crs, *crop_bbox)
            win = from_bounds(l, b, r, t, transform=src.transform)
            lst_data = src.read(1, window=win).astype(float)
            lst_data = np.where(lst_data > 0, lst_data * 0.02 - 273.15, np.nan)
            lst_mean = float(np.nanmean(lst_data)) if not np.isnan(lst_data).all() else None

        if lst_mean is not None:
            print(f"[MODIS] Real LST: {lst_mean:.1f} C")
            return round(lst_mean, 1)
        return None

    except Exception as e:
        print(f"[MODIS WARNING] {e}. Using API soil temp.")
        return None


# TIER 1 — Open-Meteo 16-Day Forecast
def fetch_open_meteo_forecast(lat, lon):
    print("[FORECAST] Fetching 16-day irrigation forecast...")
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=et0_fao_evapotranspiration,precipitation_sum,"
            f"temperature_2m_max,temperature_2m_min"
            f"&forecast_days=16&timezone=UTC"
        )
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        daily = r.json().get("daily", {})
        et0_vals  = daily.get("et0_fao_evapotranspiration", [])
        precip    = daily.get("precipitation_sum", [])
        deficit_7d = sum(
            max(0.0, (et0_vals[i] or 0.0) - (precip[i] or 0.0) * 0.8)
            for i in range(min(7, len(et0_vals)))
        )
        print(f"[FORECAST] 7-day water deficit: {deficit_7d:.1f} mm")
        return round(deficit_7d, 1)
    except Exception as e:
        print(f"[FORECAST WARNING] {e}")
        return 0.0


# TIER 1 — Empirical LAI & FCOVER
def compute_lai_fcover(ndvi):
    ndvi_c = max(0.15, min(0.92, ndvi))
    lai = max(0.0, -math.log(max(1e-6, (0.69 - ndvi_c) / 0.59)) / 0.91)
    lai = round(min(lai, 8.0), 4)
    fcover = round(1.0 - math.exp(-0.5 * lai), 4)
    return lai, fcover


# ── PIML MLP: load once at startup ─────────────────────────────
_PIML_WEIGHTS = None

def _load_piml_weights():
    global _PIML_WEIGHTS
    if _PIML_WEIGHTS is not None:
        return _PIML_WEIGHTS
    weights_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_weights_mlp.json")
    try:
        with open(weights_path) as f:
            _PIML_WEIGHTS = json.load(f)
        print(f"[PIML] Loaded trained MLP weights from {weights_path}")
    except FileNotFoundError:
        print(f"[PIML WARNING] ai_weights_mlp.json not found — Kc will use FAO-56 prior only.")
    return _PIML_WEIGHTS


def _relu(x):
    return [max(0.0, v) for v in x]

def _matmul_add(W, b, x):
    """y = W @ x + b  (where W is a 2D list with len(x) rows and len(b) columns)"""
    return [sum(W[j][i] * x[j] for j in range(len(x))) + b[i] for i in range(len(b))]

def piml_kc_ks(ndvi, ndwi, savi, Dr, weights):
    """Run the 4->16->8->1 MLP and return (kc_residual, ks_residual) using loaded weights."""
    if weights is None:
        return 0.0, 0.0
    mean = weights["feat_mean"]
    std  = weights["feat_std"]
    env  = weights.get("envelope", 0.30)
    
    Dr_norm = Dr / 72.0  # TAW = 72.0
    x = [ndvi, ndwi, savi, Dr_norm]
    x_norm = [(x[i] - mean[i]) / (std[i] if std[i] > 1e-8 else 1.0) for i in range(4)]
    
    h1 = _relu(_matmul_add(weights["W1"], weights["b1"], x_norm))
    h2 = _relu(_matmul_add(weights["W2"], weights["b2"], h1))
    out = _matmul_add(weights["W3"], weights["b3"], h2)
    
    kc_res = max(-env, min(env, out[0]))
    return kc_res, 0.0


def fao56_kc_prior(ndvi):
    """FAO-56 Eq. 66-style NDVI->Kc baseline (no crop-type hack, no fallow special-case)."""
    # Basal Kcb from NDVI: Kcb = 1.457*NDVI - 0.1725  (Bausch & Neale 1987, as in FAO-56 §6.4)
    kcb = max(0.15, min(1.20, 1.457 * ndvi - 0.1725))
    # Add soil evaporation component Ke ≈ 0.10 for the reference condition
    kc = min(1.20, kcb + 0.10)
    return round(kc, 4)


def build_url(lat, lon):
    return (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
        f"precipitation,cloud_cover,surface_pressure,shortwave_radiation,"
        f"is_day,soil_temperature_0_to_7cm,soil_moisture_0_to_1cm"
        f"&hourly=shortwave_radiation,temperature_2m,precipitation,"
        f"relative_humidity_2m,et0_fao_evapotranspiration,"
        f"soil_temperature_0_to_7cm,soil_moisture_0_to_1cm"
        f"&forecast_days=1&timezone=UTC"
    )


# ── Initialize Database with 29-Column Schema ──────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT,
            latitude      REAL,
            longitude     REAL,
            sector_row    INTEGER,
            sector_col    INTEGER,
            ndvi          REAL,
            ndwi          REAL,
            savi          REAL,
            lst           REAL,
            Kc            REAL,
            Ks            REAL,
            Dr            REAL,
            TAW           REAL,
            RAW           REAL,
            ETc           REAL,
            water_need    REAL,
            air_temp      REAL,
            humidity      REAL,
            solar_rad     REAL,
            precip        REAL,
            soil_temp     REAL,
            soil_moisture REAL
        )
    """)

    # Check for new Tier 1 columns + multi-field columns and add if missing
    cur.execute("PRAGMA table_info(telemetry_log)")
    existing_cols = [col[1] for col in cur.fetchall()]

    new_cols = {
        "ndwi_real": "REAL",
        "lai": "REAL",
        "fcover": "REAL",
        "lst_modis": "REAL",
        "et0_deficit_7d": "REAL",
        "scene_id": "TEXT",
        "field_name": "TEXT",
        "lst_source": "TEXT"
    }
    for col_name, col_type in new_cols.items():
        if col_name not in existing_cols:
            print(f"[DB] Adding column {col_name} to telemetry_log...")
            cur.execute(f"ALTER TABLE telemetry_log ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()


def fetch_and_store():
    # Normalize timestamp to top of the hour for consistency
    now_str = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:00:00")
    print(f"\n[{now_str}] Querying weather APIs & satellite indexes...")

    # Check if this UTC hour is already logged locally
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM telemetry_log WHERE timestamp = ?", (now_str,))
    if cur.fetchone()[0] > 0:
        print(f"  [SKIP] Data for {now_str} already exists in database. Skipping.")
        conn.close()
        return 0

    try:
        r = requests.get(build_url(LAT, LON), timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  [ERROR] Open-Meteo API Error: {e} - skipping cycle.")
        conn.close()
        return 0

    current = data.get("current", {})
    hourly  = data.get("hourly",  {})

    temp       = current.get("temperature_2m")            or 20.0
    humidity   = current.get("relative_humidity_2m")      or 50.0
    precip_cur = current.get("precipitation")             or 0.0
    solar_rad  = current.get("shortwave_radiation")       or 0.0
    soil_temp  = current.get("soil_temperature_0_to_7cm") or temp
    soil_moist = current.get("soil_moisture_0_to_1cm")    or 0.18
    daily_et0    = sum(x for x in hourly.get("et0_fao_evapotranspiration", []) if x) or 5.0

    print(f"  Temp       : {temp} C")
    print(f"  Soil Moist : {soil_moist*100:.1f}%")
    print(f"  Daily ET0  : {daily_et0:.2f} mm")

    print("\n[TIER 1] Fetching satellite & forecast data...")
    latest_item = get_latest_sentinel_item(LAT, LON)
    scene_id = latest_item.id if latest_item else "Fallback"
    modis_lst_val = fetch_modis_lst(LAT, LON)
    deficit_7d    = fetch_open_meteo_forecast(LAT, LON)

    # ── GIBS/VIIRS Gap-Fill: if MODIS returns None, attempt VIIRS daily fill ──
    gibs_lst_val  = None
    gibs_ndvi_val = None
    if modis_lst_val is None and _GIBS_AVAILABLE:
        print("[TIER 1] MODIS unavailable — attempting NASA GIBS/VIIRS gap-fill...")
        try:
            # Assume a 4-day gap as conservative worst-case
            gap_start = datetime.now(timezone.utc) - timedelta(days=4)
            gap_end   = datetime.now(timezone.utc)
            filled    = _gibs_fill(LAT, LON, gap_start, gap_end)
            if filled:
                latest_fill  = filled[-1]                         # most recent gap day
                raw_lst      = latest_fill.get("lst_celsius", None)
                raw_ndvi     = latest_fill.get("ndvi", None)
                # Sanity-check: reject POWER -999 fill-value and unphysical LSTs
                if raw_lst is not None and -10 < raw_lst < 70:
                    gibs_lst_val  = round(raw_lst, 2)
                    gibs_ndvi_val = round(raw_ndvi, 4) if raw_ndvi else None
                    print(f"[GIBS] Gap-fill accepted: LST={gibs_lst_val}C  NDVI={gibs_ndvi_val}  "
                          f"(flag={latest_fill.get('flag','?')})")
                else:
                    print(f"[GIBS] Gap-fill rejected (unphysical LST={raw_lst}). Falling back to soil_temp.")
        except Exception as _ge:
            print(f"[GIBS] Gap-fill error: {_ge}")

    TAW = 72.0
    RAW = 36.0
    count = 0

    # Load PIML weights once
    piml_w = _load_piml_weights()

    for field in FIELDS:
        f_name = field["name"]
        print(f"\n[PIML] Processing field: {f_name}...")

        # Fetch real Sentinel-2 raster pixels for this field's bbox
        field_sentinel = fetch_field_indices(latest_item, field["bbox"]) if latest_item else None

        if field_sentinel is None:
            # No satellite data available — do NOT fabricate. Skip this field.
            print(f"  [SKIP] No satellite imagery for {f_name}. Record omitted.")
            continue

        for row in range(8):
            for col in range(8):
                # ── Real per-pixel values from Sentinel-2 COG rasters ──
                ndvi          = round(max(0.08, min(0.90, float(field_sentinel["ndvi"][row][col]))), 4)
                ndwi_real_val = round(max(-0.5,  min(0.5,  float(field_sentinel["ndwi_real"][row][col]))), 4)
                savi          = round(max(-1.0,  min(1.0,  float(field_sentinel["savi"][row][col]))), 4)

                ndwi   = ndwi_real_val                        # unified; no soil-moisture proxy
                lai, fcover = compute_lai_fcover(ndvi)

                # ── LST priority cascade: MODIS > GIBS/VIIRS > soil_temp ──
                # If GIBS filled a valid NDVI, blend with Sentinel pixel (GIBS=field-scale, S2=pixel-scale)
                if gibs_ndvi_val is not None:
                    ndvi = round((ndvi * 0.7 + gibs_ndvi_val * 0.3), 4)  # 70% S2 pixel, 30% VIIRS field
                    lai, fcover = compute_lai_fcover(ndvi)                # recompute with blended NDVI

                if modis_lst_val is not None:
                    lst_measured = modis_lst_val          # MODIS: best quality
                    lst_source   = "MODIS"
                elif gibs_lst_val is not None:
                    lst_measured = gibs_lst_val           # GIBS/VIIRS: gap-filled
                    lst_source   = "GIBS_VIIRS"
                else:
                    lst_measured = soil_temp              # final fallback
                    lst_source   = "soil_temp_proxy"
                
                # Ks from soil water balance — FAO-56 Eq. 84 (depletion-based)
                sm_frac_sector = 0.10 + ((ndwi_real_val - (-0.5)) / 1.0) * 0.80
                sm_frac_sector = min(1.0, max(0.0, sm_frac_sector))
                Dr  = round(TAW * (1.0 - sm_frac_sector), 2)
                
                # Compute clay and slope for this sector
                base_clay = field.get("clay", 30.0)
                clay = base_clay + (row - 3.5) * 0.4 + (col - 3.5) * 0.3
                slope = 1.0 + math.sin(row / 2.0) * 0.4 + math.cos(col / 2.0) * 0.2

                # ── PIML Kc / Ks ────────────────────────────────────────────
                kc_prior = fao56_kc_prior(ndvi)               # physics-based prior
                kc_res, ks_res = piml_kc_ks(ndvi, ndwi_real_val, savi, Dr, piml_w)
                kc = round(max(0.15, min(1.20, kc_prior + kc_res)), 2)

                if Dr <= RAW:
                    ks_fao = 1.0
                else:
                    ks_fao = max(0.0, (TAW - Dr) / (TAW - RAW))
                ks = round(min(1.0, max(0.0, ks_fao + ks_res)), 2)

                ETc = round(ks * kc * daily_et0, 2)
                irr = round(Dr, 2) if Dr > RAW else 0.0

                # ── Close the irrigation loop: apply recommended I back ──
                if irr > 0:
                    Dr = round(max(0.0, Dr - irr), 2)

                cur.execute("""
                    INSERT INTO telemetry_log (
                        timestamp, latitude, longitude, sector_row, sector_col,
                        ndvi, ndwi, ndwi_real, savi, lai, fcover, lst, lst_modis,
                        Kc, Ks, Dr, TAW, RAW, ETc, water_need,
                        air_temp, humidity, solar_rad, precip, soil_temp, soil_moisture, 
                        et0_deficit_7d, scene_id, field_name, lst_source
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    now_str, field["lat"], field["lon"], row, col,
                    ndvi, ndwi, ndwi_real_val, savi, lai, fcover, lst_measured, modis_lst_val,
                    kc, ks, Dr, TAW, RAW, ETc, irr,
                    temp, humidity, solar_rad, precip_cur, soil_temp, soil_moist, 
                    deficit_7d, scene_id, f_name, lst_source
                ))
                count += 1

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM telemetry_log")
    total = cur.fetchone()[0]
    conn.close()

    print(f"  [OK] Saved {count} sectors to local database.")
    print(f"  [DB] Total records: {total}")
    return count


def main():
    print("=" * 65)
    print("  AquaVolt-AI SQLite Logger [Tier 1 Multi-Field Upgrade]")
    print(f"  Farm     : {FARM}")
    print(f"  Location : {LAT} N, {LON} W")
    print(f"  Database : {DB_PATH}")
    print("=" * 65)

    init_db()

    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'-'*65}")
        print(f"  Logging Cycle #{cycle}")
        fetch_and_store()
        next_time = datetime.fromtimestamp(time.time() + INTERVAL_SECONDS)
        print(f"  [TIME] Next run at: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
