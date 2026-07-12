import concurrent.futures
import time

def fetch_source(name, val, delay=0.1, fail=False):
    time.sleep(delay)
    if fail: return (name, None)
    return (name, val)

def fuse_data(results_dict, weights_dict):
    valid_data = {}
    valid_weights = {}
    
    # 1. Filter out failed APIs
    for name, val in results_dict.items():
        if val is not None:
            valid_data[name] = val
            valid_weights[name] = weights_dict[name]
            
    if not valid_data:
        return None
        
    # 2. Dynamically re-normalize weights to 100%
    total_valid_weight = sum(valid_weights.values())
    normalized_weights = {k: v / total_valid_weight for k, v in valid_weights.items()}
    
    # 3. Compute weighted mathematical ensemble
    fused_value = 0
    for name, val in valid_data.items():
        fused_value += val * normalized_weights[name]
        
    return {
        'fused_value': round(fused_value, 4),
        'active_sources': list(valid_data.keys()),
        'normalized_weights': {k: round(v, 3) for k,v in normalized_weights.items()}
    }

def get_ensemble_optical(lat, lon, simulate_cloud_cover=False):
    # Simulated fetching across 5 sources concurrently
    sources = [
        ('Sentinel-2 (10m)', 0.85, 0.50, simulate_cloud_cover), # Fails if cloudy
        ('Landsat 8/9 (30m)', 0.82, 0.30, simulate_cloud_cover), # Fails if cloudy
        ('Sentinel-1 SAR (10m)', 0.79, 0.10, False), # SAR sees through clouds!
        ('MODIS MCD43A4 (500m)', 0.80, 0.05, False),
        ('Math Curve Default', 0.75, 0.05, False)
    ]
    
    weights = {s[0]: s[2] for s in sources}
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(fetch_source, s[0], s[1], fail=s[3]): s[0] for s in sources}
        for future in concurrent.futures.as_completed(futures):
            name, val = future.result()
            results[name] = val
            
    return fuse_data(results, weights)

if __name__ == '__main__':
    print('--- MULTI-SENSOR ENSEMBLE FUSION TEST ---')
    print('\n[Scenario 1: Clear Sky (All Optical Satellites Working)]')
    res_clear = get_ensemble_optical(38.5, -121.8, simulate_cloud_cover=False)
    print(f"Fused Kc Value: {res_clear['fused_value']}")
    print(f"Active Satellites: {res_clear['active_sources']}")

    print('\n[Scenario 2: Heavy Clouds (Sentinel-2 and Landsat 8 Fail)]')
    res_cloudy = get_ensemble_optical(38.5, -121.8, simulate_cloud_cover=True)
    print(f"Fused Kc Value: {res_cloudy['fused_value']}")
    print(f"Active Satellites: {res_cloudy['active_sources']}")
    print(f"Dynamically Re-weighted: {res_cloudy['normalized_weights']}")
