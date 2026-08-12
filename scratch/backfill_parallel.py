import os
import sys
import glob
import pandas as pd
from datetime import datetime, timezone
from concurrent.futures import ProcessPoolExecutor, as_completed

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_dir)
sys.path.append(project_dir)

# Identify missing hours
def get_missing_hours():
    csv_path = "data/telemetry_log_2026_06_to_08.csv"
    if not os.path.exists(csv_path):
        print("[-] Telemetry log not found!")
        return []
        
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    unique_hours = set(df['timestamp'].unique())
    
    # Check range from August 7th 18:00 UTC to August 11th 09:00 UTC (14:00 PKT)
    start = pd.to_datetime('2026-08-07 18:00:00+00:00')
    now_utc = datetime.now(timezone.utc)
    end = datetime(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, 0, 0, tzinfo=timezone.utc)
    
    full_range = pd.date_range(start=start, end=end, freq='h', tz='UTC')
    missing = []
    for h in full_range:
        h_naive = pd.to_datetime(h).tz_localize(None)
        if h_naive not in unique_hours:
            missing.append(h)
            
    return missing

# Worker function to process a single hour
def run_worker(dt, temp_filename):
    import builtins
    import io
    import sys
    
    # 1. Mock builtins.open to avoid writing/truncating README.md or PROVENANCE.json concurrently
    original_open = builtins.open
    
    def mock_open(file, mode="r", *args, **kwargs):
        filename = str(file)
        if "README.md" in filename or "PROVENANCE.json" in filename:
            if "w" in mode:
                return io.StringIO()
            elif "r" in mode:
                return original_open(file, mode, *args, **kwargs)
        return original_open(file, mode, *args, **kwargs)
        
    builtins.open = mock_open
    
    # 2. Patch get_csv_filename to write to the temp file and disable Google Sheets integration
    import aquavolt_gsheet_logger
    aquavolt_gsheet_logger.get_csv_filename = lambda: temp_filename
    aquavolt_gsheet_logger.get_gspread_client = lambda: (_ for _ in ()).throw(Exception("Google Sheets disabled during backfill"))
    
    print(f"[WORKER] Starting backfill for: {dt.strftime('%Y-%m-%d %H:%M UTC')}")
    try:
        aquavolt_gsheet_logger.main(push_to_sheets=True, override_time=dt)
        return {"status": "success", "dt": dt, "file": temp_filename}
    except SystemExit as se:
        # If sys.exit(0) was called due to duplicate hours guard, it's fine
        if se.code == 0:
            return {"status": "success", "dt": dt, "file": temp_filename}
        return {"status": "error", "dt": dt, "error": f"SystemExit code {se.code}"}
    except Exception as e:
        return {"status": "error", "dt": dt, "error": str(e)}

def main():
    missing = get_missing_hours()
    total = len(missing)
    if total == 0:
        print("[OK] No missing hours found! Dataset is complete.")
        return
        
    print(f"[START] Found {total} missing hours. Preparing parallel execution (8 workers)...")
    
    # Clean up any existing temp files from previous aborted runs
    for f in glob.glob("data/telemetry_log_2026_06_to_08_temp_*.csv"):
        try:
            os.remove(f)
        except Exception:
            pass
            
    tasks = []
    # Submit tasks
    with ProcessPoolExecutor(max_workers=8) as executor:
        for idx, h in enumerate(missing):
            dt = h.to_pydatetime()
            temp_file = f"telemetry_log_2026_06_to_08_temp_{idx}_{dt.strftime('%Y%m%d%H')}.csv"
            future = executor.submit(run_worker, dt, temp_file)
            tasks.append(future)
            
        completed_count = 0
        for future in as_completed(tasks):
            res = future.result()
            completed_count += 1
            if res["status"] == "success":
                print(f"[{completed_count}/{total}] Success for {res['dt'].strftime('%Y-%m-%d %H:%M UTC')}")
            else:
                print(f"[{completed_count}/{total}] [-] Failed for {res['dt'].strftime('%Y-%m-%d %H:%M UTC')}: {res['error']}")
                
    # Merge temp CSVs into the main telemetry log CSV
    temp_files = glob.glob("data/telemetry_log_2026_06_to_08_temp_*.csv")
    if not temp_files:
        print("[-] No temp files generated. Exiting.")
        return
        
    print(f"\nMerging {len(temp_files)} temp files into main CSV...")
    main_csv_path = "data/telemetry_log_2026_06_to_08.csv"
    
    # Read existing main CSV
    main_df = pd.read_csv(main_csv_path)
    dfs = [main_df]
    
    for tf in temp_files:
        try:
            df = pd.read_csv(tf)
            dfs.append(df)
        except Exception as e:
            print(f"[-] Error reading temp file {tf}: {e}")
            
    # Concatenate all dataframes
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Drop duplicates by timestamp, field_name, sector_row, and sector_col to be absolutely safe
    merged_df = merged_df.drop_duplicates(subset=["timestamp", "field_name", "sector_row", "sector_col"])
    
    # Sort by timestamp, then sector_row, then sector_col to maintain file structure
    merged_df = merged_df.sort_values(by=["timestamp", "sector_row", "sector_col"])
    
    # Save back to main CSV
    merged_df.to_csv(main_csv_path, index=False)
    print(f"[OK] Main CSV updated. Total rows: {len(merged_df)}")
    
    # Clean up temp files
    for tf in temp_files:
        try:
            os.remove(tf)
        except Exception:
            pass
            
    print("Cleanup complete. Committing and pushing to GitHub...")
    
    # Git add, commit, and push
    import subprocess
    subprocess.run(["git", "add", main_csv_path])
    subprocess.run(["git", "commit", "-m", "chore: backfill missing telemetry data gaps in parallel [skip ci]"])
    subprocess.run(["git", "push", "origin", "main"])
    print("[SUCCESS] Pushed to GitHub main successfully!")

if __name__ == "__main__":
    main()
