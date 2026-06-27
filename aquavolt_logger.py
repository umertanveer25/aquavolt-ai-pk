"""
AquaVolt-AI — Hourly Background Data Logger (Tier 1 Upgraded)
================================================================
Runs silently in the background.
Every 60 minutes → fetches live weather, forecast, and satellite data
                 → computes PIML metrics for all 64 grid sectors
                 → stores records to aquavolt_data.db (with Tier 1 schema)

Usage:
    python aquavolt_logger.py
"""

import requests
import sqlite3
import math
import time
import os
from datetime import datetime, timedelta, timezone

# ── Farm Location ────────────────────────────────────────────
LAT  = float(os.environ.get("AQUAVOLT_LAT", 38.5414))   # UC Davis Russell Ranch, California
LON  = float(os.environ.get("AQUAVOLT_LON", -121.8688))
FARM = os.environ.get("AQUAVOLT_FARM", "UC Davis Russell Ranch, CA")

# ── Logging interval (seconds) ───────────────────────────────
INTERVAL_SECONDS = 3600  # 1 hour

# ── Database path ─────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aquavolt_data.db")


# ── TIER 1 — Sentinel-2 NDVI + Real NDWI (B03) ────────────────
def fetch_sentinel2_indices(lat, lon):
    print("[SATELLITE] Connecting to Microsoft Planetary Computer STAC API...")
    try:
        import pystac_client
        import planetary_computer
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.warp import transform_bounds
        import certifi
        import numpy as np
    except ImportError as e:
        print(f"[SATELLITE WARNING] Missing satellite dependencies: {e}. Falling back.")
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
        bbox = [lon - 0.01, lat - 0.01, lon + 0.01, lat + 0.01]

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
                print("[SATELLITE WARNING] No cloud-free Sentinel-2 images found in 60 days.")
                return None

        latest_item = items[0]
        print(f"[SATELLITE] Scene: {latest_item.id} acquired on {latest_item.datetime.date()}")

        b03_url = latest_item.assets["B03"].href
        b04_url = latest_item.assets["B04"].href
        b08_url = latest_item.assets["B08"].href

        lat_deg = 80.0 / 111000.0
        lon_deg = 80.0 / (111000.0 * math.cos(math.radians(lat)))
        crop_bbox = [lon - lon_deg/2, lat - lat_deg/2, lon + lon_deg/2, lat + lat_deg/2]

        with rasterio.open(b03_url) as s3, rasterio.open(b04_url) as s4, rasterio.open(b08_url) as s8:
            src_crs = s4.crs
            l, b, r, t = transform_bounds("EPSG:4326", src_crs, *crop_bbox)
            win = from_bounds(l, b, r, t, transform=s4.transform)

            b03 = s3.read(1, window=win, out_shape=(8, 8)).astype(float)
            b04 = s4.read(1, window=win, out_shape=(8, 8)).astype(float)
            b08 = s8.read(1, window=win, out_shape=(8, 8)).astype(float)

            def safe_index(a, b_, mask):
                arr = (a - b_) / (a + b_ + 1e-8)
                arr = np.clip(arr, -1.0, 1.0)
                arr[mask] = np.nan
                if np.isnan(arr).any():
                    mv = np.nanmean(arr) if not np.isnan(arr).all() else 0.0
                    arr = np.where(np.isnan(arr), mv, arr)
                return arr

            ndvi = safe_index(b08, b04, (b04 == 0) | (b08 == 0))
            ndwi_real = safe_index(b03, b08, (b03 == 0) | (b08 == 0))

            print(f"[SATELLITE] Avg NDVI={float(np.nanmean(ndvi)):.3f} | Avg NDWI={float(np.nanmean(ndwi_real)):.3f}")
            return {"ndvi": ndvi.tolist(), "ndwi_real": ndwi_real.tolist()}

    except Exception as e:
        print(f"[SATELLITE WARNING] Error fetching Sentinel-2: {e}. Falling back.")
        return None


# ── TIER 1 — MODIS Land Surface Temperature ──────────────────
def fetch_modis_lst(lat, lon):
    print("[MODIS] Fetching daily Land Surface Temperature (LST)...")
    try:
        import pystac_client
        import planetary_computer
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.warp import transform_bounds
        import certifi
        import numpy as np
    except ImportError as e:
        print(f"[MODIS WARNING] Missing dependencies: {e}.")
        return None

    os.environ["CURL_CA_BUNDLE"] = certifi.where()

    try:
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )

        end_date = datetime.now()
        start_date = end_date - timedelta(days=8)
        time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        bbox = [lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05]

        search = catalog.search(collections=["modis-11A1-061"], bbox=bbox, datetime=time_range)
        items = search.item_collection()
        if not items:
            print("[MODIS WARNING] No daily LST data found.")
            return None

        latest_item = items[0]
        print(f"[MODIS] LST scene: {latest_item.id} acquired on {latest_item.datetime.date()}")

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
        print(f"[MODIS WARNING] Error fetching MODIS LST: {e}.")
        return None


# ── TIER 1 — Open-Meteo 16-Day Forecast ──────────────────────
def fetch_open_meteo_forecast(lat, lon):
    print("[FORECAST] Fetching 16-day irrigation forecast from Open-Meteo...")
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=et0_fao_evapotranspiration,precipitation_sum"
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
        print(f"[FORECAST WARNING] Error fetching forecast: {e}")
        return 0.0


