import os
import requests

lat = 38.54
lon = -121.87

# 1. NASA POWER API
power_code = f"""
import requests
from datetime import datetime

SENSOR_INFO = {{'name': 'NASA POWER (Agroclimatology)', 'type': 'weather', 'status': 'active'}}

def fetch():
    try:
        url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M&community=AG&longitude={lon}&latitude={lat}&start=20240101&end=20240101&format=JSON"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()['properties']['parameter']
            return {{'status': 'success', 'source': 'NASA POWER API', 'temp_c': data['T2M']['20240101']}}
    except Exception as e:
        return {{'status': 'error', 'msg': str(e)}}
    return {{'status': 'failed'}}
"""
with open('plugins/sensors/nasa_power.py', 'w') as f: f.write(power_code)

# 2. ISRIC SoilGrids
soilgrids_code = f"""
import requests

SENSOR_INFO = {{'name': 'ISRIC SoilGrids API', 'type': 'soil', 'status': 'active'}}

def fetch():
    try:
        url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}&property=clay&property=sand"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            layers = data['properties']['layers']
            clay = layers[0]['depths'][0]['values']['mean'] / 10.0 # Convert to percentage
            sand = layers[1]['depths'][0]['values']['mean'] / 10.0
            return {{'status': 'success', 'source': 'ISRIC API', 'clay_pct': clay, 'sand_pct': sand}}
    except Exception as e:
        return {{'status': 'error', 'msg': str(e)}}
    return {{'status': 'failed'}}
"""
with open('plugins/sensors/isric_soilgrids.py', 'w') as f: f.write(soilgrids_code)

# 3. Open-Meteo
meteo_code = f"""
import requests

SENSOR_INFO = {{'name': 'Open-Meteo (Forecasting & Archive)', 'type': 'weather', 'status': 'active'}}

def fetch():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=et0_fao_evapotranspiration,precipitation_sum&timezone=UTC"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()['daily']
            return {{'status': 'success', 'source': 'Open-Meteo API', 'et0_mm': data['et0_fao_evapotranspiration'][0]}}
    except Exception as e:
        return {{'status': 'error', 'msg': str(e)}}
    return {{'status': 'failed'}}
"""
with open('plugins/sensors/open_meteo.py', 'w') as f: f.write(meteo_code)

print('Successfully injected Live API code into plugins.')
