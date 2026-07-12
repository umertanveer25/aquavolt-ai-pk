import requests

SENSOR_INFO = {'name': 'ESA Sentinel-1 (10m SAR Radar)', 'type': 'radar', 'resolution': '10m', 'source': 'Microsoft Planetary Computer STAC', 'status': 'active'}

def fetch():
    """Searches Planetary Computer STAC for the latest Sentinel-1 GRD scene over Russell Ranch."""
    try:
        url = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
        payload = {
            "collections": ["sentinel-1-grd"],
            "bbox": [-121.88000000000001, 38.53, -121.86, 38.55],
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
                    'orbit_direction': props.get('sat:orbit_state'),
                    'polarization': props.get('sar:polarizations'),
                    'instrument_mode': props.get('sar:instrument_mode'),
                }
            return {'status': 'no_scenes_found'}
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
