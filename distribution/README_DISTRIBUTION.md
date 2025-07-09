# MISR GUI Distribution Package

## 📦 What's Included

This distribution package contains a complete, self-contained MISR GUI application with:

✅ **MISR Toolkit** - Pre-installed and configured
✅ **NetCDF Processing** - Full xarray, rasterio, geopandas support  
✅ **HDF Processing** - Direct MISR Toolkit integration
✅ **All Dependencies** - Python 3.6, GDAL, NumPy, SciPy, etc.
✅ **No Installation Required** - Just extract and run!

## 🚀 How to Use

### For End Users:

1. **Download both files:**
   - `misr-gui-full.tar.gz` (359 MB)
   - `extract_and_run.sh`

2. **Extract and run:**
   ```bash
   chmod +x extract_and_run.sh
   ./extract_and_run.sh
   ```

3. **Launch the application:**
   ```bash
   cd misr-gui-full
   ./run_misr_gui.sh
   ```

### Manual Extraction:

```bash
# Extract the bundle
tar -xzf misr-gui-full.tar.gz

# Copy application code
cp -r ../gui ../processing_core ../processing_hdf ../config ../utils ../main.py misr-gui-full/

# Run the application
cd misr-gui-full
source bin/activate
python main.py
```

## 📋 System Requirements

- **OS:** Linux (64-bit)
- **Memory:** 4GB RAM minimum
- **Disk Space:** 1GB free space
- **No additional dependencies required**

## 🔧 Features Available

### NetCDF Processing:
- Reprojection to target locations
- Quality assurance filtering  
- Shapefile-based clipping
- Export to NetCDF and GeoTIFF
- Batch processing

### HDF Processing:
- Direct MISR Toolkit processing
- Regional coordinate specification
- Field selection (optical depth, surface reflectance)
- Quality filtering
- Export to GeoTIFF

## 🆘 Troubleshooting

**Application won't start:**
- Check that you extracted the bundle completely
- Ensure the launcher script is executable: `chmod +x run_misr_gui.sh`
- Run from the correct directory: `cd misr-gui-full`

**Missing dependencies:**
- The bundle is self-contained - no additional installation needed
- If you see import errors, the bundle may be corrupted - re-download

**Permission errors:**
- Make sure you have write permissions in the extraction directory
- Some Linux distributions require: `chmod +x bin/activate`

## 📁 Bundle Contents

```
misr-gui-full/
├── bin/                  # Python interpreter and tools
├── lib/                  # All libraries (MISR Toolkit, GDAL, etc.)
├── share/               # Shared resources
├── main.py              # Your GUI application
├── gui/                 # GUI components
├── processing_core/     # NetCDF processing
├── processing_hdf/      # HDF processing with MISR Toolkit
├── config/              # Configuration files
├── utils/               # Utility functions
└── run_misr_gui.sh      # Launch script
```

## 🎯 Distribution Benefits

- **No manual MISR Toolkit installation**
- **Works on any Linux system**
- **Offline capable**
- **Consistent environment**
- **Easy to share and deploy**

---

*Generated with conda-pack for maximum compatibility and ease of use.*