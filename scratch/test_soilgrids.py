"""
Inspect SoilGrids JSON response for UC Davis Russell Ranch
"""
import requests
import json

lat, lon = 38.5448, -121.8720  # Field-A
url = (
    f"https://rest.isric.org/soilgrids/v2.0/properties/query"
    f"?lon={lon}&lat={lat}"
    f"&property=clay&property=sand&property=silt"
    f"&depth=0-30cm&value=mean"
)

print(f"[TEST] Querying: {url}")
r = requests.get(url, timeout=15, headers={"Accept": "application/json"})
print(f"Status Code: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    # Print keys
    print("Keys in response:", list(data.keys()))
    if "properties" in data:
        props = data["properties"]
        print("Keys in properties:", list(props.keys()))
        layers = props.get("layers", [])
        print(f"Number of layers returned: {len(layers)}")
        for i, layer in enumerate(layers):
            print(f"\nLayer {i}:")
            print("  name:", layer.get("name"))
            print("  label:", layer.get("label"))
            depths = layer.get("depths", [])
            print(f"  depths count: {len(depths)}")
            for j, depth in enumerate(depths):
                print(f"    Depth {j}: label={depth.get('label')}, unit={depth.get('unit')}")
                print(f"    values: {depth.get('values')}")
else:
    print(r.text)
