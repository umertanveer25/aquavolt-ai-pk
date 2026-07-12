"""
Verify coordinates, aspect ratios, and label positioning to ensure the spatial plot is mathematically and visually perfect.
"""
import numpy as np

# Let's calculate the correct aspect ratio for UC Davis (Latitude ~38.54)
lat_center = 38.54
cos_lat = np.cos(np.radians(lat_center))
correct_aspect = 1.0 / cos_lat
print(f"Correct matplotlib aspect ratio for Lat {lat_center}: {correct_aspect:.4f}")
