#!/usr/bin/env python3
"""
MISR HDF Worker Script
Standalone script that runs in the misr-toolkit-py36 environment to process HDF files.
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for HDF processing worker."""
    parser = argparse.ArgumentParser(description="MISR HDF Processing Worker")
    parser.add_argument("config_file", help="Path to JSON configuration file")
    parser.add_argument("output_file", help="Path to output results JSON file")

    args = parser.parse_args()

    try:
        # Load configuration
        with open(args.config_file, "r") as f:
            config = json.load(f)

        logger.info(f"Processing {len(config['files'])} HDF files")

        # Import MISR Toolkit (should work in misr-toolkit-py36 environment)
        import MisrToolkit as Mtk
        from osgeo import gdal, osr

        # Import local modules
        sys.path.insert(0, str(Path(__file__).parent))
        from misr_processor import MISRProcessor

        # Initialize processor
        def log_callback(message):
            logger.info(message)

        def progress_callback(message, progress):
            logger.info(f"Progress: {message} ({progress:.1%})")

        processor = MISRProcessor(
            progress_callback=progress_callback, log_callback=log_callback
        )

        # Process each file
        results = []
        for i, filepath in enumerate(config["files"]):
            logger.info(f"Processing file {i+1}/{len(config['files'])}: {filepath}")

            # Generate output filename
            input_path = Path(filepath)
            output_file = str(
                Path(config["output_directory"])
                / f"{input_path.stem}_{config['field_name'].replace('/', '_')}.tif"
            )

            # Process file
            result = processor.process_file(filepath, output_file, config)
            results.append(
                {
                    "input_file": filepath,
                    "output_file": output_file if result["success"] else None,
                    "success": result["success"],
                    "error": result.get("error"),
                    "statistics": result.get("statistics", {}),
                    "bounds": result.get("bounds", {}),
                }
            )

            if result["success"]:
                logger.info(f"Successfully processed: {filepath}")
            else:
                logger.error(
                    f"Failed to process {filepath}: {result.get('error', 'Unknown error')}"
                )

        # Write results
        with open(args.output_file, "w") as f:
            json.dump(
                {
                    "success": True,
                    "results": results,
                    "total_files": len(config["files"]),
                    "successful": sum(1 for r in results if r["success"]),
                    "failed": sum(1 for r in results if not r["success"]),
                },
                f,
                indent=2,
                default=str,  # Convert numpy types to strings
            )

        logger.info(f"Processing complete. Results written to {args.output_file}")

    except Exception as e:
        logger.error(f"Worker failed: {e}")

        # Write error result
        with open(args.output_file, "w") as f:
            json.dump(
                {"success": False, "error": str(e), "results": []},
                f,
                indent=2,
                default=str,
            )

        sys.exit(1)


if __name__ == "__main__":
    main()
