"""
AquaVolt-AI — Google Sheets Hourly Data Logger (Tier 1 Upgraded)
=================================================================
Tier 1 Real-Time Integrations:
  1. Sentinel-2 NDVI + Real NDWI (B03/B08)
  2. MODIS MOD11A1 Daily LST (1km) via Microsoft Planetary Computer
  3. Open-Meteo 16-Day Irrigation Forecast (7-day deficit)
  4. Empirical LAI & FCOVER from NDVI (Baret et al., Beer-Lambert)
"""

import os
import sys
import math
import json
import requests
from datetime import datetime, timedelta, timezone

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    print("[ERROR] Missing packages. Run: pip install gspread oauth2client requests")
    sys.exit(1)

LAT = float(os.environ.get("AQUAVOLT_LAT", 38.5414))
LON = float(os.environ.get("AQUAVOLT_LON", -121.8688))
FARM_NAME = os.environ.get("AQUAVOLT_FARM", "UC Davis Russell Ranch")
DEFAULT_SHEET_NAME = "AquaVolt-AI Telemetry Log"


def get_gspread_client():
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_json = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
            return gspread.authorize(creds)
        except Exception as e:
            print(f"[ERROR] GCP secret error: {e}")
            sys.exit(1)

    local_creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "service_account.json")
    if not os.path.exists(local_creds_path):
        import glob
        matches = glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "aquavolt-ai-*.json"))
        if matches:
            local_creds_path = matches[0]

    if os.path.exists(local_creds_path):
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(local_creds_path, scopes)
            return gspread.authorize(creds)
        except Exception as e:
            print(f"[ERROR] Local creds error: {e}")
            sys.exit(1)

    print("[ERROR] No Google credentials found.")
    sys.exit(1)


# TIER 1 — Sentinel-2 NDVI + Real NDWI (B03)
def fetch_sentinel2_indices(lat, lon):
    print("[SATELLITE] Connecting to Planetary Computer STAC API...")
    try:
        import pystac_client
        import planetary_computer
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.warp import transform_bounds
        import certifi
        import numpy as np
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
                print("[SATELLITE WARNING] No cloud-free scenes found. Falling back.")
                return None

        latest_item = items[0]
        print(f"[SATELLITE] Scene: {latest_item.id} | {latest_item.datetime.date()}")

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

            bad_mask = (b04 == 0) | (b08 == 0)
            ndvi = safe_index(b08, b04, bad_mask)
            ndwi_real = safe_index(b03, b08, (b03 == 0) | (b08 == 0))

            print(f"[SATELLITE] Avg NDVI={float(np.nanmean(ndvi)):.3f} | Avg NDWI={float(np.nanmean(ndwi_real)):.3f}")
            return {"ndvi": ndvi.tolist(), "ndwi_real": ndwi_real.tolist()}

    except Exception as e:
        print(f"[SATELLITE WARNING] {e}. Falling back.")
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
        start_date = end_date - timedelta(days=8)
        time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        bbox = [lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05]

        search = catalog.search(collections=["modis-11A1-061"], bbox=bbox, datetime=time_range)
        items = search.item_collection()
        if not items:
            print("[MODIS WARNING] No MODIS LST data found.")
            return None

        latest_item = items[0]
        print(f"[MODIS] LST scene: {latest_item.id} | {latest_item.datetime.date()}")

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


# TIER 1 — Empirical LAI & FCOVER (Copernicus-compatible)
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


