"""Fix last 2 edge cases: OpenLandMap 422 and NASA POWER -999 lag"""
import os

PLUGINS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'plugins', 'sensors')
LAT = 38.54
LON = -121.87

# FIX: OpenLandMap - Their REST API is returning 422 (broken on their side).
# Replace with a direct WMS GetMap request to their GeoServer which always works.
olm = f"""import requests

SENSOR_INFO = {{'name': 'OpenLandMap API', 'type': 'soil', 'resolution': '250m', 'source': 'OpenGeoHub GeoServer', 'status': 'active'}}

def fetch():
    \"\"\"Fetches soil clay fraction from OpenLandMap GeoServer WMS GetFeatureInfo.\"\"\"
    try:
        lat, lon = {LAT}, {LON}
        d = 0.0005
        url = (
            "https://geoserver.openlandmap.org/geoserver/predicted/ows"
            "?service=WMS&version=1.1.1&request=GetFeatureInfo"
            "&layers=predicted:sol_clay.wfraction_usda.3a1a1a_m_250m_b0..0cm_1950..2017_v0.2"
            "&query_layers=predicted:sol_clay.wfraction_usda.3a1a1a_m_250m_b0..0cm_1950..2017_v0.2"
            f"&bbox={{lon-d}},{{lat-d}},{{lon+d}},{{lat+d}}"
            "&width=1&height=1&x=0&y=0"
            "&srs=EPSG:4326&info_format=application/json"
        )
        r = requests.get(url, timeout=25)
        if r.status_code == 200:
            data = r.json()
            features = data.get('features', [])
            if features:
                props = features[0].get('properties', {{}})
                return {{
                    'status': 'success',
                    'source': 'OpenLandMap GeoServer WMS (LIVE)',
                    'clay_wfraction_pct': props.get('GRAY_INDEX'),
                }}
            return {{'status': 'success', 'source': 'OpenLandMap WMS (LIVE)', 'note': 'No features at point'}}
        return {{'status': 'http_error', 'code': r.status_code}}
    except Exception as e:
        return {{'status': 'error', 'msg': str(e)}}
"""
with open(os.path.join(PLUGINS_DIR, 'openlandmap.py'), 'w', encoding='utf-8') as f:
    f.write(olm.strip() + '\n')
print("[FIX] OpenLandMap -> GeoServer WMS GetFeatureInfo (bypasses broken REST API)")

# FIX: NASA POWER returns -999 when querying dates too recent (processing lag).
# Solution: query 5 days ago instead of 2 days ago.
power = f"""import requests
from datetime import datetime, timedelta

SENSOR_INFO = {{'name': 'NASA POWER (Agroclimatology)', 'type': 'weather', 'resolution': '0.5deg', 'source': 'NASA LaRC', 'status': 'active'}}

def fetch():
    \"\"\"Fetches real agroclimatology data from NASA POWER API for Russell Ranch.\"\"\"
    try:
        # NASA POWER has a 3-5 day processing lag, so query 5 days back
        target = (datetime.utcnow() - timedelta(days=5)).strftime('%Y%m%d')
        url = (
            "https://power.larc.nasa.gov/api/temporal/daily/point"
            f"?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M,WS2M"
            f"&community=AG&longitude={LON}&latitude={LAT}"
            f"&start={{target}}&end={{target}}&format=JSON"
        )
        r = requests.get(url, timeout=25)
        if r.status_code == 200:
            params = r.json()['properties']['parameter']
            day_key = list(params['T2M'].keys())[0]
            result = {{
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
            }}
            # Validate no -999 fill values
            if result['temp_c'] == -999.0:
                return {{'status': 'error', 'msg': 'NASA POWER returned fill values (-999), data not yet processed'}}
            return result
        return {{'status': 'http_error', 'code': r.status_code}}
    except Exception as e:
        return {{'status': 'error', 'msg': str(e)}}
"""
with open(os.path.join(PLUGINS_DIR, 'nasa_power.py'), 'w', encoding='utf-8') as f:
    f.write(power.strip() + '\n')
print("[FIX] NASA POWER -> Query 5 days back to avoid processing lag (-999 fill)")

print("\nBoth fixes written. Ready to test.")
