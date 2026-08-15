"""
AquaVolt-AI: Microsoft Planetary Computer STAC API Client
=========================================================
Queries Microsoft Planetary Computer SpatioTemporal Asset Catalog (STAC) API
for:
  1. Sentinel-2 L2A (10m Optical)
  2. Sentinel-1 SAR (10m C-Band Radar)
  3. Planet-NICFI (4.77m High-Resolution Analytic Basemaps)
  4. Landsat Collection 2 (30m Thermal & Optical)
  5. Copernicus DEM GLO-30 (30m Topography)

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
            return data.get("features", [])
        else:
            return []
    except Exception as e:
        print(f"[STAC EXCEPTION] Failed to query Microsoft STAC: {e}")
        return []

def get_latest_satellite_assets(site_key="pk_hafizabad_pindi_bowra", max_cloud=25):
    """
    Retrieves the latest available Sentinel-2, Sentinel-1 SAR, and Planet-NICFI (4.77m) STAC assets.
    """
    bbox = SITES_BBOX.get(site_key, SITES_BBOX["pk_hafizabad_pindi_bowra"])
    
    # 1. Search Sentinel-2 L2A Optical
    s2_features = search_stac_scenes(bbox, collection="sentinel-2-l2a", max_cloud=max_cloud, limit=5)
    
    # 2. Search Sentinel-1 RTC / GRD Radar
    s1_features = search_stac_scenes(bbox, collection="sentinel-1-grd", limit=5)
    
    # 3. Search Planet-NICFI 4.77m Analytic Basemaps
    planet_features = search_stac_scenes(bbox, collection="planet-nicfi-analytic", limit=2)
    
    results = {
        "site_id": site_key,
        "bbox": bbox,
        "query_timestamp": datetime.now(timezone.utc).isoformat(),
        "sentinel_2": [],
        "sentinel_1": [],
        "planet_nicfi_4_77m": []
    }
    
    for feat in s2_features:
        props = feat.get("properties", {})
        results["sentinel_2"].append({
            "scene_id": feat.get("id"),
            "datetime": props.get("datetime"),
            "cloud_cover_pct": props.get("eo:cloud_cover"),
            "platform": props.get("platform"),
            "resolution_m": 10.0
        })
        
    for feat in s1_features:
        props = feat.get("properties", {})
        results["sentinel_1"].append({
            "scene_id": feat.get("id"),
            "datetime": props.get("datetime"),
            "polarizations": props.get("sar:polarizations"),
            "resolution_m": 10.0
        })
        
    for feat in planet_features:
        props = feat.get("properties", {})
        results["planet_nicfi_4_77m"].append({
            "scene_id": feat.get("id"),
            "datetime": props.get("datetime"),
            "resolution_m": 4.77,
            "bands": ["Blue", "Green", "Red", "NIR"],
            "super_resolution_gain": "4.4x pixel density over Sentinel-2"
        })
        
    return results

def main():
    print("=" * 85)
    print("  AquaVolt-AI: Microsoft Planetary Computer STAC Multi-Modal Discovery")
    print("=" * 85)
    
    for site_key in ["pk_hafizabad_pindi_bowra", "ucdavis_russell_ranch"]:
        print(f"\n[*] Querying Microsoft STAC Catalog for: {site_key.upper()}...")
        res = get_latest_satellite_assets(site_key)
        
        s2_list = res.get("sentinel_2", [])
        s1_list = res.get("sentinel_1", [])
        pl_list = res.get("planet_nicfi_4_77m", [])
        
        print(f"  [+] Sentinel-2 Optical (10m) Found:   {len(s2_list)} scenes")
        for i, s2 in enumerate(s2_list[:2]):
            print(f"      • {s2['scene_id'][:45]}... | Date: {s2['datetime'][:10]} | Cloud: {s2['cloud_cover_pct']:.1f}%")
            
        print(f"  [+] Sentinel-1 SAR Radar (10m) Found: {len(s1_list)} scenes")
        for i, s1 in enumerate(s1_list[:2]):
            print(f"      • {s1['scene_id'][:45]}... | Date: {s1['datetime'][:10]} | Pol: {s1['polarizations']}")
            
        print(f"  [+] Planet-NICFI High-Res (4.77m):    {len(pl_list)} scenes (4.4x Pixel Density)")
        for i, pl in enumerate(pl_list[:2]):
            print(f"      • {pl['scene_id'][:45]}... | Date: {pl['datetime'][:10]} | Res: {pl['resolution_m']}m")
            
    print("\n" + "=" * 85)

if __name__ == "__main__":
    main()