def main():
    print("=" * 65)
    print("  AquaVolt-AI Sheets Sync  [Tier 1: S2-NDWI, MODIS-LST, Forecast]")
    print(f"  Farm: {FARM_NAME}  |  Coords: {LAT}N, {LON}W")
    print("=" * 65)

    gc = get_gspread_client()
    sheet_name = os.environ.get("GSHEET_NAME", DEFAULT_SHEET_NAME)
    print(f"[FILE] Accessing: '{sheet_name}'...")
    try:
        sh = gc.open(sheet_name)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"[ERROR] Spreadsheet '{sheet_name}' not found!")
        sys.exit(1)

    worksheet = sh.get_worksheet(0)

    headers = [
        "timestamp", "latitude", "longitude", "sector_row", "sector_col",
        "ndvi", "ndwi", "ndwi_real", "savi", "lai", "fcover",
        "lst", "lst_modis", "Kc", "Ks", "Dr", "TAW", "RAW", "ETc", "water_need",
        "air_temp", "humidity", "solar_rad", "precip",
        "soil_temp", "soil_moisture", "et0_deficit_7d"
    ]
    existing = worksheet.row_values(1)
    if not existing or existing != headers:
        print("[HEADER] Updating sheet headers for Tier 1 columns...")
        worksheet.clear()
        worksheet.append_row(headers)

    # Duplicate-hour guard: skip if this UTC hour already has data
    now_utc = datetime.now(timezone.utc)
    current_hour_str = now_utc.strftime("%Y-%m-%d %H:")
    all_timestamps = worksheet.col_values(1)
    if len(all_timestamps) > 1:
        last_ts = all_timestamps[-1]
        if last_ts.startswith(current_hour_str):
            print(f"[SKIP] Data for UTC hour {now_utc.strftime('%Y-%m-%d %H:00')} already exists. Skipping to prevent duplicates.")
            sys.exit(0)

    print("[API] Fetching current weather from Open-Meteo...")
    r = requests.get(build_url(LAT, LON), timeout=20)
    r.raise_for_status()
    weather = r.json()

    current = weather.get("current", {})
    hourly  = weather.get("hourly", {})
    temp       = current.get("temperature_2m")            or 20.0
    humidity   = current.get("relative_humidity_2m")      or 50.0
    precip_cur = current.get("precipitation")             or 0.0
    solar_rad  = current.get("shortwave_radiation")       or 0.0
    soil_temp  = current.get("soil_temperature_0_to_7cm") or temp
    soil_moist = current.get("soil_moisture_0_to_1cm")    or 0.18
    daily_et0    = sum(x for x in hourly.get("et0_fao_evapotranspiration", []) if x) or 5.0
    daily_precip = sum(x for x in hourly.get("precipitation", []) if x) or 0.0
    print(f"  Temp: {temp}C | Soil Moist: {soil_moist*100:.1f}% | ET0: {daily_et0:.2f} mm/day")

    print("\n[TIER 1] Fetching satellite & forecast data...")
    sentinel_data = fetch_sentinel2_indices(LAT, LON)
    modis_lst_val = fetch_modis_lst(LAT, LON)
    deficit_7d    = fetch_open_meteo_forecast(LAT, LON)

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
    # Normalize to top of the hour for clean chronological hourly logging
    now_str = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:00:00")
    rows_to_append = []

    print("[PIML] Computing 64-sector metrics...")
    for row in range(8):
        for col in range(8):
            dist = math.sqrt((row - 3.5)**2 + (col - 3.5)**2)
            sp_val = 0.80 - dist * 0.10 + ((row * col) % 5 - 2) * 0.03
            pos_factor = max(0.0, min(1.0, (sp_val - 0.25) / 0.60))

            if sentinel_data:
                ndvi = round(max(0.15, min(0.90, sentinel_data["ndvi"][row][col] + (pos_factor - 0.5) * 0.24)), 4)
                ndwi_real_val = round(float(sentinel_data["ndwi_real"][row][col]), 4)
            else:
                ndvi = round(max(0.15, min(0.90, min_ndvi + pos_factor * (max_ndvi - min_ndvi))), 4)
                ndwi_real_val = round(max(-0.5, min(0.5, soil_moist * 2.0 - 0.5)), 4)

            ndwi = round(max(-0.5, min(0.5, soil_moist * 2.0 - 0.5)), 4)
            savi = round(ndvi * 1.2, 4)
            lai, fcover = compute_lai_fcover(ndvi)
            lst_api = round(soil_temp + (1.0 - ndvi) * 5.0, 1)

            kc = round(min(1.20, max(0.15, 0.15 + 0.95 / (1.0 + math.exp(-12.0 * (ndvi - 0.4))))), 2)
            ks = round(min(1.0, max(0.0, 1.0 if ndwi_real_val >= -0.1 else 1.0 + (ndwi_real_val + 0.1) * 2.0)), 2)
            Dr  = round(TAW * (1.0 - sm_frac), 2)
            ETc = round(ks * kc * daily_et0, 2)
            irr = round(Dr, 2) if Dr > RAW else 0.0

            rows_to_append.append([
                now_str, LAT, LON, row, col,
                ndvi, ndwi, ndwi_real_val, savi, lai, fcover,
                lst_api, modis_lst_val,
                kc, ks, Dr, TAW, RAW, ETc, irr,
                temp, humidity, solar_rad, precip_cur,
                soil_temp, soil_moist, deficit_7d
            ])

    print(f"[UPLOAD] Writing {len(rows_to_append)} records...")
    worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
    print(f"[OK] Done.")
    print(f"  NDWI src : {'Real Sentinel-2 B03' if sentinel_data else 'Soil moisture proxy'}")
    print(f"  LST src  : {'Real MODIS MOD11A1' if modis_lst_val else 'API soil temp estimate'}")
    print(f"  7d deficit: {deficit_7d:.1f} mm  |  New columns: ndwi_real, lai, fcover, lst_modis, et0_deficit_7d")


if __name__ == "__main__":
    main()
