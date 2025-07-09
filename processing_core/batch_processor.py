"""
Batch Processor Module
Orchestrates MISR data processing workflow for multiple files.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import traceback

from .data_loader import DataLoader
from .reprojector import Reprojector
from .qa_filter import QAFilter
from .clipper import Clipper
from .exporter import Exporter

logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """Configuration for batch processing."""

    # Reprojection settings
    target_lat: float = -13.8
    target_lon: float = -70.8
    region_margin: float = 2.0
    target_resolution: float = 0.0025

    # QA filtering
    enable_qa_filtering: bool = False
    qa_filters: List[str] = field(default_factory=lambda: [])

    # Clipping
    enable_clipping: bool = False
    shapefile_path: Optional[str] = None

    # Export settings
    output_directory: str = "."
    export_netcdf: bool = False
    export_geotiff: bool = True
    add_timestamp: bool = True

    # Processing options
    overwrite_existing: bool = False
    validate_inputs: bool = True


@dataclass
class ProcessingResult:
    """Result of processing a single file."""

    input_file: str
    success: bool
    output_files: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BatchProcessor:
    """Orchestrates batch processing of MISR files."""

    def __init__(self, config: ProcessingConfig):
        """Initialize with processing configuration."""
        self.config = config
        self.reprojector = Reprojector(
            target_lat=config.target_lat,
            target_lon=config.target_lon,
            region_margin=config.region_margin,
            target_resolution=config.target_resolution,
        )
        self.qa_filter = QAFilter()
        self.clipper = Clipper()
        self.exporter = Exporter(config.output_directory)

        # Setup QA filters
        if config.enable_qa_filtering:
            for filter_name in config.qa_filters:
                self.qa_filter.add_filter(filter_name)

        # Load shapefile if clipping enabled
        if config.enable_clipping and config.shapefile_path:
            self.clipper.load_shapefile(config.shapefile_path)

    def process_single_file(
        self,
        filepath: str,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> ProcessingResult:
        """Process a single MISR file."""
        import time

        start_time = time.time()
        result = ProcessingResult(input_file=filepath, success=False)

        try:
            if progress_callback:
                progress_callback(f"Loading {Path(filepath).name}", 0.0)

            # Load and validate file
            with DataLoader(filepath) as loader:
                if self.config.validate_inputs:
                    metadata = loader.validate_file()
                    result.metadata.update(metadata)

                if progress_callback:
                    progress_callback("Loading geometry and red band data", 0.1)

                # Get geographic grids
                lat_grid, lon_grid = loader.get_lat_lon_grids()

                # Find region bounds
                bounds = self.reprojector.find_region_bounds(lat_grid, lon_grid)
                if bounds is None:
                    raise ValueError("No data found in target region")

                if progress_callback:
                    progress_callback("Extracting regional subset", 0.2)

                # Get red band data for the region
                red_data = loader.get_red_radiance(slice(None), slice(None))

                # Extract subset
                lat_subset, lon_subset, red_subset = self.reprojector.extract_subset(
                    lat_grid, lon_grid, red_data, bounds
                )

                if progress_callback:
                    progress_callback("Creating fine resolution grid", 0.3)

                # Create fine grid
                lat_fine_grid, lon_fine_grid = self.reprojector.create_fine_grid(
                    lat_subset, lon_subset, red_subset
                )

                # Apply QA filtering if enabled
                if self.config.enable_qa_filtering:
                    if progress_callback:
                        progress_callback("Applying QA filtering", 0.4)

                    qa_dataset = loader.load_qa_data()
                    if qa_dataset is not None:
                        self.qa_filter.set_qa_dataset(qa_dataset)
                        # Get QA data subset (this would need proper implementation)
                        # For now, skip QA filtering if we can't align the data
                        logger.warning(
                            "QA filtering implementation needs refinement for alignment"
                        )

                if progress_callback:
                    progress_callback("Reprojecting to WGS84", 0.5)

                # Reproject to WGS84
                reprojected_ds = self.reprojector.reproject_to_wgs84(
                    lat_fine_grid, lon_fine_grid, red_subset
                )

                if reprojected_ds is None:
                    raise ValueError("Reprojection failed - no valid data")

                # Apply clipping if enabled
                if self.config.enable_clipping and self.clipper.geometries:
                    if progress_callback:
                        progress_callback("Clipping to shapefile", 0.7)

                    if self.clipper.check_overlap(reprojected_ds):
                        reprojected_ds = self.clipper.clip_xarray_dataset(
                            reprojected_ds
                        )
                        result.metadata["clipped"] = True
                    else:
                        logger.warning("No overlap with shapefile - skipping clipping")
                        result.metadata["clipped"] = False

                if progress_callback:
                    progress_callback("Exporting results", 0.8)

                # Generate output filename
                base_name = Path(filepath).stem
                processing_info = {
                    "red_band": True,
                    "resolution": 275,
                    "clipped": self.config.enable_clipping
                    and result.metadata.get("clipped", False),
                    "qa_filtered": self.config.enable_qa_filtering,
                }

                filename = self.exporter.create_filename(
                    base_name, processing_info, self.config.add_timestamp
                )

                # Export data
                export_results = {}
                if self.config.export_netcdf:
                    nc_path = self.exporter.export_netcdf(
                        reprojected_ds, f"{filename}.nc"
                    )
                    export_results["netcdf"] = nc_path

                if self.config.export_geotiff:
                    tiff_path = self.exporter.export_geotiff(
                        reprojected_ds, f"{filename}.tif"
                    )
                    export_results["geotiff"] = tiff_path

                result.output_files = export_results
                result.success = True

                if progress_callback:
                    progress_callback("Processing complete", 1.0)

        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            logger.error(f"Error processing {filepath}: {error_msg}")
            logger.debug(traceback.format_exc())
            result.error_message = error_msg

            if progress_callback:
                progress_callback(f"Error: {str(e)}", 1.0)

        result.processing_time = time.time() - start_time
        return result

    def process_batch(
        self,
        filepaths: List[str],
        progress_callback: Optional[Callable[[str, float, int, int], None]] = None,
    ) -> List[ProcessingResult]:
        """Process multiple MISR files."""
        results = []
        total_files = len(filepaths)

        logger.info(f"Starting batch processing of {total_files} files")

        for i, filepath in enumerate(filepaths):
            logger.info(f"Processing file {i+1}/{total_files}: {Path(filepath).name}")

            def file_progress(message: str, progress: float):
                if progress_callback:
                    overall_progress = (i + progress) / total_files
                    progress_callback(message, overall_progress, i + 1, total_files)

            result = self.process_single_file(filepath, file_progress)
            results.append(result)

            # Log result
            if result.success:
                logger.info(
                    f"Successfully processed {Path(filepath).name} in {result.processing_time:.1f}s"
                )
            else:
                logger.error(
                    f"Failed to process {Path(filepath).name}: {result.error_message}"
                )

        # Generate summary
        successful = sum(1 for r in results if r.success)
        failed = total_files - successful
        total_time = sum(r.processing_time for r in results)

        logger.info(
            f"Batch processing complete: {successful} successful, {failed} failed, total time: {total_time:.1f}s"
        )

        return results

    def update_config(self, new_config: ProcessingConfig):
        """Update processing configuration."""
        self.config = new_config

        # Update reprojector
        self.reprojector.update_target_region(
            new_config.target_lat, new_config.target_lon, new_config.region_margin
        )

        # Update QA filter
        self.qa_filter.clear_filters()
        if new_config.enable_qa_filtering:
            for filter_name in new_config.qa_filters:
                self.qa_filter.add_filter(filter_name)

        # Update clipper
        if new_config.enable_clipping and new_config.shapefile_path:
            self.clipper.load_shapefile(new_config.shapefile_path)

        # Update exporter
        self.exporter.set_output_directory(new_config.output_directory)

        logger.info("Updated processing configuration")

    def validate_inputs(self, filepaths: List[str]) -> Dict[str, List[str]]:
        """Validate input files and configuration."""
        validation_results = {
            "valid_files": [],
            "invalid_files": [],
            "warnings": [],
        }

        # Check files
        for filepath in filepaths:
            try:
                with DataLoader(filepath) as loader:
                    loader.validate_file()
                validation_results["valid_files"].append(filepath)
            except Exception as e:
                validation_results["invalid_files"].append(f"{filepath}: {str(e)}")

        # Check output directory
        if not self.exporter.validate_output_directory():
            validation_results["warnings"].append("Output directory is not writable")

        # Check shapefile if clipping enabled
        if self.config.enable_clipping:
            if not self.config.shapefile_path:
                validation_results["warnings"].append(
                    "Clipping enabled but no shapefile specified"
                )
            elif not self.clipper.validate_shapefile(self.config.shapefile_path):
                validation_results["warnings"].append(
                    f"Invalid shapefile: {self.config.shapefile_path}"
                )

        return validation_results

    def get_processing_summary(self, results: List[ProcessingResult]) -> Dict[str, Any]:
        """Generate summary statistics for processing results."""
        total_files = len(results)
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        summary = {
            "total_files": total_files,
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": (
                len(successful) / total_files * 100 if total_files > 0 else 0
            ),
            "total_processing_time": sum(r.processing_time for r in results),
            "average_processing_time": (
                sum(r.processing_time for r in results) / total_files
                if total_files > 0
                else 0
            ),
        }

        if successful:
            # Export summary
            all_output_files = []
            for result in successful:
                all_output_files.extend(result.output_files.values())

            export_summary = self.exporter.get_export_summary(
                {f"file_{i}": path for i, path in enumerate(all_output_files)}
            )
            summary["export_summary"] = export_summary

        if failed:
            summary["error_summary"] = {
                error.error_message: sum(
                    1 for r in failed if r.error_message == error.error_message
                )
                for error in failed
            }

        return summary
