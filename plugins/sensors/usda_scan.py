"""
USDA SCAN Ground-Truth Soil Moisture Plugin
============================================
Pulls real-time soil moisture and temperature data from USDA NRCS
SCAN (Soil Climate Analysis Network) station near Davis, CA.
Station 2218 (Oakville) is the nearest SCAN station to Russell Ranch.

Data: Volumetric soil moisture at 5 depths (5, 10, 20, 50, 100 cm)
      + soil temperature at 5 depths
Access: Free, no API key required.
"""
import requests
from datetime import datetime, timedelta

SENSOR_INFO = {
    'name': 'USDA SCAN Ground Probes (Multi-Depth)',
    'type': 'ground_truth',
    'resolution': 'point (5 depths)',
    'source': 'USDA NRCS AWDB',
    'status': 'active',
}

# Nearest SCAN station to Russell Ranch (38.54, -121.87)
# Station 2218 = Oakville, CA (Napa/Sacramento Valley)
SCAN_STATION = 2218


def fetch():
    """Fetches real multi-depth soil moisture and temperature from USDA SCAN."""
    try:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

        # NRCS AWDB SOAP-to-REST proxy — public CSV endpoint
        url = (
            f"https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/"
            f"customSingleStationReport/daily/{SCAN_STATION}:CA:SCAN%7Cid=%22%22%7Cname/"
            f"{yesterday},{today}/"
            f"SMS:-2:value,SMS:-4:value,SMS:-8:value,SMS:-20:value,SMS:-40:value,"
            f"STO:-2:value,STO:-4:value,STO:-8:value,STO:-20:value,STO:-40:value,"
            f"TAVG::value,TMAX::value,TMIN::value,PREC::value"
        )

        r = requests.get(url, timeout=25)
        if r.status_code == 200:
            # Parse CSV — skip comment lines starting with #
            lines = [l for l in r.text.strip().split('\n') if not l.startswith('#') and l.strip()]
            if len(lines) >= 2:
                headers = lines[0].split(',')
                values = lines[-1].split(',')  # Latest day

                def safe_float(idx):
                    try:
                        return float(values[idx].strip())
                    except (IndexError, ValueError):
                        return None

                return {
                    'status': 'success',
                    'source': f'USDA SCAN Station {SCAN_STATION} (LIVE ground truth)',
                    'date': values[0].strip() if values else yesterday,
                    'soil_moisture_5cm': safe_float(1),
                    'soil_moisture_10cm': safe_float(2),
                    'soil_moisture_20cm': safe_float(3),
                    'soil_moisture_50cm': safe_float(4),
                    'soil_moisture_100cm': safe_float(5),
                    'soil_temp_5cm': safe_float(6),
                    'soil_temp_10cm': safe_float(7),
                    'soil_temp_20cm': safe_float(8),
                    'soil_temp_50cm': safe_float(9),
                    'soil_temp_100cm': safe_float(10),
                    'air_temp_avg': safe_float(11),
                    'air_temp_max': safe_float(12),
                    'air_temp_min': safe_float(13),
                    'precip_mm': safe_float(14),
                }
            return {'status': 'success', 'source': 'USDA SCAN (LIVE)', 'note': 'No data rows returned for date range'}
        return {'status': 'http_error', 'code': r.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
