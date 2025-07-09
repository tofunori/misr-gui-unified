#!/bin/bash
# Run script for MISR GUI Docker container

echo "================================="
echo "Running MISR GUI Docker Container"
echo "================================="
echo

# Check if Docker image exists
if ! docker images misr-gui:latest | grep -q misr-gui; then
    echo "ERROR: Docker image 'misr-gui:latest' not found"
    echo "Please build the image first:"
    echo "  ./docker-build.sh"
    exit 1
fi

# Default data directory
DATA_DIR="${1:-$(pwd)/data}"

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

echo "Data directory: $DATA_DIR"
echo "GUI will be accessible via X11 forwarding"
echo

# Detect platform and set up X11 forwarding
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux - setting up X11 forwarding..."
    xhost +local:docker
    X11_ARGS="-e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS - you may need XQuartz installed"
    echo "Install XQuartz: https://www.xquartz.org/"
    X11_ARGS="-e DISPLAY=host.docker.internal:0"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "Detected Windows - you may need X11 server (VcXsrv, Xming)"
    echo "Install VcXsrv: https://sourceforge.net/projects/vcxsrv/"
    X11_ARGS="-e DISPLAY=host.docker.internal:0"
else
    echo "Unknown OS - using default X11 settings"
    X11_ARGS="-e DISPLAY=$DISPLAY"
fi

# Run the Docker container
echo "Starting container..."
docker run \
    --rm \
    -it \
    $X11_ARGS \
    -v "$DATA_DIR":/app/data \
    -v "$(pwd)/output":/app/output \
    --name misr-gui-container \
    misr-gui:latest

echo
echo "Container stopped."