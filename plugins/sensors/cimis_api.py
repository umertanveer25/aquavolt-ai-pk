"""
CIMIS API Ground-Truth Plugin
=============================
Pulls real-time agricultural weather data from California DWR CIMIS.
Station 6 (Davis, CA) is located directly at UC Davis.

Data: Reference ET (ETo), Solar Radiation, Air Temp, Humidity, Precip.
Access: Requires CIMIS API key (set CIMIS_APP_KEY in environment).
"""
import os
import requests
from datetime import datetime, timedelta

SENSOR_INFO = {
    'name': 'CIMIS Weather & ET0 Network (Station 6)',
    'type': 'ground_truth',
    'resolution': 'point',
    'source': 'CA DWR CIMIS API',
    'status': 'active',
}

CIMIS_STATION = 6

def fetch(start_date=None, end_date=None):
    """Fetches weather metrics from CIMIS. Falls back to Open-Meteo if blocked by DWR firewall."""
    app_key = os.getenv("CIMIS_APP_KEY")
    # If app_key is dummy or missing, we still try the request, but if DWR blocks it we fall back to Open-Meteo.
    # Note: We do not fail hard on missing app_key if we have a real-data Open-Meteo fallback available.
    
    if not start_date or not end_date:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = today

    # Try CIMIS first
    cimis_ok = False
    parsed_records = {}
    
    if app_key and not any(bad in app_key.lower() for bad in ['dummy', 'demo', 'test']):
        try:
            url = (
                f"https://et.water.ca.gov/api/data?appKey={app_key}&targets={CIMIS_STATION}"
                f"&startDate={start_date}&endDate={end_date}"
                f"&dataItems=day-air-tmp-avg,day-sol-rad-avg,day-rel-hum-avg,day-soil-tmp-avg,day-precip,day-eto"
                f"&unitOfMeasure=M"
            )
            r = requests.get(url, timeout=15)
            if r.status_code == 200 and "Request Rejected" not in r.text:
                c_json = r.json()
                c_records = c_json.get('Data', {}).get('Providers', [{}])[0].get('Records', [])
                for rec in c_records:
                    d_str = rec.get('Date')
                    if not d_str: continue
                    
                    temp_val = rec.get('DayAirTmpAvg', {}).get('Value') if isinstance(rec.get('DayAirTmpAvg'), dict) else None
                    solar_val = rec.get('DaySolRadAvg', {}).get('Value') if isinstance(rec.get('DaySolRadAvg'), dict) else None
                    hum_val = rec.get('DayRelHumAvg', {}).get('Value') if isinstance(rec.get('DayRelHumAvg'), dict) else None
                    soil_val = rec.get('DaySoilTmpAvg', {}).get('Value') if isinstance(rec.get('DaySoilTmpAvg'), dict) else None
                    precip_val = rec.get('DayPrecip', {}).get('Value') if isinstance(rec.get('DayPrecip'), dict) else None
                    eto_val = rec.get('DayEto', {}).get('Value') if isinstance(rec.get('DayEto'), dict) else None
                    
                    def safe_float(v):
                        try: return float(v)
                        except (ValueError, TypeError): return None
                    
                    parsed_records[d_str] = {
                        'cimis_temp': safe_float(temp_val),
                        'cimis_solar': safe_float(solar_val),
                        'cimis_humidity': safe_float(hum_val),
                        'cimis_soil_temp': safe_float(soil_val),
                        'cimis_precip': safe_float(precip_val),
                        'cimis_et0': safe_float(eto_val)
                    }
                cimis_ok = True
        except Exception as e:
            print(f"[CIMIS WARNING] Direct connection failed: {e}. Trying Open-Meteo fallback...")

    if cimis_ok and parsed_records:
        return {
            'status': 'success',
            'source': f'CIMIS Station {CIMIS_STATION} (LIVE)',
            'data': parsed_records
        }

    # Open-Meteo fallback (real data, public API, no firewall blocks)
    print("[CIMIS FALLBACK] Fetching real weather observations from Open-Meteo Archive API...")
    try:
        lat, lon = 38.5480, -121.8780
        url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lon}"
            f"&start_date={start_date}&end_date={end_date}"
            f"&daily=temperature_2m_mean,shortwave_radiation_sum,relative_humidity_2m_mean,"
            f"soil_temperature_0_to_7cm_mean,precipitation_sum,et0_fao_evapotranspiration"
            f"&timezone=UTC"
        )
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            m_json = r.json()
            m_daily = m_json.get("daily", {})
            m_times = m_daily.get("time", [])
            m_temps = m_daily.get("temperature_2m_mean", [])
            # Convert MJ/m2/day to W/m2 average if needed, but let's keep units consistent
            # Open-Meteo shortwave_radiation_sum is in MJ/m2.
            # CIMIS solar is in W/m2 (or Ly/day depending on unit). Let's convert MJ/m2 to W/m2:
            # 1 MJ/m2/day = 11.574 W/m2
            m_solar = m_daily.get("shortwave_radiation_sum", [])
            m_humidity = m_daily.get("relative_humidity_2m_mean", [])
            m_soil_temp = m_daily.get("soil_temperature_0_to_7cm_mean", [])
            m_precip = m_daily.get("precipitation_sum", [])
            m_et0 = m_daily.get("et0_fao_evapotranspiration", [])

            for i in range(len(m_times)):
                d_str = m_times[i]
                solar_wm2 = float(m_solar[i]) * 11.574 if m_solar[i] is not None else None
                parsed_records[d_str] = {
                    'cimis_temp': float(m_temps[i]) if m_temps[i] is not None else None,
                    'cimis_solar': solar_wm2,
                    'cimis_humidity': float(m_humidity[i]) if m_humidity[i] is not None else None,
                    'cimis_soil_temp': float(m_soil_temp[i]) if m_soil_temp[i] is not None else None,
                    'cimis_precip': float(m_precip[i]) if m_precip[i] is not None else None,
                    'cimis_et0': float(m_et0[i]) if m_et0[i] is not None else None
                }
            return {
                'status': 'success',
                'source': 'Open-Meteo Climate Archive (FALLBACK)',
                'data': parsed_records
            }
        return {'status': 'http_error', 'code': r.status_code, 'text': r.text[:200]}
    except Exception as e:
        return {'status': 'error', 'msg': f"CIMIS direct & fallback failed: {str(e)}"}
