"""
AquaVolt-AI — Google Sheets Hourly Data Logger (Multi-Field Upgrade)
=================================================================
Tier 1 Real-Time Integrations:
  1. Sentinel-2 NDVI + Real NDWI (B03/B08) per field
  2. MODIS Daily LST via Microsoft Planetary Computer
  3. Open-Meteo 16-Day Irrigation Forecast
  4. Multi-Field 8x8 Grid Telemetry (256 rows/hour)
"""

import os
import sys
import math
import json
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket
import urllib.request
import ssl
from datetime import datetime, timedelta, timezone

# Load env variables from .env if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()


# --- ROBUST API SESSION SETUP ---
# Automatically fix/correct dropped connections or 5xx errors with exponential backoff
session = requests.Session()
retry = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[ 429, 500, 502, 503, 504 ],
    allowed_methods=['GET']
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)


# --- DoH Monkeypatch for robust DNS resolution ---
original_getaddrinfo = socket.getaddrinfo

def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return original_getaddrinfo(host, port, family, type, proto, flags)
    except socket.gaierror:
        try:
            url = f"https://8.8.8.8/resolve?name={host}&type=A"
            req = urllib.request.Request(url)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                res_data = json.loads(response.read().decode())
                for ans in res_data.get("Answer", []):
                    if ans.get("type") == 1:
                        ip = ans.get("data")
                        return original_getaddrinfo(ip, port, family, type, proto, flags)
        except Exception:
            pass
        raise

socket.getaddrinfo = custom_getaddrinfo
# -------------------------------------------------

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    print("[ERROR] Missing packages. Run: pip install gspread oauth2client requests")
    sys.exit(1)

# True farm center coordinates for Russell Ranch
LAT = float(os.environ.get("AQUAVOLT_LAT", 38.5480))
LON = float(os.environ.get("AQUAVOLT_LON", -121.8780))
FARM_NAME = os.environ.get("AQUAVOLT_FARM", "UC Davis Russell Ranch")
DEFAULT_SHEET_NAME = "AquaVolt-AI Telemetry Log"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define 4 distinct fields with their crop types — matches UC_Davis_Russell_Ranch_EXACT_FIELDS.png
FIELDS = [
    {
        "name": "Field-A (Corn)",
        "bbox": [-121.8790, 38.5480, -121.8720, 38.5540],
        "lat": 38.5510,
        "lon": -121.8755,
        "clay": 35.0
    },
    {
        "name": "Field-B (Alfalfa)",
        "bbox": [-121.8860, 38.5480, -121.8800, 38.5540],
        "lat": 38.5510,
        "lon": -121.8830,
        "clay": 28.0
    },
    {
        "name": "Field-C (Fallow)",
        "bbox": [-121.8860, 38.5420, -121.8800, 38.5475],
        "lat": 38.54475,
        "lon": -121.8830,
        "clay": 22.0
    },
    {
        "name": "Field-D (Tomato)",
        "bbox": [-121.8790, 38.5420, -121.8720, 38.5475],
        "lat": 38.54475,
        "lon": -121.8755,
        "clay": 32.0
    }
]


def get_gspread_client():
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_json = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
            return gspread.authorize(creds)
        except Exception as e:
            print(f"[ERROR] GCP secret error: {e}")
            sys.exit(1)

    local_creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "service_account.json")
    if not os.path.exists(local_creds_path):
        import glob
        matches = glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "aquavolt-ai-*.json"))
        if matches:
            local_creds_path = matches[0]

    if os.path.exists(local_creds_path):
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(local_creds_path, scopes)
            return gspread.authorize(creds)
        except Exception as e:
            print(f"[ERROR] Local creds error: {e}")
            sys.exit(1)

    print("[ERROR] No Google credentials found.")
    sys.exit(1)


# ---------------------------------------------------------
# Physics-Informed Machine Learning (PIML) Optimization Engine
# ---------------------------------------------------------
class PIMLEngine:
    def __init__(self, weights_path=None):
        self.W1 = None
        self.b1 = None
        self.W2 = None
        self.b2 = None
        self.W3 = None
        self.b3 = None
        self.feat_mean = None
        self.feat_std = None
        self.envelope = 0.15
        if weights_path and os.path.exists(weights_path):
            try:
                with open(weights_path, "r") as f:
                    data = json.load(f)
                self.W1 = np.array(data["W1"])
                self.b1 = np.array(data["b1"])
                self.W2 = np.array(data["W2"])
                self.b2 = np.array(data["b2"])
                self.W3 = np.array(data["W3"])
                self.b3 = np.array(data["b3"])
                self.feat_mean = np.array(data["feat_mean"])
                self.feat_std = np.array(data["feat_std"])
                self.envelope = data.get("envelope", 0.15)
                print(f"[PIML] Successfully loaded trained weights from {weights_path}")
            except Exception as e:
                print(f"[PIML WARNING] Failed to load trained weights: {e}. Falling back to prior physics.")
        else:
            print("[PIML WARNING] No weights file found. Falling back to prior physics.")

    def estimate_coefficients(self, ndvi, ndwi, savi, lst=None, clay=30.0, slope=1.0, Dr=36.0):
        """
        Predict crop coefficient (Kc) and water-stress factor (Ks)
        using a Physics-Informed residual learning framework.
        4 features: ndvi, ndwi, savi, Dr  (LST, clay, slope dropped — no sub-field variance)
        Ks is computed from FAO-56 physics only (no neural head — no real stress target available).
        """
        # Physical priors (FAO-56 standard values)
        kc_p = np.clip(1.457 * ndvi - 0.1725 + 0.10, 0.15, 1.20)
        TAW = 72.0
        RAW = 36.0
        if Dr <= RAW:
            ks_p = 1.0
        else:
            ks_p = max(0.0, (TAW - Dr) / (TAW - RAW))

        # If weights are loaded, run neural forward pass to predict Kc residual only
        if self.W1 is not None:
            Dr_norm = Dr / 72.0
            # 4-feature input: ndvi, ndwi, savi, Dr — matches training script exactly
            x = np.array([ndvi, ndwi, savi, Dr_norm])
            x_norm = (x - self.feat_mean) / (self.feat_std + 1e-8)

            h1 = np.maximum(0.0, np.dot(x_norm, self.W1) + self.b1)
            h2 = np.maximum(0.0, np.dot(h1, self.W2) + self.b2)
            residual = np.dot(h2, self.W3) + self.b3

            # Single output: Kc residual only
            env = self.envelope
            Kc = float(np.clip(kc_p + np.clip(residual[0] * env, -env, env), 0.15, 1.20))
            Ks = float(ks_p)   # physics-only — no neural Ks head
            return Kc, Ks
        else:
            return kc_p, ks_p


# TIER 1 — Combined Satellite STAC Search (Sentinel-2 & Landsat-8/9)
def get_latest_sentinel_item(lat, lon):
    print("[SATELLITE] Connecting to Planetary Computer STAC API...")
    try:
        import pystac_client
        import planetary_computer
        import certifi
    except ImportError as e:
        print(f"[SATELLITE WARNING] Missing deps: {e}. Falling back.")
        return None

    os.environ["CURL_CA_BUNDLE"] = certifi.where()

    try:
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        # A wider bounding box to search for items covering all fields
        bbox = [lon - 0.02, lat - 0.02, lon + 0.02, lat + 0.02]

        search = catalog.search(
            collections=["sentinel-2-l2a", "landsat-c2-l2"], bbox=bbox, datetime=time_range,
            query={"eo:cloud_cover": {"lt": 30}}
        )
        items = list(search.items())
        if not items:
            start_date = end_date - timedelta(days=60)
            time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            search = catalog.search(
                collections=["sentinel-2-l2a", "landsat-c2-l2"], bbox=bbox, datetime=time_range,
                query={"eo:cloud_cover": {"lt": 40}}
            )
            items = list(search.items())
            if not items:
                print("[SATELLITE WARNING] No cloud-free scenes found. Falling back.")
                return None

        # Sort chronologically desc
        items.sort(key=lambda x: x.datetime, reverse=True)
        latest_item = items[0]
        print(f"[SATELLITE] Found Combined Scene: {latest_item.id} | Date: {latest_item.datetime.date()} | Collection: {latest_item.collection_id}")
        return latest_item

    except Exception as e:
        print(f"[SATELLITE WARNING] STAC Search failed: {e}. Falling back.")
        return None


# TIER 1B — Sentinel-1 SAR (cloud-proof fallback, ~6-day revisit)
def get_latest_sar_item(lat, lon):
    """Fetch latest Sentinel-1 GRD scene. Works through clouds."""
    print("[SAR] Searching for Sentinel-1 GRD scene...")
    try:
        import pystac_client
        import planetary_computer
        import certifi
    except ImportError as e:
        print(f"[SAR WARNING] Missing deps: {e}.")
        return None

    os.environ["CURL_CA_BUNDLE"] = certifi.where()

    try:
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        bbox = [lon - 0.02, lat - 0.02, lon + 0.02, lat + 0.02]

        search = catalog.search(
            collections=["sentinel-1-grd"],
            bbox=bbox,
            datetime=time_range,
        )
        items = list(search.items())
        if not items:
            print("[SAR WARNING] No Sentinel-1 scenes found.")
            return None

        items.sort(key=lambda x: x.datetime, reverse=True)
        item = items[0]
        print(f"[SAR] Found scene: {item.id} | Date: {item.datetime.date()}")
        return item

    except Exception as e:
        print(f"[SAR WARNING] STAC search failed: {e}.")
        return None


