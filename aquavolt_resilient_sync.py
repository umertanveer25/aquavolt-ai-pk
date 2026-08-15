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

print("======================================================================")
print("  AquaVolt-AI Resilient Sync [Instant Push Mode]")
print("======================================================================")

# 1. Download, process, AND push data IMMEDIATELY
print("[START] Computing and pushing telemetry data...")
try:
    worksheet, rows_to_append = aquavolt_gsheet_logger.main(push_to_sheets=True)
except SystemExit:
    print("[EXIT] Telemetry engine signaled early exit (data already current).")
    exit(0)
except Exception as e:
    print(f"[WARNING] GSheet push encountered an issue (local CSV was updated): {e}")
    worksheet, rows_to_append = None, []

# 2. Save local backup and push to GitHub
print("[BACKUP] Syncing telemetry and provenance to GitHub...")
try:
    repo_dir = os.path.dirname(os.path.abspath(__file__))
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

    # Push to GitHub
    print("[GIT] Committing and pushing telemetry to GitHub...")
    subprocess.run(["git", "add", "data/*.csv", "data/PROVENANCE.json", "README.md"], cwd=repo_dir, check=False)
    subprocess.run(["git", "commit", "-m", f"chore: automated hourly telemetry log {now_str} [skip ci]"], cwd=repo_dir, check=False)
    res = subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir, capture_output=True, text=True)
    if res.returncode == 0:
        print("[GIT] ✅ Pushed new telemetry to GitHub successfully.")
    else:
        print(f"[GIT] Push notice: {res.stderr.strip() or 'No changes or up to date'}")

except Exception as e:
    print(f"[ERROR] Git sync step: {e}")

print("[DONE] Hourly sync cycle complete.")
