"""
Test SoilGrids query without depth/property parameters to see default response
"""
import requests
import json

lat, lon = 38.5448, -121.8720  # Field-A
url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}"

print(f"[TEST] Querying base URL: {url}")
r = requests.get(url, timeout=15)
print(f"Status Code: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    props = data.get("properties", {})
    layers = props.get("layers", [])
    print(f"Total layers returned: {len(layers)}")
    if layers:
        print("First layer structure:")
        layer = layers[0]
        print("  name:", layer.get("name"))
        depths = layer.get("depths", [])
        if depths:
            print("  First depth values keys:", list(depths[0].get("values", {}).keys()))
            print("  First depth values:", depths[0].get("values"))
else:
    print(r.text)
