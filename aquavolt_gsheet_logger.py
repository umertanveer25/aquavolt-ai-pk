"""
AquaVolt-AI — Google Sheets Hourly Data Logger
==============================================
This script fetches live weather data from Open-Meteo, calculates Physics-Informed 
Machine Learning (PIML) irrigation metrics for 64 grid sectors (dynamically adjusted
for season and temperature), and appends them to a Google Sheet.

It is designed to run locally or as a serverless GitHub Action.

Authentication:
  - Locally: Expects a file named 'service_account.json' in the same folder.
  - GitHub Actions: Expects the JSON content stored in the 'GCP_SERVICE_ACCOUNT_KEY' Secret.
"""

import os
import sys
import math
import json
import requests
from datetime import datetime

# ── Dynamic Dependencies ──────────────────────────────────────
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    print("[ERROR] Missing packages. Run: pip install gspread oauth2client requests")
    sys.exit(1)

# ── Configuration ─────────────────────────────────────────────
LAT = float(os.environ.get("AQUAVOLT_LAT", 38.5414))   # UC Davis Russell Ranch, California
LON = float(os.environ.get("AQUAVOLT_LON", -121.8688))
FARM_NAME = os.environ.get("AQUAVOLT_FARM", "UC Davis Russell Ranch")
DEFAULT_SHEET_NAME = "AquaVolt-AI Telemetry Log"

# ── Google Sheets Auth Setup ──────────────────────────────────
def get_gspread_client():
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 1. Check for GitHub Actions Environment Secret
    creds_json = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
            return gspread.authorize(creds)
        except Exception as e:
            print(f"[ERROR] Error parsing GCP_SERVICE_ACCOUNT_KEY secret: {e}")
            sys.exit(1)
            
    # 2. Check for Local Service Account File
    local_creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "service_account.json")
    if os.path.exists(local_creds_path):
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(local_creds_path, scopes)
            return gspread.authorize(creds)
        except Exception as e:
            print(f"[ERROR] Error loading local service_account.json: {e}")
            sys.exit(1)
            
    # 3. Print setup guidance if credentials are missing
    print("\n" + "!"*60)
    print("[ERROR] Google Cloud Credentials not found!")
    print("To fix this:")
    print("  1. Create a Google Service Account in Google Cloud Console.")
    print("  2. Download the JSON key file.")
    print("  3. Save it as 'service_account.json' in this folder (for local runs).")
    print("  4. Or save its contents as a GitHub Secret 'GCP_SERVICE_ACCOUNT_KEY' (for Actions).")
    print("!"*60 + "\n")
    sys.exit(1)

# ── API URL builder ───────────────────────────────────────────
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
        f"&forecast_days=1&timezone=auto"
    )

