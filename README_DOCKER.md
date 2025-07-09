# MISR GUI Docker Container

## 🐳 Docker Solution for MISR Toolkit

This Docker container provides a complete MISR GUI environment with MISR Toolkit pre-installed, solving Windows compatibility issues.

## 🚀 Quick Start

### **1. Build the Container**
```bash
# Linux/macOS/WSL
./docker-build.sh

# Windows
docker-build.bat
```

### **2. Run the Application**
```bash
# Linux/macOS/WSL
./docker-run.sh

# Windows
docker-run.bat
```

## 📋 Requirements

### **All Platforms:**
- Docker installed and running
- 2GB+ disk space for container
- 4GB+ RAM recommended

### **For GUI Display:**

#### **Linux:**
- X11 forwarding (automatic)
- Container will set up X11 access

#### **Windows:**
- **X11 Server required** (one of):
  - VcXsrv: https://sourceforge.net/projects/vcxsrv/
  - Xming: https://sourceforge.net/projects/xming/
  - X410: Microsoft Store

#### **macOS:**
- XQuartz: https://www.xquartz.org/

## 🔧 Features

### **✅ Included in Container:**
- **MISR Toolkit** (fully functional)
- **All Python dependencies** (NumPy, SciPy, GDAL, etc.)
- **NetCDF processing** (xarray, rasterio, geopandas)
- **HDF processing** (MISR Toolkit integration)
- **Ubuntu 20.04 base** (stable, well-tested)

### **✅ Processing Capabilities:**
- **NetCDF Processing (Advanced)** ✅
- **HDF Processing (MISR Toolkit)** ✅
- **All GUI features** available

## 📂 Data Management

### **Directory Mapping:**
- **Input data:** `./data/` → `/app/data/` (in container)
- **Output data:** `./output/` → `/app/output/` (in container)

### **Usage:**
```bash
# Put your MISR files in ./data/
mkdir data
cp your_misr_files.hdf ./data/

# Run container
./docker-run.sh

# Processed files appear in ./output/
```

### **Custom Data Directory:**
```bash
# Use custom data directory
./docker-run.sh /path/to/your/misr/data
```

## 🛠️ Manual Docker Commands

### **Build:**
```bash
docker build -t misr-gui:latest .
```

### **Run:**
```bash
# Linux
docker run --rm -it \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/output:/app/output \
  misr-gui:latest

# Windows (with X11 server running)
docker run --rm -it \
  -e DISPLAY=host.docker.internal:0 \
  -v %CD%\data:/app/data \
  -v %CD%\output:/app/output \
  misr-gui:latest
```

## 🎯 Advantages

### **vs. Windows Executable:**
- ✅ **MISR Toolkit works** (no compilation issues)
- ✅ **Same environment** everywhere
- ✅ **No dependency conflicts**

### **vs. conda-pack:**
- ✅ **Cross-platform** (works on any OS)
- ✅ **Consistent** (same Ubuntu base)
- ✅ **Isolated** (no system conflicts)

### **vs. Manual Installation:**
- ✅ **No setup required** (everything included)
- ✅ **Reproducible** (same result every time)
- ✅ **Easy to share** (single container)

## 🆘 Troubleshooting

### **Build Issues:**

**"Docker not found"**
- Install Docker Desktop
- Ensure Docker daemon is running

**"Build failed"**
- Check internet connection
- Ensure sufficient disk space (2GB+)
- Try building again (may be temporary network issue)

### **GUI Issues:**

**"GUI not displaying" (Windows)**
- Install and start X11 server (VcXsrv/Xming)
- Ensure X11 server allows connections
- Check firewall settings

**"GUI not displaying" (Linux)**
- Run: `xhost +local:docker`
- Check DISPLAY variable: `echo $DISPLAY`

**"GUI not displaying" (macOS)**
- Install XQuartz
- Enable "Allow connections from network clients"
- Restart XQuartz

### **Container Issues:**

**"Image not found"**
- Build container first: `./docker-build.sh`

**"Permission denied"**
- Make scripts executable: `chmod +x docker-*.sh`

**"Container won't start"**
- Check Docker is running: `docker info`
- Try: `docker system prune` (cleanup)

## 📊 Size Comparison

| Method | Size | Setup Time | Cross-Platform |
|--------|------|------------|----------------|
| **Docker** | ~1.5GB | 5-10 min | ✅ |
| **conda-pack** | ~359MB | 2-3 min | ❌ (Linux only) |
| **Windows .exe** | ~50-100MB | 30+ min | ❌ (Windows only) |

## 🔄 Updates

### **Rebuild container:**
```bash
# Pull latest code
git pull

# Rebuild container
./docker-build.sh
```

### **Update dependencies:**
```bash
# Edit Dockerfile to change versions
# Rebuild container
```

---

**Docker provides the most reliable cross-platform solution for MISR Toolkit!**