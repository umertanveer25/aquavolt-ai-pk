import requests
from datetime import datetime, timedelta

SENSOR_INFO = {'name': 'NASA GPM IMERG (Half-hourly Precipitation)', 'type': 'precipitation', 'resolution': '10km', 'source': 'NASA CMR STAC', 'status': 'active'}

def fetch():
    """Searches NASA CMR for recent GPM IMERG precipitation data over Russell Ranch."""
    try:
        end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        start = (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
        url = (
            "https://cmr.earthdata.nasa.gov/stac/GES_DISC/search"
            f"?collections=GPM_3IMERGDL.v07"
            f"&bbox=-121.97,38.44,-121.77000000000001,38.64"
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
                    'source': 'NASA CMR GPM IMERG (LIVE)',
                    'scene_id': features[0].get('id', 'unknown'),
                    'datetime': props.get('datetime'),
                }
            return {'status': 'no_scenes_found'}
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
