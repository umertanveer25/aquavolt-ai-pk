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

import aquavolt_gsheet_logger

CACHE_DIR = r"C:\aquavolt_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

repo_dir = os.path.dirname(os.path.abspath(__file__))

print("======================================================================")
print("  AquaVolt-AI Resilient Sync [Autonomous Telemetry & Drone Sync]")
print("======================================================================")

# 1. Automated Drone Flight Ingestion & Provenance Audit
print("\n[DRONE] Scanning and auditing incoming UAV drone flight logs...")
try:
    drone_script = os.path.join(repo_dir, "scratch", "verify_drone_provenance.py")
    if os.path.exists(drone_script):
        subprocess.run([sys.executable, drone_script], cwd=repo_dir, check=False)
except Exception as de:
    print(f"[DRONE WARNING] Drone audit step: {de}")

# 2. Download, process, AND log hourly telemetry
print("\n[START] Computing and pushing telemetry data...")
try:
    worksheet, rows_to_append = aquavolt_gsheet_logger.main(push_to_sheets=True)
except SystemExit:
    print("[EXIT] Telemetry engine signaled early exit (data already current).")
except Exception as e:
    print(f"[WARNING] GSheet push encountered an issue (local CSV was updated): {e}")
    worksheet, rows_to_append = None, []

# 3. Save local backup and push to GitHub
print("\n[BACKUP] Syncing telemetry, drone ledger, and provenance to GitHub...")
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
    print("[GIT] Committing and pushing telemetry + drone logs to GitHub...")
    subprocess.run([
        "git", "add", 
        "data/*.csv", 
        "data/incoming_validation/*.csv", 
        "data/drone_audit_ledger.csv", 
        "data/PROVENANCE.json", 
        "README.md"
    ], cwd=repo_dir, check=False)
    subprocess.run(["git", "commit", "-m", f"chore: automated hourly telemetry and drone sync {now_str} [skip ci]"], cwd=repo_dir, check=False)
    res = subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir, capture_output=True, text=True)
    if res.returncode == 0:
        print("[GIT] ✅ Pushed new telemetry and drone records to GitHub successfully.")
    else:
        print(f"[GIT] Push status: {res.stderr.strip() or 'Up to date'}")

except Exception as e:
    print(f"[ERROR] Git sync step: {e}")

print("[DONE] Hourly sync cycle complete.")
