"""
Clipper Module
Handles shapefile-based clipping of raster data.
"""

import numpy as np
import xarray as xr
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from shapely.geometry import box
from typing import Optional, Union, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Clipper:
    """Clips raster data using shapefile geometries."""

    def __init__(self, shapefile_path: Optional[str] = None):
        """Initialize clipper with optional shapefile."""
        self.shapefile_path = shapefile_path
        self.geometries = None
        self.shapefile_crs = None

    def load_shapefile(self, shapefile_path: str):
        """Load and validate shapefile."""
        try:
            self.shapefile_path = Path(shapefile_path)
            gdf = gpd.read_file(shapefile_path)

            if gdf.empty:
                raise ValueError("Shapefile contains no geometries")

            self.geometries = gdf.geometry.tolist()
            self.shapefile_crs = gdf.crs

            logger.info(
                f"Loaded shapefile with {len(self.geometries)} geometries, CRS: {self.shapefile_crs}"
            )

            return gdf

        except Exception as e:
            logger.error(f"Failed to load shapefile: {e}")
            raise ValueError(f"Cannot load shapefile: {e}")

    def validate_shapefile(self, shapefile_path: str) -> bool:
        """Validate shapefile without loading."""
        try:
            gdf = gpd.read_file(shapefile_path)
            return not gdf.empty and gdf.crs is not None
        except Exception as e:
            logger.warning(f"Shapefile validation failed: {e}")
            return False

    def reproject_geometries(self, target_crs: Union[str, CRS]) -> list:
        """Reproject geometries to target CRS."""
        if self.geometries is None:
            raise ValueError("No geometries loaded")

        try:
            # Create GeoDataFrame for reprojection
            gdf = gpd.GeoDataFrame(geometry=self.geometries, crs=self.shapefile_crs)

            # Reproject if needed
            if gdf.crs != target_crs:
                gdf = gdf.to_crs(target_crs)
                logger.info(f"Reprojected geometries to {target_crs}")

            return gdf.geometry.tolist()

        except Exception as e:
            logger.error(f"Failed to reproject geometries: {e}")
            raise ValueError(f"Cannot reproject geometries: {e}")

    def clip_xarray_dataset(
        self, dataset: xr.Dataset, data_var: str = "red_radiance"
    ) -> xr.Dataset:
        """Clip xarray dataset using loaded geometries."""
        if self.geometries is None:
            raise ValueError("No shapefile loaded for clipping")

        try:
            # Get dataset coordinates and transform
            lats = dataset.lat.values
            lons = dataset.lon.values
            data = dataset[data_var].values

            # Create transform for rasterio
            transform = from_bounds(
                west=lons.min(),
                south=lats.min(),
                east=lons.max(),
                north=lats.max(),
                width=data.shape[1],
                height=data.shape[0],
            )

            # Determine CRS (assume WGS84 if not specified)
            if "crs" in dataset.data_vars:
                crs = CRS.from_wkt(dataset.crs.attrs.get("crs_wkt", "EPSG:4326"))
            else:
                crs = CRS.from_epsg(4326)

            # Reproject geometries to match dataset CRS
            geometries = self.reproject_geometries(crs)

            # Create in-memory raster
            with rasterio.MemoryFile() as memfile:
                with memfile.open(
                    driver="GTiff",
                    height=data.shape[0],
                    width=data.shape[1],
                    count=1,
                    dtype=data.dtype,
                    crs=crs,
                    transform=transform,
                    nodata=np.nan,
                ) as raster:
                    raster.write(data, 1)

                    # Perform clipping
                    try:
                        clipped_data, clipped_transform = mask(
                            raster, geometries, crop=True, filled=False
                        )
                        clipped_data = clipped_data[0]  # Remove band dimension

                        if clipped_data.size == 0:
                            raise ValueError("Clipping resulted in empty dataset")

                        # Calculate new coordinates
                        height, width = clipped_data.shape
                        new_lons = np.linspace(
                            clipped_transform.c,
                            clipped_transform.c + width * clipped_transform.a,
                            width,
                        )
                        new_lats = np.linspace(
                            clipped_transform.f,
                            clipped_transform.f + height * clipped_transform.e,
                            height,
                        )

                        # Create clipped dataset
                        clipped_ds = xr.Dataset(
                            {data_var: (["lat", "lon"], clipped_data)},
                            coords={"lat": new_lats, "lon": new_lons},
                        )

                        # Copy attributes
                        clipped_ds.attrs = dataset.attrs.copy()
                        clipped_ds[data_var].attrs = dataset[data_var].attrs.copy()
                        clipped_ds.lat.attrs = dataset.lat.attrs.copy()
                        clipped_ds.lon.attrs = dataset.lon.attrs.copy()

                        # Add CRS if present
                        if "crs" in dataset.data_vars:
                            clipped_ds = clipped_ds.assign(crs=dataset.crs)

                        valid_pixels = np.sum(~np.isnan(clipped_data))
                        logger.info(
                            f"Clipped dataset to {clipped_data.shape} with {valid_pixels} valid pixels"
                        )

                        return clipped_ds

                    except Exception as clip_error:
                        logger.error(f"Clipping operation failed: {clip_error}")
                        raise ValueError(f"Clipping failed: {clip_error}")

        except Exception as e:
            logger.error(f"Failed to clip dataset: {e}")
            raise ValueError(f"Cannot clip dataset: {e}")

    def get_shapefile_bounds(self) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box of loaded shapefile."""
        if self.geometries is None:
            return None

        try:
            gdf = gpd.GeoDataFrame(geometry=self.geometries, crs=self.shapefile_crs)
            bounds = gdf.bounds
            return (
                bounds.minx.min(),
                bounds.miny.min(),
                bounds.maxx.max(),
                bounds.maxy.max(),
            )
        except Exception as e:
            logger.warning(f"Failed to get shapefile bounds: {e}")
            return None

    def check_overlap(self, dataset: xr.Dataset) -> bool:
        """Check if shapefile overlaps with dataset bounds."""
        if self.geometries is None:
            return False

        try:
            # Get dataset bounds
            lats = dataset.lat.values
            lons = dataset.lon.values
            data_bounds = box(lons.min(), lats.min(), lons.max(), lats.max())

            # Get shapefile bounds
            gdf = gpd.GeoDataFrame(geometry=self.geometries, crs=self.shapefile_crs)

            # Reproject to dataset CRS for comparison
            if self.shapefile_crs != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")

            # Check for overlap
            for geom in gdf.geometry:
                if geom.intersects(data_bounds):
                    return True

            return False

        except Exception as e:
            logger.warning(f"Failed to check overlap: {e}")
            return True  # Assume overlap if check fails

    def get_geometry_info(self) -> dict:
        """Get information about loaded geometries."""
        if self.geometries is None:
            return {}

        try:
            gdf = gpd.GeoDataFrame(geometry=self.geometries, crs=self.shapefile_crs)
            bounds = self.get_shapefile_bounds()

            return {
                "num_geometries": len(self.geometries),
                "crs": str(self.shapefile_crs),
                "bounds": bounds,
                "geometry_types": gdf.geom_type.value_counts().to_dict(),
                "total_area": gdf.area.sum() if self.shapefile_crs else None,
            }

        except Exception as e:
            logger.warning(f"Failed to get geometry info: {e}")
            return {"error": str(e)}
