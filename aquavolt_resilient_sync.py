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
print("  AquaVolt-AI Resilient Sync [Hybrid Local/Cloud]")
print("======================================================================")

# 1. Download & Process data IMMEDIATELY at the exact hour mark
print("[START] Pre-processing telemetry data...")
try:
    worksheet, rows_to_append = aquavolt_gsheet_logger.main(push_to_sheets=False)
except SystemExit:
    # If the logger exited (e.g. data already existed), we just exit too.
    print("[EXIT] Telemetry engine signaled early exit.")
    exit(0)

# 2. Hold data in memory until the 15th minute
current_utc = datetime.now(timezone.utc)
target_minute = 15

minutes_to_wait = target_minute - current_utc.minute
if 0 < minutes_to_wait <= 15:
    seconds_to_wait = minutes_to_wait * 60 - current_utc.second
    print(f"[SLEEP] Holding processed data in memory for {seconds_to_wait} seconds until minute {target_minute}...")
    time.sleep(seconds_to_wait)
else:
    print(f"[SKIP SLEEP] It is already past minute {target_minute}.")

# 3. Wake up and check if GitHub Actions succeeded while we were sleeping
current_utc = datetime.now(timezone.utc)
try:
    data = worksheet.get_all_values()
except Exception as e:
    print(f"[ERROR] Could not fetch Google Sheets to verify GitHub status: {e}")
    # Force push just in case if we couldn't check? Better to fail safely.
    exit(1)

github_succeeded = False
if len(data) > 1:
    last_row_timestamp = data[-1][0] # Timestamp is in Column A
    print(f"[STATUS] Latest cloud record: {last_row_timestamp}")
    try:
        row_time = datetime.strptime(last_row_timestamp, "%Y-%m-%d %H:%M:%S")
        if (row_time.year == current_utc.year and 
            row_time.month == current_utc.month and 
            row_time.day == current_utc.day and 
            row_time.hour == current_utc.hour):
            github_succeeded = True
    except Exception:
        pass

if github_succeeded:
    print(f"[OK] GitHub Actions Succeeded for hour {current_utc.hour}. Local data discarded. Pulling local backup...")
else:
    print(f"[WARNING] GitHub Actions MISSING for hour {current_utc.hour}.")
    if rows_to_append:
        print(f"[FAILOVER] Pushing {len(rows_to_append)} pre-computed rows to Google Sheets...")
        try:
            worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
            # Refresh data to download backup
            data = worksheet.get_all_values()
        except Exception as e:
            print(f"[ERROR] Failed to push local data: {e}")
            exit(1)
    else:
        print("[ERROR] No local data available to push.")

# 4. Save local backup
headers = data[0]
rows = data[1:]
df = pd.DataFrame(rows, columns=headers)
backup_file = os.path.join(CACHE_DIR, f"aquavolt_backup_{current_utc.strftime('%Y%m%d_%H%M%S')}.csv")
df.to_csv(backup_file, index=False)
print(f"[BACKUP] Saved latest cloud dataset to local drive: {backup_file}")

# 5. Cleanup old backups (> 3 hours)
print("[CLEANUP] Scanning for local backups older than 3 hours...")
now = time.time()
for f in glob.glob(os.path.join(CACHE_DIR, "aquavolt_backup_*.csv")):
    file_age_hours = (now - os.path.getmtime(f)) / 3600
    if file_age_hours > 3.0:
        print(f"[CLEANUP] Deleting expired cache file: {f} (Age: {file_age_hours:.1f} hours)")
        os.remove(f)

print("[DONE] Resilient sync complete. Data is secure.")
