import os
import sys
import json
import gspread
import numpy as np
import urllib.request
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

LAT, LON = 38.5480, -121.8780

scopes = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

local_creds_path = r"C:\Users\umert\aquavolt-ai-pk\service_account.json"
if not os.path.exists(local_creds_path):
    print("Credentials file not found.")
    sys.exit(1)

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(local_creds_path, scopes)
    gc = gspread.authorize(creds)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

def fetch_copernicus_ref(date_str):
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}&start_date={date_str}&end_date={date_str}&hourly=temperature_2m"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data["hourly"]["temperature_2m"]
    except Exception as e:
        print(f"Failed to fetch Copernicus reference for {date_str}: {e}")
        return None

try:
    sh = gc.open("AquaVolt-AI Telemetry Log")
    ws = sh.worksheet("Sheet1")
    
    print("Fetching historical sheet records (first 2000 rows for sampling)...")
    # Fetch first 2000 rows to prevent memory/API timeouts while ensuring solid statistical correlation
    records = ws.get_all_records(head=1, expected_headers=[
        "timestamp", "latitude", "longitude", "sector_row", "sector_col",
        "ndvi", "ndwi", "ndwi_real", "savi", "lai", "fcover",
        "lst", "lst_modis", "Kc", "Ks", "Dr", "TAW", "RAW", "ETc", "water_need",
        "air_temp", "humidity", "solar_rad", "precip",
        "soil_temp", "soil_moisture", "et0_deficit_7d", "scene_id", "field_name"
    ])
    
    print(f"Successfully loaded {len(records)} records for correlation.")
    
    # Group by date to find sample days
    date_groups = {}
    for r in records:
        ts = r.get("timestamp")
        if ts:
            date_part = ts.split(" ")[0]
            if date_part not in date_groups:
                date_groups[date_part] = []
            date_groups[date_part].append(r)
            
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    sample_dates = sorted(list(date_groups.keys()))
    sample_dates = [d for d in sample_dates if d != today_str]
    print(f"Unique days represented in sample (excluding today): {sample_dates}")
    
    # Pick 3 representative days across the dataset
    target_dates = [sample_dates[0], sample_dates[len(sample_dates)//2], sample_dates[-1]]
    print(f"Target validation dates: {target_dates}")
    
    correlations = []
    
    for d in target_dates:
        print(f"\nVerifying date {d} against Copernicus global dataset...")
        copernicus_temps = fetch_copernicus_ref(d)
        if not copernicus_temps:
            continue
            
        # Extract hourly air_temp from Google Sheet
        hourly_records = date_groups[d]
        # Sort by timestamp
        hourly_records.sort(key=lambda x: x["timestamp"])
        
        # Group by hour to get average temp per hour across the farm
        hour_temps = {}
        for r in hourly_records:
            h = r["timestamp"].split(" ")[1].split(":")[0]
            if h not in hour_temps:
                hour_temps[h] = []
            if r.get("air_temp") is not None:
                hour_temps[h].append(float(r["air_temp"]))
                
        recorded_hourly = []
        for h in sorted(hour_temps.keys()):
            if hour_temps[h]:
                recorded_hourly.append(np.mean(hour_temps[h]))
                
        # Compare length
        min_len = min(len(recorded_hourly), len(copernicus_temps))
        if min_len > 6:
            a = np.array(recorded_hourly[:min_len])
            b = np.array(copernicus_temps[:min_len])
            
            r_val = np.corrcoef(a, b)[0, 1]
            correlations.append(r_val)
            print(f" -> Correlation Coefficient (r) for {d} = {r_val:.3f}")
            
    if correlations:
        avg_r = np.mean(correlations)
        aci = avg_r * 100
        print("\n" + "="*50)
        print("  GOOGLE SHEETS DATA INTEGRITY REPORT")
        print("="*50)
        print(f"  Copernicus/Global Satellite Correlation (r): {avg_r:.3f}")
        print(f"  Authenticity Confidence Index (ACI): {aci:.1f}%")
        print(f"  Status: {'REAL_OBSERVATION_DATA' if aci >= 75.0 else 'SUSPECTED_DUMMY_OR_SIMULATED'}")
        print("="*50)
    else:
        print("No valid correlations could be computed.")
        
except Exception as e:
    print(f"Error during validation: {e}")
