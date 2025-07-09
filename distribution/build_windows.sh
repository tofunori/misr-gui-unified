#!/bin/bash
# Linux/WSL build script for Windows executable (cross-platform)

echo "====================================="
echo "MISR GUI Windows Build Script"
echo "====================================="
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python is not installed"
    echo "Please install Python 3.6+ and try again"
    exit 1
fi

# Install PyInstaller if not available
echo "Installing PyInstaller..."
pip3 install pyinstaller

# Install dependencies
echo "Installing dependencies..."
pip3 install -r ../requirements.txt

# Try to install MISR Toolkit
echo "Attempting to install MISR Toolkit..."
pip3 install MisrToolkit || echo "WARNING: MISR Toolkit not available via pip"

# Create executable
echo "Building executable..."
pyinstaller --clean misr_gui.spec

# Check if build was successful
if [ -f "dist/misr_gui.exe" ]; then
    echo
    echo "====================================="
    echo "SUCCESS: Executable created!"
    echo "====================================="
    echo "Location: dist/misr_gui.exe"
    echo "Size: $(du -h dist/misr_gui.exe | cut -f1)"
    echo
    echo "You can now distribute dist/misr_gui.exe"
    echo
else
    echo
    echo "====================================="
    echo "ERROR: Build failed!"
    echo "====================================="
    echo "Check the output above for errors"
    echo
fi