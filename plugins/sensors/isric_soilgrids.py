import requests

SENSOR_INFO = {'name': 'ISRIC SoilGrids API', 'type': 'soil', 'resolution': '250m', 'source': 'ISRIC Netherlands', 'status': 'active'}

def fetch():
    """Fetches real soil clay, sand, soc, bdod from ISRIC SoilGrids for Russell Ranch."""
    try:
        url = (
            "https://rest.isric.org/soilgrids/v2.0/properties/query"
            f"?lon=-121.87&lat=38.54"
            "&property=clay&property=sand&property=soc&property=bdod"
            "&depth=0-5cm&depth=5-15cm&depth=15-30cm"
            "&value=mean"
        )
        r = requests.get(url, timeout=25)
        if r.status_code == 200:
            data = r.json()
            layers = data['properties']['layers']
            result = {'status': 'success', 'source': 'ISRIC SoilGrids (LIVE)'}
            for layer in layers:
                prop_name = layer['name']
                for depth in layer['depths']:
                    depth_label = depth['label']
                    val = depth['values'].get('mean')
                    if val is not None:
                        if prop_name in ('clay', 'sand'):
                            val = val / 10.0  # g/kg -> %
                        elif prop_name == 'soc':
                            val = val / 10.0  # dg/kg -> g/kg
                        elif prop_name == 'bdod':
                            val = val / 100.0  # cg/cm3 -> g/cm3
                    result[f'{prop_name}_{depth_label}'] = val
            return result
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
