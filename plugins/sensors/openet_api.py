"""
OpenET API Ground-Truth Plugin
==============================
Pulls real satellite-derived actual ET and reference ETo for specific points.
Includes strict local disk caching to protect the 100-query/month free tier limit.

Target: https://openet-api.org/raster/timeseries/point
"""
import os
import json
import hashlib
import requests
from datetime import datetime

SENSOR_INFO = {
    'name': 'OpenET Satellite ET Data',
    'type': 'ground_truth_satellite',
    'resolution': '30m',
    'source': 'OpenET API',
    'status': 'active',
}

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "openet_cache")

def _get_cache_key(lat, lon, start_date, end_date):
    raw = f"{lat}_{lon}_{start_date}_{end_date}"
    return hashlib.md5(raw.encode()).hexdigest() + ".json"

def fetch(lat, lon, start_date, end_date):
    """
    Fetches ET and ETo from OpenET with strict disk caching.
    Requires OPENET_API_KEY environment variable if not cached.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, _get_cache_key(lat, lon, start_date, end_date))
    
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            data = json.load(f)
        return {'status': 'success', 'source': 'OpenET (CACHED)', 'data': data}

    api_key = os.getenv("OPENET_API_KEY")
    if not api_key or any(bad in api_key.lower() for bad in ['dummy', 'demo', 'test']):
        return {'status': 'error', 'msg': 'Strict Enforcement: Invalid or dummy OPENET_API_KEY. Real key required.'}

    url = "https://openet-api.org/raster/timeseries/point"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # We query for both "ET" and "ETo"
    # Note: OpenET API structure for POST usually expects variables array
    payload = {
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "date_range": [start_date, end_date],
        "variables": ["ET", "ETo"],
        "model": "Ensemble",
        "interval": "daily"
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=45)
        if r.status_code == 200:
            resp_data = r.json()
            
            # Save to cache
            with open(cache_file, "w") as f:
                json.dump(resp_data, f)
                
            return {
                'status': 'success',
                'source': 'OpenET (LIVE)',
                'data': resp_data
            }
        return {'status': 'http_error', 'code': r.status_code, 'text': r.text[:200]}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
