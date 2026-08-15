"""
AquaVolt-AI: Farm-Specific Drone Flight & Imagery Provenance Suite
==================================================================
1. Audits incoming flight logs and enforces strict UC Davis Russell Ranch farm geofencing.
2. Organizes flight telemetry and imagery strictly by target farm and field parcel:
   data/drone_flights/YYYY_MM_DD_<farm>_<field>/
     ├── flight_telemetry.csv
     ├── flight_metadata.json
     ├── PROVENANCE.json
     └── imagery/
           ├── Field_A_Corn/
           ├── Field_B_Alfalfa/
           ├── Field_C_Fallow/
           └── Field_D_Tomato/
"""

import os
import shutil
import hashlib
import json
import pandas as pd
from datetime import datetime, timezone

# UC Davis Russell Ranch Exact Farm Coordinates & Parcels
FARM_NAME = "UC Davis Russell Ranch Sustainable Agricultural Facility"
FARM_LAT_MIN = 38.5300
FARM_LAT_MAX = 38.5700
FARM_LON_MIN = -121.9000
FARM_LON_MAX = -121.7500

FIELD_PARCELS = [
    {
        "field_id": "Field_A_Corn",
        "crop": "Corn (Zea mays)",
        "bbox": [-121.8790, 38.5480, -121.8720, 38.5540]
    },
    {
        "field_id": "Field_B_Alfalfa",
        "crop": "Alfalfa (Medicago sativa)",
        "bbox": [-121.8860, 38.5480, -121.8800, 38.5540]
    },
    {
        "field_id": "Field_C_Fallow",
        "crop": "Fallow / Bare Soil",
        "bbox": [-121.8860, 38.5420, -121.8800, 38.5475]
    },
    {
        "field_id": "Field_D_Tomato",
        "crop": "Processing Tomato",
        "bbox": [-121.8790, 38.5420, -121.8720, 38.5475]
    }
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
INCOMING_DIR = os.path.join(DATA_DIR, 'incoming_validation')
DRONE_FLIGHTS_DIR = os.path.join(DATA_DIR, 'drone_flights')

os.makedirs(INCOMING_DIR, exist_ok=True)
os.makedirs(DRONE_FLIGHTS_DIR, exist_ok=True)

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def identify_primary_field(df):
    """Identify which specific farm field was the primary target of this flight."""
    field_counts = {p["field_id"]: 0 for p in FIELD_PARCELS}
    for _, row in df.iterrows():
        lat, lon = row["latitude"], row["longitude"]
        for p in FIELD_PARCELS:
            b = p["bbox"]
            if b[1] <= lat <= b[3] and b[0] <= lon <= b[2]:
                field_counts[p["field_id"]] += 1
                break
    primary = max(field_counts, key=field_counts.get)
    return primary if field_counts[primary] > 0 else "Russell_Ranch_MultiField"

def organize_flight_folder(filepath, df, sha_hash, is_approved):
    """
    Creates a dedicated dated and farm/field-specific sub-folder on GitHub.
    """
    try:
        first_time_str = str(df['timestamp'].iloc[0])
        dt = pd.to_datetime(first_time_str).tz_localize(None)
        date_str = dt.strftime('%Y_%m_%d')
    except Exception:
        date_str = datetime.now(timezone.utc).strftime('%Y_%m_%d')
        
    primary_field = identify_primary_field(df)
    folder_name = f"{date_str}_{primary_field}"
    flight_dir = os.path.join(DRONE_FLIGHTS_DIR, folder_name)
    imagery_dir = os.path.join(flight_dir, "imagery")
    os.makedirs(flight_dir, exist_ok=True)
    os.makedirs(imagery_dir, exist_ok=True)
    
    # Create farm field subfolders for stills/video frames
    for p in FIELD_PARCELS:
        os.makedirs(os.path.join(imagery_dir, p["field_id"]), exist_ok=True)
    
    # 1. Save Telemetry CSV
    dest_csv = os.path.join(flight_dir, "flight_telemetry.csv")
    df.to_csv(dest_csv, index=False)
    
    # 2. Metadata JSON (Strictly Farm-Specific)
    sensor_id = str(df['sensor_id'].iloc[0]) if 'sensor_id' in df.columns else "FLIR-G300a-SN9021"
    mean_methane = float(df['methane_ppm'].mean()) if 'methane_ppm' in df.columns else 2.0
    
    meta = {
        "flight_date": date_str,
        "facility_name": FARM_NAME,
        "target_field": primary_field,
        "farm_geofence": {
            "lat_min": FARM_LAT_MIN,
            "lat_max": FARM_LAT_MAX,
            "lon_min": FARM_LON_MIN,
            "lon_max": FARM_LON_MAX
        },
        "sensor_payload": sensor_id,
        "sensor_type": "Optical Gas Imaging (OGI) & Thermal Radiometric Stills",
        "total_farm_waypoints": len(df),
        "mean_methane_ppm": round(mean_methane, 3),
        "audit_status": "APPROVED" if is_approved else "REJECTED",
        "sha256_checksum": sha_hash,
        "farm_specific_storage": {
            "telemetry_file": "flight_telemetry.csv",
            "metadata_file": "flight_metadata.json",
            "imagery_directories": [f"imagery/{p['field_id']}/" for p in FIELD_PARCELS],
            "provenance_file": "PROVENANCE.json"
        }
    }
    with open(os.path.join(flight_dir, "flight_metadata.json"), "w", encoding="utf-8") as mf:
        json.dump(meta, mf, indent=2)
        
    # 3. Individual Provenance Token
    prov = {
        "record_type": "UAV_DRONE_FARM_PROVENANCE",
        "farm": FARM_NAME,
        "target_field": primary_field,
        "sha256": sha_hash,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "status": "APPROVED" if is_approved else "REJECTED"
    }
    with open(os.path.join(flight_dir, "PROVENANCE.json"), "w", encoding="utf-8") as pf:
        json.dump(prov, pf, indent=2)
        
    print(f"  [STORAGE] [PASS] Farm-specific flight folder created: data/drone_flights/{folder_name}/")

def verify_drone_flight_log(filepath):
    filename = os.path.basename(filepath)
    print(f"\n[AUDIT] Initiating provenance verification for: {filename}")
    
    file_hash = calculate_sha256(filepath)
    print(f"  -> Cryptographic SHA-256 Checksum: {file_hash}")
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"  [REJECT] CSV parsing failed: {e}")
        return False, file_hash, None
        
    required_cols = ['latitude', 'longitude', 'timestamp', 'sensor_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"  [REJECT] Telemetry log missing required headers: {missing_cols}")
        return False, file_hash, df
        
    # Strict Farm Geofence Boundary Check
    lat_in_bounds = df['latitude'].between(FARM_LAT_MIN, FARM_LAT_MAX).all()
    lon_in_bounds = df['longitude'].between(FARM_LON_MIN, FARM_LON_MAX).all()
    
    if not (lat_in_bounds and lon_in_bounds):
        print(f"  [REJECT] Spatial violation! Coordinates outside Russell Ranch farm boundaries.")
        return False, file_hash, df
        
    print(f"  [PASS] All GPS coordinates verified strictly within {FARM_NAME} boundaries.")
    return True, file_hash, df

def main():
    print("=" * 75)
    print("  AquaVolt-AI: Farm-Specific Drone Flight & Imagery Organizer")
    print("=" * 75)
    
    files = [os.path.join(INCOMING_DIR, f) for f in os.listdir(INCOMING_DIR) if f.endswith('.csv')]
    if not files:
        print("[INFO] No new flight logs in data/incoming_validation/.")
        return
        
    approved_count = 0
    audit_trail = []
    
    for f_path in files:
        success, sha_hash, df = verify_drone_flight_log(f_path)
        if success and df is not None:
            approved_count += 1
            organize_flight_folder(f_path, df, sha_hash, is_approved=True)
            
        audit_trail.append({
            'file': os.path.basename(f_path),
            'sha256': sha_hash,
            'status': 'APPROVED' if success else 'REJECTED'
        })
        
    audit_df = pd.DataFrame(audit_trail)
    audit_df.to_csv(os.path.join(DATA_DIR, 'drone_audit_ledger.csv'), index=False)
    print(f"\nAudit complete: {approved_count}/{len(files)} flight missions validated.")
    print("=" * 75)

if __name__ == "__main__":
    main()
