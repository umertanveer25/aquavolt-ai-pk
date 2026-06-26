import os
import sys
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scopes = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_json = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
if not creds_json:
    print("[ERROR] Missing GCP_SERVICE_ACCOUNT_KEY environment variable")
    sys.exit(1)

try:
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
    gc = gspread.authorize(creds)
except Exception as e:
    print(f"[ERROR] Auth failed: {e}")
    sys.exit(1)

sheet_name = "AquaVolt-AI Telemetry Log"
try:
    sh = gc.open(sheet_name)
    worksheet = sh.get_worksheet(0)
except Exception as e:
    print(f"[ERROR] Could not open sheet '{sheet_name}': {e}")
    sys.exit(1)

# Get all records
rows = worksheet.get_all_values()
if not rows:
    print("Sheet is empty.")
    sys.exit(0)

header = rows[0]
# Find indices of 'latitude' and 'longitude' columns
try:
    lat_idx = header.index("latitude")
    lon_idx = header.index("longitude")
except ValueError:
    print("[ERROR] Could not find latitude or longitude columns in header")
    sys.exit(1)

# Target coordinates to keep
target_lat = "38.5414"
target_lon = "-121.8688"

# We iterate backwards to safely delete rows without shifting indices of upcoming deletions
rows_to_delete = []
for idx in range(1, len(rows)):
    row = rows[idx]
    if len(row) > max(lat_idx, lon_idx):
        lat_val = row[lat_idx].strip()
        lon_val = row[lon_idx].strip()
        # If it doesn't match UC Davis, mark for deletion
        # (Handling potential float formats, e.g. 38.5414 or 38.54)
        try:
            is_match = abs(float(lat_val) - float(target_lat)) < 0.001 and abs(float(lon_val) - float(target_lon)) < 0.001
        except ValueError:
            is_match = False
            
        if not is_match:
            # Row index in Google Sheets is 1-indexed, so row index = idx + 1
            rows_to_delete.append(idx + 1)

if not rows_to_delete:
    print("No wrong coordinates found. Everything is clean!")
    sys.exit(0)

print(f"Found {len(rows_to_delete)} rows with wrong coordinates. Deleting...")

# Delete rows in reverse order to keep indices correct
for r in reversed(rows_to_delete):
    worksheet.delete_rows(r)
    print(f"Deleted row {r}")

print("Clean up finished successfully!")
