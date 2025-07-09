#!/usr/bin/env python3
"""
MISR Data Processing Tool - Main Entry Point
Launches the graphical user interface for MISR satellite data processing.
"""

import sys
import logging
from pathlib import Path
from tkinter import messagebox

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from gui import MainWindow
except ImportError as e:
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Import Error",
            f"Failed to import GUI components: {e}\n\n"
            "Please ensure all dependencies are installed:\n"
            "pip install -r requirements.txt",
        )
        root.destroy()
    except:
        print(f"Failed to import GUI components: {e}")
        print("Please ensure all dependencies are installed (see requirements.txt)")
    sys.exit(1)


def setup_logging():
    """Configure application logging."""
    log_dir = current_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "misr_gui.log"),
            logging.StreamHandler(),
        ],
    )

    # Reduce verbose logging from some libraries
    for lib in ["matplotlib", "PIL", "rasterio", "fiona"]:
        logging.getLogger(lib).setLevel(logging.WARNING)


def main():
    """Main application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting MISR Data Processing Tool")

    try:
        app = MainWindow()
        app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        try:
            messagebox.showerror("Fatal Error", f"Application error: {e}")
        except:
            print(f"Fatal error: {e}")
        sys.exit(1)

    logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()
