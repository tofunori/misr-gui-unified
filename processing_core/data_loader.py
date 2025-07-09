"""
Data Loader Module
Handles loading and validation of MISR .nc and .hdf files.
"""

import xarray as xr
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from osgeo import gdal
    import rioxarray

    HDF_SUPPORT = True
except ImportError:
    HDF_SUPPORT = False
    logger.warning("GDAL/rioxarray not available - HDF files not supported")

# Mapping from NetCDF group/variable paths to HDF field names
HDF_FIELD_MAPPING = {
    "Radiance_275_m/Red_Band": "Red Radiance/RDQI",
    "QA": "Red Radiance/RDQI",  # RDQI contains quality info
}


class DataLoader:
    """Loads and validates MISR .nc and .hdf files with lazy loading."""

    def __init__(self, filepath: str):
        """Initialize with MISR file path."""
        self.filepath = Path(filepath)
        self.is_hdf = self._detect_hdf_format()

        # For HDF files, ensure we're using the right file type
        if self.is_hdf:
            self.filepath = self._ensure_correct_hdf_file(self.filepath)

        self._geom_ds = None
        self._red_ds = None
        self._qa_ds = None
        self._metadata = {}
        self._hdf_subdatasets = None

    def _detect_hdf_format(self) -> bool:
        """Detect if file is HDF format."""
        suffix = self.filepath.suffix.lower()
        return suffix in [".hdf", ".hdf4"]

    def _ensure_correct_hdf_file(self, filepath: Path) -> Path:
        """Ensure we're using the correct HDF file type for processing.

        For MISR HDF files:
        - GMP files contain geometry data only
        - GRP_TERRAIN_GM files contain radiance data and can reference GMP for geometry

        Always prefer GRP_TERRAIN_GM files for processing.
        """
        filename = filepath.name

        # If this is already a GRP_TERRAIN_GM file, use it
        if "GRP_TERRAIN_GM" in filename:
            logger.info(f"Using GRP_TERRAIN_GM file: {filepath}")
            return filepath

        # If this is a GMP file, try to find corresponding GRP_TERRAIN_GM file
        if "GP_GMP" in filename:
            # Try to find corresponding GRP_TERRAIN_GM file
            terrain_filename = filename.replace("GP_GMP", "GRP_TERRAIN_GM")
            terrain_filename = terrain_filename.replace(
                "_F03_", "_AN_F03_"
            )  # Add camera designation
            terrain_path = filepath.parent / terrain_filename

            if terrain_path.exists():
                logger.info(
                    f"Switching from GMP to GRP_TERRAIN_GM file: {terrain_path}"
                )
                return terrain_path
            else:
                # Search for any GRP_TERRAIN_GM file with similar pattern
                base_pattern = filename.split("_MISR_")[0]
                terrain_files = list(
                    filepath.parent.glob(f"{base_pattern}_*GRP_TERRAIN_GM*.hdf")
                )

                if terrain_files:
                    logger.info(
                        f"Found GRP_TERRAIN_GM file by pattern: {terrain_files[0]}"
                    )
                    return terrain_files[0]
                else:
                    logger.warning(
                        f"No GRP_TERRAIN_GM file found for {filename}, using GMP file"
                    )
                    return filepath

        # For other file types, return as-is
        return filepath

    def _get_hdf_subdatasets(self) -> Dict[str, str]:
        """Get HDF subdatasets using GDAL."""
        if not HDF_SUPPORT:
            raise RuntimeError("GDAL not available for HDF support")

        if self._hdf_subdatasets is None:
            try:
                gdal.UseExceptions()
                ds = gdal.Open(str(self.filepath), gdal.GA_ReadOnly)
                if ds is None:
                    raise ValueError(f"Could not open HDF file: {self.filepath}")

                subdatasets = ds.GetSubDatasets()
                self._hdf_subdatasets = {}

                for full_name, description in subdatasets:
                    # Extract field name from subdataset name
                    # Format: HDF4_EOS:EOS_GRID:"file.hdf":GroupName:FieldName
                    parts = full_name.split(":")
                    if len(parts) >= 5:
                        field_name = parts[-1]
                        # Remove quotes if present
                        if field_name.startswith('"') and field_name.endswith('"'):
                            field_name = field_name[1:-1]
                        self._hdf_subdatasets[field_name] = full_name
                        logger.debug(f"Found HDF field: {field_name}")

                ds = None  # Close dataset
                logger.info(f"Found {len(self._hdf_subdatasets)} HDF subdatasets")

            except Exception as e:
                logger.error(f"Failed to read HDF subdatasets: {e}")
                raise ValueError(f"Cannot read HDF file structure: {e}")

        return self._hdf_subdatasets

    def _find_best_radiance_band(self, red_da: xr.DataArray) -> int:
        """Find the best band index with valid radiance data."""
        # 65515 is likely a fill value, so we want to avoid bands with all/mostly this value
        fill_value = 65515

        best_band_idx = None
        best_score = -1

        for band_idx in range(red_da.shape[0]):
            band_data = red_da[band_idx].values

            # Skip bands where all values are fill values
            if np.all(band_data == fill_value):
                continue

            # Calculate score based on:
            # 1. Percentage of non-fill values
            # 2. Reasonable radiance value range
            non_fill_mask = band_data != fill_value
            non_fill_count = np.sum(non_fill_mask)

            if non_fill_count == 0:
                continue

            # Calculate score
            non_fill_percentage = non_fill_count / band_data.size

            # Check if values are in reasonable radiance range (not all zeros)
            valid_values = band_data[non_fill_mask]
            has_reasonable_values = np.any(valid_values > 0) and np.any(
                valid_values < 60000
            )

            if has_reasonable_values:
                score = non_fill_percentage
                if score > best_score:
                    best_score = score
                    best_band_idx = band_idx

        if best_band_idx is not None:
            logger.info(
                f"Best radiance band: {best_band_idx} (score: {best_score:.3f})"
            )

        return best_band_idx

    def _load_hdf_field(self, nc_path: str) -> xr.DataArray:
        """Load HDF field as xarray DataArray."""
        if nc_path not in HDF_FIELD_MAPPING:
            raise ValueError(f"No HDF mapping for NetCDF path: {nc_path}")

        hdf_field = HDF_FIELD_MAPPING[nc_path]
        subdatasets = self._get_hdf_subdatasets()

        if hdf_field not in subdatasets:
            raise ValueError(f"HDF field not found: {hdf_field}")

        try:
            gdal_path = subdatasets[hdf_field]
            da = rioxarray.open_rasterio(gdal_path, chunks=True)
            # Remove band dimension if present
            if da.dims[0] == "band" and da.shape[0] == 1:
                da = da.squeeze("band", drop=True)

            logger.info(f"Loaded HDF field {hdf_field} from {self.filepath}")
            return da

        except Exception as e:
            logger.error(f"Failed to load HDF field {hdf_field}: {e}")
            raise ValueError(f"Cannot load HDF field {hdf_field}: {e}")

    def _create_hdf_geometry(self) -> xr.Dataset:
        """Create lat/lon grids from GMP file metadata."""
        try:
            # Try to find corresponding GMP file
            gmp_filepath = self._find_gmp_file()
            if gmp_filepath is None:
                raise ValueError(
                    "Cannot find corresponding GMP file for coordinate data"
                )

            # Open GMP file to get lat/lon coordinates from metadata
            gdal.UseExceptions()
            ds = gdal.Open(str(gmp_filepath), gdal.GA_ReadOnly)
            if ds is None:
                raise ValueError(f"Could not open GMP file: {gmp_filepath}")

            # Get coordinate data from GMP metadata
            metadata = ds.GetMetadata()

            # Extract GRING coordinate points from metadata
            gring_lat_keys = [
                k for k in metadata.keys() if "GRINGPOINTLATITUDE" in k.upper()
            ]
            gring_lon_keys = [
                k for k in metadata.keys() if "GRINGPOINTLONGITUDE" in k.upper()
            ]
            gring_seq_keys = [
                k for k in metadata.keys() if "GRINGPOINTSEQUENCENO" in k.upper()
            ]

            if not gring_lat_keys or not gring_lon_keys or not gring_seq_keys:
                raise ValueError(
                    "No complete GRING coordinate data found in GMP metadata"
                )

            # Parse coordinate data
            gring_lats = [
                float(x.strip()) for x in metadata[gring_lat_keys[0]].split(",")
            ]
            gring_lons = [
                float(x.strip()) for x in metadata[gring_lon_keys[0]].split(",")
            ]
            gring_seq = [int(x.strip()) for x in metadata[gring_seq_keys[0]].split(",")]

            # Get spatial dimensions from the main HDF file
            subdatasets = self._get_hdf_subdatasets()
            first_field = list(subdatasets.keys())[0]
            gdal_path = subdatasets[first_field]

            with rioxarray.open_rasterio(gdal_path, chunks=True) as da:
                height, width = da.shape[-2:]

            logger.info(
                f"Found {len(gring_lats)} GRING coordinate points for {height}x{width} grid"
            )

            # GRING coordinates represent boundary/sampling points for Saskatchewan Glacier
            # Create coordinate grids by interpolating from these reference points
            logger.info(
                f"Creating coordinate grids from {len(gring_lats)} GRING reference points for Saskatchewan Glacier area"
            )

            # Extract coordinate bounds from GRING data
            lat_min, lat_max = min(gring_lats), max(gring_lats)
            lon_min, lon_max = min(gring_lons), max(gring_lons)

            logger.info(
                f"Saskatchewan Glacier coordinate bounds: "
                f"lat [{lat_min:.4f}, {lat_max:.4f}], "
                f"lon [{lon_min:.4f}, {lon_max:.4f}]"
            )

            # Create coordinate grids using geographic bounds
            # Saskatchewan Glacier is in Canadian Rockies (~52°N, -117°W)
            y_coords = np.linspace(lat_max, lat_min, height)  # Top to bottom
            x_coords = np.linspace(lon_min, lon_max, width)  # Left to right
            lons, lats = np.meshgrid(x_coords, y_coords)

            logger.info(
                f"Created {height}x{width} coordinate grids for Saskatchewan Glacier"
            )
            logger.info(
                f"Coordinate range: lat [{np.min(lats):.4f}, {np.max(lats):.4f}], lon [{np.min(lons):.4f}, {np.max(lons):.4f}]"
            )

            # Create coordinate arrays with proper dimensions
            lat_da = xr.DataArray(
                lats,
                dims=["y", "x"],
                coords={"y": np.arange(height), "x": np.arange(width)},
                name="Latitude",
            )
            lon_da = xr.DataArray(
                lons,
                dims=["y", "x"],
                coords={"y": np.arange(height), "x": np.arange(width)},
                name="Longitude",
            )

            ds = None  # Close dataset
            return xr.Dataset({"Latitude": lat_da, "Longitude": lon_da})

        except Exception as e:
            logger.error(f"Failed to create HDF geometry: {e}")
            raise ValueError(f"Cannot create coordinate grids from HDF: {e}")

    def _find_gmp_file(self) -> Optional[Path]:
        """Find corresponding GMP file for this HDF file."""
        # Extract base pattern from filename
        # Example: 16_08_2022_Saska_MISR_AM1_GRP_TERRAIN_GM_P043_O120540_AN_F03_0024.hdf
        # Should find: 16_08_2022_Saska_MISR_AM1_GP_GMP_P043_O120540_F03_0013.hdf

        filename = self.filepath.name

        # Replace GRP_TERRAIN_GM with GP_GMP
        if "GRP_TERRAIN_GM" in filename:
            gmp_filename = filename.replace("GRP_TERRAIN_GM", "GP_GMP")
            # Also replace the camera designation (AN->empty) and block number
            # This is a simplified pattern - may need refinement
            gmp_filename = gmp_filename.replace("_AN_F", "_F")
            gmp_path = self.filepath.parent / gmp_filename

            if gmp_path.exists():
                logger.info(f"Found GMP file: {gmp_path}")
                return gmp_path

        # Alternative: search for GMP files in the same directory
        gmp_pattern = filename.split("_MISR_")[0] + "_MISR_*GP_GMP*.hdf"
        data_dir = self.filepath.parent
        gmp_files = list(data_dir.glob("*GP_GMP*.hdf"))

        if gmp_files:
            # Use the first GMP file found (assuming they correspond)
            logger.info(f"Found GMP file by pattern: {gmp_files[0]}")
            return gmp_files[0]

        logger.warning("No corresponding GMP file found")
        return None

    def load_geometry(self) -> xr.Dataset:
        """Load geometric parameters (lat/lon grids)."""
        if self._geom_ds is None:
            try:
                if self.is_hdf:
                    # For HDF files, generate lat/lon grids from geotransform
                    self._geom_ds = self._create_hdf_geometry()
                else:
                    # Load from NetCDF
                    self._geom_ds = xr.open_dataset(
                        self.filepath, group="GeometricParameters"
                    )
                logger.info(f"Loaded geometry from {self.filepath}")
            except Exception as e:
                logger.error(f"Failed to load geometry: {e}")
                raise ValueError(f"Cannot load geometric parameters: {e}")
        return self._geom_ds

    def load_red_band(self) -> xr.Dataset:
        """Load red band radiance data."""
        if self._red_ds is None:
            try:
                if self.is_hdf:
                    # Load red band from HDF
                    red_da = self._load_hdf_field("Radiance_275_m/Red_Band")

                    # For HDF, the data may have multiple bands
                    # Need to select appropriate band with actual radiance data
                    if len(red_da.shape) == 3:
                        # Multiple bands - need to find the best one with valid data
                        best_band_idx = self._find_best_radiance_band(red_da)
                        if best_band_idx is not None:
                            radiance_da = red_da[best_band_idx].rename("Radiance")
                            logger.info(
                                f"Selected band {best_band_idx} for radiance data"
                            )
                        else:
                            # Fall back to first band if no clear best choice
                            radiance_da = red_da[0].rename("Radiance")
                            logger.warning("No clear best band found, using first band")

                        self._red_ds = xr.Dataset({"Radiance": radiance_da})
                    else:
                        # Single band data
                        red_da = red_da.rename("Radiance")
                        self._red_ds = xr.Dataset({"Radiance": red_da})
                else:
                    # Load from NetCDF
                    self._red_ds = xr.open_dataset(
                        self.filepath, group="Radiance_275_m/Red_Band"
                    )
                logger.info(f"Loaded red band from {self.filepath}")
            except Exception as e:
                logger.error(f"Failed to load red band: {e}")
                raise ValueError(f"Cannot load red band data: {e}")
        return self._red_ds

    def load_qa_data(self) -> Optional[xr.Dataset]:
        """Load QA data if available."""
        if self._qa_ds is None:
            try:
                if self.is_hdf:
                    # Try to load QA data from HDF
                    try:
                        qa_da = self._load_hdf_field("QA")
                        self._qa_ds = xr.Dataset({"QA": qa_da})
                        logger.info("Loaded QA data from HDF")
                    except (ValueError, KeyError):
                        logger.info("No QA data found in HDF file")
                        return None
                else:
                    # Try common QA group names for NetCDF
                    qa_groups = ["QA", "Quality", "QualityAssurance"]
                    for group in qa_groups:
                        try:
                            self._qa_ds = xr.open_dataset(self.filepath, group=group)
                            logger.info(f"Loaded QA data from group '{group}'")
                            break
                        except (KeyError, OSError):
                            continue
                    else:
                        logger.warning("No QA data found in file")
                        return None
            except Exception as e:
                logger.warning(f"Could not load QA data: {e}")
                return None
        return self._qa_ds

    def get_lat_lon_grids(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get latitude and longitude grids."""
        geom_ds = self.load_geometry()
        return geom_ds["Latitude"].values, geom_ds["Longitude"].values

    def get_red_radiance(self, row_slice: slice, col_slice: slice) -> np.ndarray:
        """Get red band radiance data for specified region."""
        red_ds = self.load_red_band()
        return red_ds["Radiance"][row_slice, col_slice].values

    def validate_file(self) -> Dict[str, Any]:
        """Validate MISR file structure and return metadata."""
        try:
            # Check file exists and is readable
            if not self.filepath.exists():
                raise FileNotFoundError(f"File not found: {self.filepath}")

            # Check HDF support if needed
            if self.is_hdf and not HDF_SUPPORT:
                raise RuntimeError(
                    "HDF files require GDAL/rioxarray - please install: pip install rioxarray"
                )

            # Try to load essential datasets
            geom_ds = self.load_geometry()
            red_ds = self.load_red_band()

            # Extract metadata
            metadata = {
                "filepath": str(self.filepath),
                "file_format": "HDF4" if self.is_hdf else "NetCDF",
                "file_size_mb": self.filepath.stat().st_size / (1024 * 1024),
                "geometry_shape": geom_ds["Latitude"].shape,
                "red_band_shape": red_ds["Radiance"].shape,
                "has_qa_data": self.load_qa_data() is not None,
            }

            # Add HDF subdataset info if HDF file
            if self.is_hdf:
                subdatasets = self._get_hdf_subdatasets()
                metadata["hdf_subdatasets"] = list(subdatasets.keys())

            # Add dataset attributes if available
            if hasattr(geom_ds, "attrs"):
                metadata["geometry_attrs"] = dict(geom_ds.attrs)
            if hasattr(red_ds, "attrs"):
                metadata["red_band_attrs"] = dict(red_ds.attrs)

            self._metadata = metadata
            logger.info(f"Validated MISR file: {metadata}")
            return metadata

        except Exception as e:
            logger.error(f"File validation failed: {e}")
            raise ValueError(f"Invalid MISR file: {e}")

    def get_file_info(self) -> Dict[str, Any]:
        """Get cached file metadata."""
        if not self._metadata:
            return self.validate_file()
        return self._metadata

    def close(self):
        """Close all open datasets."""
        for ds in [self._geom_ds, self._red_ds, self._qa_ds]:
            if ds is not None:
                try:
                    ds.close()
                except:
                    pass
        self._geom_ds = None
        self._red_ds = None
        self._qa_ds = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
