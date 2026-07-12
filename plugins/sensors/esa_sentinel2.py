import requests

SENSOR_INFO = {'name': 'ESA Sentinel-2 (Copernicus 10m)', 'type': 'optical', 'resolution': '10m', 'source': 'Microsoft Planetary Computer STAC', 'status': 'active'}

def fetch():
    """Searches Planetary Computer STAC for the latest Sentinel-2 scene over Russell Ranch."""
    try:
        url = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
        payload = {
            "collections": ["sentinel-2-l2a"],
            "bbox": [-121.88000000000001, 38.53, -121.86, 38.55],
            "limit": 1,
            "sortby": [{"field": "datetime", "direction": "desc"}],
            "filter-lang": "cql2-json",
            "filter": {"op": "<=", "args": [{"property": "eo:cloud_cover"}, 30]}
        }
        r = requests.post(url, json=payload, timeout=20)
        if r.status_code == 200:
            features = r.json().get('features', [])
            if features:
                props = features[0]['properties']
                return {
                    'status': 'success',
                    'source': 'Planetary Computer STAC (LIVE)',
                    'scene_id': props.get('s2:granule_id', 'unknown'),
                    'datetime': props.get('datetime'),
                    'cloud_cover_pct': props.get('eo:cloud_cover'),
                    'platform': props.get('platform'),
                }
            return {'status': 'no_scenes_found'}
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
