@echo off
REM Windows build script for MISR GUI executable

echo =====================================
echo MISR GUI Windows Build Script
echo =====================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.6+ and try again
    pause
    exit /b 1
)

REM Navigate to parent directory (where main.py is)
cd /d "%~dp0.."
echo Current directory: %CD%

REM Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found in current directory
    echo Please run this script from the misr_gui_unified directory
    pause
    exit /b 1
)

REM Install PyInstaller if not available
echo Installing PyInstaller...
pip install pyinstaller

REM Install dependencies
echo Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo WARNING: requirements.txt not found, installing basic dependencies
    pip install xarray numpy scipy rasterio rioxarray geopandas fiona shapely pyproj netCDF4 h5py matplotlib pillow
)

REM Install numpy first (required for MISR Toolkit)
echo Installing numpy first...
pip install numpy

REM Try to install MISR Toolkit
echo Attempting to install MISR Toolkit...
pip install MisrToolkit
if %errorlevel% neq 0 (
    echo WARNING: MISR Toolkit not available via pip
    echo HDF processing will be disabled
    echo NetCDF processing will still work
)

REM Create executable using simple PyInstaller command
echo Building executable...
pyinstaller --onefile --windowed --name misr_gui --add-data "gui;gui" --add-data "processing_core;processing_core" --add-data "processing_hdf;processing_hdf" --add-data "config;config" --add-data "utils;utils" --hidden-import tkinter --hidden-import matplotlib.backends.backend_tkagg --exclude-module matplotlib.tests --exclude-module numpy.tests --exclude-module scipy.tests main.py

REM Check if build was successful
if exist "dist\misr_gui.exe" (
    echo.
    echo =====================================
    echo SUCCESS: Executable created!
    echo =====================================
    echo Location: dist\misr_gui.exe
    echo Size: 
    dir "dist\misr_gui.exe" | find "misr_gui.exe"
    echo.
    echo You can now distribute dist\misr_gui.exe
    echo.
) else (
    echo.
    echo =====================================
    echo ERROR: Build failed!
    echo =====================================
    echo Check the output above for errors
    echo.
)

pause