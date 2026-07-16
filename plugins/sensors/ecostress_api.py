"""
ECOSTRESS NASA Plugin — Independent ET Validation (Area Task)
===================================================
Fetches ET from NASA ECOSTRESS ECO3ETPTJPL product via AppEEARS API.
"""
import os
import json
import hashlib
import time
import requests
from datetime import datetime
import glob

SENSOR_INFO = {
    'name': 'ECOSTRESS ECO_L3T_JET (Tiled Daily ET)',
    'type': 'independent_validation',
    'resolution': '70m',
    'source': 'NASA AppEEARS — ECO_L3T_JET.002',
    'status': 'active',
    'citation': 'Fisher et al. (2020). ECOSTRESS: NASA\'s next generation mission to measure '
                'evapotranspiration from the International Space Station. WRR. doi:10.1029/2019WR026058',
}

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ecostress_cache")
APPEEARS_BASE = "https://appeears.earthdatacloud.nasa.gov/api"


def _cache_key(bbox, start_date, end_date):
    raw = f"ecostress_area_{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}_{start_date}_{end_date}"
    return hashlib.md5(raw.encode()).hexdigest()

def _get_token(user, pwd):
    r = requests.post(f"{APPEEARS_BASE}/login", auth=(user, pwd), timeout=20)
    if r.status_code == 200:
        return r.json().get("token")
    return None

