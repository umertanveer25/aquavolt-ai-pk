import os
import time
import glob
from datetime import datetime, timezone
import pandas as pd
import aquavolt_gsheet_logger

CACHE_DIR = r"C:\aquavolt_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

print("======================================================================")
print("  AquaVolt-AI Resilient Sync [Instant Push Mode]")
print("======================================================================")

# 1. Download, process, AND push data IMMEDIATELY — no waiting
print("[START] Computing and pushing telemetry data instantly...")
try:
    worksheet, rows_to_append = aquavolt_gsheet_logger.main(push_to_sheets=True)
except SystemExit:
    # If the logger exited early (e.g. data already existed for this hour), exit cleanly.
    print("[EXIT] Telemetry engine signaled early exit (data already current).")
    exit(0)

print(f"[OK] {len(rows_to_append)} rows pushed to Google Sheets instantly.")

# 2. Save local backup immediately after push
print("[BACKUP] Saving local backup...")
try:
    data = worksheet.get_all_values()
    headers = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=headers)
    current_utc = datetime.now(timezone.utc)
    backup_file = os.path.join(CACHE_DIR, f"aquavolt_backup_{current_utc.strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(backup_file, index=False)
    print(f"[BACKUP] Saved to: {backup_file}")
except Exception as e:
    print(f"[WARNING] Backup failed (data already pushed to cloud safely): {e}")

# 3. Cleanup old backups (> 3 hours)
print("[CLEANUP] Scanning for local backups older than 3 hours...")
now = time.time()
for f in glob.glob(os.path.join(CACHE_DIR, "aquavolt_backup_*.csv")):
    file_age_hours = (now - os.path.getmtime(f)) / 3600
    if file_age_hours > 3.0:
        print(f"[CLEANUP] Deleting expired cache file: {f} (Age: {file_age_hours:.1f} hours)")
        os.remove(f)

print("[DONE] Instant sync complete. Data is live in Google Sheets.")

