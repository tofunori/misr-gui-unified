"""
Reprojector Module
Handles reprojection of MISR data to WGS84 coordinates.
"""

import numpy as np
import xarray as xr
from scipy.interpolate import griddata
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Reprojector:
    """Reprojects MISR data from sinusoidal to WGS84 projection."""

    def __init__(
        self,
        target_lat: float = -13.8,
        target_lon: float = -70.8,
        region_margin: float = 2.0,
        target_resolution: float = 0.0025,
        scale_factor: int = 64,
    ):
        """Initialize reprojector with target parameters."""
        self.target_lat = target_lat
        self.target_lon = target_lon
        self.region_margin = region_margin
        self.target_resolution = target_resolution
        self.scale_factor = scale_factor

    def find_region_bounds(
        self, lat_grid: np.ndarray, lon_grid: np.ndarray
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find bounding box for target region."""
        try:
            in_region = (
                (lat_grid >= self.target_lat - self.region_margin)
                & (lat_grid <= self.target_lat + self.region_margin)
                & (lon_grid >= self.target_lon - self.region_margin)
                & (lon_grid <= self.target_lon + self.region_margin)
            )

            if np.sum(in_region) == 0:
                logger.warning("No data found in target region")
                return None

            rows, cols = np.where(in_region)
            row_min, row_max = rows.min(), rows.max()
            col_min, col_max = cols.min(), cols.max()

            logger.info(
                f"Found region bounds: rows[{row_min}:{row_max}], cols[{col_min}:{col_max}]"
            )
            return row_min, row_max, col_min, col_max

        except Exception as e:
            logger.error(f"Failed to find region bounds: {e}")
            raise ValueError(f"Cannot determine region bounds: {e}")

    def extract_subset(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        red_data: np.ndarray,
        bounds: Tuple[int, int, int, int],
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Extract geographic and data subsets for region."""
        row_min, row_max, col_min, col_max = bounds

        # Extract geographic subset
        lat_subset = lat_grid[row_min : row_max + 1, col_min : col_max + 1]
        lon_subset = lon_grid[row_min : row_max + 1, col_min : col_max + 1]

        # Check if red data has the same resolution as geometry data
        if red_data.shape == lat_grid.shape:
            # Same resolution - no scale factor needed
            red_subset = red_data[row_min : row_max + 1, col_min : col_max + 1]
        else:
            # Calculate red band indices with scale factor
            red_row_start = row_min * self.scale_factor
            red_row_end = (row_max + 1) * self.scale_factor
            red_col_start = col_min * self.scale_factor
            red_col_end = (col_max + 1) * self.scale_factor

            # Extract red band subset
            red_subset = red_data[red_row_start:red_row_end, red_col_start:red_col_end]

        logger.info(
            f"Extracted subsets - geo: {lat_subset.shape}, red: {red_subset.shape}"
        )
        return lat_subset, lon_subset, red_subset

    def create_fine_grid(
        self, lat_subset: np.ndarray, lon_subset: np.ndarray, red_subset: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create fine-resolution coordinate grids for red band data."""
        lat_coords_fine = np.linspace(
            lat_subset[0, 0], lat_subset[-1, -1], red_subset.shape[0]
        )
        lon_coords_fine = np.linspace(
            lon_subset[0, 0], lon_subset[-1, -1], red_subset.shape[1]
        )

        lon_fine_grid, lat_fine_grid = np.meshgrid(lon_coords_fine, lat_coords_fine)
        return lat_fine_grid, lon_fine_grid

    def _calculate_native_resolution(
        self, center_lat: float, target_ground_resolution_m: float = 275.0
    ) -> Tuple[float, float]:
        """Calculate native resolution in degrees for both lat/lon at given latitude.

        Args:
            center_lat: Center latitude in degrees
            target_ground_resolution_m: Target ground resolution in meters (default: 275m)

        Returns:
            Tuple of (lat_resolution_deg, lon_resolution_deg)
        """
        # Latitude resolution (constant globally)
        lat_resolution_deg = target_ground_resolution_m / 111320.0  # ~0.0025° for 275m

        # Longitude resolution (varies by latitude)
        lon_resolution_deg = target_ground_resolution_m / (
            111320.0 * np.cos(np.radians(center_lat))
        )

        return lat_resolution_deg, lon_resolution_deg

    def reproject_to_wgs84(
        self,
        lat_fine_grid: np.ndarray,
        lon_fine_grid: np.ndarray,
        red_subset: np.ndarray,
    ) -> Optional[xr.Dataset]:
        """Reproject data to regular WGS84 grid."""
        try:
            # Remove invalid data
            valid_mask = ~np.isnan(red_subset)
            if np.sum(valid_mask) == 0:
                logger.warning("No valid data found in subset")
                return None

            # Extract valid points
            lat_points = lat_fine_grid[valid_mask]
            lon_points = lon_fine_grid[valid_mask]
            red_points = red_subset[valid_mask]

            # Define output grid
            lat_min, lat_max = lat_points.min(), lat_points.max()
            lon_min, lon_max = lon_points.min(), lon_points.max()

            # Calculate native resolution for rectangular pixels
            center_lat = (lat_min + lat_max) / 2
            lat_res, lon_res = self._calculate_native_resolution(center_lat)

            logger.info(
                f"Native resolution at {center_lat:.2f}°: lat={lat_res:.6f}°, lon={lon_res:.6f}°"
            )

            output_lats = np.arange(lat_min, lat_max + lat_res, lat_res)
            output_lons = np.arange(lon_min, lon_max + lon_res, lon_res)

            output_lon_grid, output_lat_grid = np.meshgrid(output_lons, output_lats)

            # Interpolate to regular grid
            output_points = np.column_stack(
                [output_lat_grid.ravel(), output_lon_grid.ravel()]
            )
            source_points = np.column_stack([lat_points, lon_points])

            logger.info(f"Interpolating {len(red_points)} points to regular grid")
            red_output_flat = griddata(
                source_points,
                red_points,
                output_points,
                method="linear",
                fill_value=np.nan,
            )
            red_output = red_output_flat.reshape(output_lat_grid.shape)

            if np.sum(~np.isnan(red_output)) == 0:
                logger.warning("No valid data after interpolation")
                return None

            # Create xarray dataset
            result_ds = self._create_dataset(red_output, output_lats, output_lons)
            logger.info(f"Successfully reprojected to {red_output.shape} grid")
            return result_ds

        except Exception as e:
            logger.error(f"Reprojection failed: {e}")
            raise ValueError(f"Cannot reproject data: {e}")

    def _create_dataset(
        self, red_output: np.ndarray, output_lats: np.ndarray, output_lons: np.ndarray
    ) -> xr.Dataset:
        """Create xarray dataset with proper metadata."""
        result_ds = xr.Dataset(
            {"red_radiance": (["lat", "lon"], red_output)},
            coords={"lat": output_lats, "lon": output_lons},
        )

        # Add coordinate attributes
        result_ds["lat"].attrs = {
            "units": "degrees_north",
            "long_name": "latitude",
            "standard_name": "latitude",
        }

        result_ds["lon"].attrs = {
            "units": "degrees_east",
            "long_name": "longitude",
            "standard_name": "longitude",
        }

        # Add data variable attributes
        result_ds["red_radiance"].attrs = {
            "units": "W/m²/sr/μm",
            "long_name": "Red band radiance",
            "grid_mapping": "crs",
        }

        # Add global attributes
        result_ds.attrs = {
            "title": "MISR Red Band - Native 275m Resolution WGS84",
            "source": "MISR Camera",
            "description": "Native 275m resolution reprojected to WGS84 grid",
            "Conventions": "CF-1.6",
            "resolution": f"{self.target_resolution}° (~275m)",
        }

        # Add CRS information
        result_ds = result_ds.assign(
            crs=xr.DataArray(
                data=0,
                attrs={
                    "grid_mapping_name": "latitude_longitude",
                    "longitude_of_prime_meridian": 0.0,
                    "semi_major_axis": 6378137.0,
                    "inverse_flattening": 298.257223563,
                    "spatial_ref": 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]',
                    "crs_wkt": 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]',
                },
            )
        )

        return result_ds

    def update_target_region(
        self, target_lat: float, target_lon: float, region_margin: float = None
    ):
        """Update target region parameters."""
        self.target_lat = target_lat
        self.target_lon = target_lon
        if region_margin is not None:
            self.region_margin = region_margin
        logger.info(f"Updated target region: ({target_lat}, {target_lon})")

    def get_config(self) -> Dict[str, Any]:
        """Get current reprojector configuration."""
        return {
            "target_lat": self.target_lat,
            "target_lon": self.target_lon,
            "region_margin": self.region_margin,
            "target_resolution": self.target_resolution,
            "scale_factor": self.scale_factor,
        }