def fetch_area(bbox, start_date, end_date):
    """
    Submit and retrieve an AppEEARS area sample request for ECOSTRESS ET.

    Parameters
    ----------
    bbox         : list   — [min_lon, min_lat, max_lon, max_lat]
    start_date   : str    — 'YYYY-MM-DD'
    end_date     : str    — 'YYYY-MM-DD'

    Returns
    -------
    dict with status, data (dict of date string -> path to local .tif file)
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    c_key = _cache_key(bbox, start_date, end_date)
    task_dir = os.path.join(CACHE_DIR, c_key)
    
    # Check if we already have files for this task
    if os.path.exists(task_dir):
        tifs = glob.glob(os.path.join(task_dir, "*.tif"))
        if tifs:
            # Parse dates from AppEEARS filenames, usually ends with _dYYYYMMDD_...
            data_map = {}
            for tif in tifs:
                # AppEEARS area files look like: ECO_L3T_JET_002_ETdaily_d20240626_...
                # We'll try to extract date.
                parts = os.path.basename(tif).split('_')
                for p in parts:
                    if p.startswith('doy') and len(p) >= 10:
                        try:
                            year = p[3:7]
                            doy = p[7:10]
                            dt = datetime.strptime(f"{year}{doy}", "%Y%j").strftime("%Y-%m-%d")
                            data_map[dt] = tif
                        except:
                            pass
                    elif p.startswith('d20') and len(p) == 9:
                        try:
                            dt = datetime.strptime(p[1:], "%Y%m%d").strftime("%Y-%m-%d")
                            data_map[dt] = tif
                        except:
                            pass
            if data_map:
                return {"status": "success", "data": data_map, "source": "ECOSTRESS (CACHED)"}

    user = os.getenv("EARTHDATA_USER")
    pwd  = os.getenv("EARTHDATA_PASS")
    if not user or not pwd:
        return {"status": "error", "msg": "EARTHDATA_USER and EARTHDATA_PASS environment variables not set."}

    token = _get_token(user, pwd)
    if not token:
        return {"status": "error", "msg": "AppEEARS authentication failed. Check EARTHDATA credentials."}

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        start_appeears = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m-%d-%Y")
        end_appeears = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m-%d-%Y")
    except Exception:
        start_appeears = start_date
        end_appeears = end_date

    min_lon, min_lat, max_lon, max_lat = bbox
    task = {
        "task_type": "area",
        "task_name": f"AquaVolt_ECO_Area_{c_key}",
        "params": {
            "dates": [{"startDate": start_appeears, "endDate": end_appeears}],
            "layers": [{"product": "ECO_L3T_JET.002", "layer": "PTJPLSMinst"}],
            "output": {"format": {"type": "geotiff"}, "projection": "geographic"},
            "geo": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[min_lon, min_lat], [max_lon, min_lat], [max_lon, max_lat], [min_lon, max_lat], [min_lon, min_lat]]]
                    }
                }]
            }
        }
    }

    try:
        r = requests.post(f"{APPEEARS_BASE}/task", headers=headers, json=task, timeout=30)
        if r.status_code not in (200, 202):
            return {"status": "http_error", "code": r.status_code, "text": r.text[:300]}

        task_id = r.json().get("task_id")
        if not task_id:
            return {"status": "error", "msg": f"No task_id in response: {r.text[:300]}"}

        print(f"[ECOSTRESS] Task {task_id} submitted. Polling for results (up to 45 min)...")
        for _ in range(270):
            time.sleep(10)
            try:
                status_r = requests.get(f"{APPEEARS_BASE}/task/{task_id}", headers=headers, timeout=20)
                if status_r.status_code == 200:
                    status = status_r.json().get("status")
                    if status == "done":
                        break
                    elif status in ("error", "failed"):
                        return {"status": "error", "msg": f"AppEEARS task failed: {status_r.text[:300]}"}
            except requests.RequestException as e:
                print(f"[ECOSTRESS WARNING] Connection error during polling: {e}. Retrying in 10s...")
        else:
            return {"status": "error", "msg": "AppEEARS task timed out after 45 minutes."}

        # Retry logic for getting bundle files list
        files = []
        for retry in range(5):
            try:
                files_r = requests.get(f"{APPEEARS_BASE}/bundle/{task_id}", headers=headers, timeout=20)
                if files_r.status_code == 200:
                    files = files_r.json().get("files", [])
                    break
            except requests.RequestException as e:
                print(f"[ECOSTRESS WARNING] Failed to get bundle files list (attempt {retry+1}/5): {e}")
                time.sleep(5)
        else:
            return {"status": "error", "msg": "Failed to get bundle files list after 5 retries."}
        
        os.makedirs(task_dir, exist_ok=True)
        data_map = {}
        for f in files:
            fname = f.get("file_name", "")
            if fname.endswith(".tif"):
                # extract date from dYYYYMMDD
                parts = fname.split('_')
                date_str = None
                for p in parts:
                    if p.startswith('doy') and len(p) >= 10:
                        try:
                            year = p[3:7]
                            doy = p[7:10]
                            date_str = datetime.strptime(f"{year}{doy}", "%Y%j").strftime("%Y-%m-%d")
                        except:
                            pass
                    elif p.startswith('d20') and len(p) == 9:
                        try:
                            date_str = datetime.strptime(p[1:], "%Y%m%d").strftime("%Y-%m-%d")
                        except:
                            pass
                
                if date_str:
                    # Retry logic for downloading each GeoTIFF
                    base_fname = os.path.basename(fname)
                    tif_path = os.path.join(task_dir, base_fname)
                    for retry in range(5):
                        try:
                            dl_r = requests.get(f"{APPEEARS_BASE}/bundle/{task_id}/{f['file_id']}", headers=headers, stream=True, timeout=60)
                            if dl_r.status_code == 200:
                                with open(tif_path, 'wb') as out_f:
                                    for chunk in dl_r.iter_content(chunk_size=8192):
                                        out_f.write(chunk)
                                data_map[date_str] = tif_path
                                break
                        except requests.RequestException as e:
                            print(f"[ECOSTRESS WARNING] Failed to download {fname} (attempt {retry+1}/5): {e}")
                            time.sleep(5)
                    else:
                        return {"status": "error", "msg": f"Failed to download {fname} after 5 retries."}

        result = {
            "status": "success",
            "source": "ECOSTRESS AppEEARS (LIVE)",
            "task_id": task_id,
            "data": data_map,
            "citation": SENSOR_INFO["citation"],
        }
        return result

    except Exception as e:
        return {"status": "error", "msg": str(e)}
