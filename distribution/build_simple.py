#!/usr/bin/env python3
"""
Simple PyInstaller build script for MISR GUI
Alternative to the batch/shell scripts
"""

import subprocess
import sys
import os
from pathlib import Path


def main():
    print("=====================================")
    print("MISR GUI Simple Build Script")
    print("=====================================")
    print()

    # Get directories
    current_dir = Path(__file__).parent
    app_dir = current_dir.parent

    # Change to app directory
    os.chdir(app_dir)
    print(f"Working directory: {os.getcwd()}")

    # Install PyInstaller
    print("Installing PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=False)

    # Install dependencies
    print("Installing dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=False
    )

    # Try to install MISR Toolkit
    print("Attempting to install MISR Toolkit...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "MisrToolkit"], check=False
    )
    if result.returncode != 0:
        print("WARNING: MISR Toolkit installation failed")
        print("HDF processing will be disabled")

    # Build executable with simple command
    print("Building executable...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name",
        "misr_gui",
        "--add-data",
        "gui:gui",
        "--add-data",
        "processing_core:processing_core",
        "--add-data",
        "processing_hdf:processing_hdf",
        "--add-data",
        "config:config",
        "--add-data",
        "utils:utils",
        "--add-data",
        "requirements.txt:.",
        "--hidden-import",
        "tkinter",
        "--hidden-import",
        "matplotlib.backends.backend_tkagg",
        "--hidden-import",
        "MisrToolkit",
        "--exclude-module",
        "matplotlib.tests",
        "--exclude-module",
        "numpy.tests",
        "--exclude-module",
        "scipy.tests",
        "main.py",
    ]

    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)

    # Check result
    exe_path = Path("dist/misr_gui.exe")
    if exe_path.exists():
        print()
        print("=====================================")
        print("SUCCESS: Executable created!")
        print("=====================================")
        print(f"Location: {exe_path}")
        print(f"Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        print()
        print("You can now distribute dist/misr_gui.exe")
    else:
        print()
        print("=====================================")
        print("ERROR: Build failed!")
        print("=====================================")
        print("Check the output above for errors")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
