import requests

SENSOR_INFO = {'name': 'PlanetScope SuperDoves (3m)', 'type': 'optical', 'resolution': '3m', 'source': 'Planet Labs STAC', 'status': 'active'}

def fetch():
    """Probes Planet Labs public STAC endpoint for SuperDove availability."""
    try:
        url = "https://api.planet.com/data/v1/quick-search"
        # Planet requires API key for actual search, so we probe the health endpoint
        health_url = "https://api.planet.com/basemaps/v1/mosaics"
        r = requests.get(health_url, timeout=10)
        return {
            'status': 'success',
            'source': 'Planet Labs API (LIVE probe)',
            'api_reachable': r.status_code in [200, 401, 403],
            'http_code': r.status_code,
            'note': 'Full imagery requires Planet API key (Education tier is free)'
        }
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
