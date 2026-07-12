"""
Quick Sheet Stats — AquaVolt-AI
Total records, days running, per-field breakdown
"""
import requests
import csv
import io
from datetime import datetime, timezone
from collections import defaultdict

SHEET_ID = '1c2a-3t8fF2g_PX_0ape4ASTsbr5uX0Zb6YPzT8jtuN8'
url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1'

print("[INFO] Fetching Google Sheet data...")
r = requests.get(url, timeout=30)
if r.status_code != 200:
    print(f"[ERROR] HTTP {r.status_code}")
    exit(1)

reader = csv.DictReader(io.StringIO(r.text))
rows = list(reader)

total_rows = len(rows)
print(f"\n{'='*55}")
print(f"  AquaVolt-AI  —  Google Sheet Stats")
print(f"{'='*55}")
print(f"  Total rows (incl. all sectors): {total_rows:,}")

# Parse timestamps
timestamps = set()
field_counts = defaultdict(int)
field_timestamps = defaultdict(set)
dates = set()
min_ts = None
max_ts = None

for row in rows:
    ts_raw = (row.get('timestamp') or row.get('Timestamp') or '').strip()
    field = (row.get('field_name') or row.get('Field Name') or 'Unknown').strip()
    
    if not ts_raw:
        continue
    
    try:
        # Try parsing
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M'):
            try:
                dt = datetime.strptime(ts_raw, fmt)
                break
            except ValueError:
                continue
        else:
            continue
        
        timestamps.add(ts_raw)
        field_counts[field] += 1
        field_timestamps[field].add(ts_raw)
        dates.add(dt.date())
        
        if min_ts is None or dt < min_ts:
            min_ts = dt
        if max_ts is None or dt > max_ts:
            max_ts = dt
    except Exception:
        continue

# Unique hourly slots (one per hour, not per sector)
unique_hours = len(timestamps)
total_days = len(dates)

if min_ts and max_ts:
    span_days = (max_ts.date() - min_ts.date()).days + 1
else:
    span_days = 0

now = datetime.now(timezone.utc).replace(tzinfo=None)
days_since_start = (now.date() - min_ts.date()).days + 1 if min_ts else 0

print(f"\n  [START]  First record   : {min_ts.strftime('%Y-%m-%d %H:%M UTC') if min_ts else 'N/A'}")
print(f"  [LATEST] Latest record  : {max_ts.strftime('%Y-%m-%d %H:%M UTC') if max_ts else 'N/A'}")
print(f"  [TIME]   Days running   : {days_since_start} days")
print(f"  [DATES]  Days with data : {total_days} unique calendar days")
print(f"  [HOURS]  Unique hours   : {unique_hours:,} hourly syncs")
print(f"\n  [TOTAL]  Total sheet rows : {total_rows:,}")
print(f"  (= {unique_hours} syncs x {total_rows // unique_hours if unique_hours else 0} sectors/sync)")

print(f"\n{'─'*55}")
print(f"  Per-Field Breakdown")
print(f"{'─'*55}")
print(f"  {'Field':<28} {'Rows':>8}  {'Uniq Hours':>10}")
print(f"  {'─'*28} {'─'*8}  {'─'*10}")

for field in sorted(field_counts.keys()):
    count = field_counts[field]
    unique_field_hours = len(field_timestamps[field])
    print(f"  {field:<28} {count:>8,}  {unique_field_hours:>10,}")

print(f"{'─'*55}")
print(f"  {'TOTAL':<28} {total_rows:>8,}  {unique_hours:>10,}")
print(f"{'='*55}\n")
