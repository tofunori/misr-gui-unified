@echo off
REM Simple Windows build script for MISR GUI
REM Copy this file to your Windows machine and run it from the project directory

echo =====================================
echo MISR GUI Simple Windows Build
echo =====================================
echo.

REM Check if we're in the right directory
if not exist "main.py" (
    echo ERROR: main.py not found!
    echo Please copy this script to your misr_gui_unified directory
    echo and run it from there.
    pause
    exit /b 1
)

echo Found main.py - continuing with build...
echo.

REM Install requirements
echo Installing Python packages...
pip install pyinstaller
pip install numpy scipy matplotlib pillow
pip install xarray netCDF4 h5py
pip install rasterio rioxarray geopandas fiona shapely pyproj

REM Build executable
echo.
echo Building executable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name misr_gui ^
    --add-data "gui;gui" ^
    --add-data "processing_core;processing_core" ^
    --add-data "processing_hdf;processing_hdf" ^
    --add-data "config;config" ^
    --add-data "utils;utils" ^
    --hidden-import tkinter ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --exclude-module matplotlib.tests ^
    --exclude-module numpy.tests ^
    --exclude-module scipy.tests ^
    main.py

REM Check result
if exist "dist\misr_gui.exe" (
    echo.
    echo =====================================
    echo SUCCESS!
    echo =====================================
    echo.
    echo Executable created: dist\misr_gui.exe
    for %%A in (dist\misr_gui.exe) do echo File size: %%~zA bytes
    echo.
    echo You can now distribute this file to other Windows users.
    echo No Python installation required to run it.
    echo.
) else (
    echo.
    echo =====================================
    echo BUILD FAILED!
    echo =====================================
    echo.
    echo Check the output above for errors.
    echo.
)

pause