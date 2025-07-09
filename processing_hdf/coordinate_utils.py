#!/usr/bin/env python3
"""
Coordinate Utilities for Simple MISR Reprojection
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from constants import PROGRESS_UPDATE_INTERVAL


class CoordinateUtils:
    """Utility class for coordinate operations"""

    @staticmethod
    def convert_pixel_coordinates(mapinfo, data_shape, progress_callback=None):
        """Convert pixel coordinates to lat/lon using MISR Toolkit

        Args:
            mapinfo: MISR Toolkit map info object
            data_shape: Shape of the data array (rows, cols)
            progress_callback: Optional callback for progress updates

        Returns:
            tuple: (lat_array, lon_array) as numpy arrays
        """
        rows, cols = data_shape
        lat_array = np.zeros((rows, cols))
        lon_array = np.zeros((rows, cols))

        # Convert coordinates (with progress updates)
        for i in range(rows):
            if progress_callback and i % max(1, rows // PROGRESS_UPDATE_INTERVAL) == 0:
                progress_pct = int(100 * i / rows)
                progress_callback(f"Converting coordinates... {progress_pct}%")

            for j in range(cols):
                try:
                    lat, lon = mapinfo.ls_to_latlon(i, j)
                    lat_array[i, j] = lat
                    lon_array[i, j] = lon
                except:
                    lat_array[i, j] = np.nan
                    lon_array[i, j] = np.nan

        return lat_array, lon_array

    @staticmethod
    def calculate_geotransform(lat_array, lon_array, data_shape):
        """Calculate GeoTIFF geotransform parameters

        Args:
            lat_array: Latitude array
            lon_array: Longitude array
            data_shape: Shape of the data array (rows, cols)

        Returns:
            list: GDAL geotransform parameters
        """
        rows, cols = data_shape

        min_lon = np.nanmin(lon_array)
        max_lon = np.nanmax(lon_array)
        min_lat = np.nanmin(lat_array)
        max_lat = np.nanmax(lat_array)

        pixel_width = (max_lon - min_lon) / cols
        pixel_height = (max_lat - min_lat) / rows

        geotransform = [min_lon, pixel_width, 0, max_lat, 0, -pixel_height]

        return geotransform

    @staticmethod
    def get_coordinate_bounds(lat_array, lon_array):
        """Get coordinate bounds from lat/lon arrays

        Args:
            lat_array: Latitude array
            lon_array: Longitude array

        Returns:
            dict: Dictionary with min/max lat/lon values
        """
        return {
            "min_lat": np.nanmin(lat_array),
            "max_lat": np.nanmax(lat_array),
            "min_lon": np.nanmin(lon_array),
            "max_lon": np.nanmax(lon_array),
        }
