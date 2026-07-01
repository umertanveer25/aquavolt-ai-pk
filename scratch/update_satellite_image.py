"""
Download latest Sentinel-2 image, reproject to EPSG:4326 to ensure 100% correct
spatial alignment, overlay all 4 field 8x8 grids, and save to docs/
"""
import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import sys

try:
    import planetary_computer
    import pystac_client
    import rasterio
    from rasterio.warp import reproject, Resampling
    from rasterio.transform import from_origin
    import certifi
    os.environ["CURL_CA_BUNDLE"] = certifi.where()
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)

# ── Study area & field definitions ──────────────────────────────────────────
FIELDS = [
    {"name": "Field-A (Corn)",   "bbox": [-121.8750, 38.5430, -121.8690, 38.5465], "color": "#4caf50"},
    {"name": "Field-B (Alfalfa)","bbox": [-121.8825, 38.5430, -121.8755, 38.5465], "color": "#2196f3"},
    {"name": "Field-C (Fallow)", "bbox": [-121.8825, 38.5395, -121.8755, 38.5428], "color": "#ff9800"},
    {"name": "Field-D (Tomato)", "bbox": [-121.8750, 38.5395, -121.8690, 38.5428], "color": "#e91e63"},
]

AREA_BBOX = [-121.885, 38.538, -121.868, 38.549]   # full study area

# ── Fetch latest combined scene (Sentinel-2 or Landsat 8/9) ─────────────────
print("Searching for latest Sentinel-2 or Landsat 8/9 scene...")
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)
search = catalog.search(
    collections=["sentinel-2-l2a", "landsat-c2-l2"],
    bbox=AREA_BBOX,
    datetime="2026-06-01/2026-07-02",
    query={"eo:cloud_cover": {"lt": 30}},
)
items = list(search.get_items())
if not items:
    print("No usable scene found. Exiting.")
    sys.exit(1)

# Sort chronologically desc
items.sort(key=lambda x: x.datetime, reverse=True)
item = items[0]
scene_date = item.datetime.strftime("%Y-%m-%d")
cloud_pct  = item.properties.get("eo:cloud_cover", 0)
print(f"Using scene: {item.id} | Date: {scene_date} | Cloud: {cloud_pct:.1f}% | Collection: {item.collection_id}")

is_landsat = "landsat" in item.collection_id.lower()
if is_landsat:
    red_key = "red"
    green_key = "green"
    blue_key = "blue"
else:
    red_key = "B04"
    green_key = "B03"
    blue_key = "B02"

# ── Read and warp bands directly to EPSG:4326 ───────────────────────────────
print(f"Reading and reprojecting RGB bands ({red_key}, {green_key}, {blue_key}) to EPSG:4326...")
def read_and_reproject_band(band_key, out_shape=(512, 512)):
    lon_min, lat_min, lon_max, lat_max = AREA_BBOX
    dst_crs = "EPSG:4326"
    
    with rasterio.open(item.assets[band_key].href) as src:
        # Destination resolution
        res_x = (lon_max - lon_min) / out_shape[1]
        res_y = (lat_max - lat_min) / out_shape[0]
        
        # Create destination transform
        dst_transform = from_origin(lon_min, lat_max, res_x, res_y)
        
        # Initialize destination array
        dst_data = np.zeros(out_shape, dtype=np.float32)
        
        # Perform reprojection
        reproject(
            source=rasterio.band(src, 1),
            destination=dst_data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=Resampling.bilinear
        )
        return dst_data

b04 = read_and_reproject_band(red_key)   # Red
b03 = read_and_reproject_band(green_key) # Green
b02 = read_and_reproject_band(blue_key)  # Blue

# ── Normalise to 0-1 (percentile stretch) ───────────────────────────────────
def norm(band):
    p2, p98 = np.percentile(band[band > 0], [2, 98]) if np.any(band > 0) else (0, 1)
    return np.clip((band - p2) / (p98 - p2 + 1e-9), 0, 1)

