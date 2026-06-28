import functions_framework
import os
import math
import json
import requests
import socket
import urllib.request
import ssl
from datetime import datetime, timedelta, timezone

# DoH Monkeypatch for robust DNS resolution
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

import gspread
from oauth2client.service_account import ServiceAccountCredentials

LAT = 38.5480
LON = -121.8780
FARM_NAME = "UC Davis Russell Ranch"
DEFAULT_SHEET_NAME = "AquaVolt-AI Telemetry Log"

FIELDS = [
    {"name": "Field-A (Corn)",    "bbox": [-121.8750, 38.5430, -121.8690, 38.5465], "lat": 38.5448, "lon": -121.8720},
    {"name": "Field-B (Alfalfa)", "bbox": [-121.8825, 38.5430, -121.8755, 38.5465], "lat": 38.5448, "lon": -121.8790},
    {"name": "Field-C (Fallow)",  "bbox": [-121.8825, 38.5395, -121.8755, 38.5428], "lat": 38.5412, "lon": -121.8790},
    {"name": "Field-D (Tomato)",  "bbox": [-121.8750, 38.5395, -121.8690, 38.5428], "lat": 38.5412, "lon": -121.8720},
]

def get_gspread_client():
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        return gspread.authorize(creds)
    raise RuntimeError("GCP_SERVICE_ACCOUNT_KEY not set")

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

def compute_lai_fcover(ndvi):
    ndvi_c = max(0.15, min(0.92, ndvi))
    lai = max(0.0, -math.log(max(1e-6, (0.69 - ndvi_c) / 0.59)) / 0.91)
    lai = round(min(lai, 8.0), 4)
    fcover = round(1.0 - math.exp(-0.5 * lai), 4)
    return lai, fcover

@functions_framework.http
def aquavolt_sync(request):
    """GCP Cloud Function — triggered by Cloud Scheduler as HTTP POST."""
    print("=" * 60)
    print("  AquaVolt-AI GCP Cloud Failover")
    print(f"  Farm: {FARM_NAME}")
    print("=" * 60)

    try:
        gc = get_gspread_client()
        sheet_name = os.environ.get("GSHEET_NAME", DEFAULT_SHEET_NAME)
        sh = gc.open(sheet_name)
        worksheet = sh.get_worksheet(0)

        # Duplicate-hour guard
        now_utc = datetime.now(timezone.utc)
        current_hour_str = now_utc.strftime("%Y-%m-%d %H:")
        all_timestamps = worksheet.col_values(1)
        if len(all_timestamps) > 1:
            last_ts = all_timestamps[-1]
            if last_ts.startswith(current_hour_str):
                msg = f"[SKIP] Hour {now_utc.strftime('%Y-%m-%d %H:00')} already exists. GCP failover not needed."
                print(msg)
                return msg, 200

        print("[FAILOVER] GitHub Actions & local PC both missed this hour. GCP stepping in...")

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
        daily_et0  = sum(x for x in hourly.get("et0_fao_evapotranspiration", []) if x) or 5.0

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
        now_str = now_utc.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:00:00")
        rows_to_append = []

        for field in FIELDS:
            f_name = field["name"]
            if "Corn" in f_name:
                max_ndvi, min_ndvi = 0.50 + 0.40 * growth_multiplier, 0.20 + 0.15 * growth_multiplier
            elif "Alfalfa" in f_name:
                max_ndvi, min_ndvi = 0.40 + 0.35 * growth_multiplier, 0.15 + 0.15 * growth_multiplier
            elif "Tomato" in f_name:
                max_ndvi, min_ndvi = 0.45 + 0.35 * growth_multiplier, 0.18 + 0.15 * growth_multiplier
            else:
                max_ndvi, min_ndvi = 0.18 + 0.05 * growth_multiplier, 0.08 + 0.02 * growth_multiplier

            for row in range(8):
                for col in range(8):
                    dist = math.sqrt((row - 3.5)**2 + (col - 3.5)**2)
                    sp_val = 0.80 - dist * 0.10 + ((row * col) % 5 - 2) * 0.03
                    pos_factor = max(0.0, min(1.0, (sp_val - 0.25) / 0.60))
                    ndvi = round(max(0.08, min(0.90, min_ndvi + pos_factor * (max_ndvi - min_ndvi))), 4)
                    ndwi_real_val = round(max(-0.5, min(0.5, soil_moist * 2.0 - 0.5)), 4)
                    ndwi = ndwi_real_val
                    savi = round(ndvi * 1.2, 4)
                    lai, fcover = compute_lai_fcover(ndvi)
                    lst_api = round(soil_temp + (1.0 - ndvi) * 5.0, 1)
                    kc = round(min(1.20, max(0.15, 0.15 + 0.95 / (1.0 + math.exp(-12.0 * (ndvi - 0.4))))), 2)
                    if "Fallow" in f_name:
                        kc = round(kc * 0.3, 2)
                    ks = round(min(1.0, max(0.0, 1.0 if ndwi_real_val >= -0.1 else 1.0 + (ndwi_real_val + 0.1) * 2.0)), 2)
                    sm_frac = 0.10 + ((ndwi_real_val - (-0.5)) / 1.0) * 0.80
                    sm_frac = min(1.0, max(0.0, sm_frac))
                    Dr  = round(TAW * (1.0 - sm_frac), 2)
                    ETc = round(ks * kc * daily_et0, 2)
                    irr = round(Dr, 2) if Dr > RAW else 0.0
                    rows_to_append.append([
                        now_str, field["lat"], field["lon"], row, col,
                        ndvi, ndwi, ndwi_real_val, savi, lai, fcover,
                        lst_api, None,
                        kc, ks, Dr, TAW, RAW, ETc, irr,
                        temp, humidity, solar_rad, precip_cur,
                        soil_temp, soil_moist, 0.0, "GCP-Fallback", f_name
                    ])

        worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        msg = f"[OK] GCP pushed {len(rows_to_append)} rows for hour {now_str}"
        print(msg)
        return msg, 200

    except Exception as e:
        err = f"[ERROR] GCP failover failed: {e}"
        print(err)
        return err, 500