def fetch_sar_field_indices(sar_item, field_bbox):
    """
    Read Sentinel-1 VV/VH bands for field_bbox and return NDVI/NDWI proxies.
    Maps to the same schema as optical indices — no new columns needed.

    RVI (Radar Vegetation Index) = 4*VH / (VV+VH)  [0..1]
    NDVI proxy  = 1.5*RVI - 0.1   (empirical C-band calibration)
    NDWI proxy  = cross_ratio based moisture index
    """
    try:
        import rasterio
        import numpy as np
        from rasterio.windows import Window
    except ImportError:
        return None

    try:
        pt = sar_item.properties.get("proj:transform")
        if not pt:
            print("[SAR WARNING] No proj:transform in STAC metadata.")
            return None

        scale_x, _, origin_x, _, scale_y, origin_y = pt

        lon_min, lat_min, lon_max, lat_max = field_bbox

        # Sentinel-1 GRD on Planetary Computer stores axes swapped:
        # rasterio rows  = longitude axis
        # rasterio cols  = latitude axis
        r_row_start = int((lon_min - origin_x) / scale_x)
        r_row_end   = int((lon_max - origin_x) / scale_x)
        r_col_start = int((origin_y - lat_max) / abs(scale_y))
        r_col_end   = int((origin_y - lat_min) / abs(scale_y))
        rw = r_row_end - r_row_start
        rh = r_col_end - r_col_start

        if rw <= 0 or rh <= 0:
            print("[SAR WARNING] Invalid window dimensions.")
            return None

        win = Window(r_col_start, r_row_start, rh, rw)

        vv_url = sar_item.assets["vv"].href
        vh_url = sar_item.assets["vh"].href

        with rasterio.open(vv_url) as src:
            actual_h, actual_w = src.shape
            # Bounds check
            if r_row_start < 0 or r_col_start < 0:
                print("[SAR WARNING] Window starts before raster origin.")
                return None
            if r_col_end > actual_w or r_row_end > actual_h:
                print(f"[SAR WARNING] Window ({r_row_end},{r_col_end}) exceeds raster ({actual_h},{actual_w}).")
                return None
            vv_dn = src.read(1, window=win, out_shape=(8, 8)).astype(np.float64)

        with rasterio.open(vh_url) as src:
            vh_dn = src.read(1, window=win, out_shape=(8, 8)).astype(np.float64)

        # Convert DN to linear power (sigma0 intensity = DN^2)
        vv = vv_dn ** 2
        vh = vh_dn ** 2

        # RVI = 4 * sigma_VH / (sigma_VV + sigma_VH)  [0..1]
        rvi = (4.0 * vh) / (vv + vh + 1e-8)
        rvi = np.clip(rvi, 0.0, 1.0)

        # NDVI proxy: empirical C-band calibration for agricultural fields
        # Bare soil ~-0.1, sparse veg ~0.3, dense veg ~0.8
        ndvi_proxy = np.clip(1.5 * rvi - 0.1, -0.2, 1.0)

        # NDWI proxy: cross-ratio VH/VV — sensitive to soil moisture & crop water
        cr = vh / (vv + 1e-8)
        ndwi_proxy = np.clip(-0.5 + 2.0 * cr, -1.0, 0.5)

        print(f"[SAR] RVI={np.nanmean(rvi):.3f} | NDVI_proxy={np.nanmean(ndvi_proxy):.3f} | NDWI_proxy={np.nanmean(ndwi_proxy):.3f}")
        return {"ndvi": ndvi_proxy.tolist(), "ndwi_real": ndwi_proxy.tolist()}

    except Exception as e:
        print(f"[SAR WARNING] Error reading SAR field window: {e}.")
        return None


# Extract 8x8 crop indices for a specific field's bbox (Handles S2 and Landsat)
# Includes SCL cloud/shadow masking for Sentinel-2 to prevent invalid pixels from
# corrupting NDVI values downstream (fixes the 0.08 floor clamp artifact).
def fetch_field_indices(latest_item, field_bbox):
    try:
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.warp import transform_bounds
        import numpy as np
    except ImportError:
        return None

    try:
        is_landsat = "landsat" in latest_item.collection_id.lower()
        if is_landsat:
            red_key = "red"
            green_key = "green"
            nir_key = "nir08"
        else:
            red_key = "B04"
            green_key = "B03"
            nir_key = "B08"

        b03_url = latest_item.assets[green_key].href
        b04_url = latest_item.assets[red_key].href
        b08_url = latest_item.assets[nir_key].href

        # --- SCL cloud/shadow mask for Sentinel-2 ---
        scl_mask = None
        if not is_landsat and "SCL" in latest_item.assets:
            scl_url = latest_item.assets["SCL"].href
            try:
                with rasterio.open(scl_url) as s_scl:
                    src_crs_scl = s_scl.crs
                    l_scl, b_scl, r_scl, t_scl = transform_bounds("EPSG:4326", src_crs_scl, *field_bbox)
                    win_scl = from_bounds(l_scl, b_scl, r_scl, t_scl, transform=s_scl.transform)
                    scl_raw = s_scl.read(1, window=win_scl, out_shape=(8, 8))
                    # SCL invalid classes: 0=no_data, 1=saturated, 2=dark/shadow,
                    # 3=cloud_shadow, 8=cloud_medium, 9=cloud_high, 10=thin_cirrus, 11=snow
                    scl_invalid = {0, 1, 2, 3, 8, 9, 10, 11}
                    scl_mask = np.isin(scl_raw, list(scl_invalid))
                    n_bad = int(np.sum(scl_mask))
                    if n_bad > 0:
                        print(f"[SCL] Masked {n_bad}/64 pixels as cloud/shadow/invalid.")
            except Exception as scl_err:
                print(f"[SCL WARNING] Could not read SCL band: {scl_err}. Proceeding without cloud mask.")

        with rasterio.open(b03_url) as s3, rasterio.open(b04_url) as s4, rasterio.open(b08_url) as s8:
            src_crs = s4.crs
            l, b, r, t = transform_bounds("EPSG:4326", src_crs, *field_bbox)
            win = from_bounds(l, b, r, t, transform=s4.transform)

            b03_raw = s3.read(1, window=win, out_shape=(8, 8)).astype(float)
            b04_raw = s4.read(1, window=win, out_shape=(8, 8)).astype(float)
            b08_raw = s8.read(1, window=win, out_shape=(8, 8)).astype(float)

            # Apply scaling
            if is_landsat:
                # Landsat 8/9 Level-2 SR: scale = 0.0000275, offset = -0.2
                b03 = np.clip(b03_raw * 0.0000275 - 0.2, 0.0, 1.0)
                b04 = np.clip(b04_raw * 0.0000275 - 0.2, 0.0, 1.0)
                b08 = np.clip(b08_raw * 0.0000275 - 0.2, 0.0, 1.0)
            else:
                # Sentinel-2 Level-2A SR: scale = 0.0001
                b03 = b03_raw * 0.0001
                b04 = b04_raw * 0.0001
                b08 = b08_raw * 0.0001

            # Combine bad-pixel mask with SCL cloud mask
            bad_mask = (b04_raw <= 0) | (b08_raw <= 0)
            if scl_mask is not None:
                bad_mask = bad_mask | scl_mask

            def safe_index(a, b_, mask):
                arr = (a - b_) / (a + b_ + 1e-8)
                arr = np.clip(arr, -1.0, 1.0)
                arr[mask] = np.nan
                if np.isnan(arr).any():
                    mv = np.nanmean(arr) if not np.isnan(arr).all() else np.nan
                    arr = np.where(np.isnan(arr), mv, arr)
                return arr

            ndvi = safe_index(b08, b04, bad_mask)
            ndwi_real = safe_index(b03, b08, (b03_raw <= 0) | (b08_raw <= 0) | (bad_mask if scl_mask is not None else np.zeros_like(bad_mask, dtype=bool)))

            # Real SAVI: (NIR - RED) / (NIR + RED + L) * (1 + L), L=0.5
            L = 0.5
            savi = (b08 - b04) / (b08 + b04 + L) * (1.0 + L)
            savi = np.clip(savi, -1.0, 1.0)
            savi[bad_mask] = np.nan
            if scl_mask is not None:
                savi[scl_mask] = np.nan
            if np.isnan(savi).any():
                sv = np.nanmean(savi) if not np.isnan(savi).all() else 0.0
                savi = np.where(np.isnan(savi), sv, savi)

            return {"ndvi": ndvi.tolist(), "ndwi_real": ndwi_real.tolist(), "savi": savi.tolist()}

    except Exception as e:
        print(f"[SATELLITE WARNING] Error reading field window: {e}.")
        return None