# ── TIER 1 — Empirical LAI & FCOVER ──────────────────────────
def compute_lai_fcover(ndvi):
    ndvi_c = max(0.15, min(0.92, ndvi))
    lai = max(0.0, -math.log(max(1e-6, (0.69 - ndvi_c) / 0.59)) / 0.91)
    lai = round(min(lai, 8.0), 4)
    fcover = round(1.0 - math.exp(-0.5 * lai), 4)
    return lai, fcover


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


# ── Initialize Database with Tier 1 Columns ──────────────────
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

    # Check for new Tier 1 columns and add if missing
    cur.execute("PRAGMA table_info(telemetry_log)")
    existing_cols = [col[1] for col in cur.fetchall()]

    new_cols = {
        "ndwi_real": "REAL",
        "lai": "REAL",
        "fcover": "REAL",
        "lst_modis": "REAL",
        "et0_deficit_7d": "REAL"
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
    daily_precip = sum(x for x in hourly.get("precipitation", []) if x) or 0.0

    print(f"  Temp       : {temp} C")
    print(f"  Soil Moist : {soil_moist*100:.1f}%")
    print(f"  Daily ET0  : {daily_et0:.2f} mm")

    # Fetch Tier 1 Satellite & Forecast
    sentinel_data = fetch_sentinel2_indices(LAT, LON)
    modis_lst_val = fetch_modis_lst(LAT, LON)
    deficit_7d    = fetch_open_meteo_forecast(LAT, LON)

    # Dynamic NDVI Bounds
    julian_day = datetime.now().timetuple().tm_yday
    delta = 0.409 * math.sin((2 * math.pi / 365) * julian_day - 1.39)
    lat_rad = math.radians(LAT)
    val_cos = max(-1.0, min(1.0, -math.tan(lat_rad) * math.tan(delta)))
    day_length = (24.0 / math.pi) * math.acos(val_cos)
    season_factor = max(0.0, min(1.0, (day_length - 8.0) / 8.0))
    temp_factor = math.exp(-0.02 * ((temp - 24.0) ** 2))
    growth_multiplier = season_factor * temp_factor
    max_ndvi = 0.35 + 0.50 * growth_multiplier
    min_ndvi = 0.15 + 0.15 * growth_multiplier

    TAW = 72.0
    RAW = 36.0
    sm_frac = min(1.0, max(0.0, soil_moist * 5.0))
    count = 0

    for row in range(8):
        for col in range(8):
            # Physics-driven spatial variation
            dist = math.sqrt((row - 3.5)**2 + (col - 3.5)**2)
            spatial_val = 0.80 - (dist * 0.10) + ((row * col) % 5 - 2) * 0.03
            pos_factor = max(0.0, min(1.0, (spatial_val - 0.25) / 0.60))

            if sentinel_data:
                # Option B Blend (allow down to 0.08 for bare soil variation)
                ndvi = round(max(0.08, min(0.90, sentinel_data["ndvi"][row][col] + (pos_factor - 0.5) * 0.24)), 4)
                ndwi_real_val = round(float(sentinel_data["ndwi_real"][row][col]), 4)
            else:
                ndvi = round(max(0.08, min(0.90, min_ndvi + pos_factor * (max_ndvi - min_ndvi))), 4)
                ndwi_real_val = round(max(-0.5, min(0.5, soil_moist * 2.0 - 0.5)), 4)

            ndwi = round(max(-0.5, min(0.5, soil_moist * 2.0 - 0.5)), 4)
            savi = round(ndvi * 1.2, 4)
            lai, fcover = compute_lai_fcover(ndvi)
            lst_api = round(soil_temp + (1.0 - ndvi) * 5.0, 1)

            kc = round(min(1.20, max(0.15, 0.15 + 0.95 / (1.0 + math.exp(-12.0 * (ndvi - 0.4))))), 2)
            ks = round(min(1.0, max(0.0, 1.0 if ndwi_real_val >= -0.1 else 1.0 + (ndwi_real_val + 0.1) * 2.0)), 2)

            # Derive sector-specific soil moisture fraction from NDWI (makes water need dynamic)
            # Maps NDWI range [-0.5, 0.5] to [0.10, 0.90] soil moisture fraction
            sm_frac_sector = 0.10 + ((ndwi_real_val - (-0.5)) / (0.5 - (-0.5))) * 0.80
            sm_frac_sector = min(1.0, max(0.0, sm_frac_sector))

            Dr  = round(TAW * (1.0 - sm_frac_sector), 2)
            ETc = round(ks * kc * daily_et0, 2)
            irr = round(Dr, 2) if Dr > RAW else 0.0

            cur.execute("""
                INSERT INTO telemetry_log (
                    timestamp, latitude, longitude, sector_row, sector_col,
                    ndvi, ndwi, ndwi_real, savi, lai, fcover, lst, lst_modis,
                    Kc, Ks, Dr, TAW, RAW, ETc, water_need,
                    air_temp, humidity, solar_rad, precip, soil_temp, soil_moisture, et0_deficit_7d
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                now_str, LAT, LON, row, col,
                ndvi, ndwi, ndwi_real_val, savi, lai, fcover, lst_api, modis_lst_val,
                kc, ks, Dr, TAW, RAW, ETc, irr,
                temp, humidity, solar_rad, precip_cur, soil_temp, soil_moist, deficit_7d
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
    print("  AquaVolt-AI SQLite Logger [Tier 1 Upgraded]")
    print(f"  Farm     : {FARM}")
    print(f"  Location : {LAT} N, {LON} W")
    print(f"  Database : {DB_PATH}")
    print(f"  Interval : Every {INTERVAL_SECONDS // 60} minutes")
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
