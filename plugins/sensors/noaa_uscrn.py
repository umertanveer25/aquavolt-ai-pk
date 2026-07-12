"""
NOAA USCRN Climate Reference Network Plugin
=============================================
Pulls hourly quality-controlled climate data from NOAA's US Climate
Reference Network (USCRN) — the highest-accuracy weather stations
operated by NOAA with triple-redundant sensors.

Nearest USCRN station to Russell Ranch: Merced, CA or Bodega Bay, CA
Data: Air temp, precipitation, solar radiation, soil moisture at 5 depths,
      soil temperature at 5 depths, relative humidity, wind speed.
Access: Free, no API key required.
"""
import requests
from datetime import datetime, timedelta

SENSOR_INFO = {
    'name': 'NOAA USCRN (Triple-Redundant Climate)',
    'type': 'ground_truth',
    'resolution': 'point (5 depths)',
    'source': 'NOAA NCEI',
    'status': 'active',
}

# USCRN station near Davis CA — Merced (closest to Sacramento Valley)
STATION_ID = 'CA_Merced_23_WSW_NW'


def fetch():
    """Fetches hourly climate data from NOAA USCRN text files."""
    try:
        year = datetime.utcnow().year
        # NOAA serves hourly USCRN data as yearly text files
        url = (
            f"https://www.ncei.noaa.gov/pub/data/uscrn/products/hourly02/"
            f"{year}/CRNH0203-{year}-{STATION_ID}.txt"
        )

        r = requests.get(url, timeout=25)
        if r.status_code == 200:
            lines = r.text.strip().split('\n')
            if lines:
                # Parse the last complete record (latest hour)
                latest = lines[-1].split()
                if len(latest) >= 28:
                    def safe_float(idx, missing=-9999.0):
                        try:
                            v = float(latest[idx])
                            return v if v != missing else None
                        except (IndexError, ValueError):
                            return None

                    return {
                        'status': 'success',
                        'source': f'NOAA USCRN {STATION_ID} (LIVE ground truth)',
                        'utc_date': latest[1] if len(latest) > 1 else None,
                        'utc_time': latest[2] if len(latest) > 2 else None,
                        'air_temp_c': safe_float(8),
                        'precip_mm': safe_float(10),
                        'solar_wm2': safe_float(12),
                        'rh_pct': safe_float(26),
                        'soil_moisture_5cm': safe_float(14),
                        'soil_moisture_10cm': safe_float(15),
                        'soil_moisture_20cm': safe_float(16),
                        'soil_moisture_50cm': safe_float(17),
                        'soil_moisture_100cm': safe_float(18),
                        'soil_temp_5cm': safe_float(19),
                        'soil_temp_10cm': safe_float(20),
                        'soil_temp_20cm': safe_float(21),
                        'soil_temp_50cm': safe_float(22),
                        'soil_temp_100cm': safe_float(23),
                        'total_hourly_records': len(lines),
                    }
            return {'status': 'success', 'source': 'NOAA USCRN', 'note': 'No records in file'}

        # Fallback: try previous year if current year file not yet published
        prev_year = year - 1
        url2 = url.replace(str(year), str(prev_year))
        r2 = requests.get(url2, timeout=20)
        if r2.status_code == 200:
            lines2 = r2.text.strip().split('\n')
            if lines2:
                return {
                    'status': 'success',
                    'source': f'NOAA USCRN {STATION_ID} (LIVE - {prev_year} archive)',
                    'total_records': len(lines2),
                    'note': f'Current year file not available. Using {prev_year} archive.',
                }
        return {'status': 'http_error', 'code': r.status_code, 'fallback_code': r2.status_code}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}
