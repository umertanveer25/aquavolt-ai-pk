"""
AquaVolt-AI — Hourly Background Data Logger
============================================
Runs silently in the background.
Every 60 minutes → fetches live weather from Open-Meteo
                 → computes PIML metrics for all 64 grid sectors
                 → stores records to aquavolt_data.db

Usage:
    python aquavolt_logger.py

Leave this running in the background. It will log data every hour automatically.
Press Ctrl+C to stop.
"""

import requests
import sqlite3
import math
import time
import os
from datetime import datetime

# ── Farm Location ────────────────────────────────────────────
LAT  = float(os.environ.get("AQUAVOLT_LAT", 38.5414))   # UC Davis Russell Ranch, California
LON  = float(os.environ.get("AQUAVOLT_LON", -121.8688))
FARM = os.environ.get("AQUAVOLT_FARM", "UC Davis Russell Ranch, CA")

# ── Logging interval (seconds) ───────────────────────────────
INTERVAL_SECONDS = 3600  # 1 hour

# ── Database path ─────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aquavolt_data.db")


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
    conn.commit()
    conn.close()


def fetch_and_store():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{now_str}] Fetching live data from Open-Meteo...")

    try:
        r = requests.get(build_url(LAT, LON), timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ❌ API Error: {e} — skipping this cycle.")
        return 0

    current = data.get("current", {})
    hourly  = data.get("hourly",  {})

    temp        = current.get("temperature_2m")        or 20.0
    humidity    = current.get("relative_humidity_2m")  or 50.0
    wind        = current.get("wind_speed_10m")        or 2.0
    precip      = current.get("precipitation")         or 0.0
    solar_rad   = current.get("shortwave_radiation")   or 0.0
    is_day      = current.get("is_day", 1)
    soil_temp   = current.get("soil_temperature_0_to_7cm") or temp
    soil_moist  = current.get("soil_moisture_0_to_1cm")    or 0.18
    api_time    = current.get("time", "N/A")

    h_et0    = hourly.get("et0_fao_evapotranspiration", [])
    h_precip = hourly.get("precipitation", [])
    daily_et0    = sum(x for x in h_et0    if x is not None) or 5.0
    daily_precip = sum(x for x in h_precip if x is not None) or 0.0

    print(f"  📡 API Time   : {api_time}")
    print(f"  🌡️  Temp       : {temp}°C")
    print(f"  💧 Humidity   : {humidity}%")
    print(f"  ☀️  Solar      : {solar_rad} W/m²  ({'Day' if is_day else 'Night'})")
    print(f"  🌱 Soil Temp  : {soil_temp}°C")
    print(f"  💦 Soil Moist : {soil_moist*100:.1f}%")
    print(f"  🌿 Daily ET₀  : {daily_et0:.2f} mm/day")
    print(f"  🌧️  Precip     : {daily_precip:.2f} mm")

    # ── Soil water balance constants ──────────────────────────
    TAW = 72.0   # Total Available Water (mm)
    RAW = 36.0   # Readily Available Water (mm)
    sm_frac = min(1.0, max(0.0, soil_moist * 5.0))

    # ── Dynamic Crop Growth & NDVI baseline (season & temperature driven) ──
    julian_day = datetime.now().timetuple().tm_yday
    delta = 0.409 * math.sin((2 * math.pi / 365) * julian_day - 1.39)
    lat_rad = math.radians(LAT)
    val_cos = -math.tan(lat_rad) * math.tan(delta)
    val_cos = max(-1.0, min(1.0, val_cos))
    omega_s = math.acos(val_cos)
    day_length = (24.0 / math.pi) * omega_s
    season_factor = max(0.0, min(1.0, (day_length - 8.0) / 8.0))

    # Temperature Factor (bell curve centered at 24°C)
    optimal_temp = 24.0
    temp_factor = math.exp(-0.02 * ((temp - optimal_temp) ** 2))

    # Crop growth dynamic multiplier (ranges from 0.0 to 1.0)
    growth_multiplier = season_factor * temp_factor

    max_ndvi = 0.35 + 0.50 * growth_multiplier
    min_ndvi = 0.15 + 0.15 * growth_multiplier

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    count = 0

    for row in range(8):
        for col in range(8):
            dist = math.sqrt((row - 3.5)**2 + (col - 3.5)**2)
            val = 0.80 - (dist * 0.10)
            val += ((row * col) % 5 - 2) * 0.03
            
            # Scale based on spatial position and seasonal growth
            pos_factor = (val - 0.25) / 0.60
            pos_factor = max(0.0, min(1.0, pos_factor))
            ndvi = round(min_ndvi + pos_factor * (max_ndvi - min_ndvi), 4)
            ndvi = max(0.15, min(0.90, ndvi))

            # ── Derived indices ───────────────────────────────
            ndwi = round(max(-0.5, min(0.5, soil_moist * 2.0 - 0.5)), 4)
            savi = round(ndvi * 1.2, 4)
            lst  = round(soil_temp + (1.0 - ndvi) * 5.0, 1)

            # ── PIML Kc/Ks ───────────────────────────────────
            kc = round(min(1.20, max(0.15,
                       0.15 + 0.95 / (1.0 + math.exp(-12.0 * (ndvi - 0.4))))), 2)
            ks = round(min(1.0, max(0.0,
                       1.0 if ndwi >= -0.1 else 1.0 + (ndwi + 0.1) * 2.0)), 2)

            # ── Water balance ─────────────────────────────────
            Dr  = round(TAW * (1.0 - sm_frac), 2)
            ETc = round(ks * kc * daily_et0, 2)
            irr = round(Dr, 2) if Dr > RAW else 0.0

            cur.execute("""
                INSERT INTO telemetry_log VALUES
                (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                now_str, LAT, LON, row, col,
                ndvi, ndwi, savi, lst,
                kc, ks, Dr, TAW, RAW, ETc, irr,
                temp, humidity, solar_rad, precip,
                soil_temp, soil_moist
            ))
            count += 1

    conn.commit()

    # ── Summary stats ─────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM telemetry_log")
    total = cur.fetchone()[0]
    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM telemetry_log")
    first, last = cur.fetchone()
    cur.execute("SELECT AVG(ndvi), AVG(ETc), AVG(water_need) FROM telemetry_log")
    avg_ndvi, avg_etc, avg_irr = cur.fetchone()
    conn.close()

    print(f"\n  ✅ Written     : {count} sector records")
    print(f"  📦 Total in DB : {total} records")
    print(f"  🗓️  First record: {first}")
    print(f"  🗓️  Last record : {last}")
    print(f"  📊 Avg NDVI    : {avg_ndvi:.4f}")
    print(f"  📊 Avg ETc     : {avg_etc:.2f} mm/day")
    print(f"  📊 Avg Irrig   : {avg_irr:.2f} mm")
    return count


def main():
    print("=" * 55)
    print("  AquaVolt-AI Hourly Background Logger")
    print(f"  Farm   : {FARM}")
    print(f"  Coords : {LAT}°N, {LON}°W")
    print(f"  DB     : {DB_PATH}")
    print(f"  Interval: Every {INTERVAL_SECONDS // 60} minutes")
    print("=" * 55)
    print("  Press Ctrl+C to stop.\n")

    init_db()

    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'─'*55}")
        print(f"  Cycle #{cycle}")
        fetch_and_store()
        next_time = datetime.fromtimestamp(time.time() + INTERVAL_SECONDS)
        print(f"\n  ⏰ Next sync at: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
