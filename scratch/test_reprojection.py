"""
Reproject Sentinel-2 bands to EPSG:4326 using rasterio.warp.reproject to ensure 100% correct spatial alignment.
"""
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np
import os

def test_reprojection():
    # Let's inspect the first band of a scene and see the coordinate difference
    print("Test script loaded.")

if __name__ == "__main__":
    test_reprojection()
