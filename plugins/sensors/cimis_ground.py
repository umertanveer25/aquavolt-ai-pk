import requests
from datetime import datetime, timedelta

SENSOR_INFO = {'name': 'CIMIS Ground Stations', 'type': 'ground_truth', 'resolution': 'point', 'source': 'Open-Meteo Ground Proxy (Davis CA)', 'status': 'active'}

def fetch():
    """Fetches real hourly ground-level weather for Davis, CA via Open-Meteo (mirrors CIMIS)."""
    try:
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=38.54&longitude=-121.87"
            "&hourly=temperature_2m,relative_humidity_2m,shortwave_radiation"
            ",soil_temperature_0cm,precipitation,et0_fao_evapotranspiration"
            "&start_date=" + yesterday + "&end_date=" + yesterday +
            "&timezone=America%2FLos_Angeles"
        )
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            hourly = r.json().get('hourly', {})
            temps = [t for t in hourly.get('temperature_2m', []) if t is not None]
            rhs = [h for h in hourly.get('relative_humidity_2m', []) if h is not None]
            solar = [s for s in hourly.get('shortwave_radiation', []) if s is not None]
            soil_t = [s for s in hourly.get('soil_temperature_0cm', []) if s is not None]
            precip = [p for p in hourly.get('precipitation', []) if p is not None]
            et0 = [e for e in hourly.get('et0_fao_evapotranspiration', []) if e is not None]
            return {
                'status': 'success',
                'source': 'CIMIS Ground Proxy via Open-Meteo (LIVE)',
                'date': yesterday,
                'avg_temp_c': round(sum(temps) / len(temps), 2) if temps else None,
                'max_temp_c': round(max(temps), 2) if temps else None,
                'min_temp_c': round(min(temps), 2) if temps else None,
                'avg_rh_pct': round(sum(rhs) / len(rhs), 1) if rhs else None,
                'total_solar_wm2': round(sum(solar), 1) if solar else None,
                'avg_soil_temp_c': round(sum(soil_t) / len(soil_t), 2) if soil_t else None,
                'total_precip_mm': round(sum(precip), 2) if precip else None,
                'total_et0_mm': round(sum(et0), 2) if et0 else None,
                'hourly_readings': len(temps),
            }
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
