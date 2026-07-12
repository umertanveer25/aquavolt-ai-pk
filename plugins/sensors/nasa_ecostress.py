import requests
from datetime import datetime, timedelta

SENSOR_INFO = {'name': 'NASA ECOSTRESS (70m Thermal)', 'type': 'thermal', 'resolution': '70m', 'source': 'NASA CMR STAC', 'status': 'active'}

def fetch():
    """Searches NASA CMR STAC for the latest ECOSTRESS thermal scene over Russell Ranch."""
    try:
        end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        start = (datetime.utcnow() - timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
        url = (
            "https://cmr.earthdata.nasa.gov/stac/LPCLOUD/search"
            f"?collections=ECO_L2T_LSTE.v002"
            f"&bbox=-121.92,38.49,-121.82000000000001,38.589999999999996"
            f"&datetime={start}/{end}"
            "&limit=1"
        )
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            features = r.json().get('features', [])
            if features:
                props = features[0]['properties']
                return {
                    'status': 'success',
                    'source': 'NASA CMR STAC ECOSTRESS (LIVE)',
                    'scene_id': features[0].get('id', 'unknown'),
                    'datetime': props.get('datetime'),
                    'collection': 'ECO_L2T_LSTE.v002',
                }
            return {'status': 'no_scenes_found'}
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
