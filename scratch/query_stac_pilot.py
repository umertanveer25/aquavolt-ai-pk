import pystac_client
import planetary_computer
from datetime import datetime

# Russell Ranch farm center coordinates
LAT, LON = 38.5480, -121.8780

print("Connecting to Planetary Computer...")
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    ignore_conformance=True,
)

# Search Sentinel-2 L2A during the pilot period (June 28 to July 18, 2026)
search = catalog.search(
    collections=["sentinel-2-l2a"],
    intersects={"type": "Point", "coordinates": [LON, LAT]},
    datetime="2026-06-28/2026-07-18",
)

items = list(search.item_collection())
print(f"Total Sentinel-2 scenes found: {len(items)}")
for i, item in enumerate(items, 1):
    # Get cloud cover
    cloud_cover = item.properties.get("eo:cloud_cover", 100)
    print(f" {i}. Date: {item.datetime.strftime('%Y-%m-%d %H:%M:%S')} | Cloud Cover: {cloud_cover:.1f}% | ID: {item.id}")
