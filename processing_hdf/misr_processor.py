"""
MISR Processor Module
Core reprojection logic adapted from MISR Toolkit GUI.
"""

import os
import numpy as np
from typing import Optional, Callable, Dict, Any
from pathlib import Path

try:
    import MisrToolkit as Mtk
    from osgeo import gdal, osr

    MISR_TOOLKIT_AVAILABLE = True
except ImportError:
    MISR_TOOLKIT_AVAILABLE = False

# Import with proper path handling
import sys
from pathlib import Path

processing_hdf_path = Path(__file__).parent
sys.path.insert(0, str(processing_hdf_path))

from constants import WGS84_EPSG, GEOTIFF_NODATA
from data_processing import DataProcessor
from coordinate_utils import CoordinateUtils


class MISRProcessor:
    """Main class for MISR reprojection operations using MISR Toolkit"""

    def __init__(
        self,
        progress_callback: Optional[Callable] = None,
        log_callback: Optional[Callable] = None,
    ):
        """Initialize processor with callbacks"""
        if not MISR_TOOLKIT_AVAILABLE:
            raise ImportError(
                "MISR Toolkit is not available. Please install MisrToolkit."
            )

        self.progress_callback = progress_callback
        self.log_callback = log_callback

    def log_message(self, message: str):
        """Log a message"""
        if self.log_callback:
            self.log_callback(message)

    def update_progress(self, message: str, progress: float = 0.0):
        """Update progress"""
        if self.progress_callback:
            self.progress_callback(message, progress)

    def process_file(
        self, input_file: str, output_file: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a single MISR HDF file

        Args:
            input_file: Path to input MISR HDF file
            output_file: Path to output GeoTIFF file
            config: Processing configuration dictionary

        Returns:
            Processing result dictionary
        """
        try:
            # Extract configuration
            ulc_lat = config.get("ulc_lat", 0.0)
            ulc_lon = config.get("ulc_lon", 0.0)
            lrc_lat = config.get("lrc_lat", 0.0)
            lrc_lon = config.get("lrc_lon", 0.0)
            field_name = config.get("field_name", "Red Radiance/RDQI")
            apply_quality_filter = config.get("apply_quality_filter", True)

            # Log the coordinates received from config
            self.log_message(f"Received coordinates from config:")
            self.log_message(f"  Upper Left: {ulc_lat:.4f}°N, {ulc_lon:.4f}°W")
            self.log_message(f"  Lower Right: {lrc_lat:.4f}°N, {lrc_lon:.4f}°W")

            self.update_progress("Starting MISR reprojection...", 0.1)
            self.log_message("MISR Toolkit Reprojection to WGS84")
            self.log_message("=" * 50)
            self.log_message(f"Input: {os.path.basename(input_file)}")
            self.log_message(f"Output: {output_file}")

            # Load MISR file
            self.update_progress("Loading MISR file...", 0.2)
            self.log_message("\nLoading MISR file...")
            file_obj = Mtk.MtkFile(input_file)

            self.log_message(f"   File Type: {file_obj.file_type}")
            self.log_message(f"   Path: {file_obj.path}")
            self.log_message(f"   Orbit: {file_obj.orbit}")

            # Get grid and field
            grid_name = DataProcessor.get_grid_name(field_name)
            self.log_message(f"\nUsing grid: {grid_name}")
            grid_obj = file_obj.grid(grid_name)
            field_obj = grid_obj.field(field_name)

            # Define region
            self.update_progress("Defining region...", 0.3)
            self.log_message(f"\nDefining region:")
            self.log_message(f"   Upper Left: {ulc_lat}°N, {ulc_lon}°W")
            self.log_message(f"   Lower Right: {lrc_lat}°N, {lrc_lon}°W")

            region = Mtk.MtkRegion(ulc_lat, ulc_lon, lrc_lat, lrc_lon)

            # Read data
            self.update_progress("Reading MISR data...", 0.4)
            self.log_message("\nReading data...")
            data_obj = field_obj.read(region)
            data_array = data_obj.data()
            mapinfo = data_obj.mapinfo()

            self.log_message(f"   Data shape: {data_array.shape}")
            self.log_message(f"   Data type: {data_array.dtype}")
            self.log_message(f"   Resolution: {mapinfo.resolution}m")

            # Convert coordinates
            self.update_progress("Converting coordinates...", 0.5)
            self.log_message("\nCreating coordinate arrays...")

            lat_array, lon_array = CoordinateUtils.convert_pixel_coordinates(
                mapinfo, data_array.shape, self.update_progress
            )

            bounds = CoordinateUtils.get_coordinate_bounds(lat_array, lon_array)
            self.log_message(
                f"   Lat range: {bounds['min_lat']:.4f}° to {bounds['max_lat']:.4f}°"
            )
            self.log_message(
                f"   Lon range: {bounds['min_lon']:.4f}° to {bounds['max_lon']:.4f}°"
            )

            # Process data
            self.update_progress("Processing data...", 0.7)
            self.log_message("\nProcessing data...")

            if apply_quality_filter:
                self.log_message("   Applying quality filtering...")

            processed_data = DataProcessor.apply_quality_filtering(
                data_array, field_name, grid_obj, region, apply_quality_filter
            )

            # Calculate statistics
            stats = DataProcessor.calculate_statistics(processed_data)
            self.log_message(
                f"   Valid pixels: {stats['valid_pixels']:,} / {stats['total_pixels']:,} "
                f"({stats['valid_percentage']:.1f}%)"
            )

            # Create GeoTIFF
            self.update_progress("Creating GeoTIFF...", 0.9)
            self.log_message(f"\nCreating GeoTIFF: {output_file}")

            self._create_geotiff(
                processed_data,
                lat_array,
                lon_array,
                output_file,
                field_name,
                file_obj,
                input_file,
            )

            # Success!
            self.update_progress("Reprojection completed successfully!", 1.0)
            self.log_message("\nReprojection completed successfully!")
            self._log_summary(output_file, file_obj, field_name, stats, bounds)

            return {
                "success": True,
                "output_file": output_file,
                "statistics": stats,
                "bounds": bounds,
                "processing_time": 0.0,  # TODO: Add timing
            }

        except Exception as e:
            self.log_message(f"\nError: {str(e)}")
            return {"success": False, "error": str(e), "output_file": None}

    def _create_geotiff(
        self,
        data_array,
        lat_array,
        lon_array,
        output_file,
        field_name,
        file_obj,
        input_file,
    ):
        """Create GeoTIFF file"""
        rows, cols = data_array.shape

        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(output_file, cols, rows, 1, gdal.GDT_Float32)

        # Set geotransform
        geotransform = CoordinateUtils.calculate_geotransform(
            lat_array, lon_array, data_array.shape
        )
        out_ds.SetGeoTransform(geotransform)

        # Set WGS84 projection
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(WGS84_EPSG)
        out_ds.SetProjection(srs.ExportToWkt())

        # Write data
        band = out_ds.GetRasterBand(1)
        band.WriteArray(data_array)
        band.SetNoDataValue(GEOTIFF_NODATA)
        band.SetDescription(f"MISR {field_name}")

        # Set metadata
        out_ds.SetMetadata(
            {
                "DESCRIPTION": f"MISR {field_name} reprojected to WGS84",
                "SOURCE_FILE": os.path.basename(input_file),
                "FIELD": field_name,
                "PATH": str(file_obj.path),
                "ORBIT": str(file_obj.orbit),
                "COORDINATE_SYSTEM": "WGS84 (EPSG:4326)",
            }
        )

        out_ds = None

    def _log_summary(self, output_file, file_obj, field_name, stats, bounds):
        """Log summary information"""
        self.log_message(f"\nSUMMARY:")
        self.log_message(f"   Output: {output_file}")
        self.log_message(
            f"   Source: MISR Path {file_obj.path}, Orbit {file_obj.orbit}"
        )
        self.log_message(f"   Field: {field_name}")
        self.log_message(f"   Coordinate system: WGS84 (EPSG:4326)")
        self.log_message(f"   Valid data: {stats['valid_percentage']:.1f}%")
        self.log_message(
            f"   Geographic bounds: {bounds['min_lat']:.4f}° to {bounds['max_lat']:.4f}°N, "
            f"{bounds['min_lon']:.4f}° to {bounds['max_lon']:.4f}°W"
        )
