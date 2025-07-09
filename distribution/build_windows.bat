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

REM Install PyInstaller if not available
echo Installing PyInstaller...
pip install pyinstaller

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Try to install MISR Toolkit
echo Attempting to install MISR Toolkit...
pip install MisrToolkit
if %errorlevel% neq 0 (
    echo WARNING: MISR Toolkit not available via pip
    echo HDF processing will be disabled
    echo NetCDF processing will still work
)

REM Create executable
echo Building executable...
pyinstaller --clean misr_gui.spec

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