import requests

SENSOR_INFO = {'name': 'NASA SMAP (9km Soil Moisture)', 'type': 'microwave', 'resolution': '9km', 'source': 'Open-Meteo Soil API', 'status': 'active'}

def fetch():
    """Fetches real soil moisture at multiple depths from Open-Meteo (satellite-calibrated)."""
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude=38.54&longitude=-121.87"
            "&current=soil_moisture_0_to_1cm,soil_moisture_1_to_3cm"
            ",soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_temperature_0cm"
            "&timezone=UTC"
        )
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            current = r.json().get('current', {})
            return {
                'status': 'success',
                'source': 'Open-Meteo Soil API (LIVE - satellite calibrated)',
                'sm_0_1cm': current.get('soil_moisture_0_to_1cm'),
                'sm_1_3cm': current.get('soil_moisture_1_to_3cm'),
                'sm_3_9cm': current.get('soil_moisture_3_to_9cm'),
                'sm_9_27cm': current.get('soil_moisture_9_to_27cm'),
                'soil_temp_0cm': current.get('soil_temperature_0cm'),
            }
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
