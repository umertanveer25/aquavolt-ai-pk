import os
import sys
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scopes = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

local_creds_path = r"C:\Users\umert\aquavolt-ai-pk\service_account.json"
if not os.path.exists(local_creds_path):
    print("Credentials file not found.")
    sys.exit(1)

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(local_creds_path, scopes)
    gc = gspread.authorize(creds)
except Exception as e:
    print(f"Error authorizing credentials: {e}")
    sys.exit(1)

sheet_name = "AquaVolt-AI Telemetry Log"
try:
    sh = gc.open(sheet_name)
    print(f"Connected to Spreadsheet: '{sheet_name}'")
    worksheets = sh.worksheets()
    print(f"Found {len(worksheets)} worksheet tabs:")
    total_records = 0
    for ws in worksheets:
        # Get count of values in column 1 (to ignore empty rows at the end of the sheet)
        timestamps = ws.col_values(1)
        # minus 1 for header row
        records_count = max(0, len(timestamps) - 1)
        print(f" - Tab: '{ws.title}' | Total Rows (including headers): {ws.row_count} | Actual Telemetry Records: {records_count}")
        total_records += records_count
    print(f"\nTotal Telemetry Records across all tabs: {total_records}")
except Exception as e:
    print(f"Error accessing spreadsheet: {e}")
