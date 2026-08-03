import os
import sys
import csv
import pandas as pd
from datetime import datetime

# Add parent directory to path to import aquavolt logger
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import aquavolt_gsheet_logger

def main():
    print("Downloading 25+ days of history from public Google Sheet...")
    sheet_id = '1c2a-3t8fF2g_PX_0ape4ASTsbr5uX0Zb6YPzT8jtuN8'
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Sheet1'
    
    try:
        df = pd.read_csv(url, low_memory=False)
        print(f"Downloaded {len(df)} rows.")
        
        # Clean columns to match new schema
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        csv_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        os.makedirs(csv_dir, exist_ok=True)
        csv_file = os.path.join(csv_dir, "telemetry_log.csv")
        
        # We need the exact headers used in aquavolt_gsheet_logger.py
        # "timestamp", "latitude", "longitude", "sector_row", "sector_col",
        # "ndvi", "ndwi", "ndwi_real", "savi", "lai", "fcover",
        # "lst", "lst_modis", "Kc", "Ks", "Dr", "TAW", "RAW", "ETc", "water_need",
        # "air_temp", "humidity", "solar_rad", "precip",
        # "soil_temp", "soil_moisture", "et0_deficit_7d", "scene_id", "field_name"
        
        # Create a new df with exactly those columns, filling missing with empty string
        target_cols = [
            "timestamp", "latitude", "longitude", "sector_row", "sector_col",
            "ndvi", "ndwi", "ndwi_real", "savi", "lai", "fcover",
            "lst", "lst_modis", "Kc", "Ks", "Dr", "TAW", "RAW", "ETc", "water_need",
            "air_temp", "humidity", "solar_rad", "precip",
            "soil_temp", "soil_moisture", "et0_deficit_7d", "scene_id", "field_name"
        ]
        
        final_df = pd.DataFrame(columns=target_cols)
        
        # Map columns (capitalization is tricky, so we use lower case matching)
        target_cols_lower = [c.lower() for c in target_cols]
        for c in df.columns:
            if c in target_cols_lower:
                # Find original capitalization
                orig_c = target_cols[target_cols_lower.index(c)]
                final_df[orig_c] = df[c]
                
        print(f"Saving to {csv_file}")
        final_df.to_csv(csv_file, index=False)
        print("Success! Historical data saved.")
    except Exception as e:
        print(f"Error fetching history: {e}")

if __name__ == "__main__":
    main()
