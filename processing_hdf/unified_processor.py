"""
Unified MISR Processor
Direct integration of MISR Toolkit processing with BatchProcessor interface.
Eliminates subprocess calls for simplified architecture.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

# Import with proper path handling
import sys
from pathlib import Path

base_path = Path(__file__).parent.parent
sys.path.insert(0, str(base_path))

from processing_core import ProcessingResult
from processing_hdf.misr_processor import MISRProcessor

logger = logging.getLogger(__name__)


class UnifiedMISRProcessor:
    """Unified MISR processor that works directly with MISR Toolkit in same environment"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize unified processor with configuration"""
        self.config = config

        # Initialize MISR processor directly
        try:
            self.misr_processor = MISRProcessor()
        except ImportError as e:
            raise ImportError(
                f"MISR Toolkit is not available in current environment: {e}\n\n"
                f"Please ensure you're running in the misr-toolkit environment:\n"
                f"conda activate misr-toolkit-py36"
            )

    def process_single_file(
        self, filepath: str, progress_callback: Optional[Callable] = None
    ) -> ProcessingResult:
        """Process a single MISR HDF file directly

        Args:
            filepath: Path to MISR HDF file
            progress_callback: Progress callback function

        Returns:
            ProcessingResult object
        """
        # Use batch processing for single files
        results = self.process_batch([filepath], progress_callback)
        return (
            results[0]
            if results
            else ProcessingResult(input_file=filepath, success=False)
        )

    def validate_inputs(self, files: List[str]) -> Dict[str, Any]:
        """Validate input files for MISR processing

        Args:
            files: List of file paths

        Returns:
            Validation result dictionary
        """
        valid_files = []
        invalid_files = []
        warnings = []

        for filepath in files:
            path = Path(filepath)

            # Check if file exists
            if not path.exists():
                invalid_files.append(f"{filepath}: File does not exist")
                continue

            # Check file extension
            if not path.suffix.lower() in [".hdf", ".he5"]:
                invalid_files.append(f"{filepath}: Not a valid HDF file")
                continue

            # Check if it looks like a MISR file (basic check)
            if "MISR" not in path.name.upper():
                warnings.append(f"{filepath}: File name doesn't contain 'MISR'")

            valid_files.append(filepath)

        return {
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "warnings": warnings,
        }

    def process_batch(
        self, files: List[str], progress_callback: Optional[Callable] = None
    ) -> List[ProcessingResult]:
        """Process multiple MISR HDF files directly

        Args:
            files: List of file paths to process
            progress_callback: Progress callback function

        Returns:
            List of ProcessingResult objects
        """
        results = []
        total_files = len(files)

        if progress_callback:
            progress_callback("Initializing HDF processing...", 0.0, 0, total_files)

        for i, filepath in enumerate(files):
            start_time = time.time()

            if progress_callback:
                progress_callback(
                    f"Processing {Path(filepath).name}...",
                    i / total_files,
                    i,
                    total_files,
                )

            try:
                # Generate output filename
                output_file = self._generate_output_filename(filepath)

                # Configure processor callbacks
                def file_progress_callback(message: str, progress: float):
                    if progress_callback:
                        # Scale progress within current file's portion
                        file_progress = (i + progress) / total_files
                        progress_callback(
                            f"File {i+1}/{total_files}: {message}",
                            file_progress,
                            i,
                            total_files,
                        )

                def log_callback(message: str):
                    logger.info(f"[{Path(filepath).name}] {message}")

                # Set up processor with callbacks
                processor = MISRProcessor(
                    progress_callback=file_progress_callback, log_callback=log_callback
                )

                # Process file directly
                result_data = processor.process_file(filepath, output_file, self.config)

                # Create ProcessingResult object
                proc_result = ProcessingResult(
                    input_file=filepath,
                    success=result_data["success"],
                )
                proc_result.processing_time = time.time() - start_time

                if result_data["success"]:
                    proc_result.output_files = {"geotiff": result_data["output_file"]}
                    proc_result.metadata = {
                        "statistics": result_data.get("statistics", {}),
                        "bounds": result_data.get("bounds", {}),
                        "processor": "MISR_Toolkit_Direct",
                    }
                else:
                    proc_result.error_message = result_data.get(
                        "error", "Unknown error"
                    )

                results.append(proc_result)

                logger.info(
                    f"Processed {filepath} in {proc_result.processing_time:.2f}s "
                    f"({'SUCCESS' if proc_result.success else 'FAILED'})"
                )

            except Exception as e:
                # Handle processing errors
                proc_result = ProcessingResult(
                    input_file=filepath,
                    success=False,
                )
                proc_result.processing_time = time.time() - start_time
                proc_result.error_message = str(e)
                results.append(proc_result)

                logger.error(f"Failed to process {filepath}: {e}")

        # Final progress update
        if progress_callback:
            successful = sum(1 for r in results if r.success)
            progress_callback(
                f"Completed: {successful}/{total_files} files processed successfully",
                1.0,
                total_files,
                total_files,
            )

        logger.info(
            f"Batch processing complete: {sum(1 for r in results if r.success)}/{total_files} files successful"
        )

        return results

    def _generate_output_filename(self, filepath: str) -> str:
        """Generate output filename for processed file"""
        input_path = Path(filepath)
        output_dir = Path(self.config.get("output_directory", "."))

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename
        output_filename = f"{input_path.stem}_reprojected.tif"
        return str(output_dir / output_filename)

    def get_processing_summary(self, results: List[ProcessingResult]) -> Dict[str, Any]:
        """Generate processing summary from results

        Args:
            results: List of ProcessingResult objects

        Returns:
            Summary dictionary
        """
        total_files = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total_files - successful

        total_time = sum(r.processing_time for r in results)
        avg_time = total_time / total_files if total_files > 0 else 0

        return {
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_files * 100) if total_files > 0 else 0,
            "total_processing_time": total_time,
            "average_processing_time": avg_time,
            "processor_type": "MISR_Toolkit_Direct",
        }
