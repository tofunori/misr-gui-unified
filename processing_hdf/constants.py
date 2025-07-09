#!/usr/bin/env python3
"""
Constants for Simple MISR Reprojection GUI
"""

# Saskatchewan Glacier default coordinates
DEFAULT_SASKATCHEWAN_COORDS = {
    "ulc_lat": 52.3,
    "ulc_lon": -117.5,
    "lrc_lat": 52.0,
    "lrc_lon": -117.0,
}

# Full scene default coordinates
DEFAULT_FULL_SCENE_COORDS = {
    "ulc_lat": 55.0,
    "ulc_lon": -120.0,
    "lrc_lat": 50.0,
    "lrc_lon": -115.0,
}

# Data type options
DATA_TYPE_OPTIONS = [
    "Red Radiance/RDQI",
    "Red Radiance",
    "Red Brf",
    "Green Radiance/RDQI",
    "Blue Radiance/RDQI",
    "NIR Radiance/RDQI",
]

# Grid name mapping
GRID_NAME_MAP = {
    "Red": "RedBand",
    "Green": "GreenBand",
    "Blue": "BlueBand",
    "NIR": "NIRBand",
}

# Quality filtering constants
RDQI_FILL_VALUE = 65515
RDQI_RADIANCE_MASK = 0x3FFF
RDQI_QUALITY_MASK = 0x3
RDQI_QUALITY_SHIFT = 14

# Default output filename
DEFAULT_OUTPUT_FILE = "misr_reprojected_wgs84.tif"

# Default MISR data directory
DEFAULT_DATA_DIR = "/home/tofunori/Projects/misr_reproject/data"

# Progress update interval (for coordinate conversion)
PROGRESS_UPDATE_INTERVAL = 10

# EPSG code for WGS84
WGS84_EPSG = 4326

# NoData value for GeoTIFF
GEOTIFF_NODATA = -9999
