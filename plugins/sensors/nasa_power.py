import requests
from datetime import datetime, timedelta

SENSOR_INFO = {'name': 'NASA POWER (Agroclimatology)', 'type': 'weather', 'resolution': '0.5deg', 'source': 'NASA LaRC', 'status': 'active'}

def fetch():
    """Fetches real agroclimatology data from NASA POWER API for Russell Ranch."""
    try:
        # NASA POWER has a 3-5 day processing lag, so query 5 days back
        target = (datetime.utcnow() - timedelta(days=5)).strftime('%Y%m%d')
        url = (
            "https://power.larc.nasa.gov/api/temporal/daily/point"
            f"?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M,WS2M"
            f"&community=AG&longitude=-121.87&latitude=38.54"
            f"&start={target}&end={target}&format=JSON"
        )
        r = requests.get(url, timeout=25)
        if r.status_code == 200:
            params = r.json()['properties']['parameter']
            day_key = list(params['T2M'].keys())[0]
            result = {
                'status': 'success',
                'source': 'NASA POWER API (LIVE)',
                'date': day_key,
                'temp_c': params['T2M'][day_key],
                'temp_max_c': params['T2M_MAX'][day_key],
                'temp_min_c': params['T2M_MIN'][day_key],
                'precip_mm': params['PRECTOTCORR'][day_key],
                'solar_w_m2': params['ALLSKY_SFC_SW_DWN'][day_key],
                'rh_pct': params['RH2M'][day_key],
                'wind_m_s': params['WS2M'][day_key],
            }
            # Validate no -999 fill values
            if result['temp_c'] == -999.0:
                return {'status': 'error', 'msg': 'NASA POWER returned fill values (-999), data not yet processed'}
            return result
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
