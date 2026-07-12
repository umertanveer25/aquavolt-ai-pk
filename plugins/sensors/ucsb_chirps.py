import requests
from datetime import datetime, timedelta

SENSOR_INFO = {'name': 'CHIRPS (Satellite Precipitation)', 'type': 'precipitation', 'resolution': '5km', 'source': 'Open-Meteo Archive', 'status': 'active'}

def fetch():
    """Fetches satellite-calibrated precipitation data via Open-Meteo historical archive."""
    try:
        end = (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d')
        start = (datetime.utcnow() - timedelta(days=8)).strftime('%Y-%m-%d')
        url = (
            "https://archive-api.open-meteo.com/v1/archive"
            f"?latitude=38.54&longitude=-121.87"
            f"&start_date={start}&end_date={end}"
            "&daily=precipitation_sum,rain_sum,et0_fao_evapotranspiration"
            "&timezone=UTC"
        )
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json().get('daily', {})
            precip_list = data.get('precipitation_sum', [])
            total_precip = sum(p for p in precip_list if p is not None)
            return {
                'status': 'success',
                'source': 'Open-Meteo Historical Archive (LIVE)',
                '7day_total_precip_mm': round(total_precip, 2),
                '7day_daily_precip': precip_list,
            }
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
