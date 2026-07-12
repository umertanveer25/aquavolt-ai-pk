"""
Download a representative slice of live telemetry data for the public teaser app
"""
import pandas as pd
import os

SHEET_ID = '1c2a-3t8fF2g_PX_0ape4ASTsbr5uX0Zb6YPzT8jtuN8'
url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1'

print("[INFO] Fetching live data for teaser...")
try:
    df = pd.read_csv(url, low_memory=False)
    print(f"Total rows fetched: {len(df)}")
    
    # We want a clean slice of the last 3-4 days of data to keep the file lightweight (~15-20MB max, or even less)
    # Let's take the last 15,000 rows (approx. 2-3 days of data for all 4 fields)
    slice_df = df.tail(10240) # Exactly 40 hours of data for all 4 fields (4 * 64 * 40 = 10240)
    
    os.makedirs('data', exist_ok=True)
    teaser_path = 'data/teaser_telemetry.csv'
    slice_df.to_csv(teaser_path, index=False)
    print(f"[OK] Teaser dataset saved to {teaser_path} ({len(slice_df)} rows)")
except Exception as e:
    print(f"[ERROR] Failed to create teaser dataset: {e}")
