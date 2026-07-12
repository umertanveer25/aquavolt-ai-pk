import requests

SENSOR_INFO = {'name': 'Open-Meteo (Forecasting & Archive)', 'type': 'weather', 'resolution': '1km', 'source': 'Open-Meteo / DWD / ECMWF', 'status': 'active'}

def fetch():
    """Fetches real-time forecast + hourly ET0 from Open-Meteo for Russell Ranch."""
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude=38.54&longitude=-121.87"
            "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,surface_pressure"
            "&daily=et0_fao_evapotranspiration,precipitation_sum,temperature_2m_max,temperature_2m_min"
            "&timezone=America%2FLos_Angeles"
        )
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            current = data.get('current', {})
            daily = data.get('daily', {})
            return {
                'status': 'success',
                'source': 'Open-Meteo API (LIVE)',
                'current_temp_c': current.get('temperature_2m'),
                'current_rh_pct': current.get('relative_humidity_2m'),
                'current_wind_ms': current.get('wind_speed_10m'),
                'current_pressure_hpa': current.get('surface_pressure'),
                'today_et0_mm': daily.get('et0_fao_evapotranspiration', [None])[0],
                'today_precip_mm': daily.get('precipitation_sum', [None])[0],
                'today_tmax_c': daily.get('temperature_2m_max', [None])[0],
                'today_tmin_c': daily.get('temperature_2m_min', [None])[0],
            }
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
