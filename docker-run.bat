@echo off
REM Windows batch script to run MISR GUI Docker container

echo =================================
echo Running MISR GUI Docker Container
echo =================================
echo.

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop for Windows
    echo https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker image exists
docker images misr-gui:latest | findstr misr-gui >nul
if %errorlevel% neq 0 (
    echo ERROR: Docker image 'misr-gui:latest' not found
    echo Please build the image first:
    echo   docker-build.bat
    pause
    exit /b 1
)

REM Set data directory
set DATA_DIR=%1
if "%DATA_DIR%"=="" set DATA_DIR=%CD%\data

REM Create data directory if it doesn't exist
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

echo Data directory: %DATA_DIR%
echo.
echo IMPORTANT: For GUI to work on Windows, you need an X11 server:
echo   - Install VcXsrv: https://sourceforge.net/projects/vcxsrv/
echo   - Or install Xming: https://sourceforge.net/projects/xming/
echo   - Start the X11 server before running this script
echo.

REM Run the Docker container
echo Starting container...
docker run ^
    --rm ^
    -it ^
    -e DISPLAY=host.docker.internal:0 ^
    -v "%DATA_DIR%":/app/data ^
    -v "%CD%\output":/app/output ^
    --name misr-gui-container ^
    misr-gui:latest

echo.
echo Container stopped.
pause