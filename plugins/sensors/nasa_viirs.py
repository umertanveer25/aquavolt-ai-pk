import requests
from datetime import datetime, timedelta

SENSOR_INFO = {'name': 'NASA VIIRS SNPP (375m Thermal)', 'type': 'thermal', 'resolution': '375m', 'source': 'NASA CMR STAC', 'status': 'active'}

def fetch():
    """Searches NASA CMR STAC for recent VIIRS thermal granules over Russell Ranch."""
    try:
        end = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        start = (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%SZ')
        # Search LANCEMODIS provider for near-real-time VIIRS data
        url = (
            "https://cmr.earthdata.nasa.gov/stac/LANCEMODIS/search"
            f"?bbox=-122.37,38.04,-121.37,39.04"
            f"&datetime={start}/{end}"
            "&limit=3"
        )
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            features = r.json().get('features', [])
            if features:
                props = features[0]['properties']
                return {
                    'status': 'success',
                    'source': 'NASA CMR VIIRS LANCEMODIS (LIVE)',
                    'scenes_found': len(features),
                    'latest_id': features[0].get('id', 'unknown'),
                    'datetime': props.get('datetime'),
                    'collection': features[0].get('collection', 'unknown'),
                }
            return {'status': 'no_scenes_found', 'source': 'NASA CMR LANCEMODIS'}
        # Fallback: try LPCLOUD provider
        url2 = (
            "https://cmr.earthdata.nasa.gov/stac/LPCLOUD/search"
            f"?collections=VNP21A1D.v002"
            f"&bbox=-121.97,38.44,-121.77000000000001,38.64"
            f"&datetime={start}/{end}"
            "&limit=1"
        )
        r2 = requests.get(url2, timeout=20)
        if r2.status_code == 200:
            features2 = r2.json().get('features', [])
            if features2:
                return {
                    'status': 'success',
                    'source': 'NASA CMR VIIRS LPCLOUD (LIVE fallback)',
                    'scene_id': features2[0].get('id', 'unknown'),
                    'datetime': features2[0]['properties'].get('datetime'),
                }
        return {'status': 'http_error', 'lance_code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
