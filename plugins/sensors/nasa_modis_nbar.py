import requests

SENSOR_INFO = {'name': 'NASA MODIS MCD43A4 (500m NBAR)', 'type': 'optical', 'resolution': '500m', 'source': 'Microsoft Planetary Computer STAC', 'status': 'active'}

def fetch():
    """Searches Planetary Computer STAC for the latest MODIS NBAR scene over Russell Ranch."""
    try:
        url = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
        payload = {
            "collections": ["modis-43A4-061"],
            "bbox": [-121.92, 38.49, -121.82000000000001, 38.589999999999996],
            "limit": 1,
            "sortby": [{"field": "datetime", "direction": "desc"}],
        }
        r = requests.post(url, json=payload, timeout=20)
        if r.status_code == 200:
            features = r.json().get('features', [])
            if features:
                props = features[0]['properties']
                return {
                    'status': 'success',
                    'source': 'Planetary Computer STAC (LIVE)',
                    'scene_id': features[0].get('id', 'unknown'),
                    'datetime': props.get('datetime'),
                }
            return {'status': 'no_scenes_found'}
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
