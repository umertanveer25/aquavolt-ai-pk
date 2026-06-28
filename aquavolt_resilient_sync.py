import os
import time
import glob
import subprocess
from datetime import datetime, timezone
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

CACHE_DIR = r"C:\aquavolt_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

print("======================================================================")
print("  AquaVolt-AI Resilient Sync [Hybrid Local/Cloud]")
print("======================================================================")

# 1. Connect to Google Sheets
print("[API] Checking Google Sheets for latest cloud sync...")
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# Ensure we are in the correct directory to find service_account.json
script_dir = os.path.dirname(os.path.abspath(__file__))
creds_path = os.path.join(script_dir, "service_account.json")

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open("AquaVolt-AI Telemetry Log").sheet1
    data = sheet.get_all_values()
except Exception as e:
    print(f"[ERROR] Could not connect to Google Sheets: {e}")
    exit(1)

# 2. Check latest timestamp
current_utc = datetime.now(timezone.utc)

github_succeeded = False
if len(data) > 1:
    last_row_timestamp = data[-1][0] # Timestamp is in Column A
    print(f"[STATUS] Latest cloud record: {last_row_timestamp}")
    try:
        # aquavolt_gsheet_logger logs as "%Y-%m-%d %H:%M:%S"
        row_time = datetime.strptime(last_row_timestamp, "%Y-%m-%d %H:%M:%S")
        if (row_time.year == current_utc.year and 
            row_time.month == current_utc.month and 
            row_time.day == current_utc.day and 
            row_time.hour == current_utc.hour):
            github_succeeded = True
    except Exception:
        pass

if github_succeeded:
    print(f"[OK] GitHub Actions Succeeded for hour {current_utc.hour}. Pulling local backup...")
else:
    print(f"[WARNING] GitHub Actions MISSING for hour {current_utc.hour}.")
    print("[FAILOVER] Initiating local telemetry engine to push to cloud...")
    try:
        # Run the logger script locally
        logger_script = os.path.join(script_dir, "aquavolt_gsheet_logger.py")
        subprocess.run(["python", logger_script], check=True, cwd=script_dir)
        # Refresh data to download backup
        data = sheet.get_all_values()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Local telemetry execution failed: {e}")
        exit(1)

# 3. Save local backup
headers = data[0]
rows = data[1:]
df = pd.DataFrame(rows, columns=headers)
backup_file = os.path.join(CACHE_DIR, f"aquavolt_backup_{current_utc.strftime('%Y%m%d_%H%M%S')}.csv")
df.to_csv(backup_file, index=False)
print(f"[BACKUP] Saved latest cloud dataset to local drive: {backup_file}")

# 4. Cleanup old backups (> 3 hours)
print("[CLEANUP] Scanning for local backups older than 3 hours...")
now = time.time()
for f in glob.glob(os.path.join(CACHE_DIR, "aquavolt_backup_*.csv")):
    file_age_hours = (now - os.path.getmtime(f)) / 3600
    if file_age_hours > 3.0:
        print(f"[CLEANUP] Deleting expired cache file: {f} (Age: {file_age_hours:.1f} hours)")
        os.remove(f)

print("[DONE] Resilient sync complete. Data is secure.")
