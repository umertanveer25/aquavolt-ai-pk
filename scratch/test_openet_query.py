import os
import requests
import json

# Load env variables from .env if present
env_path = ".env"
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

api_key = os.getenv("OPENET_API_KEY")
print(f"API Key: {api_key}")

url = "https://openet-api.org/raster/timeseries/point"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Try correct format
payload = {
    "geometry": [-121.872, 38.545],  # lon, lat
    "date_range": ["2023-06-24", "2023-07-04"],
    "variable": "ET",
    "reference_et": "gridMET",
    "model": "Ensemble",
    "units": "mm",
    "interval": "monthly",
    "file_format": "JSON"
}

r = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {r.status_code}")
try:
    print(json.dumps(r.json(), indent=2))
except Exception:
    print(r.text)
