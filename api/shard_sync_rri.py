import os
import json
import urllib.request
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# RRI Field: 65 Hectares -> 6,500 sectors (10x10m grids)
RRI_CONFIG = {
    'id': 'rri_kala_shah_kaku',
    'name': 'RRI Kala Shah Kaku (65 Hectares)',
    'lat': 31.7240,
    'lon': 74.2693,
    'is_rice': True,
    'rows': 65,
    'cols': 100,
    'field_name': 'RRI Kala Shah Kaku (65ha Mega-Field)'
}

STANDARD_SCHEMA = [
    'timestamp', 'latitude', 'longitude', 'sector_row', 'sector_col',
    'ndvi', 'ndwi', 'lst', 'Kc', 'Ks', 'Dr', 'TAW', 'RAW', 'ETc',
    'water_need', 'air_temp', 'humidity', 'solar_rad', 'precip',
    'soil_temp', 'soil_moisture', 'methane_flux_kg_hr', 'field_name'
]

def safe_float(val, default=0.0):
    if val is None: return float(default)
    try:
        if pd.isna(val): return float(default)
        return float(val)
    except: return float(default)

def fetch_live_weather(lat, lon, start_date, end_date):
    url = (
        f'https://archive-api.open-meteo.com/v1/archive?'
        f'latitude={lat:.4f}&longitude={lon:.4f}&start_date={start_date}&end_date={end_date}&'
        f'hourly=temperature_2m,relative_humidity_2m,direct_normal_irradiance,precipitation,'
        f'soil_temperature_0_to_7cm,soil_moisture_0_to_7cm,et0_fao_evapotranspiration&timezone=UTC'
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'AquaVolt-ShardSync/2.0'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data.get('hourly', {})

def sync_rri_shard():
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    current_month_str = now_utc.strftime('%Y_%m')
    
    shard_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data_shard')
    os.makedirs(shard_dir, exist_ok=True)
    parquet_path = os.path.join(shard_dir, f'rri_telemetry_{current_month_str}.parquet')
    
    if os.path.exists(parquet_path):
        df = pd.read_parquet(parquet_path)
        df['dt'] = pd.to_datetime(df['timestamp'])
        latest_dt = df['dt'].max()
    else:
        df = pd.DataFrame(columns=STANDARD_SCHEMA)
        latest_dt = datetime(now_utc.year, now_utc.month, 1, 0, 0, 0)
    
    missing_hours = pd.date_range(start=latest_dt + pd.Timedelta(hours=1), end=now_utc, freq='h')
    
    if len(missing_hours) == 0:
        print(f'  [OK] {RRI_CONFIG["name"]}: Up to date.')
        return

    print(f'  [+] {RRI_CONFIG["name"]}: {len(missing_hours)} hrs missing. Processing 6,500 sectors...')
    start_d = missing_hours[0].strftime('%Y-%m-%d')
    end_d = missing_hours[-1].strftime('%Y-%m-%d')
    
    try: hourly = fetch_live_weather(RRI_CONFIG['lat'], RRI_CONFIG['lon'], start_d, end_d)
    except: return

    times = hourly.get('time', [])
    temps = hourly.get('temperature_2m', [])
    rhs = hourly.get('relative_humidity_2m', [])
    rads = hourly.get('direct_normal_irradiance', [])
    precips = hourly.get('precipitation', [])
    st_list = hourly.get('soil_temperature_0_to_7cm', [])
    sm_list = hourly.get('soil_moisture_0_to_7cm', [])
    et0_list = hourly.get('et0_fao_evapotranspiration', [])
    
    new_rows = []
    for i, t in enumerate(times):
        t_dt = pd.to_datetime(t)
        if t_dt not in missing_hours: continue
        t_str = t_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        t_air = safe_float(temps[i], 30.0)
        rh = safe_float(rhs[i], 60.0)
        sol_rad = safe_float(rads[i], 0.0)
        precip_mm = safe_float(precips[i], 0.0)
        soil_t = safe_float(st_list[i], 28.0)
        sm_real = safe_float(sm_list[i], 0.32)
        et0_real = safe_float(et0_list[i], 0.30)
        
        etc_real = round(max(0.0, et0_real * 1.15), 3)
        lst_real = round(soil_t + (sol_rad / 280.0) - (precip_mm * 0.5), 1)
        dr_real = round(max(0.0, (0.380 - sm_real) * 100.0), 1)
        water_need_real = 0.0 if sm_real >= 0.24 else round(etc_real * 1.8, 1)
        
        anaerobic_fraction = np.clip((sm_real - 0.220) / 0.160, 0.0, 1.0)
        flux_base = 0.0512 * anaerobic_fraction * (0.648 / 0.65) * np.exp(0.080 * (soil_t - 30.0))

        for r in range(RRI_CONFIG['rows']):
            for c in range(RRI_CONFIG['cols']):
                sec_lat = round(RRI_CONFIG['lat'] - 0.003 + r * 0.0001, 6)
                sec_lon = round(RRI_CONFIG['lon'] - 0.005 + c * 0.0001, 6)
                new_rows.append({
                    'timestamp': t_str, 'latitude': sec_lat, 'longitude': sec_lon,
                    'sector_row': r, 'sector_col': c, 'ndvi': 0.648, 'ndwi': 0.09,
                    'lst': lst_real, 'Kc': 1.15, 'Ks': 1.0, 'Dr': dr_real,
                    'TAW': 55.0, 'RAW': 27.5, 'ETc': etc_real, 'water_need': water_need_real,
                    'air_temp': round(t_air, 1), 'humidity': int(round(rh)),
                    'solar_rad': int(round(sol_rad)), 'precip': round(precip_mm, 1),
                    'soil_temp': round(soil_t, 1), 'soil_moisture': round(sm_real, 3),
                    'methane_flux_kg_hr': round(flux_base, 5), 'field_name': RRI_CONFIG['field_name']
                })

    if 'dt' in df.columns: df = df.drop(columns=['dt'])
    df_clean = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df_clean = df_clean[STANDARD_SCHEMA]
    df_clean.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
    print(f'  [OK] Appended {len(new_rows):,} rows -> Total {len(df_clean):,} rows.')

if __name__ == '__main__':
    sync_rri_shard()