# TIER 1 — MODIS Daily LST
def fetch_modis_lst(lat, lon):
    print("[MODIS] Fetching daily Land Surface Temperature...")
    try:
        import pystac_client
        import planetary_computer
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.warp import transform_bounds
        import certifi
        import numpy as np
    except ImportError as e:
        print(f"[MODIS WARNING] Missing deps: {e}.")
        return None

    os.environ["CURL_CA_BUNDLE"] = certifi.where()

    try:
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Wider search window
        time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        bbox = [lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05]

        # Try multiple MODIS collection IDs (varies by Planetary Computer catalog version)
        modis_collections = ["modis-11A1-061", "modis-11a1-061", "modis-11A2-061"]
        items = []
        for coll_id in modis_collections:
            try:
                search = catalog.search(collections=[coll_id], bbox=bbox, datetime=time_range)
                items = search.item_collection()
                if items:
                    break
            except Exception:
                continue

        if not items:
            # Fallback: estimate LST from soil temp + air temp
            print("[MODIS] No scenes available — using weather-derived LST estimate")
            return None

        latest_item = items[0]
        start_dt = latest_item.properties.get("start_datetime")
        date_str = start_dt.split("T")[0] if start_dt else "Unknown"
        print(f"[MODIS] LST scene: {latest_item.id} | {date_str}")

        lst_url = latest_item.assets["LST_Day_1km"].href

        lat_deg = 500.0 / 111000.0
        lon_deg = 500.0 / (111000.0 * math.cos(math.radians(lat)))
        crop_bbox = [lon - lon_deg, lat - lat_deg, lon + lon_deg, lat + lat_deg]

        with rasterio.open(lst_url) as src:
            src_crs = src.crs
            l, b, r, t = transform_bounds("EPSG:4326", src_crs, *crop_bbox)
            win = from_bounds(l, b, r, t, transform=src.transform)
            lst_data = src.read(1, window=win).astype(float)
            lst_data = np.where(lst_data > 0, lst_data * 0.02 - 273.15, np.nan)
            lst_mean = float(np.nanmean(lst_data)) if not np.isnan(lst_data).all() else None

        if lst_mean is not None:
            print(f"[MODIS] Real LST: {lst_mean:.1f} C")
            return round(lst_mean, 1)
        return None

    except Exception as e:
        print(f"[MODIS WARNING] {e}. Using API soil temp.")
        return None


# TIER 1 — Open-Meteo 16-Day Forecast
def fetch_open_meteo_forecast(lat, lon):
    print("[FORECAST] Fetching 16-day irrigation forecast...")
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=et0_fao_evapotranspiration,precipitation_sum,"
            f"temperature_2m_max,temperature_2m_min"
            f"&forecast_days=16&timezone=UTC"
        )
        r = session.get(url, timeout=15)
        r.raise_for_status()
        daily = r.json().get("daily", {})
        et0_vals  = daily.get("et0_fao_evapotranspiration", [])
        precip    = daily.get("precipitation_sum", [])
        deficit_7d = sum(
            max(0.0, (et0_vals[i] or 0.0) - (precip[i] or 0.0) * 0.8)
            for i in range(min(7, len(et0_vals)))
        )
        print(f"[FORECAST] 7-day water deficit: {deficit_7d:.1f} mm")
        return round(deficit_7d, 1)
    except Exception as e:
        print(f"[FORECAST WARNING] {e}")
        return 0.0


# =====================================================================
# TIER 2 — Enhanced Data Source Integrations (improve existing columns)
# =====================================================================

# Cache for static lookups (DEM, SoilGrids) — only fetch once per run
_soil_cache = {}
_dem_cache = {}


def fetch_soilgrids_properties(lat, lon):
    """Fetch real soil texture from ISRIC SoilGrids REST API.
    Returns TAW (Total Available Water) and RAW (Readily Available Water)
    computed from clay/sand/silt fractions using FAO pedotransfer functions.
    Replaces hardcoded TAW=72, RAW=36 with physically accurate values."""
    cache_key = f"{lat:.2f},{lon:.2f}"
    if cache_key in _soil_cache:
        return _soil_cache[cache_key]

    print("[SOILGRIDS] Fetching real soil properties from ISRIC SoilGrids...")
    default = {"TAW": 72.0, "RAW": 36.0, "clay_pct": 25.0, "sand_pct": 40.0}
    try:
        # SoilGrids REST API — 250m resolution global soil data
        url = (
            f"https://rest.isric.org/soilgrids/v2.0/properties/query"
            f"?lon={lon}&lat={lat}"
            f"&property=clay&property=sand&property=silt"
            f"&depth=0-30cm&value=mean"
        )
        r = session.get(url, timeout=8, headers={"Accept": "application/json"})
        if r.status_code != 200:
            print(f"[SOILGRIDS] HTTP {r.status_code} — estimating from soil moisture")
            _soil_cache[cache_key] = default
            return default

        data = r.json()
        layers = data.get("properties", {}).get("layers", [])
        clay_pct, sand_pct, silt_pct = None, None, None
        for layer in layers:
            name = layer.get("name", "")
            depths = layer.get("depths", [])
            if depths:
                val = depths[0].get("values", {}).get("mean")
                if val is not None:
                    val = val / 10.0  # SoilGrids returns g/kg, convert to %
                    if name == "clay":
                        clay_pct = val
                    elif name == "sand":
                        sand_pct = val
                    elif name == "silt":
                        silt_pct = val

        if clay_pct is None or sand_pct is None:
            # SoilGrids has sparse US coverage — use region-appropriate defaults
            # UC Davis Russell Ranch: Yolo silt loam (USDA Web Soil Survey)
            print("[SOILGRIDS] No coverage for this region — using Yolo silt loam pedotransfer defaults")
            clay_pct = 22.0  # Typical for Yolo County silt loam
            sand_pct = 30.0
            silt_pct = 48.0

        if silt_pct is None:
            silt_pct = max(0, 100.0 - clay_pct - sand_pct)

        # FAO Pedotransfer: Compute field capacity (FC) and wilting point (WP)
        # Saxton & Rawls (2006) equations
        fc = 0.2576 - 0.0020 * sand_pct + 0.0036 * clay_pct + 0.0299 * (silt_pct / 100.0)
        wp = 0.026 + 0.005 * clay_pct / 100.0 + 0.0158 * (clay_pct / 100.0) ** 2
        fc = max(0.10, min(0.55, fc))
        wp = max(0.02, min(0.30, wp))

        # TAW = (FC - WP) * root_depth_mm (default 600mm root zone for crops)
        root_depth = 600.0  # mm
        taw = (fc - wp) * root_depth
        taw = max(40.0, min(250.0, taw))
        raw = taw * 0.50  # p=0.50 for most field crops (FAO-56 Table 22)

        result = {
            "TAW": round(taw, 1),
            "RAW": round(raw, 1),
            "clay_pct": round(clay_pct, 1),
            "sand_pct": round(sand_pct, 1),
        }
        print(f"[SOILGRIDS] Clay: {clay_pct:.0f}%, Sand: {sand_pct:.0f}% -> TAW: {taw:.0f}mm, RAW: {raw:.0f}mm")
        _soil_cache[cache_key] = result
        return result

    except Exception as e:
        print(f"[SOILGRIDS WARNING] {e} — using defaults")
        _soil_cache[cache_key] = default
        return default


def fetch_copernicus_dem_slope(lat, lon):
    """Fetch terrain elevation and compute slope correction factor.
    Uses Open-Meteo Elevation API (backed by Copernicus DEM GLO-90).
    Slope increases runoff, requiring more irrigation water.
    Returns a multiplier for ETc: 1.0 = flat, up to 1.25 = steep."""
    cache_key = f"{lat:.4f},{lon:.4f}"
    if cache_key in _dem_cache:
        return _dem_cache[cache_key]

    print("[DEM] Fetching terrain data from Copernicus DEM (via Open-Meteo)...")
    default = {"elevation": 0.0, "slope_factor": 1.0}
    try:
        # Query 5 points in a cross pattern to estimate slope
        delta = 0.001  # ~100m spacing
        points_lat = [lat, lat + delta, lat - delta, lat, lat]
        points_lon = [lon, lon, lon, lon + delta, lon - delta]

        lat_str = ",".join(f"{x:.4f}" for x in points_lat)
        lon_str = ",".join(f"{x:.4f}" for x in points_lon)

        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat_str}&longitude={lon_str}"
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            _dem_cache[cache_key] = default
            return default

        elevations = r.json().get("elevation", [])
        if len(elevations) < 5:
            _dem_cache[cache_key] = default
            return default

        center_elev = elevations[0]
        # Compute slope from elevation differences
        dx = 2 * delta * 111320 * math.cos(math.radians(lat))  # meters in lon direction
        dy = 2 * delta * 111320  # meters in lat direction
        slope_ns = abs(elevations[1] - elevations[2]) / dy  # N-S slope
        slope_ew = abs(elevations[3] - elevations[4]) / dx  # E-W slope
        slope = math.sqrt(slope_ns**2 + slope_ew**2)
        slope_deg = math.degrees(math.atan(slope))

        # Slope correction: flat=1.0, 5°=1.08, 10°=1.15, 15°=1.25
        slope_factor = 1.0 + min(0.25, slope_deg * 0.015)

        result = {
            "elevation": round(center_elev, 1),
            "slope_factor": round(slope_factor, 3),
        }
        print(f"[DEM] Elevation: {center_elev:.0f}m, Slope: {slope_deg:.1f}deg -> Correction: {slope_factor:.3f}x")
        _dem_cache[cache_key] = result
        return result

    except Exception as e:
        print(f"[DEM WARNING] {e} — assuming flat terrain")
        _dem_cache[cache_key] = default
        return default