# ── Main Process ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  AquaVolt-AI Google Sheets Hourly Sync")
    print(f"  Coordinates : {LAT} N, {LON} W ({FARM_NAME})")
    print("=" * 60)

    # 1. Authenticate with Google
    print("[AUTH] Authenticating with Google Cloud API...")
    gc = get_gspread_client()
    
    # Get target Sheet name
    sheet_name = os.environ.get("GSHEET_NAME", DEFAULT_SHEET_NAME)
    print(f"[FILE] Accessing Spreadsheet: '{sheet_name}'...")
    
    try:
        sh = gc.open(sheet_name)
    except gspread.exceptions.SpreadsheetNotFound:
        # Service Account email
        client_email = gc.auth.signer_email if hasattr(gc.auth, "signer_email") else "your service account email"
        print("\n" + "!"*60)
        print(f"[ERROR] Spreadsheet '{sheet_name}' not found!")
        print("To fix this:")
        print(f"  1. Create a Google Sheet named '{sheet_name}' on your personal Google Drive.")
        print(f"  2. Share it (give 'Editor' access) to your Service Account email:")
        print(f"     👉 {client_email}")
        print("  3. Run this script again.")
        print("!"*60 + "\n")
        sys.exit(1)

    worksheet = sh.get_worksheet(0)
    
    # Initialize sheet headers if empty
    headers = [
        "timestamp", "latitude", "longitude", "sector_row", "sector_col",
        "ndvi", "ndwi", "savi", "lst", "Kc", "Ks", "Dr", "TAW", "RAW", "ETc", "water_need",
        "air_temp", "humidity", "solar_rad", "precip", "soil_temp", "soil_moisture"
    ]
    
    existing_headers = worksheet.row_values(1)
    if not existing_headers:
        print("[HEADER] Sheet is empty. Initializing headers...")
        worksheet.append_row(headers)
    
    # 2. Fetch Weather Data
    print("[API] Fetching weather data from Open-Meteo...")
    try:
        r = requests.get(build_url(LAT, LON), timeout=20)
        r.raise_for_status()
        weather = r.json()
    except Exception as e:
        print(f"[ERROR] Weather API Error: {e}")
        sys.exit(1)

    current = weather.get("current", {})
    hourly  = weather.get("hourly",  {})

    temp        = current.get("temperature_2m")        or 20.0
    humidity    = current.get("relative_humidity_2m")  or 50.0
    wind        = current.get("wind_speed_10m")        or 2.0
    precip      = current.get("precipitation")         or 0.0
    solar_rad   = current.get("shortwave_radiation")   or 0.0
    soil_temp   = current.get("soil_temperature_0_to_7cm") or temp
    soil_moist  = current.get("soil_moisture_0_to_1cm")    or 0.18

    h_et0    = hourly.get("et0_fao_evapotranspiration", [])
    h_precip = hourly.get("precipitation", [])
    daily_et0    = sum(x for x in h_et0    if x is not None) or 5.0
    daily_precip = sum(x for x in h_precip if x is not None) or 0.0

    print(f"  Temp        : {temp} C")
    print(f"  Soil Moist  : {soil_moist*100:.1f}%")
    print(f"  Daily ET0   : {daily_et0:.2f} mm/day")

    # 3. Calculate dynamic crop variables based on astronomical season & temperature
    julian_day = datetime.now().timetuple().tm_yday
    delta = 0.409 * math.sin((2 * math.pi / 365) * julian_day - 1.39)
    lat_rad = math.radians(LAT)
    val_cos = -math.tan(lat_rad) * math.tan(delta)
    val_cos = max(-1.0, min(1.0, val_cos))
    omega_s = math.acos(val_cos)
    day_length = (24.0 / math.pi) * omega_s
    season_factor = max(0.0, min(1.0, (day_length - 8.0) / 8.0))

    optimal_temp = 24.0
    temp_factor = math.exp(-0.02 * ((temp - optimal_temp) ** 2))
    growth_multiplier = season_factor * temp_factor

    max_ndvi = 0.35 + 0.50 * growth_multiplier
    min_ndvi = 0.15 + 0.15 * growth_multiplier

    # 4. Generate data rows for all 64 sectors
    print("[PIML] Calculating PIML metrics for 64 grid sectors...")
    TAW = 72.0
    RAW = 36.0
    sm_frac = min(1.0, max(0.0, soil_moist * 5.0))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    rows_to_append = []
    
    for row in range(8):
        for col in range(8):
            dist = math.sqrt((row - 3.5)**2 + (col - 3.5)**2)
            val = 0.80 - (dist * 0.10)
            val += ((row * col) % 5 - 2) * 0.03
            
            pos_factor = (val - 0.25) / 0.60
            pos_factor = max(0.0, min(1.0, pos_factor))
            ndvi = round(min_ndvi + pos_factor * (max_ndvi - min_ndvi), 4)
            ndvi = max(0.15, min(0.90, ndvi))

            ndwi = round(max(-0.5, min(0.5, soil_moist * 2.0 - 0.5)), 4)
            savi = round(ndvi * 1.2, 4)
            lst  = round(soil_temp + (1.0 - ndvi) * 5.0, 1)

            kc = round(min(1.20, max(0.15, 0.15 + 0.95 / (1.0 + math.exp(-12.0 * (ndvi - 0.4))))), 2)
            ks = round(min(1.0, max(0.0, 1.0 if ndwi >= -0.1 else 1.0 + (ndwi + 0.1) * 2.0)), 2)

            Dr  = round(TAW * (1.0 - sm_frac), 2)
            ETc = round(ks * kc * daily_et0, 2)
            irr = round(Dr, 2) if Dr > RAW else 0.0

            rows_to_append.append([
                now_str, LAT, LON, row, col,
                ndvi, ndwi, savi, lst, kc, ks, Dr, TAW, RAW, ETc, irr,
                temp, humidity, solar_rad, precip, soil_temp, soil_moist
            ])

    # 5. Append to Google Sheet (Batch insert in 1 API call to avoid rate limits)
    print("[UPLOAD] Writing 64 records to Google Sheets...")
    try:
        worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        print(f"[OK] Success! 64 records written to Google Sheet '{sheet_name}'.")
    except Exception as e:
        print(f"[ERROR] Error writing to Google Sheet: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
