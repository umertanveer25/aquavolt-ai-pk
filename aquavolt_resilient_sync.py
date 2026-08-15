import os
import sys
import time
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
print("  AquaVolt-AI Resilient Sync [Unified Telemetry, Drone & V2 Streams]")
print("======================================================================")

# 1. Automated Drone Flight Ingestion & Provenance Audit
print("\n[DRONE] Scanning and auditing incoming UAV drone flight logs...")
try:
    drone_script = os.path.join(repo_dir, "scratch", "verify_drone_provenance.py")
    if os.path.exists(drone_script):
        subprocess.run([sys.executable, drone_script], cwd=repo_dir, check=False)
except Exception as de:
    print(f"[DRONE WARNING] Drone audit step: {de}")

# 2. Query Microsoft Planetary Computer STAC for latest satellite scenes (USA & Pakistan)
print("\n[MICROSOFT STAC] Querying Microsoft Planetary Computer STAC Catalog...")
try:
    import microsoft_planetary_stac
    stac_pk = microsoft_planetary_stac.get_latest_satellite_assets("pk_hafizabad_pindi_bowra")
    stac_us = microsoft_planetary_stac.get_latest_satellite_assets("ucdavis_russell_ranch")
    print(f"[STAC] Pakistan: {len(stac_pk.get('sentinel_2', []))} Sentinel-2 & {len(stac_pk.get('sentinel_1', []))} Sentinel-1 scenes available.")
    print(f"[STAC] USA: {len(stac_us.get('sentinel_2', []))} Sentinel-2 & {len(stac_us.get('sentinel_1', []))} Sentinel-1 scenes available.")
except Exception as stace:
    print(f"[STAC WARNING] Microsoft STAC discovery step: {stace}")

# 3. Download, process, AND log hourly telemetry
print("\n[START] Computing and pushing primary telemetry data...")
try:
    worksheet, rows_to_append = aquavolt_gsheet_logger.main(push_to_sheets=True)
except SystemExit:
    print("[EXIT] Telemetry engine signaled early exit (data already current).")
except Exception as e:
    print(f"[WARNING] GSheet push encountered an issue (local CSV was updated): {e}")
    worksheet, rows_to_append = None, []

# 3. Log 7 Advanced Streams in Isolation (V2 Engine)
print("\n[V2 STREAMS] Recording 7 advanced agro-environmental streams in isolation...")
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

# 4. Ingest and Log Pakistan Pindi Bowra Basmati Rice Stream
print("\n[PAKISTAN] Ingesting real-time observations for Pindi Bowra Rice Hub...")
try:
    import aquavolt_pk_pindi_bowra
    import v2_advanced_streams_pk
    n_new = aquavolt_pk_pindi_bowra.sync_pakistan_hourly()
    if n_new and n_new > 0:
        # Append to isolated Pakistan V2 dataset
        v2_advanced_streams_pk.process_and_backfill_pakistan_v2(max_rows=n_new)
except Exception as pke:
    print(f"[PAKISTAN WARNING] Pindi Bowra sync step: {pke}")

# 5. Live Dual-Continent Correlation & Online PIML Self-Calibration
print("\n[LIVE PIML & CORRELATION] Executing online physics-informed self-updating loop...")
try:
    import dual_continent_validation_engine
    dual_continent_validation_engine.run_dual_continent_validation()
    print("[LIVE PIML] AI model weights and empirical matrices successfully recalibrated.")
except Exception as dce:
    print(f"[CORRELATION WARNING] Online calibration step: {dce}")

# 6. Save local backup and push to GitHub
print("\n[BACKUP] Syncing telemetry, live correlation matrix, and provenance to GitHub...")
try:
    current_utc = datetime.now(timezone.utc)
    now_str = current_utc.strftime('%Y-%m-%d %H:00 UTC')
    
    # Save cache backup
    csv_file = os.path.join(repo_dir, "data", "telemetry_log_2026_06_to_08.csv")
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        backup_file = os.path.join(CACHE_DIR, f"aquavolt_backup_{current_utc.strftime('%Y%m%d_%H%M%S')}.csv")
        df.tail(256).to_csv(backup_file, index=False)
        print(f"[BACKUP] Cached latest telemetry to: {backup_file}")

    # Cleanup old cache files (> 10)
    files = sorted(glob.glob(os.path.join(CACHE_DIR, "aquavolt_backup_*.csv")), key=os.path.getmtime)
    for f in files[:-10]:
        try:
            os.remove(f)
        except Exception:
            pass

    # Stage and push to GitHub
    print("[GIT] Committing and pushing all streams to GitHub...")
    subprocess.run([
        "git", "add", 
        "data/*.csv", 
        "data/incoming_validation/*.csv", 
        "data/drone_audit_ledger.csv", 
        "data/PROVENANCE.json", 
        "data/PROVENANCE_PK_PINDI_BOWRA.json",
        "aquavolt_pk_pindi_bowra.py",
        "api/*.py",
        "README.md"
    ], cwd=repo_dir, check=False)
    subprocess.run(["git", "commit", "-m", f"chore: automated hourly multi-site sync (USA & Pakistan) {now_str} [skip ci]"], cwd=repo_dir, check=False)
    res = subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir, capture_output=True, text=True)
    if res.returncode == 0:
        print("[GIT] ✅ Pushed all streams (USA & Pakistan) to GitHub successfully.")
    else:
        print(f"[GIT] Push status: {res.stderr.strip() or 'Up to date'}")

except Exception as e:
    print(f"[ERROR] Git sync step: {e}")

print("[DONE] Hourly sync cycle complete.")