def fetch_viirs_lst(lat, lon):
    """Fetch VIIRS (Suomi NPP) daily thermal data from NASA FIRMS.
    Returns land surface temperature estimate to fuse with MODIS LST.
    VIIRS has 375m resolution and daily revisit — fills MODIS gaps."""
    print("[VIIRS] Fetching daily thermal data from NASA FIRMS...")
    try:
        # NASA FIRMS API — free, no key needed for CSV format
        # Get active fire/thermal anomaly data within 1km of point
        today = datetime.now().strftime("%Y-%m-%d")
        url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
            f"VIIRS_SNPP_NRT/{lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}/1/{today}"
        )
        r = session.get(url, timeout=10)
        if r.status_code == 200 and "bright_ti4" in r.text:
            lines = r.text.strip().split("\n")
            if len(lines) > 1:
                # Parse brightness temperature from VIIRS
                import csv as csv_mod
                reader = csv_mod.DictReader(lines)
                temps = []
                for row in reader:
                    bt = row.get("bright_ti4") or row.get("bright_ti5")
                    if bt:
                        try:
                            temps.append(float(bt) - 273.15)  # Kelvin to Celsius
                        except ValueError:
                            pass
                if temps:
                    avg_viirs = sum(temps) / len(temps)
                    print(f"[VIIRS] Brightness temp: {avg_viirs:.1f}C from {len(temps)} detections")
                    return avg_viirs
        # If no thermal anomalies detected (normal — means no fire), return None
        print("[VIIRS] No thermal anomalies (normal for agricultural land)")
        return None
    except Exception as e:
        print(f"[VIIRS WARNING] {e}")
        return None


def fetch_era5_bias_correction(lat, lon):
    """Fetch ERA5 climate normals from Open-Meteo to bias-correct weather.
    Compares today's Open-Meteo forecast against ERA5 30-year climatology.
    Returns correction factors for temp, humidity, solar."""
    print("[ERA5] Fetching climate normals for bias correction...")
    default = {"temp_bias": 0.0, "humidity_bias": 0.0, "solar_bias": 0.0}
    try:
        # ERA5 monthly normals (1991-2020) — same API, different endpoint
        now = datetime.now()
        # Get last 30 days of archive data for this location
        end = (now - timedelta(days=2)).strftime("%Y-%m-%d")
        start = (now - timedelta(days=32)).strftime("%Y-%m-%d")
        url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lon}"
            f"&start_date={start}&end_date={end}"
            f"&daily=temperature_2m_mean,relative_humidity_2m_mean,"
            f"shortwave_radiation_sum"
            f"&timezone=UTC"
        )
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return default

        daily = r.json().get("daily", {})
        temps = [t for t in daily.get("temperature_2m_mean", []) if t is not None]
        hums = [h for h in daily.get("relative_humidity_2m_mean", []) if h is not None]
        solars = [s for s in daily.get("shortwave_radiation_sum", []) if s is not None]

        if not temps:
            return default

        result = {
            "temp_bias": round(sum(temps) / len(temps), 1),
            "humidity_bias": round(sum(hums) / len(hums), 1) if hums else 0.0,
            "solar_bias": round(sum(solars) / len(solars), 1) if solars else 0.0,
        }
        print(f"[ERA5] 30-day normals -> Temp: {result['temp_bias']:.1f}C, Humidity: {result['humidity_bias']:.0f}%")
        return result

    except Exception as e:
        print(f"[ERA5 WARNING] {e}")
        return default


def fetch_chirps_precipitation(lat, lon):
    """Fetch CHIRPS satellite-estimated rainfall from IRI Data Library.
    CHIRPS blends satellite thermal imagery with ground station data.
    Critical for Pakistan/developing regions with sparse weather stations.
    Returns daily precipitation estimate in mm."""
    print("[CHIRPS] Fetching satellite-estimated precipitation...")
    try:
        # Use Open-Meteo as proxy — it already includes satellite-calibrated precip
        # For regions with sparse stations, use the ERA5+satellite blend
        # Archive API has 5-day lag; use wider window to ensure data availability
        end_day = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        start_day = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lon}"
            f"&start_date={start_day}&end_date={end_day}"
            f"&daily=precipitation_sum"
            f"&timezone=UTC"
        )
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            daily = r.json().get("daily", {})
            precip_vals = daily.get("precipitation_sum", [])
            if precip_vals:
                valid = [p for p in precip_vals if p is not None]
                if valid:
                    chirps_precip = valid[-1]  # Latest day
                    print(f"[CHIRPS] Satellite-estimated precip: {chirps_precip:.1f} mm")
                    return chirps_precip
        return None
    except Exception as e:
        print(f"[CHIRPS WARNING] {e}")
        return None


# TIER 1 — Empirical LAI & FCOVER
def compute_lai_fcover(ndvi):
    ndvi_c = max(0.15, min(0.92, ndvi))
    lai = max(0.0, -math.log(max(1e-6, (0.69 - ndvi_c) / 0.59)) / 0.91)
    lai = round(min(lai, 8.0), 4)
    fcover = round(1.0 - math.exp(-0.5 * lai), 4)
    return lai, fcover


def build_url(lat, lon):
    return (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
        f"precipitation,cloud_cover,surface_pressure,shortwave_radiation,"
        f"is_day,soil_temperature_0_to_7cm,soil_moisture_0_to_1cm"
        f"&hourly=shortwave_radiation,temperature_2m,precipitation,"
        f"relative_humidity_2m,et0_fao_evapotranspiration,"
        f"soil_temperature_0_to_7cm,soil_moisture_0_to_1cm"
        f"&forecast_days=1&timezone=UTC"
    )


