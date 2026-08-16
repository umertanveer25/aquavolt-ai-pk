import os
import sys
import time
import json
import glob
import subprocess
from datetime import datetime, timezone
import pandas as pd

# Load env variables from .env if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

repo_dir = os.path.dirname(os.path.abspath(__file__))
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)
api_dir = os.path.join(repo_dir, "api")
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

import aquavolt_gsheet_logger

CACHE_DIR = r"C:\aquavolt_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

print("======================================================================")
print("  AquaVolt-AI Resilient Sync [Unified Dynamic Multi-Farm Engine]")
print("======================================================================")

# 1. Automated Drone Flight Ingestion & Provenance Audit
print("\n[DRONE] Scanning and auditing incoming UAV drone flight logs...")
try:
    drone_script = os.path.join(repo_dir, "scratch", "verify_drone_provenance.py")
    if os.path.exists(drone_script):
        subprocess.run([sys.executable, drone_script], cwd=repo_dir, check=False)
except Exception as de:
    print(f"[DRONE WARNING] Drone audit step: {de}")

# 2. Query Microsoft Planetary Computer STAC for latest satellite scenes
print("\n[MICROSOFT STAC] Querying Microsoft Planetary Computer STAC Catalog...")
try:
    import microsoft_planetary_stac
    stac_pk = microsoft_planetary_stac.get_latest_satellite_assets("pk_hafizabad_pindi_bowra")
    stac_us = microsoft_planetary_stac.get_latest_satellite_assets("ucdavis_russell_ranch")
    print(f"[STAC] Pakistan: {len(stac_pk.get('sentinel_2', []))} Sentinel-2 & {len(stac_pk.get('sentinel_1', []))} Sentinel-1 scenes available.")
    print(f"[STAC] USA: {len(stac_us.get('sentinel_2', []))} Sentinel-2 & {len(stac_us.get('sentinel_1', []))} Sentinel-1 scenes available.")
except Exception as stace:
    print(f"[STAC WARNING] Microsoft STAC discovery step: {stace}")

# 3. Download, process, AND log hourly telemetry for USA
print("\n[USA] Computing and pushing primary USA telemetry data...")
try:
    worksheet, rows_to_append = aquavolt_gsheet_logger.main(push_to_sheets=True)
except SystemExit:
    print("[EXIT] Telemetry engine signaled early exit (data already current).")
except Exception as e:
    print(f"[WARNING] GSheet push encountered an issue: {e}")
    worksheet, rows_to_append = None, []

# 4. Log 7 Advanced Streams in Isolation (V2 Engine)
print("\n[V2 STREAMS] Recording 7 advanced agro-environmental streams...")
try:
    import v2_advanced_streams
    csv_file = os.path.join(repo_dir, "data", "telemetry_log_2026_06_to_08.csv")
    if os.path.exists(csv_file):
        df_latest = pd.read_csv(csv_file).tail(256)
        v2_batch = []
        for _, r in df_latest.iterrows():
            rec = v2_advanced_streams.record_advanced_streams_cycle(
                str(r['timestamp']), str(r['field_name']), int(r['sector_row']), int(r['sector_col']),
                ndvi=float(r.get('ndvi', 0.65)),
                air_temp=float(r.get('air_temp', 20.0)),
                humidity=float(r.get('humidity', 50.0)),
                solar_rad=float(r.get('solar_rad', 0.0)),
                surface_sm=float(r.get('soil_moisture', 0.18)),
                clay_pct=float(r.get('clay', 30.0))
            )
            v2_batch.append(rec)
        v2_advanced_streams.process_and_save_advanced_batch(v2_batch)
except Exception as ve:
    print(f"[V2 WARNING] Advanced streams step: {ve}")

# 5. Ingest and Log Pakistan Pindi Bowra Basmati Rice Stream
print("\n[PAKISTAN] Ingesting real-time observations for Pindi Bowra Rice Hub...")
try:
    import aquavolt_pk_pindi_bowra
    import v2_advanced_streams_pk
    n_new = aquavolt_pk_pindi_bowra.sync_pakistan_hourly()
    if n_new and n_new > 0:
        v2_advanced_streams_pk.process_and_backfill_pakistan_v2(max_rows=n_new)
except Exception as pke:
    print(f"[PAKISTAN WARNING] Pindi Bowra sync step: {pke}")

# 6. Dynamic Sync for Any Custom Registered Farms in farm_registry.json
print("\n[CUSTOM FARMS] Checking and updating dynamically registered farms...")
try:
    registry_path = os.path.join(repo_dir, "data", "farm_registry.json")
    if os.path.exists(registry_path):
        with open(registry_path, "r") as f:
            reg = json.load(f)
        for farm in reg.get("active_farms", []):
            f_id = farm.get("id")
            if f_id not in ["pk_pindi_bowra", "usa_russell_ranch"]:
                print(f"[DYNAMIC SYNC] Syncing custom farm: {farm.get('name')} ({f_id})...")
                # Dynamic backfiller handles updating latest hours
                import dynamic_farm_backfiller
                dynamic_farm_backfiller.integrate_new_farm(
                    farm.get("name"), farm.get("centroid_lat"), farm.get("centroid_lon"),
                    crop_type=farm.get("crop_type", "Super Basmati Rice"),
                    acreage=farm.get("acreage", 5.0),
                    grid_size=(farm.get("grid_rows", 8), farm.get("grid_cols", 8)),
                    start_date=farm.get("start_date", "2026-06-01")
                )
except Exception as dyn_e:
    print(f"[CUSTOM FARMS WARNING] Dynamic sync step: {dyn_e}")

# 7. Live Dual-Continent Correlation & Online PIML Self-Calibration
print("\n[DUAL-CONTINENT ENGINE] Recalibrating Dual-Continent Validation Matrix...")
try:
    val_script = os.path.join(repo_dir, "api", "dual_continent_validation_engine.py")
    if os.path.exists(val_script):
        subprocess.run([sys.executable, val_script], cwd=repo_dir, check=False)
except Exception as vale:
    print(f"[VALIDATION WARNING] Dual-Continent engine step: {vale}")

print("\n[COMPLETED] Resilient multi-site sync finished successfully at:", datetime.now(timezone.utc).isoformat())
