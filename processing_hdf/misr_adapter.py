"""
MISR Processing Adapter
Adapts MISR Toolkit processing to work with the existing BatchProcessor interface.
Uses subprocess to execute HDF processing in the misr-toolkit-py36 environment.
"""

import time
import json
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

# Import with proper path handling
import sys
from pathlib import Path

base_path = Path(__file__).parent.parent
sys.path.insert(0, str(base_path))

from processing_core import ProcessingResult

logger = logging.getLogger(__name__)


class MISRProcessingAdapter:
    """Adapter to make MISR processing compatible with BatchProcessor interface"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize adapter with configuration"""
        self.config = config
        self.conda_env = "misr-toolkit-py36"
        self.worker_script = Path(__file__).parent / "misr_hdf_worker.py"

        # Check if environment is available
        if not self._check_environment():
            raise RuntimeError(
                f"MISR Toolkit environment '{self.conda_env}' is not available. "
                "Please ensure the misr-toolkit-py36 conda environment is installed."
            )

    def _check_environment(self) -> bool:
        """Check if the MISR Toolkit environment is available"""
        try:
            cmd = [
                "conda",
                "run",
                "-n",
                self.conda_env,
                "python",
                "-c",
                "import MisrToolkit",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Environment check failed: {e}")
            return False

    def process_single_file(
        self, filepath: str, progress_callback: Optional[Callable] = None
    ) -> ProcessingResult:
        """Process a single MISR HDF file using subprocess

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

    def validate_inputs(self, files: list) -> Dict[str, Any]:
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
        self, files: list, progress_callback: Optional[Callable] = None
    ) -> list:
        """Process multiple MISR HDF files using subprocess

        Args:
            files: List of file paths to process
            progress_callback: Progress callback function

        Returns:
            List of ProcessingResult objects
        """
        start_time = time.time()

        if progress_callback:
            progress_callback("Initializing HDF processing...", 0.0, 0, len(files))

        try:
            # Create temporary files for communication
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as config_file:
                config_path = config_file.name

                # Prepare configuration for worker
                worker_config = {
                    "files": files,
                    "ulc_lat": self.config.get("ulc_lat", 0.0),
                    "ulc_lon": self.config.get("ulc_lon", 0.0),
                    "lrc_lat": self.config.get("lrc_lat", 0.0),
                    "lrc_lon": self.config.get("lrc_lon", 0.0),
                    "field_name": self.config.get("field_name", "Red Radiance/RDQI"),
                    "apply_quality_filter": self.config.get(
                        "apply_quality_filter", True
                    ),
                    "output_directory": self.config.get("output_directory", "."),
                }

                json.dump(worker_config, config_file, indent=2)

            # Create output file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as output_file:
                output_path = output_file.name

            if progress_callback:
                progress_callback(
                    "Starting HDF processing in misr-toolkit-py36...",
                    0.1,
                    0,
                    len(files),
                )

            logger.info(f"Starting HDF processing with {len(files)} files")
            logger.info(f"Configuration: {worker_config}")

            # Execute worker script in conda environment
            cmd = [
                "conda",
                "run",
                "-n",
                self.conda_env,
                "python",
                str(self.worker_script),
                config_path,
                output_path,
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3600  # 1 hour timeout
            )

            if progress_callback:
                progress_callback(
                    "Processing complete, parsing results...",
                    0.9,
                    len(files),
                    len(files),
                )

            # Parse results
            if result.returncode == 0:
                with open(output_path, "r") as f:
                    worker_results = json.load(f)

                if worker_results["success"]:
                    # Convert to ProcessingResult objects
                    results = []
                    for result_data in worker_results["results"]:
                        proc_result = ProcessingResult(
                            input_file=result_data["input_file"],
                            success=result_data["success"],
                        )
                        proc_result.processing_time = time.time() - start_time

                        if result_data["success"]:
                            proc_result.output_files = {
                                "geotiff": result_data["output_file"]
                            }
                            proc_result.metadata = {
                                "statistics": result_data.get("statistics", {}),
                                "bounds": result_data.get("bounds", {}),
                                "processor": "MISR_Toolkit_Subprocess",
                            }
                        else:
                            proc_result.error_message = result_data.get(
                                "error", "Unknown error"
                            )

                        results.append(proc_result)

                    logger.info(
                        f"Successfully processed {worker_results['successful']}/{worker_results['total_files']} files"
                    )
                    return results
                else:
                    raise RuntimeError(
                        f"Worker failed: {worker_results.get('error', 'Unknown error')}"
                    )
            else:
                # Process failed
                error_msg = f"HDF processing failed (exit code {result.returncode})"
                if result.stderr:
                    error_msg += f"\nError: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nOutput: {result.stdout}"

                logger.error(error_msg)
                raise RuntimeError(error_msg)

        finally:
            # Clean up temporary files
            try:
                Path(config_path).unlink(missing_ok=True)
                Path(output_path).unlink(missing_ok=True)
            except:
                pass

    def get_processing_summary(self, results: list) -> Dict[str, Any]:
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
            "processor_type": "MISR_Toolkit",
        }
