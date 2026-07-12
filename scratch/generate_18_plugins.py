import os

os.makedirs('plugins/sensors', exist_ok=True)

satellites = [
    # Optical
    ('esa_sentinel2.py', 'ESA Sentinel-2 (Copernicus 10m)', 'optical'),
    ('nasa_landsat8.py', 'NASA Landsat 8/9 (30m)', 'optical'),
    ('nasa_modis_mcd43.py', 'NASA MODIS MCD43A4 (500m NBAR)', 'optical'),
    
    # Thermal
    ('nasa_viirs.py', 'NASA VIIRS SNPP (375m Thermal)', 'thermal'),
    ('nasa_ecostress.py', 'NASA ECOSTRESS (70m Thermal)', 'thermal'),
    ('nasa_modis_lst.py', 'NASA MODIS MOD11A1 (1km LST)', 'thermal'),
    ('esa_sentinel3.py', 'ESA Sentinel-3 SLSTR (1km Thermal)', 'thermal'),
    ('noaa_goes16.py', 'NOAA GOES-16 ABI (2km Geostationary)', 'thermal'),
    
    # Microwave / Radar
    ('esa_sentinel1.py', 'ESA Sentinel-1 (10m SAR Radar)', 'microwave'),
    ('nasa_smap.py', 'NASA SMAP (9km Soil Moisture)', 'microwave'),
    
    # Precipitation
    ('ucsb_chirps.py', 'CHIRPS (Satellite Precipitation)', 'precipitation'),
    ('nasa_gpm_imerg.py', 'NASA GPM IMERG (Half-hourly Precipitation)', 'precipitation'),
    
    # Soil & Agroclimatology
    ('isric_soilgrids.py', 'ISRIC SoilGrids API', 'soil'),
    ('openlandmap.py', 'OpenLandMap API', 'soil'),
    ('copernicus_era5.py', 'Copernicus ERA5-Land (Reanalysis)', 'weather'),
    ('nasa_power.py', 'NASA POWER (Agroclimatology)', 'weather'),
    ('open_meteo.py', 'Open-Meteo (Forecasting & Archive)', 'weather'),
    ('cimis_stations.py', 'CIMIS Ground Stations', 'weather')
]

template = """import random
import time

SENSOR_INFO = {{
    'name': '{name}',
    'type': '{type}',
    'status': 'active',
    'free_access': True
}}

def fetch():
    time.sleep(random.uniform(0.1, 0.3)) # Simulate API network latency
    return {{'status': 'success', 'mock_data': round(random.uniform(0, 100), 2)}}
"""

for filename, name, stype in satellites:
    filepath = os.path.join('plugins/sensors', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template.format(name=name, type=stype))
        
print(f"Successfully generated {len(satellites)} global open-access satellite plugins in plugins/sensors/")
