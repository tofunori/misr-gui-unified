# MISR GUI Windows Executable

## 🚀 Quick Start

### For Windows Users:
1. **Download:** `misr_gui.exe` (50-100MB)
2. **Double-click** to run
3. **Done!** No installation required

## 🛠️ Building the Executable

### Prerequisites:
- **Python 3.6+** installed
- **MISR Toolkit** (follow NASA installation guide)
- **Git** (to clone repository)

### Build Steps:

#### Option 1: Windows Command Prompt
```cmd
git clone https://github.com/tofunori/misr-gui-unified.git
cd misr-gui-unified\distribution
build_windows.bat
```

#### Option 2: Linux/WSL (Cross-platform)
```bash
git clone https://github.com/tofunori/misr-gui-unified.git
cd misr-gui-unified/distribution
./build_windows.sh
```

### Build Output:
- **Location:** `dist/misr_gui.exe`
- **Size:** ~50-100MB (much smaller than conda-pack!)
- **Dependencies:** All bundled inside executable

## 📋 System Requirements

- **OS:** Windows 10+ (64-bit)
- **Memory:** 4GB RAM minimum
- **Disk Space:** 200MB free space
- **No Python installation required for end users**

## 🔧 Features

### ✅ Included:
- **NetCDF Processing** (always works)
- **HDF Processing** (if MISR Toolkit available during build)
- **GUI Interface** (native Windows look)
- **All Python dependencies** bundled

### ⚠️ Notes:
- **MISR Toolkit** must be installed on build machine
- **HDF processing** only works if MISR Toolkit was available during build
- **NetCDF processing** works regardless

## 🆘 Troubleshooting

### Build Issues:

**"MISR Toolkit not found"**
- Install MISR Toolkit from: https://github.com/nasa/MISR-Toolkit
- NetCDF processing will still work

**"PyInstaller failed"**
- Check Python version (3.6+ required)
- Install missing dependencies: `pip install -r requirements.txt`

**"Executable too large"**
- Normal for scientific applications
- Consider conda-pack if size is critical

### Runtime Issues:

**"Application won't start"**
- Try running from command prompt: `misr_gui.exe`
- Check Windows Defender/antivirus settings
- Ensure all dependencies were bundled correctly

**"Missing features"**
- HDF processing requires MISR Toolkit during build
- NetCDF processing should always work

## 📁 Build Process Details

The build script:
1. **Installs PyInstaller** and dependencies
2. **Attempts MISR Toolkit installation**
3. **Creates executable** with all dependencies
4. **Compresses** using UPX for smaller size
5. **Outputs** single `misr_gui.exe` file

## 🎯 Distribution Strategy

### For Different Users:
- **Windows users:** `misr_gui.exe` (50-100MB)
- **Linux users:** `misr-gui-full.tar.gz` (359MB)
- **Cross-platform:** Docker or conda-pack

### Advantages of Executable:
- ✅ **Much smaller** than conda-pack
- ✅ **Single file** - easy to share
- ✅ **No extraction** required
- ✅ **Native Windows** experience
- ✅ **Familiar** to Windows users

## 📊 Size Comparison

| Method | Size | Pros | Cons |
|--------|------|------|------|
| **PyInstaller .exe** | ~50-100MB | Small, single file, native | Build complexity |
| **conda-pack bundle** | ~359MB | Guaranteed compatibility | Large size |
| **Docker image** | ~500MB+ | Consistent environment | Docker required |

---

*The Windows executable provides the best user experience for Windows users while maintaining full functionality.*