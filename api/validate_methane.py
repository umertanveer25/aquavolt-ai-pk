import os
import sys
import numpy as np

# Ensure api directory is in path
api_path = os.path.dirname(os.path.abspath(__file__))
if api_path not in sys.path:
    sys.path.append(api_path)

from methane_downscaler import apply_downscaling

def run_validation():
    print("=" * 60)
    print("  AquaVolt-AI: Sentinel-5P Methane Downscaler Validation")
    print("=" * 60)
    
    # Simulate a macro-level satellite reading (e.g., from Sentinel-5P 5.5km grid)
    # Unit: mol/m^2
    macro_methane = 0.0450
    print(f"[TEST] Input Sentinel-5P Macro Reading: {macro_methane} mol/m²\n")

    # Generate synthetic telemetry for 256 sectors (4 fields x 64 sectors)
    # Features: [ndvi, lst_measured, clay, soil_moist, slope]
    print("[TEST] Generating 256 physical sector variations (NDVI, Moisture, LST)...")
    np.random.seed(42) # For reproducible validation
    
    features = []
    for _ in range(256):
        # Create physical variance
        # High moisture should correlate with higher methane logically (handled by downscaler)
        moist = np.random.uniform(0.1, 0.4)
        ndvi = np.random.uniform(0.1, 0.9)
        lst = np.random.uniform(20.0, 35.0)
        clay = np.random.uniform(20.0, 40.0)
        slope = np.random.uniform(1.0, 1.25)
        
        features.append([ndvi, lst, clay, moist, slope])
        
    print("[TEST] Running Physics-Informed Downscaling...")
    
    # Run the downscaler
    downscaled_anomalies = apply_downscaling(macro_methane, features)
    
    print("\n" + "-" * 60)
    print("  LAYER 1: MASS CONSERVATION CHECK")
    print("-" * 60)
    
    # Calculate the mean of all downscaled sectors
    downscaled_mean = np.mean(downscaled_anomalies)
    error = abs(macro_methane - downscaled_mean)
    
    print(f"Original Satellite Value : {macro_methane:.6f}")
    print(f"Downscaled Sector Mean   : {downscaled_mean:.6f}")
    print(f"Conservation Error       : {error:.6f}")
    
    if error < 1e-4:
        print(">> [PASS] Mass Conservation strictly preserved. No data hallucinated.")
    else:
        print(">> [FAIL] Mass Conservation violated.")
        
    print("\n" + "-" * 60)
    print("  LAYER 2: PHYSICAL CONSISTENCY CHECK")
    print("-" * 60)
    
    # Extract features for correlation
    moistures = [f[3] for f in features]
    ndvis = [f[0] for f in features]
    
    # Compute Pearson correlation coefficient
    corr_moisture = np.corrcoef(moistures, downscaled_anomalies)[0, 1]
    corr_ndvi = np.corrcoef(ndvis, downscaled_anomalies)[0, 1]
    
    print(f"Correlation (Methane vs Soil Moisture): {corr_moisture:+.4f}")
    print(f"Correlation (Methane vs NDVI)         : {corr_ndvi:+.4f}")
    
    # Methane is largely driven by anaerobic (high moisture) conditions and active vegetation
    if corr_moisture > 0:
        print(">> [PASS] Positive correlation with Soil Moisture (Anaerobic consistency)")
    else:
        print(">> [WARNING] Unexpected negative correlation with moisture.")
        
    print("=" * 60)

if __name__ == "__main__":
    run_validation()
