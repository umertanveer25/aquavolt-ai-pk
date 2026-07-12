"""
Test file to run aquavolt_gsheet_logger main without pushing to sheets
"""
import os
import sys

# Ensure parent directory is in path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from aquavolt_gsheet_logger import main

try:
    print("[TEST] Running main(push_to_sheets=False)...")
    main(push_to_sheets=False)
    print("[TEST] Success!")
except Exception as e:
    print(f"[TEST ERROR] Failed to run: {e}")
    import traceback
    traceback.print_exc()
