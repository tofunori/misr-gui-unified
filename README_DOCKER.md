# MISR GUI Docker Setup

This Docker setup provides a complete environment for running the MISR GUI with both Python 3.6 (MISR Toolkit) and Python 3.12 (main application) in a single container.

## Prerequisites

- Docker and Docker Compose installed
- MISR Toolkit installation files (see MISR Toolkit Setup below)
- X11 forwarding setup for GUI display (Linux/macOS)

## Quick Start

### 1. Build and Run
```bash
# Build the Docker image
docker-compose build

# Run the application
docker-compose up
```

### 2. With VNC Access (Recommended for Remote Use)
```bash
# Run with VNC server for remote GUI access
docker-compose --profile vnc up
```

Access the GUI via VNC at `localhost:6901` (password: `password`)

## Directory Structure

```
misr_gui_unified/
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── data/                   # Input data directory (mounted)
├── output/                 # Output files directory (mounted)
├── config/                 # Configuration files (mounted)
└── misr_toolkit_installation/ # MISR Toolkit files (see below)
```

## MISR Toolkit Setup

### Option 1: Pre-built MISR Toolkit
1. Create directory: `mkdir misr_toolkit_installation`
2. Copy your MISR Toolkit installation files to this directory
3. Ensure `setup.py` is in the root of this directory

### Option 2: Manual Installation
If you don't have MISR Toolkit installation files:
1. Comment out the MISR Toolkit installation lines in the Dockerfile
2. Build the container and install manually:
```bash
docker-compose run --rm misr-gui bash
conda activate misr-toolkit-py36
# Install MISR Toolkit manually
```

## Usage

### Local Display (Linux/macOS)
```bash
# Allow X11 forwarding
xhost +local:docker

# Run with display forwarding
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/output:/app/output \
  misr-gui-app
```

### Remote Access via VNC
```bash
# Start with VNC
docker-compose --profile vnc up

# Access via web browser
open http://localhost:6901

# Or use VNC client
vncviewer localhost:5901
```

## Configuration

### Environment Variables
- `DISPLAY`: X11 display (set automatically)
- `PYTHONPATH`: Python module path (set automatically)

### Volume Mounts
- `./data:/app/data` - Input data files
- `./output:/app/output` - Output files
- `./config:/app/config` - Configuration files

## Troubleshooting

### GUI Not Displaying
1. **X11 forwarding issues**: Ensure `xhost +local:docker` is run
2. **VNC connection**: Check if port 6901 is accessible
3. **Container logs**: `docker-compose logs misr-gui`

### MISR Toolkit Issues
1. **Import errors**: Verify MISR Toolkit is installed in Python 3.6 environment
2. **Library dependencies**: Check HDF4/HDF5 system libraries
3. **Path issues**: Ensure `/opt/conda/envs/misr-toolkit-py36` exists

### Performance Issues
1. **Memory**: Increase Docker memory allocation
2. **CPU**: Limit concurrent processing in GUI settings
3. **Storage**: Ensure sufficient disk space for output files

## Development

### Building Custom Image
```bash
# Build with custom tag
docker build -t misr-gui:custom .

# Run development version
docker run -it --rm -v $(pwd):/app misr-gui:custom bash
```

### Debugging
```bash
# Run interactive shell
docker-compose run --rm misr-gui bash

# Check environments
docker-compose exec misr-gui conda env list

# Test MISR Toolkit
docker-compose exec misr-gui conda run -n misr-toolkit-py36 python -c "import MisrToolkit"
```

## Sharing with Colleagues

### Method 1: Docker Hub
```bash
# Build and push
docker build -t yourusername/misr-gui .
docker push yourusername/misr-gui

# Colleague usage
docker pull yourusername/misr-gui
docker run -it yourusername/misr-gui
```

### Method 2: Archive
```bash
# Save image as tar
docker save misr-gui:latest | gzip > misr-gui.tar.gz

# Load on colleague's machine
docker load < misr-gui.tar.gz
```

### Method 3: Git + Docker Compose
```bash
# Push to GitHub
git init
git add .
git commit -m "MISR GUI Docker setup"
git push origin main

# Colleague usage
git clone https://github.com/yourusername/misr-gui
cd misr-gui
docker-compose up
```

## Benefits of Docker Approach

1. **Environment Isolation**: No conflicts with local Python installations
2. **Reproducibility**: Same environment across all machines
3. **Easy Distribution**: Single command deployment
4. **Version Control**: Docker images can be versioned
5. **Multi-Python Support**: Handles Python 3.6 and 3.12 automatically
6. **Cross-Platform**: Works on Linux, macOS, and Windows
7. **No Manual Setup**: MISR Toolkit and dependencies handled automatically

## Limitations

1. **GUI Performance**: Slightly slower than native GUI
2. **File Access**: Need to use mounted volumes
3. **Initial Setup**: Requires MISR Toolkit installation files
4. **Size**: Docker image will be larger than native installation