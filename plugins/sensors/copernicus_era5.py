import requests
from datetime import datetime, timedelta

SENSOR_INFO = {'name': 'Copernicus ERA5-Land (Reanalysis)', 'type': 'reanalysis', 'resolution': '9km', 'source': 'ECMWF via Open-Meteo', 'status': 'active'}

def fetch():
    """Fetches real ERA5-Land reanalysis data via Open-Meteo archive API."""
    try:
        end = (datetime.utcnow() - timedelta(days=6)).strftime('%Y-%m-%d')
        start = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
        url = (
            "https://archive-api.open-meteo.com/v1/era5"
            f"?latitude=38.54&longitude=-121.87"
            f"&start_date={start}&end_date={end}"
            "&daily=temperature_2m_mean,precipitation_sum,et0_fao_evapotranspiration"
            "&daily=shortwave_radiation_sum,windspeed_10m_max"
            "&timezone=UTC"
        )
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json().get('daily', {})
            return {
                'status': 'success',
                'source': 'ERA5-Land Reanalysis (LIVE)',
                'era5_temp_c': data.get('temperature_2m_mean', [None])[0],
                'era5_precip_mm': data.get('precipitation_sum', [None])[0],
                'era5_et0_mm': data.get('et0_fao_evapotranspiration', [None])[0],
                'era5_solar_mj': data.get('shortwave_radiation_sum', [None])[0],
                'era5_wind_max_ms': data.get('windspeed_10m_max', [None])[0],
            }
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
