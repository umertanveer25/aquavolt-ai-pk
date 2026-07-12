import requests
from datetime import datetime, timedelta

SENSOR_INFO = {'name': 'NOAA GOES-16 ABI (2km Geostationary)', 'type': 'geostationary', 'resolution': '2km', 'source': 'NASA CMR STAC', 'status': 'active'}

def fetch():
    """Searches NASA CMR for recent GOES-16 ABI scenes over California."""
    try:
        end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        start = (datetime.utcnow() - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%SZ')
        url = (
            "https://cmr.earthdata.nasa.gov/stac/GES_DISC/search"
            f"?bbox=-122.87,37.54,-120.87,39.54"
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
                    'source': 'NASA CMR GOES-16 (LIVE)',
                    'scene_id': features[0].get('id', 'unknown'),
                    'datetime': props.get('datetime'),
                }
            return {'status': 'no_scenes_found'}
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