rgb = np.dstack([norm(b04), norm(b03), norm(b02)])

# ── Build geographic extent for imshow ──────────────────────────────────────
lon_min, lat_min, lon_max, lat_max = AREA_BBOX
extent = [lon_min, lon_max, lat_min, lat_max]

# ── Plot ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 8), facecolor="#0e1117")
ax.set_facecolor("#0e1117")

# Calculate correct aspect ratio to prevent geographic projection distortion
lat_center = (lat_min + lat_max) / 2.0
correct_aspect = 1.0 / np.cos(np.radians(lat_center))

ax.imshow(rgb, extent=extent, origin="upper", aspect=correct_aspect, interpolation="bilinear")

# ── Draw 8×8 grids for each field ────────────────────────────────────────────
GRID_ROWS, GRID_COLS = 8, 8
for field in FIELDS:
    flon_min, flat_min, flon_max, flat_max = field["bbox"]
    cell_w = (flon_max - flon_min) / GRID_COLS
    cell_h = (flat_max - flat_min) / GRID_ROWS
    color  = field["color"]

    # Field bounding box
    rect = patches.Rectangle(
        (flon_min, flat_min), flon_max - flon_min, flat_max - flat_min,
        linewidth=2.5, edgecolor=color, facecolor="none", zorder=3
    )
    ax.add_patch(rect)

    # Inner grid cells
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx = flon_min + col * cell_w
            cy = flat_min + row * cell_h
            cell_rect = patches.Rectangle(
                (cx, cy), cell_w, cell_h,
                linewidth=0.4, edgecolor=color, facecolor=color,
                alpha=0.10, zorder=2
            )
            ax.add_patch(cell_rect)

    # Position labels to avoid overlaps (top fields labeled above, bottom fields labeled below)
    if flat_min < 38.5410:
        label_y = flat_min - 0.0004
        va_align = "top"
    else:
        label_y = flat_max + 0.0004
        va_align = "bottom"

    ax.text(
        (flon_min + flon_max) / 2, label_y,
        field["name"],
        color=color, fontsize=8.5, fontweight="bold",
        ha="center", va=va_align, zorder=4,
        bbox=dict(boxstyle="round,pad=0.2", facecolor="#0e1117", alpha=0.7, edgecolor=color)
    )

# ── Axis formatting ───────────────────────────────────────────────────────────
ax.set_xlim(lon_min, lon_max)
ax.set_ylim(lat_min, lat_max)

# Fix offset notation — show full lon/lat values
import matplotlib.ticker as mticker
ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.3f'))
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.3f'))
ax.xaxis.get_offset_text().set_visible(False)

ax.tick_params(colors="white", labelsize=8)
for sp in ax.spines.values():
    sp.set_edgecolor("#334155")

ax.set_xlabel("Longitude (deg)", color="white", fontsize=9)
ax.set_ylabel("Latitude (deg)",  color="white", fontsize=9)
ax.set_title(
    f"AquaVolt-AI — Combined Satellite True Colour + 4-Field 8×8 Precision Grid\n"
    f"UC Davis Russell Ranch | Scene: {scene_date} ({'Landsat-8/9' if is_landsat else 'Sentinel-2'}) | Cloud Cover: {cloud_pct:.1f}%",
    color="white", fontsize=11, fontweight="bold", pad=10
)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_patches = [
    patches.Patch(facecolor=f["color"], edgecolor=f["color"],
                  label=f["name"], alpha=0.8)
    for f in FIELDS
]
ax.legend(handles=legend_patches, loc="lower right", fontsize=8,
          facecolor="#1e293b", edgecolor="#334155", labelcolor="white")

plt.tight_layout()
os.makedirs("docs", exist_ok=True)
out_path = "docs/UC_Davis_Russell_Ranch_EXACT_FIELDS.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#0e1117")
plt.close()
print(f"\nSaved updated satellite image with grids to: {out_path}")
print(f"Scene date: {scene_date} | Cloud cover: {cloud_pct:.1f}%")
