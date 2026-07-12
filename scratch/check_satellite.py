import requests
from datetime import datetime, timedelta, timezone

end = datetime.now(timezone.utc)
start = end - timedelta(days=30)

url = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
payload = {
    "collections": ["sentinel-2-l2a"],
    "bbox": [-121.883, 38.539, -121.869, 38.549],
    "datetime": f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end.strftime('%Y-%m-%dT%H:%M:%SZ')}",
    "limit": 20
}

r = requests.post(url, json=payload)
items = r.json().get("features", [])

if items:
    print(f"Found {len(items)} Sentinel-2 scenes in last 30 days:\n")
    for item in items:
        date = item["properties"]["datetime"][:10]
        cloud = item["properties"].get("eo:cloud_cover", "N/A")
        scene_id = item["id"]
        usable = "USABLE" if isinstance(cloud, (int, float)) and cloud < 30 else "CLOUDY"
        print(f"  {date} | Cloud: {cloud:.1f}% | {usable} | {scene_id[:40]}")
else:
    print("No scenes found in last 30 days — API may be down or area not covered")
