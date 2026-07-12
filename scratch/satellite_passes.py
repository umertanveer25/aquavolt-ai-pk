"""
Satellite Pass Stats — AquaVolt-AI
Count unique satellite passes from scene_id column
"""
import requests
import csv
import io
from collections import defaultdict, Counter

SHEET_ID = '1c2a-3t8fF2g_PX_0ape4ASTsbr5uX0Zb6YPzT8jtuN8'
url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1'

print("[INFO] Fetching Google Sheet data...")
r = requests.get(url, timeout=60)
reader = csv.DictReader(io.StringIO(r.text))
rows = list(reader)

print(f"Total rows: {len(rows):,}")

# Find scene_id column (could be named differently)
sample = rows[0] if rows else {}
scene_col = None
for k in sample.keys():
    kl = k.strip().lower().replace(' ', '_')
    if 'scene' in kl:
        scene_col = k
        break

if not scene_col:
    print("[ERROR] No scene_id column found!")
    print(f"Available columns: {list(sample.keys())}")
    exit(1)

print(f"Scene column found: '{scene_col}'")

# Collect all unique scene IDs with their timestamps and fields
scene_timestamps = defaultdict(set)   # scene_id -> set of timestamps
scene_fields = defaultdict(set)       # scene_id -> set of fields
scene_first_seen = {}                 # scene_id -> earliest timestamp
all_scenes = []

ts_col = None
field_col = None
for k in sample.keys():
    kl = k.strip().lower().replace(' ', '_')
    if kl == 'timestamp':
        ts_col = k
    if 'field' in kl and 'name' in kl:
        field_col = k

for row in rows:
    sid = (row.get(scene_col) or '').strip()
    ts = (row.get(ts_col) or '').strip() if ts_col else ''
    field = (row.get(field_col) or '').strip() if field_col else ''
    
    if not sid or sid.lower() in ('n/a', 'none', '', 'fallback'):
        continue
    
    scene_timestamps[sid].add(ts)
    scene_fields[sid].add(field)
    
    if sid not in scene_first_seen:
        scene_first_seen[sid] = ts

# Categorize by satellite
sentinel2_scenes = []
landsat_scenes = []
sar_scenes = []
other_scenes = []

for sid in scene_timestamps:
    sid_lower = sid.lower()
    if 's2' in sid_lower or 'sentinel-2' in sid_lower or sid.startswith('S2'):
        sentinel2_scenes.append(sid)
    elif 'lc08' in sid_lower or 'lc09' in sid_lower or 'landsat' in sid_lower or 'LC0' in sid:
        landsat_scenes.append(sid)
    elif 's1' in sid_lower or 'sar' in sid_lower or 'grd' in sid_lower:
        sar_scenes.append(sid)
    else:
        other_scenes.append(sid)

total_unique = len(scene_timestamps)

print(f"\n{'='*65}")
print(f"  AquaVolt-AI -- Satellite Pass Summary")
print(f"{'='*65}")
print(f"  Total unique satellite scenes used: {total_unique}")
print(f"")
print(f"  By Satellite:")
print(f"    Sentinel-2 (optical, 10m) : {len(sentinel2_scenes)} passes")
print(f"    Landsat-8/9 (optical, 30m): {len(landsat_scenes)} passes")
print(f"    Sentinel-1 SAR (radar)    : {len(sar_scenes)} passes")
print(f"    Other/unclassified        : {len(other_scenes)} passes")

print(f"\n{'='*65}")
print(f"  Detailed Scene List (sorted by first seen)")
print(f"{'='*65}")
print(f"  {'#':<4} {'Scene ID':<55} {'First Seen':<20}")
print(f"  {'--':<4} {'--':<55} {'--':<20}")

sorted_scenes = sorted(scene_first_seen.items(), key=lambda x: x[1])
for i, (sid, first_ts) in enumerate(sorted_scenes, 1):
    # Truncate long IDs
    sid_display = sid[:52] + '...' if len(sid) > 55 else sid
    print(f"  {i:<4} {sid_display:<55} {first_ts:<20}")

print(f"{'='*65}")

# Show how many rows used each scene
print(f"\n  Rows per scene:")
for sid, first_ts in sorted_scenes:
    n_rows = sum(1 for row in rows if (row.get(scene_col) or '').strip() == sid)
    sid_short = sid[:45] + '...' if len(sid) > 48 else sid
    print(f"    {sid_short:<48} {n_rows:>6,} rows")

print(f"\n{'='*65}\n")
