"""
AquaVolt-AI: Programmatic Multi-Modal Farm & Satellite Imagery Loader
=====================================================================
Directly links telemetry CSVs with their authentic spaceborne satellite imagery:
  - Loads 100% real numerical telemetry data
  - Loads high-resolution true-color satellite photographs
  - Loads daily timeseries satellite progressions (July 1 to August 16)
"""

import os
import json
import pandas as pd
from PIL import Image

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
REGISTRY_PATH = os.path.join(DATA_DIR, "farm_registry.json")

def load_farm_registry():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"active_farms": []}

def get_farm(farm_id):
    """
    Returns a unified farm object linking numerical telemetry with spatial satellite imagery.
    """
    registry = load_farm_registry()
    farm_info = next((f for f in registry.get("active_farms", []) if f["id"] == farm_id), None)
    if not farm_info:
        raise ValueError(f"Farm ID '{farm_id}' not found in registry.")
        
    return FarmDataset(farm_info)

class FarmDataset:
    def __init__(self, info):
        self.info = info
        self.id = info.get("id")
        self.name = info.get("name")
        self.crop = info.get("crop_type")
        self.acreage = info.get("acreage")
        self.coords = (info.get("centroid_lat"), info.get("centroid_lon"))
        
        self.csv_path = os.path.join(ROOT_DIR, info.get("telemetry_csv", ""))
        self.v2_csv_path = os.path.join(ROOT_DIR, info.get("v2_telemetry_csv", ""))
        
        # Linked Satellite Imagery
        imagery_meta = info.get("satellite_imagery", {})
        self.photo_path = os.path.join(ROOT_DIR, imagery_meta.get("satellite_photo", "")) if imagery_meta.get("satellite_photo") else None
        self.daily_dir = os.path.join(ROOT_DIR, imagery_meta.get("daily_imagery_dir", "")) if imagery_meta.get("daily_imagery_dir") else None

    def get_telemetry(self):
        """Loads numerical telemetry dataframe."""
        if os.path.exists(self.csv_path):
            return pd.read_csv(self.csv_path, on_bad_lines='skip')
        return pd.DataFrame()

    def get_v2_telemetry(self):
        """Loads isolated V2 frontier satellite telemetry."""
        if os.path.exists(self.v2_csv_path):
            return pd.read_csv(self.v2_csv_path, on_bad_lines='skip')
        return pd.DataFrame()

    def get_satellite_image(self):
        """Loads authentic high-resolution spaceborne satellite photograph."""
        if self.photo_path and os.path.exists(self.photo_path):
            return Image.open(self.photo_path)
        return None

    def get_daily_imagery(self):
        """Returns dict of daily satellite imagery filenames."""
        if self.daily_dir and os.path.exists(self.daily_dir):
            files = sorted([os.path.join(self.daily_dir, f) for f in os.listdir(self.daily_dir) if f.endswith('.png')])
            return files
        return []

    def __repr__(self):
        return f"<FarmDataset: {self.name} | Crop: {self.crop} | Area: {self.acreage} Ac | Satellite Photo: {'Available' if self.photo_path else 'None'}>"

if __name__ == "__main__":
    print("=" * 80)
    print("TESTING PROGRAMMATIC FARM & SATELLITE IMAGERY INTEGRATION")
    print("=" * 80)
    for fid in ["usa_field_1_corn", "usa_field_2_alfalfa", "usa_field_3_fallow", "usa_field_4_tomato", "pk_pindi_bowra"]:
        try:
            f = get_farm(fid)
            df = f.get_telemetry()
            img = f.get_satellite_image()
            daily_imgs = f.get_daily_imagery()
            print(f"\n[+] Loaded: {f.name}")
            print(f"    - Telemetry Rows:     {len(df):,} observations")
            print(f"    - High-Res Photo:     {img.size if img else 'N/A'}")
            print(f"    - Daily Images Count: {len(daily_imgs)} daily captures (July 1 to Aug 16)")
        except Exception as e:
            print(f"    [-] Error loading {fid}: {e}")
    print("=" * 80)
