#!/bin/bash
# Build script for MISR GUI Docker container

echo "================================="
echo "Building MISR GUI Docker Container"
echo "================================="
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    echo "Please install Docker first:"
    echo "  - Linux: sudo apt-get install docker.io"
    echo "  - Windows: Download Docker Desktop"
    echo "  - macOS: Download Docker Desktop"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon is not running"
    echo "Please start Docker first"
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t misr-gui:latest .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo
    echo "================================="
    echo "SUCCESS: Docker image built!"
    echo "================================="
    echo
    echo "Image name: misr-gui:latest"
    echo "Image size:"
    docker images misr-gui:latest
    echo
    echo "To run the container:"
    echo "  ./docker-run.sh"
    echo
    echo "To run with custom data directory:"
    echo "  ./docker-run.sh /path/to/your/data"
    echo
else
    echo
    echo "================================="
    echo "ERROR: Docker build failed!"
    echo "================================="
    echo
    echo "Check the output above for errors"
    exit 1
fi