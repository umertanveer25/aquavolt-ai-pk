"""
AquaVolt-AI — Google Sheets Hourly Data Logger (Multi-Field Upgrade)
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
import json
import requests
import socket
import urllib.request
import ssl
from datetime import datetime, timedelta, timezone

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

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    print("[ERROR] Missing packages. Run: pip install gspread oauth2client requests")
    sys.exit(1)

# True farm center coordinates for Russell Ranch
LAT = float(os.environ.get("AQUAVOLT_LAT", 38.5480))
LON = float(os.environ.get("AQUAVOLT_LON", -121.8780))
FARM_NAME = os.environ.get("AQUAVOLT_FARM", "UC Davis Russell Ranch")
DEFAULT_SHEET_NAME = "AquaVolt-AI Telemetry Log"

# Define 4 distinct fields with their crop types — matches UC_Davis_Russell_Ranch_EXACT_FIELDS.png
FIELDS = [
    {
        "name": "Field-A (Corn)",
        "bbox": [-121.8750, 38.5430, -121.8690, 38.5465],
        "lat": 38.5448,
        "lon": -121.8720
    },
    {
        "name": "Field-B (Alfalfa)",
        "bbox": [-121.8825, 38.5430, -121.8755, 38.5465],
        "lat": 38.5448,
        "lon": -121.8790
    },
    {
        "name": "Field-C (Fallow)",
        "bbox": [-121.8825, 38.5395, -121.8755, 38.5428],
        "lat": 38.5412,
        "lon": -121.8790
    },
    {
        "name": "Field-D (Tomato)",
        "bbox": [-121.8750, 38.5395, -121.8690, 38.5428],
        "lat": 38.5412,
        "lon": -121.8720
    }
]


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
        # A wider bounding box to search for items covering all fields
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

            return {"ndvi": ndvi.tolist(), "ndwi_real": ndwi_real.tolist()}

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


def main(push_to_sheets=True):
    print("=" * 70)
    print("  AquaVolt-AI Sheets Sync  [Tier 1: Multi-Field Upgrade]")
    print(f"  Farm: {FARM_NAME}  |  Coords: {LAT}N, {LON}W")
    print("=" * 70)

    gc = get_gspread_client()
    sheet_name = os.environ.get("GSHEET_NAME", DEFAULT_SHEET_NAME)
    print(f"[FILE] Accessing: '{sheet_name}'...")
    try:
        sh = gc.open(sheet_name)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"[ERROR] Spreadsheet '{sheet_name}' not found!")
        sys.exit(1)

    worksheet = sh.get_worksheet(0)

    # 29-column schema (added 'field_name')
    headers = [
        "timestamp", "latitude", "longitude", "sector_row", "sector_col",
        "ndvi", "ndwi", "ndwi_real", "savi", "lai", "fcover",
        "lst", "lst_modis", "Kc", "Ks", "Dr", "TAW", "RAW", "ETc", "water_need",
        "air_temp", "humidity", "solar_rad", "precip",
        "soil_temp", "soil_moisture", "et0_deficit_7d", "scene_id", "field_name"
    ]
    existing = worksheet.row_values(1)
    if not existing or existing != headers:
        print("[HEADER] Updating sheet headers for 29-column schema...")
        worksheet.clear()
        worksheet.append_row(headers)

    # Duplicate-hour guard
    now_utc = datetime.now(timezone.utc)
    current_hour_str = now_utc.strftime("%Y-%m-%d %H:")
    all_timestamps = worksheet.col_values(1)
    if len(all_timestamps) > 1:
        last_ts = all_timestamps[-1]
        if last_ts.startswith(current_hour_str):
            print(f"[SKIP] Data for UTC hour {now_utc.strftime('%Y-%m-%d %H:00')} already exists. Skipping.")
            if not push_to_sheets:
                return worksheet, []
            sys.exit(0)

    print("[API] Fetching weather from Open-Meteo...")
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
    print(f"  Temp: {temp}C | Soil Moist: {soil_moist*100:.1f}% | ET0: {daily_et0:.2f} mm/day")

    print("\n[TIER 1] Fetching satellite & forecast data...")
    latest_item = get_latest_sentinel_item(LAT, LON)
    scene_id = latest_item.id if latest_item else "Fallback"
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

    TAW = 72.0
    RAW = 36.0
    now_str = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:00:00")
    rows_to_append = []

    # Loop through each field and generate 64 rows of data per field (total 256 rows)
    for field in FIELDS:
        f_name = field["name"]
        print(f"\n[PIML] Processing field: {f_name}...")
        
        # Crop Sentinel-2 data for this specific field's bounding box
        field_sentinel = fetch_field_indices(latest_item, field["bbox"]) if latest_item else None
        
        # NDVI bounds adjusted dynamically based on crop characteristics
        if "Corn" in f_name:
            # Fully green, heavy water demand
            max_ndvi = 0.50 + 0.40 * growth_multiplier
            min_ndvi = 0.20 + 0.15 * growth_multiplier
        elif "Alfalfa" in f_name:
            # Moderate green
            max_ndvi = 0.40 + 0.35 * growth_multiplier
            min_ndvi = 0.15 + 0.15 * growth_multiplier
        elif "Tomato" in f_name:
            # Row crop, mid-high green
            max_ndvi = 0.45 + 0.35 * growth_multiplier
            min_ndvi = 0.18 + 0.15 * growth_multiplier
        else: # Fallow
            # Bare soil
            max_ndvi = 0.18 + 0.05 * growth_multiplier
            min_ndvi = 0.08 + 0.02 * growth_multiplier

        for row in range(8):
            for col in range(8):
                dist = math.sqrt((row - 3.5)**2 + (col - 3.5)**2)
                sp_val = 0.80 - dist * 0.10 + ((row * col) % 5 - 2) * 0.03
                pos_factor = max(0.0, min(1.0, (sp_val - 0.25) / 0.60))

                if field_sentinel:
                    ndvi = round(max(0.08, min(0.90, field_sentinel["ndvi"][row][col] + (pos_factor - 0.5) * 0.24)), 4)
                    ndwi_real_val = round(float(field_sentinel["ndwi_real"][row][col]), 4)
                else:
                    ndvi = round(max(0.08, min(0.90, min_ndvi + pos_factor * (max_ndvi - min_ndvi))), 4)
                    ndwi_real_val = round(max(-0.5, min(0.5, soil_moist * 2.0 - 0.5)), 4)

                ndwi = round(max(-0.5, min(0.5, soil_moist * 2.0 - 0.5)), 4)
                savi = round(ndvi * 1.2, 4)
                lai, fcover = compute_lai_fcover(ndvi)
                lst_api = round(soil_temp + (1.0 - ndvi) * 5.0, 1)

                kc = round(min(1.20, max(0.15, 0.15 + 0.95 / (1.0 + math.exp(-12.0 * (ndvi - 0.4))))), 2)
                
                # Apply crop-specific parameters
                if "Fallow" in f_name:
                    kc = round(kc * 0.3, 2)  # crop demand is minimal for fallow field

                ks = round(min(1.0, max(0.0, 1.0 if ndwi_real_val >= -0.1 else 1.0 + (ndwi_real_val + 0.1) * 2.0)), 2)
                
                sm_frac_sector = 0.10 + ((ndwi_real_val - (-0.5)) / (0.5 - (-0.5))) * 0.80
                sm_frac_sector = min(1.0, max(0.0, sm_frac_sector))
                Dr  = round(TAW * (1.0 - sm_frac_sector), 2)
                ETc = round(ks * kc * daily_et0, 2)
                irr = round(Dr, 2) if Dr > RAW else 0.0

                rows_to_append.append([
                    now_str, field["lat"], field["lon"], row, col,
                    ndvi, ndwi, ndwi_real_val, savi, lai, fcover,
                    lst_api, modis_lst_val,
                    kc, ks, Dr, TAW, RAW, ETc, irr,
                    temp, humidity, solar_rad, precip_cur,
                    soil_temp, soil_moist, deficit_7d, scene_id, f_name
                ])

    if push_to_sheets:
        print(f"\n[UPLOAD] Writing {len(rows_to_append)} records...")
        worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        print(f"[OK] Done.")
        
    # --- GENERATE LIVE GITHUB DASHBOARD ---
    print("\n[DASHBOARD] Generating live GitHub markdown dashboard...")
    try:
        field_summaries = {}
        for row in rows_to_append:
            fname = row[28]  # field_name
            if fname not in field_summaries:
                field_summaries[fname] = {"ndvi": [], "ndwi": [], "etc": [], "irr": []}
            field_summaries[fname]["ndvi"].append(row[5])
            field_summaries[fname]["ndwi"].append(row[7])
            field_summaries[fname]["etc"].append(row[18])
            field_summaries[fname]["irr"].append(row[19])
        
        md_content = f"# 📡 AquaVolt-AI Live Telemetry\n\n"
        md_content += f"**Latest Update:** `{now_str} UTC`\n"
        md_content += f"> This dashboard updates automatically every hour via GitHub Actions.\n\n"
        
        md_content += f"### ⛅ Current Weather (Russell Ranch)\n\n"
        md_content += f"- **Air Temp:** {temp}°C\n"
        md_content += f"- **Humidity:** {humidity}%\n"
        md_content += f"- **Solar Radiation:** {solar_rad} W/m²\n"
        md_content += f"- **Soil Moisture (Proxy):** {soil_moist*100:.1f}%\n"
        md_content += f"- **Reference ET₀ (24h):** {daily_et0:.2f} mm\n\n"
        
        md_content += f"### 🌱 Field Averages (Current Hour)\n\n"
        md_content += f"| Field Name | Avg NDVI | Avg NDWI | Avg ETc (mm/hr) | Avg Water Deficit (mm) |\n"
        md_content += f"|---|---|---|---|---|\n"
        
        for fname, data in field_summaries.items():
            avg_ndvi = sum(data["ndvi"]) / len(data["ndvi"])
            avg_ndwi = sum(data["ndwi"]) / len(data["ndwi"])
            avg_etc = sum(data["etc"]) / len(data["etc"])
            avg_irr = sum(data["irr"]) / len(data["irr"])
            md_content += f"| **{fname}** | {avg_ndvi:.3f} | {avg_ndwi:.3f} | {avg_etc:.2f} | **{avg_irr:.2f}** |\n"
            
        md_content += f"\n---\n*Powered by Python, Planetary Computer STAC APIs, and FAO-56 Thermodynamics.*\n"
        
        # Inject into README.md
        readme_path = "README.md"
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_text = f.read()
            
            import re
            pattern = r"(<!-- LIVE_TELEMETRY_START -->)(.*?)(<!-- LIVE_TELEMETRY_END -->)"
            replacement = r"\1\n" + md_content + r"\n\3"
            new_readme = re.sub(pattern, replacement, readme_text, flags=re.DOTALL)
            
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(new_readme)
            print("[OK] README.md live dashboard updated successfully.")
        else:
            print("[ERROR] README.md not found.")
            
    except Exception as e:
        print(f"[ERROR] Failed to generate dashboard: {e}")

    return worksheet, rows_to_append

if __name__ == "__main__":
    main()
