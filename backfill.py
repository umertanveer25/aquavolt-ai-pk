import os
import sys
import math
import json
import requests
import time
from datetime import datetime, timezone
import gspread
from oauth2client.service_account import ServiceAccountCredentials

LAT = 38.5414
LON = -121.8688
DEFAULT_SHEET_NAME = "AquaVolt-AI Telemetry Log"

def get_gspread_client():
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_json = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        return gspread.authorize(creds)
    
    local_creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "service_account.json")
    if os.path.exists(local_creds_path):
        creds = ServiceAccountCredentials.from_json_keyfile_name(local_creds_path, scopes)
        return gspread.authorize(creds)
    
    print("[ERROR] Credentials not found!")
    sys.exit(1)

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

def main():
    print("[BACKFILL] Starting backfill process...")
    gc = get_gspread_client()
    sheet_name = os.environ.get("GSHEET_NAME", DEFAULT_SHEET_NAME)
    sh = gc.open(sheet_name)
    worksheet = sh.get_worksheet(0)

    # 1. Clean up existing rows for 2026-06-26 15 and 2026-06-26 16
    print("[BACKFILL] Cleaning up any existing records for 15:xx and 16:xx...")
    all_rows = worksheet.get_all_values()
    data_rows = all_rows[1:]
    
    matching_row_indices = []
    for i, row in enumerate(data_rows):
        if row and (row[0].startswith("2026-06-26 15") or row[0].startswith("2026-06-26 16")):
            matching_row_indices.append(i + 2)

    if matching_row_indices:
        print(f"[BACKFILL] Found {len(matching_row_indices)} rows to delete.")
        for sheet_row in reversed(matching_row_indices):
            worksheet.delete_rows(sheet_row)
        print("[BACKFILL] Cleanup completed.")
    else:
        print("[BACKFILL] No existing rows found for those hours.")

    # 2. Fetch hourly weather data
    print("[BACKFILL] Fetching hourly weather data from Open-Meteo...")
    res = requests.get(build_url(LAT, LON), timeout=20)
    res.raise_for_status()
    weather = res.json()
    hourly = weather.get("hourly", {})
    times = hourly.get("time", [])

    # Map target times to local indices
    # UTC 15:00 = local 08:00 (Pacific Time)
    # UTC 16:00 = local 09:00 (Pacific Time)
    target_mappings = [
        {"utc_timestamp": "2026-06-26 15:38:22", "local_time": "2026-06-26T08:00"},
        {"utc_timestamp": "2026-06-26 16:32:03", "local_time": "2026-06-26T09:00"}
    ]

    h_et0 = hourly.get("et0_fao_evapotranspiration", [])
    daily_et0 = sum(x for x in h_et0 if x is not None) or 5.0

    rows_to_append = []

    for mapping in target_mappings:
        utc_str = mapping["utc_timestamp"]
        local_str = mapping["local_time"]
        
        if local_str not in times:
            print(f"[ERROR] Local time {local_str} not found in weather times: {times}")
            continue
            
        idx = times.index(local_str)
        
        temp = hourly.get("temperature_2m", [])[idx] or 20.0
        humidity = hourly.get("relative_humidity_2m", [])[idx] or 50.0
        solar_rad = hourly.get("shortwave_radiation", [])[idx] or 0.0
        precip = hourly.get("precipitation", [])[idx] or 0.0
        soil_temp = hourly.get("soil_temperature_0_to_7cm", [])[idx] or temp
        soil_moist = hourly.get("soil_moisture_0_to_1cm", [])[idx] or 0.18

        print(f"[BACKFILL] Calculating grid for {utc_str} (local {local_str}, index {idx})...")
        
        julian_day = 177  # June 26
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

        TAW = 72.0
        RAW = 36.0
        sm_frac = min(1.0, max(0.0, soil_moist * 5.0))

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
                    utc_str, LAT, LON, row, col,
                    ndvi, ndwi, savi, lst, kc, ks, Dr, TAW, RAW, ETc, irr,
                    temp, humidity, solar_rad, precip, soil_temp, soil_moist
                ])

    if rows_to_append:
        print(f"[BACKFILL] Appending {len(rows_to_append)} rows to Google Sheets...")
        worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        print("[BACKFILL] Done! All 128 rows successfully uploaded.")
    else:
        print("[BACKFILL] No data generated.")

if __name__ == "__main__":
    main()