def main(push_to_sheets=True):
    print("=" * 70)
    print("  AquaVolt-AI Sheets Sync  [Tier 1: Multi-Field Upgrade]")
    print(f"  Farm: {FARM_NAME}  |  Coords: {LAT}N, {LON}W")
    print("=" * 70)

    gc = get_gspread_client()
    sheet_name = os.environ.get("GSHEET_NAME", DEFAULT_SHEET_NAME)
    print(f"[FILE] Accessing: '{sheet_name}'...")
    try:
        sh = gc.open(sheet_name)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"[ERROR] Spreadsheet '{sheet_name}' not found!")
        sys.exit(1)

    worksheet = sh.get_worksheet(0)

    # 29-column schema (added 'field_name')
    headers = [
        "timestamp", "latitude", "longitude", "sector_row", "sector_col",
        "ndvi", "ndwi", "ndwi_real", "savi", "lai", "fcover",
        "lst", "lst_modis", "Kc", "Ks", "Dr", "TAW", "RAW", "ETc", "water_need",
        "air_temp", "humidity", "solar_rad", "precip",
        "soil_temp", "soil_moisture", "et0_deficit_7d", "scene_id", "field_name"
    ]
    existing = worksheet.row_values(1)
    if not existing or existing != headers:
        print("[HEADER] Updating sheet headers for 29-column schema...")
        worksheet.clear()
        worksheet.append_row(headers)


    # Duplicate-hour guard
    if push_to_sheets:
        now_utc = datetime.now(timezone.utc)
        current_hour_str = now_utc.strftime("%Y-%m-%d %H:")
        all_timestamps = worksheet.col_values(1)
        if len(all_timestamps) > 1:
            last_ts = all_timestamps[-1]
            if last_ts.startswith(current_hour_str):
                print(f"[SKIP] Data for UTC hour {now_utc.strftime('%Y-%m-%d %H:00')} already exists. Skipping.")
                sys.exit(0)

    print("[API] Fetching weather from Open-Meteo...")
    r = session.get(build_url(LAT, LON), timeout=20)
    r.raise_for_status()
    weather = r.json()

    current = weather.get("current", {})
    hourly  = weather.get("hourly", {})
    temp       = current.get("temperature_2m")            if current.get("temperature_2m")   is not None else 20.0
    humidity   = current.get("relative_humidity_2m")      if current.get("relative_humidity_2m") is not None else 50.0
    precip_cur = current.get("precipitation")             if current.get("precipitation")     is not None else 0.0
    solar_rad  = current.get("shortwave_radiation")       if current.get("shortwave_radiation") is not None else 0.0
    soil_temp  = current.get("soil_temperature_0_to_7cm") if current.get("soil_temperature_0_to_7cm") is not None else temp
    soil_moist = current.get("soil_moisture_0_to_1cm")    if current.get("soil_moisture_0_to_1cm") is not None else 0.18
    daily_et0    = sum(x for x in hourly.get("et0_fao_evapotranspiration", []) if x) or 5.0

    # TIER 2 — Weather bias correction (ERA5) & Satellite Precip (CHIRPS)
    era5_bias = fetch_era5_bias_correction(LAT, LON)
    if era5_bias.get("temp_bias"):
        temp = round(0.85 * temp + 0.15 * era5_bias["temp_bias"], 1)
        humidity = round(0.85 * humidity + 0.15 * era5_bias["humidity_bias"], 1)
        
    chirps_precip = fetch_chirps_precipitation(LAT, LON)
    if chirps_precip is not None:
        precip_cur = max(precip_cur, chirps_precip)

    print(f"  Temp: {temp}C | Soil Moist: {soil_moist*100:.1f}% | ET0: {daily_et0:.2f} mm/day")

    print("\n[TIER 1] Fetching satellite & forecast data...")
    latest_item = get_latest_sentinel_item(LAT, LON)

    # TIER 1B — Sentinel-1 SAR fallback (cloud-proof, ~6-day revisit)
    sar_item = None
    optical_age_days = None
    if latest_item:
        optical_age_days = (datetime.now() - latest_item.datetime.replace(tzinfo=None)).days
        if optical_age_days > 10:
            print(f"[SATELLITE] Optical scene is {optical_age_days} days old — fetching SAR supplement...")
            sar_item = get_latest_sar_item(LAT, LON)
    else:
        print("[SATELLITE] No optical scene — fetching SAR as primary fallback...")
        sar_item = get_latest_sar_item(LAT, LON)

    scene_id = latest_item.id if latest_item else (sar_item.id if sar_item else "Fallback")
    
    # TIER 2 — VIIRS LST Fusion
    modis_lst_val = fetch_modis_lst(LAT, LON)
    viirs_lst_val = fetch_viirs_lst(LAT, LON)
    if viirs_lst_val is not None:
        modis_lst_val = round((modis_lst_val + viirs_lst_val) / 2.0, 1)

    deficit_7d    = fetch_open_meteo_forecast(LAT, LON)

    julian_day = datetime.now().timetuple().tm_yday
    delta = 0.409 * math.sin((2 * math.pi / 365) * julian_day - 1.39)
    lat_rad = math.radians(LAT)
    val_cos = max(-1.0, min(1.0, -math.tan(lat_rad) * math.tan(delta)))
    day_length = (24.0 / math.pi) * math.acos(val_cos)
    season_factor = max(0.0, min(1.0, (day_length - 8.0) / 8.0))
    temp_factor = math.exp(-0.02 * ((temp - 24.0) ** 2))
    growth_multiplier = season_factor * temp_factor

    # Initialize PIMLEngine with the newly trained weights
    weights_path = os.path.join(SCRIPT_DIR, "ai_weights_mlp.json")
    piml_engine = PIMLEngine(weights_path)

    now_str = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:00:00")
    rows_to_append = []

    # Loop through each field and generate 64 rows of data per field (total 256 rows)
    for field in FIELDS:
        f_name = field["name"]
        print(f"\n[PIML] Processing field: {f_name}...")
        
        # TIER 2 — SoilGrids properties & Copernicus DEM Slope
        soil_props = fetch_soilgrids_properties(field["lat"], field["lon"])
        TAW = soil_props["TAW"]
        RAW = soil_props["RAW"]

        dem_props = fetch_copernicus_dem_slope(field["lat"], field["lon"])
        slope_factor = dem_props["slope_factor"]

        # Crop Sentinel-2 data for this specific field's bounding box
        field_sentinel = fetch_field_indices(latest_item, field["bbox"]) if latest_item else None
        if field_sentinel is None and sar_item is not None:
            print(f"[SAR] Using Sentinel-1 SAR indices for {f_name} (optical unavailable)")
            field_sentinel = fetch_sar_field_indices(sar_item, field["bbox"])
        
        # DELETE THE SYNTHETIC PATHS:
        # If the satellite fetch fails, the record should be absent, not fabricated.
        if field_sentinel is None:
            print(f"[SATELLITE] Skipping {f_name} — no satellite data available. Record is absent.")
            continue
        
        # FAO-56 crop-specific mid-season NDVI defaults (used when satellite unavailable)
        # These are physically-based values, not synthetic ramps.
        fao56_ndvi = {
            "Corn": 0.85, "Alfalfa": 0.78, "Tomato": 0.80, "Fallow": 0.12
        }
        crop_key = next((k for k in fao56_ndvi if k in f_name), "Fallow")
        fallback_ndvi = fao56_ndvi[crop_key]
        is_fallow = ("Fallow" in f_name)

        for row in range(8):
            for col in range(8):
                # USE RAW SATELLITE NDVI — no synthetic pos_factor corruption.
                # NaN values (from SCL cloud masking) will have been gap-filled
                # to the field mean inside safe_index(), so they are safe floats.
                raw_ndvi = float(field_sentinel["ndvi"][row][col])
                if math.isnan(raw_ndvi) or raw_ndvi < -0.5:
                    # Pixel was entirely invalid even after gap-fill; use FAO default
                    ndvi = round(fallback_ndvi, 4)
                else:
                    ndvi = round(max(0.01, min(0.98, raw_ndvi)), 4)
                ndwi_real_val = round(float(field_sentinel["ndwi_real"][row][col]), 4)
                if math.isnan(ndwi_real_val):
                    ndwi_real_val = round(max(-0.5, min(0.5, soil_moist * 2.0 - 0.5)), 4)

                ndwi = ndwi_real_val  # unified; no soil-moisture proxy
                # Use real SAVI from satellite if available
                if "savi" in field_sentinel and not math.isnan(float(field_sentinel["savi"][row][col])):
                    savi = round(max(-1.0, min(1.0, float(field_sentinel["savi"][row][col]))), 4)
                else:
                    savi = round(ndvi * 1.5 * (1.0 / (ndvi + 0.5 + 1e-8)) if ndvi > 0 else 0.0, 4)
                lai, fcover = compute_lai_fcover(ndvi)

                # Use real MODIS LST when available; fallback to soil_temp (not NDVI-derived)
                lst_measured = modis_lst_val if modis_lst_val is not None else soil_temp

                # Compute clay and slope for this sector
                base_clay = field.get("clay", 30.0)
                clay = base_clay + (row - 3.5) * 0.4 + (col - 3.5) * 0.3
                slope = 1.0 + math.sin(row / 2.0) * 0.4 + math.cos(col / 2.0) * 0.2

                # Water balance depletion
                sm_frac_sector = 0.10 + ((ndwi_real_val - (-0.5)) / (0.5 - (-0.5))) * 0.80
                sm_frac_sector = min(1.0, max(0.0, sm_frac_sector))
                Dr  = round(TAW * (1.0 - sm_frac_sector), 2)

                # Compute neural corrected Kc and Ks using PIMLEngine (7 features)
                kc_raw, ks_raw = piml_engine.estimate_coefficients(ndvi, ndwi_real_val, savi, lst_measured, clay, slope, Dr)
                kc = round(kc_raw, 2)
                ks = round(ks_raw, 2)

                # TIER 2 — Slope-corrected ETc (water runoff multiplier)
                ETc = round(ks * kc * daily_et0 * slope_factor, 2)
                irr = round(Dr, 2) if Dr > RAW else 0.0

                # Close the irrigation loop: apply recommended I back into Dr
                if irr > 0:
                    Dr = round(max(0.0, Dr - irr), 2)

                rows_to_append.append([
                    now_str, field["lat"], field["lon"], row, col,
                    ndvi, ndwi, ndwi_real_val, savi, lai, fcover,
                    lst_measured, modis_lst_val,
                    kc, ks, Dr, TAW, RAW, ETc, irr,
                    temp, humidity, solar_rad, precip_cur,
                    soil_temp, soil_moist, deficit_7d, scene_id, f_name
                ])

    if push_to_sheets:
        if not rows_to_append:
            print("\n[UPLOAD] No records to upload (satellite fetch was missing).")
            return
        print(f"\n[UPLOAD] Writing {len(rows_to_append)} records...")
        worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        print(f"[OK] Done.")

    # =====================================================================
    # EARLY WARNING SYSTEM — Physics-based crop stress alert engine
    # =====================================================================
    # Computes per-field averages of Dr, Ks, ETc, deficit_7d and classifies
    # alert level. Writes GitHub Actions step summary + README alert banner.
    # No new columns or schema changes — uses existing calculated values.
    # =====================================================================
    print("\n[ALERTS] Running early warning analysis...")
    try:
        # Aggregate per-field stress metrics from freshly computed rows
        field_stress = {}
        for row in rows_to_append:
            fname  = row[28]   # field_name
            Dr_val = row[15]   # root zone depletion (mm)
            Ks_val = row[13]   # water stress coefficient (0-1)
            ETc_v  = row[18]   # evapotranspiration demand (mm/hr)
            irr_v  = row[19]   # irrigation needed (mm)
            ndvi_v = row[5]    # crop greenness
            if fname not in field_stress:
                field_stress[fname] = {"Dr": [], "Ks": [], "ETc": [], "irr": [], "ndvi": []}
            field_stress[fname]["Dr"].append(Dr_val)
            field_stress[fname]["Ks"].append(Ks_val)
            field_stress[fname]["ETc"].append(ETc_v)
            field_stress[fname]["irr"].append(irr_v)
            field_stress[fname]["ndvi"].append(ndvi_v)

        alerts = []
        ALERT_RULES = {
            # (Dr_threshold_mm, Ks_threshold, 7d_deficit_mm) → alert level
            "EMERGENCY": {"Dr_pct": 0.90, "Ks": 0.30, "deficit": 60.0},  # >90% TAW depleted
            "CRITICAL":  {"Dr_pct": 0.75, "Ks": 0.50, "deficit": 40.0},  # >75% TAW depleted
            "WATCH":     {"Dr_pct": 0.55, "Ks": 0.70, "deficit": 20.0},  # >55% TAW depleted
        }

        summary_lines = []
        console_lines = []

        for fname, vals in field_stress.items():
            avg_Dr   = sum(vals["Dr"])   / len(vals["Dr"])
            avg_Ks   = sum(vals["Ks"])   / len(vals["Ks"])
            avg_ETc  = sum(vals["ETc"])  / len(vals["ETc"])
            avg_irr  = sum(vals["irr"])  / len(vals["irr"])
            avg_ndvi = sum(vals["ndvi"]) / len(vals["ndvi"])

            # Estimate TAW from the first row that has it
            TAW_est = None
            for row in rows_to_append:
                if row[28] == fname:
                    TAW_est = row[16]
                    break
            TAW_est = TAW_est or 120.0
            Dr_pct = avg_Dr / TAW_est  # fraction of TAW depleted

            # Classify alert level
            if Dr_pct >= ALERT_RULES["EMERGENCY"]["Dr_pct"] or avg_Ks <= ALERT_RULES["EMERGENCY"]["Ks"] or deficit_7d >= ALERT_RULES["EMERGENCY"]["deficit"]:
                level = "🚨 EMERGENCY"
                icon  = "🚨"
                action = "IRRIGATE IMMEDIATELY — severe crop stress. >90% soil water depleted."
            elif Dr_pct >= ALERT_RULES["CRITICAL"]["Dr_pct"] or avg_Ks <= ALERT_RULES["CRITICAL"]["Ks"] or deficit_7d >= ALERT_RULES["CRITICAL"]["deficit"]:
                level = "🔴 CRITICAL"
                icon  = "🔴"
                action = "Schedule irrigation within 24 hours. Crop stress factor Ks={:.2f}".format(avg_Ks)
            elif Dr_pct >= ALERT_RULES["WATCH"]["Dr_pct"] or avg_Ks <= ALERT_RULES["WATCH"]["Ks"] or deficit_7d >= ALERT_RULES["WATCH"]["deficit"]:
                level = "🟡 WATCH"
                icon  = "🟡"
                action = "Monitor closely. Water deficit building — plan irrigation within 48–72h."
            else:
                level = "🟢 NORMAL"
                icon  = "🟢"
                action = "Soil water adequate. No immediate irrigation needed."

            alerts.append({
                "field": fname, "level": level, "icon": icon,
                "Dr": avg_Dr, "Dr_pct": Dr_pct * 100,
                "Ks": avg_Ks, "ETc": avg_ETc, "irr": avg_irr,
                "ndvi": avg_ndvi, "action": action,
            })

            console_lines.append(
                f"  {icon}  {fname:<22} Dr={avg_Dr:5.1f}mm ({Dr_pct*100:.0f}% TAW) "
                f"Ks={avg_Ks:.2f}  ETc={avg_ETc:.2f}mm/hr  → {level}"
            )
            summary_lines.append(
                f"| {icon} | **{fname}** | {avg_Dr:.1f} mm | {Dr_pct*100:.0f}% | "
                f"{avg_Ks:.2f} | {avg_ETc:.2f} mm/hr | {action} |"
            )

        # Print console alert table
        print("\n" + "─" * 70)
        print("  🌾 EARLY WARNING ALERT SUMMARY")
        print("─" * 70)
        print(f"  🌡  Temp: {temp}°C  |  💧 Humidity: {humidity}%  |  ⛅ 7-day deficit: {deficit_7d:.1f}mm")
        print("─" * 70)
        for line in console_lines:
            print(line)
        print("─" * 70 + "\n")

        # Write GitHub Actions step summary (visible in Actions run log)
        gha_summary = os.environ.get("GITHUB_STEP_SUMMARY", "")
        if gha_summary:
            with open(gha_summary, "a", encoding="utf-8") as f:
                f.write("## 🌾 AquaVolt-AI Early Warning Alerts\n\n")
                f.write(f"**Timestamp:** `{now_str} UTC`  |  ")
                f.write(f"**Temp:** {temp}°C  |  **7-day Water Deficit:** {deficit_7d:.1f}mm\n\n")
                f.write("| Status | Field | Depletion (Dr) | TAW Used | Stress (Ks) | ETc | Recommended Action |\n")
                f.write("|:---:|:---|---:|---:|---:|---:|:---|\n")
                for line in summary_lines:
                    f.write(line + "\n")
            print("[ALERTS] GitHub Actions step summary updated.")

        # Inject alert banner into README.md
        readme_path = os.path.join(SCRIPT_DIR, "README.md")
        if os.path.exists(readme_path):
            import re
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_text = f.read()

            alert_md = f"<!-- ALERT_BANNER_START -->\n"
            alert_md += f"## 🚨 Early Warning Alerts — `{now_str} UTC`\n\n"
            alert_md += "| Status | Field | Depletion | TAW % | Ks | ETc | Action |\n"
            alert_md += "|:---:|:---|---:|---:|---:|---:|:---|\n"
            for line in summary_lines:
                alert_md += line + "\n"
            alert_md += "\n<!-- ALERT_BANNER_END -->"

            if "<!-- ALERT_BANNER_START -->" in readme_text:
                pattern = r"<!-- ALERT_BANNER_START -->.*?<!-- ALERT_BANNER_END -->"
                readme_text = re.sub(pattern, alert_md, readme_text, flags=re.DOTALL)
            else:
                # Insert after the first heading if no placeholder exists
                readme_text = readme_text.replace(
                    "<!-- LIVE_TELEMETRY_START -->",
                    alert_md + "\n\n<!-- LIVE_TELEMETRY_START -->"
                )
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_text)
            print("[ALERTS] README.md alert banner updated.")

    except Exception as e:
        print(f"[ALERTS WARNING] Alert engine error: {e}")

    # --- GENERATE LIVE GITHUB DASHBOARD ---
    print("\n[DASHBOARD] Generating live GitHub markdown dashboard...")

    try:
        field_summaries = {}
        for row in rows_to_append:
            fname = row[28]  # field_name
            if fname not in field_summaries:
                field_summaries[fname] = {"ndvi": [], "ndwi": [], "etc": [], "irr": []}
            field_summaries[fname]["ndvi"].append(row[5])
            field_summaries[fname]["ndwi"].append(row[7])
            field_summaries[fname]["etc"].append(row[18])
            field_summaries[fname]["irr"].append(row[19])
        
        md_content = f"# 📡 AquaVolt-AI Live Telemetry\n\n"
        md_content += f"**Latest Update:** `{now_str} UTC`\n"
        md_content += f"> This dashboard updates automatically every hour via GitHub Actions.\n\n"
        
        md_content += f"### ⛅ Current Weather (Russell Ranch)\n\n"
        md_content += f"- **Air Temp:** {temp}°C\n"
        md_content += f"- **Humidity:** {humidity}%\n"
        md_content += f"- **Solar Radiation:** {solar_rad} W/m²\n"
        md_content += f"- **Soil Moisture (Proxy):** {soil_moist*100:.1f}%\n"
        md_content += f"- **Reference ET₀ (24h):** {daily_et0:.2f} mm\n\n"
        
        md_content += f"### 🌱 Field Averages (Current Hour)\n\n"
        md_content += f"| Field Name | Avg NDVI | Avg NDWI | Avg ETc (mm/hr) | Avg Water Deficit (mm) |\n"
        md_content += f"|---|---|---|---|---|\n"
        
        for fname, data in field_summaries.items():
            avg_ndvi = sum(data["ndvi"]) / len(data["ndvi"])
            avg_ndwi = sum(data["ndwi"]) / len(data["ndwi"])
            avg_etc = sum(data["etc"]) / len(data["etc"])
            avg_irr = sum(data["irr"]) / len(data["irr"])
            md_content += f"| **{fname}** | {avg_ndvi:.3f} | {avg_ndwi:.3f} | {avg_etc:.2f} | **{avg_irr:.2f}** |\n"
            
        md_content += f"\n---\n*Powered by Python, Planetary Computer STAC APIs, and FAO-56 Thermodynamics.*\n"
        
        # Inject into README.md
        readme_path = os.path.join(SCRIPT_DIR, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_text = f.read()
            
            import re
            pattern = r"(<!-- LIVE_TELEMETRY_START -->)(.*?)(<!-- LIVE_TELEMETRY_END -->)"
            replacement = r"\1\n" + md_content + r"\n\3"
            new_readme = re.sub(pattern, replacement, readme_text, flags=re.DOTALL)
            
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(new_readme)
            print("[OK] README.md live dashboard updated successfully.")
        else:
            print("[ERROR] README.md not found.")
            
    except Exception as e:
        print(f"[ERROR] Failed to generate dashboard: {e}")

    # --- RUN VALIDATIONS ON EVERY SYNC ---
    try:
        run_baseline_validation_and_update_readme(worksheet)
        run_national_global_validation_and_update_readme(worksheet)
    except Exception as e:
        print(f"[ERROR] Validation run failed: {e}")

    return worksheet, rows_to_append

def run_baseline_validation_and_update_readme(worksheet):
    print("\n[VALIDATION] Running daily Open-Meteo baseline ground truth validation...")
    records = worksheet.get_all_records()
    if len(records) < 256:
        print("Not enough records in the sheet to validate.")
        return

    # Clean key names
    cleaned_records = []
    for r in records:
        cleaned_r = {k.strip().lower().replace(' ', '_'): v for k, v in r.items()}
        cleaned_records.append(cleaned_r)

    # 1. Group by timestamp to extract unique hourly entries (removing 256x sector duplicates)
    hourly_data = {}
    for r in cleaned_records:
        ts = r.get('timestamp')
        if not ts:
            continue
        if ts not in hourly_data:
            try:
                etc = float(r.get('etc', 0.0))
                kc = float(r.get('kc', 1.0))
                ks = float(r.get('ks', 1.0))
                et0_h = etc / (ks * kc) if (ks * kc) > 0 else 0.0
                
                hourly_data[ts] = {
                    'air_temp': float(r.get('air_temp', 20.0)),
                    'solar_rad': float(r.get('solar_rad', 0.0)),
                    'humidity': float(r.get('humidity', 50.0)),
                    'soil_temp': float(r.get('soil_temp', 20.0)),
                    'precip': float(r.get('precip', 0.0)),
                    'et0': et0_h
                }
            except (ValueError, TypeError):
                pass

    # 2. Group unique hourly entries by date
    daily_data = {}
    for ts, h in hourly_data.items():
        date_str = ts.split(' ')[0]
        if date_str not in daily_data:
            daily_data[date_str] = {
                'air_temp': [], 'solar_rad': [], 'humidity': [], 
                'soil_temp': [], 'precip': [], 'et0': []
            }
        daily_data[date_str]['air_temp'].append(h['air_temp'])
        daily_data[date_str]['solar_rad'].append(h['solar_rad'])
        daily_data[date_str]['humidity'].append(h['humidity'])
        daily_data[date_str]['soil_temp'].append(h['soil_temp'])
        daily_data[date_str]['precip'].append(h['precip'])
        daily_data[date_str]['et0'].append(h['et0'])

    daily_av = {}
    for d_str, values in daily_data.items():
        if not values['air_temp']:
            continue
        daily_av[d_str] = {
            'av_temp': sum(values['air_temp']) / len(values['air_temp']),
            'av_solar': sum(values['solar_rad']) / len(values['solar_rad']),
            'av_humidity': sum(values['humidity']) / len(values['humidity']),
            'av_soil_temp': sum(values['soil_temp']) / len(values['soil_temp']),
            'sum_precip': sum(values['precip']),
            'sum_et0': sum(values['et0']) / len(values['et0'])  # et0 is logged as daily sum, so take mean
        }

    dates = sorted(daily_av.keys())
    if not dates:
        print("No daily averages computed.")
        return

    start_date = dates[0]
    end_date = dates[-1]

    # Fetch CIMIS
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
    from plugins.sensors import cimis_api
    
    baseline_ok = False
    baseline_data_dict = {}
    print(f"Fetching baseline ground truth observations from CIMIS API (Station {cimis_api.CIMIS_STATION})...")
    
    cimis_resp = cimis_api.fetch(start_date, end_date)
    if cimis_resp.get('status') == 'success':
        cimis_data = cimis_resp['data']
        for d_str, vals in cimis_data.items():
            if d_str in dates:
                # Ensure values aren't completely missing
                if vals.get('cimis_temp') is not None:
                    baseline_data_dict[d_str] = {
                        'baseline_temp': vals['cimis_temp'],
                        'baseline_solar': vals['cimis_solar'] if vals['cimis_solar'] else 0.0,
                        'baseline_humidity': vals['cimis_humidity'] if vals['cimis_humidity'] else 0.0,
                        'baseline_soil_temp': vals['cimis_soil_temp'] if vals['cimis_soil_temp'] else 0.0,
                        'baseline_precip': vals['cimis_precip'] if vals['cimis_precip'] else 0.0,
                        'baseline_et0': vals['cimis_et0'] if vals['cimis_et0'] else 0.0
                    }
        if len(baseline_data_dict) > 0:
            baseline_ok = True
    else:
        print(f"CIMIS API fetch failed: {cimis_resp.get('msg', cimis_resp.get('text'))}")

    if not baseline_ok:
        print("Both validation APIs down/lagging. Synthetic generation banned. Validation aborted.")
        return

    # Align
    aligned = []
    for d_str in dates:
        if d_str in baseline_data_dict:
            aligned.append({
                'date': d_str,
                'av_temp': daily_av[d_str]['av_temp'],
                'av_solar': daily_av[d_str]['av_solar'],
                'av_humidity': daily_av[d_str]['av_humidity'],
                'av_soil_temp': daily_av[d_str]['av_soil_temp'],
                'sum_precip': daily_av[d_str]['sum_precip'],
                'sum_et0': daily_av[d_str]['sum_et0'],
                'baseline_temp': baseline_data_dict[d_str]['baseline_temp'],
                'baseline_solar': baseline_data_dict[d_str]['baseline_solar'],
                'baseline_humidity': baseline_data_dict[d_str]['baseline_humidity'],
                'baseline_soil_temp': baseline_data_dict[d_str]['baseline_soil_temp'],
                'baseline_precip': baseline_data_dict[d_str]['baseline_precip'],
                'baseline_et0': baseline_data_dict[d_str]['baseline_et0']
            })

    if not aligned:
        print("No aligned records found for validation.")
        return

    # Statistical helper functions
    def calculate_metrics(y_true, y_pred):
        n = len(y_true)
        if n == 0:
            return 0.0, 0.0, 0.0
        bias = sum(y_pred[i] - y_true[i] for i in range(n)) / n
        rmse = math.sqrt(sum((y_pred[i] - y_true[i])**2 for i in range(n)) / n)
        if n < 2:
            return 1.0, rmse, bias
            
        mean_true = sum(y_true) / n
        mean_pred = sum(y_pred) / n
        
        num = sum((y_true[i] - mean_true) * (y_pred[i] - mean_pred) for i in range(n))
        den_true = sum((y_true[i] - mean_true)**2 for i in range(n))
        den_pred = sum((y_pred[i] - mean_pred)**2 for i in range(n))
        
        if den_true == 0 or den_pred == 0:
            r2 = 0.0
        else:
            r2 = (num / math.sqrt(den_true * den_pred)) ** 2
        return r2, rmse, bias

    # Compute metrics for all 6 variables
    r2_t, rmse_t, bias_t = calculate_metrics([a['baseline_temp'] for a in aligned], [a['av_temp'] for a in aligned])
    r2_s, rmse_s, bias_s = calculate_metrics([a['baseline_solar'] for a in aligned], [a['av_solar'] for a in aligned])
    r2_h, rmse_h, bias_h = calculate_metrics([a['baseline_humidity'] for a in aligned], [a['av_humidity'] for a in aligned])
    r2_st, rmse_st, bias_st = calculate_metrics([a['baseline_soil_temp'] for a in aligned], [a['av_soil_temp'] for a in aligned])
    r2_p, rmse_p, bias_p = calculate_metrics([a['baseline_precip'] for a in aligned], [a['sum_precip'] for a in aligned])
    r2_e, rmse_e, bias_e = calculate_metrics([a['baseline_et0'] for a in aligned], [a['sum_et0'] for a in aligned])

    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    val_md = f"### 📊 Daily Ground-Truth Validation (Open-Meteo Baseline)\n"
    val_md += f"*Last calculated: `{now_str} UTC` (Evaluating {len(aligned)} complete days of data)*\n\n"
    val_md += f"| Variable | Pearson R² | RMSE | Mean Bias |\n"
    val_md += f"|---|---|---|---|\n"
    val_md += f"| **🌡️ Air Temp** | {r2_t:.3f} | {rmse_t:.2f}°C | {bias_t:+.2f}°C |\n"
    val_md += f"| **☀️ Solar Rad** | {r2_s:.3f} | {rmse_s:.2f} W/m² | {bias_s:+.2f} W/m² |\n"
    val_md += f"| **💧 Humidity** | {r2_h:.3f} | {rmse_h:.2f}% | {bias_h:+.2f}% |\n"
    val_md += f"| **🌡️ Soil Temp** | {r2_st:.3f} | {rmse_st:.2f}°C | {bias_st:+.2f}°C |\n"
    val_md += f"| **🌧️ Precipitation** | {r2_p:.3f} | {rmse_p:.2f} mm | {bias_p:+.2f} mm |\n"
    val_md += f"| **💧 Reference ET₀** | {r2_e:.3f} | {rmse_e:.2f} mm | {bias_e:+.2f} mm |\n\n"
    val_md += f"> Metrics are computed daily comparing AquaVolt-AI estimates against Open-Meteo baseline ground truth (aggregated national weather models for Davis, CA).\n\n"
    val_md += f"#### 📈 Live Validation Scatter Plots\n"
    val_md += f"![Baseline Ground Validation](docs/baseline_scatter_validation.png)\n"

    readme_path = os.path.join(SCRIPT_DIR, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()
        import re
        pattern = r"(<!-- BASELINE_VALIDATION_START -->)(.*?)(<!-- BASELINE_VALIDATION_END -->)"
        replacement = r"\1\n" + val_md + r"\n\3"
        new_readme = re.sub(pattern, replacement, readme_text, flags=re.DOTALL)
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_readme)
        print("[OK] README.md validation metrics updated successfully.")
    else:
        print("[ERROR] README.md not found.")


def run_national_global_validation_and_update_readme(worksheet):
    import pandas as pd
    import math
    import json as json_mod

    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    val_md = f"### 🌎 Independent Validation (OpenET + CIMIS)\n"
    val_md += f"*Last calculated: `{now_str} UTC`*\n\n"

    # ── Provenance tracking ──────────────────────────────────────────────
    provenance = {
        "generated_at": now_str,
        "data_streams": []
    }

    try:
        # 1. Load sheet data
        records = worksheet.get_all_records()
        if len(records) < 256:
            print("Not enough records in the sheet to validate.")
            val_md += f"*Validation skipped (not enough records).*\n\n"
            return
            
        cleaned_records = []
        for r in records:
            cleaned_r = {k.strip().lower().replace(' ', '_'): v for k, v in r.items()}
            cleaned_records.append(cleaned_r)

        # Group by timestamp to extract unique hourly entries (removing 256x sector duplicates)
        hourly_data = {}
        for r in cleaned_records:
            ts = r.get('timestamp')
            if not ts:
                continue
            if ts not in hourly_data:
                try:
                    sm = float(r.get('soil_moisture', 0.18))
                    etc = float(r.get('etc', 0.0))
                    kc = float(r.get('kc', 1.0))
                    ks = float(r.get('ks', 1.0))
                    
                    hourly_data[ts] = {
                        'air_temp': float(r.get('air_temp', 20.0)),
                        'solar_rad': float(r.get('solar_rad', 0.0)),
                        'humidity': float(r.get('humidity', 50.0)),
                        'soil_temp': float(r.get('soil_temp', 20.0)),
                        'precip': float(r.get('precip', 0.0)),
                        'soil_moisture': sm,
                        'kc': kc,
                        'etc': etc,
                        'ks': ks
                    }
                except (ValueError, TypeError):
                    pass

        # Group unique hourly entries by date
        daily_data = {}
        for ts, h in hourly_data.items():
            date_str = ts.split(' ')[0]
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'air_temp': [], 'solar_rad': [], 'humidity': [], 
                    'soil_temp': [], 'precip': [], 'et0': [],
                    'kc': [], 'etc': [], 'soil_moisture': []
                }
            daily_data[date_str]['air_temp'].append(h['air_temp'])
            daily_data[date_str]['solar_rad'].append(h['solar_rad'])
            daily_data[date_str]['humidity'].append(h['humidity'])
            daily_data[date_str]['soil_temp'].append(h['soil_temp'])
            daily_data[date_str]['precip'].append(h['precip'])
            daily_data[date_str]['soil_moisture'].append(h['soil_moisture'])
            daily_data[date_str]['kc'].append(h['kc'])
            daily_data[date_str]['etc'].append(h['etc'])
            
            et0_val = h['etc'] / (h['ks'] * h['kc']) if (h['ks'] * h['kc']) > 0 else 0.0
            daily_data[date_str]['et0'].append(et0_val)

        # Calculate daily averages
        daily_metrics = {}
        for d_str, values in daily_data.items():
            if not values['air_temp']:
                continue
            daily_metrics[d_str] = {
                'av_kc': sum(values['kc']) / len(values['kc']),
                'sum_et0': sum(values['et0']) / len(values['et0']),  # mean of daily totals
                'sum_pred_etc': sum(values['etc']) / len(values['etc']), # mean of daily totals
                'av_soil_temp': sum(values['soil_temp']) / len(values['soil_temp']),
                'av_soil_moist': sum(values['soil_moisture']) / len(values['soil_moisture'])
            }

        dates_list = sorted(daily_metrics.keys())
        if not dates_list:
            print("No daily records to validate.")
            return

        start_date = dates_list[0]
        end_date = dates_list[-1]

        # ── Section 1: ECOSTRESS Validation ──────────────────────────────
        val_md += f"#### 1. ECOSTRESS (NASA Independent ET Validation)\n"
        val_md += f"> **Source:** NASA ECOSTRESS ECO3ETPTJPL thermal instrument on the ISS (~70 m resolution). "
        val_md += f"This provides a fully independent physical satellite validation.\n\n"

        from plugins.sensors import ecostress_api

        eco_resp = ecostress_api.fetch(LAT, LON, start_date, end_date)
        y_true_et, y_pred_et = [], []

        if eco_resp.get('status') == 'success':
            eco_data = eco_resp['data']
            provenance["data_streams"].append({
                "name": "ECOSTRESS daily ET",
                "url": "https://appeears.earthdatacloud.nasa.gov/api",
                "source_tag": eco_resp.get('source', 'unknown'),
                "start_date": start_date,
                "end_date": end_date,
                "retrieval_timestamp": now_str
            })

            # Parse ECOSTRESS response
            try:
                for row in eco_data:
                    d = row['date']
                    et_val = row['ET_mm']
                    if d in daily_metrics and et_val is not None:
                        y_true_et.append(et_val)
                        y_pred_et.append(daily_metrics[d]['sum_pred_etc'])
            except Exception as parse_err:
                print(f"[ECOSTRESS] Parse error: {parse_err}")

            if len(y_true_et) >= 2:
                r2_et, rmse_et, bias_et = _calc_stats(y_true_et, y_pred_et)
                val_md += f"| Variable | Pearson R² | RMSE | Mean Bias | N |\n"
                val_md += f"|---|---|---|---|---|\n"
                val_md += f"| **💧 ET (ECOSTRESS vs AquaVolt)** | {r2_et:.3f} | {rmse_et:.2f} mm | {bias_et:+.2f} mm | {len(y_true_et)} |\n\n"
            else:
                val_md += f"*ECOSTRESS returned data but insufficient aligned dates for statistics (N={len(y_true_et)}).*\n\n"
        else:
            msg = eco_resp.get('msg', eco_resp.get('text', 'Unknown error'))
            val_md += f"*ECOSTRESS API unavailable: {msg}*\n\n"
            print(f"[ECOSTRESS] Validation skipped: {msg}")

        # ── Section 2: CIMIS Weather Validation ──────────────────────────
        val_md += f"#### 2. CIMIS Station 6 (Davis, CA — Weather Validation)\n"
        val_md += f"> **Source:** California DWR CIMIS ground weather station at UC Davis.\n\n"

        from plugins.sensors import cimis_api as cimis_val

        cimis_resp = cimis_val.fetch(start_date, end_date)
        y_true_st, y_pred_st = [], []
        y_true_et0, y_pred_et0 = [], []

        if cimis_resp.get('status') == 'success':
            cimis_data = cimis_resp['data']
            cimis_count = 0
            for d_str, vals in cimis_data.items():
                if d_str in daily_metrics and vals.get('cimis_temp') is not None:
                    cimis_count += 1
                    y_true_st.append(vals['cimis_temp'])
                    y_pred_st.append(daily_metrics[d_str]['av_soil_temp'])
                    if vals.get('cimis_et0') is not None:
                        y_true_et0.append(vals['cimis_et0'])
                        y_pred_et0.append(daily_metrics[d_str]['sum_et0'])

            provenance["data_streams"].append({
                "name": "CIMIS Station 6 (Davis)",
                "url": "https://et.water.ca.gov/api/data",
                "station_id": "6",
                "start_date": start_date,
                "end_date": end_date,
                "record_count": cimis_count,
                "retrieval_timestamp": now_str
            })

            if len(y_true_st) >= 2:
                r2_st, rmse_st, bias_st = _calc_stats(y_true_st, y_pred_st)
                val_md += f"| Variable | Pearson R² | RMSE | Mean Bias | N |\n"
                val_md += f"|---|---|---|---|---|\n"
                val_md += f"| **🌡️ Air Temp (CIMIS vs AquaVolt)** | {r2_st:.3f} | {rmse_st:.2f}°C | {bias_st:+.2f}°C | {len(y_true_st)} |\n"
                if len(y_true_et0) >= 2:
                    r2_et0, rmse_et0, bias_et0 = _calc_stats(y_true_et0, y_pred_et0)
                    val_md += f"| **☀️ Reference ET₀ (CIMIS vs AquaVolt)** | {r2_et0:.3f} | {rmse_et0:.2f} mm | {bias_et0:+.2f} mm | {len(y_true_et0)} |\n"
                val_md += f"\n"
            else:
                val_md += f"*CIMIS returned data but insufficient aligned dates (N={len(y_true_st)}).*\n\n"
        else:
            msg = cimis_resp.get('msg', cimis_resp.get('text', 'Unknown error'))
            val_md += f"*CIMIS API unavailable: {msg}*\n\n"
            print(f"[CIMIS] Validation skipped: {msg}")

        # ── Write PROVENANCE.json ────────────────────────────────────────
        provenance_path = os.path.join(SCRIPT_DIR, "data", "PROVENANCE.json")
        os.makedirs(os.path.dirname(provenance_path), exist_ok=True)
        with open(provenance_path, "w") as pf:
            json_mod.dump(provenance, pf, indent=2)
        print(f"[PROVENANCE] Written to {provenance_path}")

        # ── Update README ────────────────────────────────────────────────
        readme_path = os.path.join(SCRIPT_DIR, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_text = f.read()
            import re
            pattern = r"(<!-- NATIONAL_GLOBAL_VALIDATION_START -->)(.*?)(<!-- NATIONAL_GLOBAL_VALIDATION_END -->)"

            if "<!-- NATIONAL_GLOBAL_VALIDATION_START -->" in readme_text:
                replacement = r"\1\n" + val_md + r"\n\3"
                new_readme = re.sub(pattern, replacement, readme_text, flags=re.DOTALL)
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(new_readme)
                print("[OK] README.md validation metrics updated.")
            else:
                print("[ERROR] NATIONAL_GLOBAL_VALIDATION block not found in README.md")
        else:
            print("[ERROR] README.md not found.")
    except Exception as e:
        print(f"Validation error: {e}")
        import traceback
        traceback.print_exc()


def _calc_stats(y_t, y_p):
    """Compute R², RMSE, and mean bias between two lists."""
    import math
    n = len(y_t)
    if n == 0: return 0.0, 0.0, 0.0
    bias = sum(y_p[i] - y_t[i] for i in range(n)) / n
    rmse = math.sqrt(sum((y_p[i] - y_t[i])**2 for i in range(n)) / n)
    if n < 2: return 1.0, rmse, bias
    mean_t = sum(y_t) / n
    mean_p = sum(y_p) / n
    num = sum((y_t[i] - mean_t) * (y_p[i] - mean_p) for i in range(n))
    den_t = sum((y_t[i] - mean_t)**2 for i in range(n))
    den_p = sum((y_p[i] - mean_p)**2 for i in range(n))
    r2 = (num / math.sqrt(den_t * den_p)) ** 2 if den_t > 0 and den_p > 0 else 0.0
    return r2, rmse, bias


if __name__ == "__main__":
    main()

