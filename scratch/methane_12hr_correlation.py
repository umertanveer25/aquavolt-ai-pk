import sys
import os
import random
import numpy as np

# Ensure api directory is in path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'api'))
from methane_downscaler import apply_downscaling

def run_12hr_test():
    print("=" * 60)
    print("  12-HOUR METHANE vs WEATHER STATION CORRELATION REPORT")
    print("=" * 60)
    
    # We track a single specific 10m sector (e.g., Field-A Corn) over 12 hours
    # Simulating a diurnal cycle from 6 AM to 6 PM
    hours = list(range(6, 18)) 
    
    soil_moistures = []
    temperatures = []
    methane_outputs = []
    
    macro_methane_base = 0.045
    
    print("Simulating Weather Station Data (Diurnal Temp + 8 AM Irrigation Event)...\n")
    
    for h in hours:
        # Temperature peaks around 2 PM (14:00)
        temp = 20.0 + 15.0 * np.sin(np.pi * (h - 6) / 12) 
        
        # Soil moisture drops slightly as it dries, but irrigation hits at 8 AM
        sm = 0.25 - 0.005 * (h - 6)
        if h == 8:
            sm += 0.20 # Huge irrigation spike
        elif h > 8:
            sm = 0.45 - 0.01 * (h - 8) # Dries out after irrigation
            
        soil_moistures.append(sm)
        temperatures.append(temp)
        
        # Downscaler needs: [ndvi, lst_celsius, clay_ratio, soil_moist, slope]
        features = [[0.65, temp, 0.35, sm, 1.2]]
        
        # The macro satellite reading stays roughly the same over the day
        macro = macro_methane_base + random.uniform(-0.001, 0.001)
        
        methane_res = apply_downscaling(macro, features)
        methane = methane_res[0] if isinstance(methane_res, (list, np.ndarray)) else methane_res
        methane_outputs.append(methane)
        
    # Calculate Statistical Correlation
    corr_sm = np.corrcoef(soil_moistures, methane_outputs)[0,1]
    corr_temp = np.corrcoef(temperatures, methane_outputs)[0,1]
    
    print("-" * 60)
    print("  CORRELATION STATISTICS (Pearson r)")
    print("-" * 60)
    print(f"Methane vs Soil Moisture : {corr_sm:+.4f} (Ideal: Positive)")
    print(f"Methane vs Temperature   : {corr_temp:+.4f} (Ideal: Positive)")
    print("-" * 60)
    
    print("\nHOURLY BREAKDOWN:")
    print("Time  | Temp (°C) | Moisture (m³/m³) | Methane (mol/m²)")
    print("-" * 60)
    for i, h in enumerate(hours):
        event = "  <-- IRRIGATION EVENT" if h == 8 else ""
        print(f"{h:02d}:00 |   {temperatures[i]:5.1f}   |      {soil_moistures[i]:.3f}       |    {methane_outputs[i]:.5f}{event}")

if __name__ == '__main__':
    run_12hr_test()
