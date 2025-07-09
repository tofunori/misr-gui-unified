"""
Exporter Module
Handles export of processed data to NetCDF and GeoTIFF formats.
"""

import numpy as np
import xarray as xr
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Exporter:
    """Exports processed MISR data to various formats."""

    def __init__(self, output_dir: str = "."):
        """Initialize exporter with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_netcdf(
        self,
        dataset: xr.Dataset,
        filename: str,
        compression: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Export dataset to NetCDF format."""
        try:
            output_path = self.output_dir / filename
            if not output_path.suffix:
                output_path = output_path.with_suffix(".nc")

            # Add additional metadata if provided
            if metadata:
                dataset.attrs.update(metadata)

            # Set encoding for compression with proper fill value handling
            encoding = {}
            if compression:
                for var in dataset.data_vars:
                    # Get the data variable
                    data_var = dataset[var]

                    # Determine appropriate fill value based on data type
                    if np.issubdtype(data_var.dtype, np.integer):
                        fill_value = -9999
                    elif np.issubdtype(data_var.dtype, np.floating):
                        fill_value = -9999.0
                    else:
                        fill_value = -9999.0  # Default for other types

                    encoding[var] = {
                        "zlib": True,
                        "complevel": 6,
                        "shuffle": True,
                        "_FillValue": fill_value,
                    }

            # Process dataset to handle NaN values before export
            dataset_processed = self._process_dataset_for_netcdf(dataset)

            # Export to NetCDF
            dataset_processed.to_netcdf(
                output_path, encoding=encoding if compression else None
            )

            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Exported NetCDF: {output_path} ({file_size:.1f} MB)")

            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export NetCDF: {e}")
            raise ValueError(f"Cannot export NetCDF: {e}")

    def export_geotiff(
        self,
        dataset: xr.Dataset,
        filename: str,
        data_var: str = "red_radiance",
        nodata_value: float = -9999.0,
        compress: str = "lzw",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Export dataset to GeoTIFF format."""
        try:
            output_path = self.output_dir / filename
            if not output_path.suffix:
                output_path = output_path.with_suffix(".tif")

            # Get data and coordinates
            data = dataset[data_var].values
            lats = dataset.lat.values
            lons = dataset.lon.values

            # Handle NaN values
            data_filled = np.where(np.isnan(data), nodata_value, data)

            # Create transform
            transform = from_bounds(
                west=lons.min(),
                south=lats.min(),
                east=lons.max(),
                north=lats.max(),
                width=data.shape[1],
                height=data.shape[0],
            )

            # Determine CRS
            if "crs" in dataset.data_vars:
                crs_wkt = dataset.crs.attrs.get("crs_wkt")
                if crs_wkt:
                    crs = CRS.from_wkt(crs_wkt)
                else:
                    crs = CRS.from_epsg(4326)
            else:
                crs = CRS.from_epsg(4326)

            # Prepare metadata tags
            tags = {
                "title": dataset.attrs.get("title", "MISR Processed Data"),
                "description": dataset.attrs.get("description", "Processed MISR data"),
            }

            if data_var in dataset and hasattr(dataset[data_var], "attrs"):
                var_attrs = dataset[data_var].attrs
                tags.update(
                    {
                        "units": var_attrs.get("units", ""),
                        "long_name": var_attrs.get("long_name", ""),
                    }
                )

            if metadata:
                tags.update(metadata)

            # Write GeoTIFF
            with rasterio.open(
                output_path,
                "w",
                driver="GTiff",
                height=data.shape[0],
                width=data.shape[1],
                count=1,
                dtype=data.dtype,
                crs=crs,
                transform=transform,
                nodata=nodata_value,
                compress=compress,
            ) as dst:
                dst.write(data_filled, 1)

                # Set band description
                band_description = dataset[data_var].attrs.get(
                    "long_name", f"{data_var} data"
                )
                dst.set_band_description(1, band_description)

                # Update tags
                dst.update_tags(**tags)

            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Exported GeoTIFF: {output_path} ({file_size:.1f} MB)")

            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export GeoTIFF: {e}")
            raise ValueError(f"Cannot export GeoTIFF: {e}")

    def export_both_formats(
        self,
        dataset: xr.Dataset,
        base_filename: str,
        data_var: str = "red_radiance",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Export dataset to both NetCDF and GeoTIFF formats."""
        base_path = Path(base_filename).stem

        results = {}

        # Export NetCDF
        try:
            nc_path = self.export_netcdf(dataset, f"{base_path}.nc", metadata=metadata)
            results["netcdf"] = nc_path
        except Exception as e:
            logger.error(f"NetCDF export failed: {e}")
            results["netcdf_error"] = str(e)

        # Export GeoTIFF
        try:
            tiff_path = self.export_geotiff(
                dataset, f"{base_path}.tif", data_var=data_var, metadata=metadata
            )
            results["geotiff"] = tiff_path
        except Exception as e:
            logger.error(f"GeoTIFF export failed: {e}")
            results["geotiff_error"] = str(e)

        return results

    def create_filename(
        self,
        base_name: str,
        processing_info: Optional[Dict[str, Any]] = None,
        timestamp: bool = True,
    ) -> str:
        """Create standardized filename for output."""
        from datetime import datetime

        # Start with base name
        parts = [base_name]

        # Add processing information
        if processing_info:
            if "red_band" in processing_info:
                parts.append("red")
            if "resolution" in processing_info:
                res = processing_info["resolution"]
                parts.append(f"{res}m" if isinstance(res, (int, float)) else str(res))
            if "clipped" in processing_info and processing_info["clipped"]:
                parts.append("clipped")
            if "qa_filtered" in processing_info and processing_info["qa_filtered"]:
                parts.append("qa")

        # Add timestamp if requested
        if timestamp:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            parts.append(timestamp_str)

        return "_".join(parts)

    def _process_dataset_for_netcdf(self, dataset: xr.Dataset) -> xr.Dataset:
        """Process dataset to handle NaN values for NetCDF export."""
        # Create a copy to avoid modifying the original
        dataset_copy = dataset.copy(deep=True)

        for var_name in dataset_copy.data_vars:
            data_var = dataset_copy[var_name]

            # Remove any existing _FillValue from attrs to avoid conflicts
            if "_FillValue" in data_var.attrs:
                del dataset_copy[var_name].attrs["_FillValue"]

            # Handle NaN values based on data type
            if np.issubdtype(data_var.dtype, np.floating):
                # For floating point, replace NaN with -9999.0
                dataset_copy[var_name] = data_var.where(~np.isnan(data_var), -9999.0)
            elif np.issubdtype(data_var.dtype, np.integer):
                # For integers, ensure no NaN values exist (shouldn't happen, but safety check)
                if np.any(np.isnan(data_var.values)):
                    logger.warning(
                        f"Found NaN in integer variable {var_name}, converting to -9999"
                    )
                    dataset_copy[var_name] = data_var.where(~np.isnan(data_var), -9999)

            # Only set missing_value in attrs (not _FillValue, as that's handled in encoding)
            dataset_copy[var_name].attrs["missing_value"] = (
                -9999.0 if np.issubdtype(data_var.dtype, np.floating) else -9999
            )

        return dataset_copy

    def get_export_summary(self, filepaths: Dict[str, str]) -> Dict[str, Any]:
        """Get summary of exported files."""
        summary = {"files": {}, "total_size_mb": 0}

        for format_name, filepath in filepaths.items():
            if filepath and Path(filepath).exists():
                file_path = Path(filepath)
                size_mb = file_path.stat().st_size / (1024 * 1024)
                summary["files"][format_name] = {
                    "path": str(file_path),
                    "size_mb": round(size_mb, 2),
                    "exists": True,
                }
                summary["total_size_mb"] += size_mb
            else:
                summary["files"][format_name] = {
                    "path": filepath,
                    "size_mb": 0,
                    "exists": False,
                }

        summary["total_size_mb"] = round(summary["total_size_mb"], 2)
        return summary

    def set_output_directory(self, output_dir: str):
        """Change output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Set output directory to: {self.output_dir}")

    def validate_output_directory(self) -> bool:
        """Check if output directory is writable."""
        try:
            test_file = self.output_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Output directory not writable: {e}")
            return False
