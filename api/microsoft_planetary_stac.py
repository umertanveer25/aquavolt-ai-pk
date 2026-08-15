"""
AquaVolt-AI: Microsoft Planetary Computer STAC API Client
=========================================================
Queries Microsoft Planetary Computer SpatioTemporal Asset Catalog (STAC) API
for Sentinel-2 L2A (10m), Sentinel-1 SAR (10m), Copernicus DEM (30m), and Landsat
over multi-site agricultural bounding boxes (USA & Pakistan).

STAC Endpoint: https://planetarycomputer.microsoft.com/api/stac/v1
"""

import os
import json
import requests
from datetime import datetime, timezone

STAC_SEARCH_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"

# Pre-registered multi-site bounding boxes
SITES_BBOX = {
    "pk_hafizabad_pindi_bowra": [73.5850, 32.0820, 73.5980, 32.0950],
    "ucdavis_russell_ranch": [-121.8860, 38.5420, -121.8720, 38.5540]
}

def search_stac_scenes(bbox, collection="sentinel-2-l2a", start_date="2026-06-01", end_date=None, max_cloud=30, limit=10):
    """
    Search STAC scenes across Microsoft Planetary Computer.
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    datetime_range = f"{start_date}T00:00:00Z/{end_date}T23:59:59Z"
    
    payload = {
        "collections": [collection],
        "bbox": bbox,
        "datetime": datetime_range,
        "limit": limit
    }
    
    if collection == "sentinel-2-l2a":
        payload["query"] = {"eo:cloud_cover": {"lt": max_cloud}}
        
    try:
        resp = requests.post(STAC_SEARCH_URL, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            return features
        else:
            print(f"[STAC ERROR] Status {resp.status_code}: {resp.text}")
            return []
    except Exception as e:
        print(f"[STAC EXCEPTION] Failed to query Microsoft STAC: {e}")
        return []

def get_latest_satellite_assets(site_key="pk_hafizabad_pindi_bowra", max_cloud=25):
    """
    Retrieves the latest available Sentinel-2 and Sentinel-1 STAC assets for a farm site.
    """
    bbox = SITES_BBOX.get(site_key, SITES_BBOX["pk_hafizabad_pindi_bowra"])
    
    # 1. Search Sentinel-2 L2A Optical
    s2_features = search_stac_scenes(bbox, collection="sentinel-2-l2a", max_cloud=max_cloud, limit=5)
    
    # 2. Search Sentinel-1 RTC / GRD Radar
    s1_features = search_stac_scenes(bbox, collection="sentinel-1-grd", limit=5)
    
    results = {
        "site_id": site_key,
        "bbox": bbox,
        "query_timestamp": datetime.now(timezone.utc).isoformat(),
        "sentinel_2": [],
        "sentinel_1": []
    }
    
    for feat in s2_features:
        props = feat.get("properties", {})
        assets = feat.get("assets", {})
        results["sentinel_2"].append({
            "scene_id": feat.get("id"),
            "datetime": props.get("datetime"),
            "cloud_cover_pct": props.get("eo:cloud_cover"),
            "platform": props.get("platform"),
            "b04_red_href": assets.get("B04", {}).get("href"),
            "b08_nir_href": assets.get("B08", {}).get("href"),
            "b11_swir_href": assets.get("B11", {}).get("href"),
            "visual_thumbnail": assets.get("rendered_preview", {}).get("href")
        })
        
    for feat in s1_features:
        props = feat.get("properties", {})
        assets = feat.get("assets", {})
        results["sentinel_1"].append({
            "scene_id": feat.get("id"),
            "datetime": props.get("datetime"),
            "platform": props.get("platform"),
            "polarizations": props.get("sar:polarizations"),
            "vv_href": assets.get("vv", {}).get("href"),
            "vh_href": assets.get("vh", {}).get("href")
        })
        
    return results

def main():
    print("=" * 85)
    print("  AquaVolt-AI: Microsoft Planetary Computer STAC Client Test")
    print("=" * 85)
    
    for site_key in ["pk_hafizabad_pindi_bowra", "ucdavis_russell_ranch"]:
        print(f"\n[*] Querying Microsoft STAC Catalog for: {site_key}...")
        res = get_latest_satellite_assets(site_key)
        
        s2_list = res.get("sentinel_2", [])
        s1_list = res.get("sentinel_1", [])
        
        print(f"  [+] Sentinel-2 Optical Scenes Found: {len(s2_list)}")
        for i, s2 in enumerate(s2_list[:3]):
            print(f"      {i+1}. ID: {s2['scene_id']} | Date: {s2['datetime'][:10]} | Cloud: {s2['cloud_cover_pct']:.1f}%")
            
        print(f"  [+] Sentinel-1 SAR Radar Scenes Found: {len(s1_list)}")
        for i, s1 in enumerate(s1_list[:3]):
            print(f"      {i+1}. ID: {s1['scene_id']} | Date: {s1['datetime'][:10]} | Pol: {s1['polarizations']}")
            
    print("\n" + "=" * 85)

if __name__ == "__main__":
    main()
