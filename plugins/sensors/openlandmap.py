import requests

SENSOR_INFO = {'name': 'OpenLandMap API', 'type': 'soil', 'resolution': '250m', 'source': 'OpenGeoHub GeoServer', 'status': 'active'}

def fetch():
    """Fetches soil clay fraction from OpenLandMap GeoServer WMS GetFeatureInfo."""
    try:
        lat, lon = 38.54, -121.87
        d = 0.0005
        url = (
            "https://geoserver.openlandmap.org/geoserver/predicted/ows"
            "?service=WMS&version=1.1.1&request=GetFeatureInfo"
            "&layers=predicted:sol_clay.wfraction_usda.3a1a1a_m_250m_b0..0cm_1950..2017_v0.2"
            "&query_layers=predicted:sol_clay.wfraction_usda.3a1a1a_m_250m_b0..0cm_1950..2017_v0.2"
            f"&bbox={lon-d},{lat-d},{lon+d},{lat+d}"
            "&width=1&height=1&x=0&y=0"
            "&srs=EPSG:4326&info_format=application/json"
        )
        r = requests.get(url, timeout=25)
        if r.status_code == 200:
            data = r.json()
            features = data.get('features', [])
            if features:
                props = features[0].get('properties', {})
                return {
                    'status': 'success',
                    'source': 'OpenLandMap GeoServer WMS (LIVE)',
                    'clay_wfraction_pct': props.get('GRAY_INDEX'),
                }
            return {'status': 'success', 'source': 'OpenLandMap WMS (LIVE)', 'note': 'No features at point'}
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
