#!/usr/bin/env python3
"""
Data Processing Utilities for Simple MISR Reprojection
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from constants import (
    RDQI_FILL_VALUE,
    RDQI_RADIANCE_MASK,
    RDQI_QUALITY_MASK,
    RDQI_QUALITY_SHIFT,
)


class DataProcessor:
    """Utility class for MISR data processing"""

    @staticmethod
    def apply_quality_filtering(
        data_array, field_name, grid_obj, region, apply_filter=True
    ):
        """Apply quality filtering to MISR data

        Args:
            data_array: Raw data array
            field_name: Name of the field being processed
            grid_obj: MISR grid object
            region: MISR region object
            apply_filter: Whether to apply quality filtering

        Returns:
            numpy.ndarray: Processed data array
        """
        processed_data = data_array.astype(np.float64)

        if not apply_filter or "Radiance" not in field_name:
            # Basic filtering without quality flags
            if "RDQI" in field_name:
                fill_value = RDQI_FILL_VALUE
                radiance_dn = processed_data.astype(np.int32) & RDQI_RADIANCE_MASK
                quality_mask = (processed_data != fill_value) & (processed_data < 16384)
                processed_data = radiance_dn.astype(np.float64)
                processed_data[~quality_mask] = np.nan
            else:
                processed_data[processed_data < -1000] = np.nan
            return processed_data

        # Apply quality filtering
        if "RDQI" in field_name:
            # Extract quality from packed RDQI data
            radiance_dn = processed_data.astype(np.int32) & RDQI_RADIANCE_MASK
            quality_flags = (
                processed_data.astype(np.int32) >> RDQI_QUALITY_SHIFT
            ) & RDQI_QUALITY_MASK
            quality_mask = (processed_data != RDQI_FILL_VALUE) & (quality_flags <= 1)
            processed_data = radiance_dn.astype(np.float64)
            processed_data[~quality_mask] = np.nan
        else:
            # For pure radiance data, get quality from corresponding RDQI field
            try:
                rdqi_field_name = field_name + "/RDQI"
                rdqi_field_obj = grid_obj.field(rdqi_field_name)
                rdqi_data = rdqi_field_obj.read(region).data()

                # Extract quality flags from RDQI data
                quality_flags = (
                    rdqi_data.astype(np.int32) >> RDQI_QUALITY_SHIFT
                ) & RDQI_QUALITY_MASK
                quality_mask = (rdqi_data != RDQI_FILL_VALUE) & (quality_flags <= 1)

                # Apply quality mask to radiance data
                processed_data[~quality_mask] = np.nan

            except Exception:
                # Fallback to basic filtering
                processed_data[processed_data < -1000] = np.nan

        return processed_data

    @staticmethod
    def calculate_statistics(data_array):
        """Calculate basic statistics for the data array

        Args:
            data_array: Data array to analyze

        Returns:
            dict: Dictionary with statistics
        """
        valid_mask = ~np.isnan(data_array)
        valid_pixels = np.sum(valid_mask)
        total_pixels = data_array.size

        stats = {
            "valid_pixels": valid_pixels,
            "total_pixels": total_pixels,
            "valid_percentage": (
                100 * valid_pixels / total_pixels if total_pixels > 0 else 0
            ),
        }

        if valid_pixels > 0:
            valid_data = data_array[valid_mask]
            stats.update(
                {
                    "min_value": float(valid_data.min()),
                    "max_value": float(valid_data.max()),
                    "mean_value": float(valid_data.mean()),
                    "std_value": float(valid_data.std()),
                }
            )

        return stats

    @staticmethod
    def get_grid_name(field_name):
        """Get the appropriate grid name for a field

        Args:
            field_name: Name of the field

        Returns:
            str: Grid name
        """
        from constants import GRID_NAME_MAP

        for color, grid_name in GRID_NAME_MAP.items():
            if color in field_name:
                return grid_name

        return "RedBand"  # default
