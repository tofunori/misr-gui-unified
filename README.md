# MISR Unified GUI Application

A unified graphical application for processing MISR satellite data supporting both NetCDF (advanced processing) and HDF (MISR Toolkit) formats.

## Features

### Dual Processing Modes
- **NetCDF Processing (Advanced)**: Full-featured processing with QA filtering, clipping, and advanced export options
- **HDF Processing (MISR Toolkit)**: Direct HDF processing using the MISR Toolkit library

### Supported File Types
- NetCDF files (`.nc`)
- HDF files (`.hdf`, `.he5`)

### Processing Capabilities
- **NetCDF Mode**: 
  - Reprojection to target locations
  - Quality assurance filtering
  - Shapefile-based clipping
  - Export to NetCDF and GeoTIFF formats
  - Batch processing

- **HDF Mode**:
  - Direct MISR Toolkit processing
  - Regional coordinate specification
  - Field selection (optical depth, surface reflectance, etc.)
  - Quality filtering
  - Export to GeoTIFF format

## Installation

### Prerequisites
- Python 3.8+
- MISR Toolkit (for HDF processing)
- GDAL libraries

### Setup
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install MISR Toolkit (for HDF processing):
   - Download from NASA's MISR Toolkit website
   - Follow platform-specific installation instructions
   - Ensure `MisrToolkit` is importable in Python

3. Install GDAL (usually comes with MISR Toolkit):
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install gdal-bin libgdal-dev
   
   # On macOS with Homebrew
   brew install gdal
   ```

## Usage

### Starting the Application
```bash
python main.py
```

### Processing Workflow

1. **Select Processing Mode**:
   - Choose "NetCDF Processing (Advanced)" for .nc files
   - Choose "HDF Processing (MISR Toolkit)" for .hdf/.he5 files

2. **Add Files**:
   - Click "Add Files" to select individual files
   - Click "Add Directory" to add all supported files from a folder

3. **Configure Processing**:
   - **NetCDF Mode**: Configure region, QA filtering, clipping, and output options
   - **HDF Mode**: Set region coordinates, select data field, and enable quality filtering

4. **Process Files**:
   - Click "Start Processing" to begin batch processing
   - Monitor progress in the progress panel
   - View results and logs in real-time

### Configuration Management
- Save/load processing configurations
- Preset configurations for common regions
- Validation of settings before processing

## File Structure

```
misr_gui_unified/
├── gui/                    # GUI components
│   ├── main_window.py     # Main application window
│   ├── config_panel.py    # Configuration panel with mode switching
│   ├── file_panel.py      # File selection and management
│   └── progress_panel.py  # Progress monitoring
├── processing_core/       # NetCDF processing (original)
│   ├── batch_processor.py
│   ├── reprojector.py
│   └── ...
├── processing_hdf/        # HDF processing (MISR Toolkit)
│   ├── misr_processor.py
│   ├── misr_adapter.py
│   └── ...
└── main.py               # Application entry point
```

## Safety Features

- **Non-destructive Integration**: Original NetCDF processing is completely preserved
- **Separate Processing Pipelines**: HDF and NetCDF processing are isolated
- **Input Validation**: Comprehensive file and configuration validation
- **Error Handling**: Robust error handling with detailed logging

## Troubleshooting

### MISR Toolkit Issues
- Ensure MISR Toolkit is properly installed
- Check that `MisrToolkit` module is importable
- Verify GDAL installation

### File Processing Issues
- Check file formats are supported (.nc, .hdf, .he5)
- Verify file permissions and accessibility
- Review processing logs for detailed error messages

### Performance Considerations
- HDF processing may be slower than NetCDF
- Large batch processing may require significant memory
- Monitor system resources during processing

## Development

### Adding New Features
- NetCDF features: Extend `processing_core/` modules
- HDF features: Extend `processing_hdf/` modules
- GUI features: Modify `gui/` components

### Testing
- Test NetCDF processing with known good files
- Test HDF processing with MISR Toolkit examples
- Verify GUI responsiveness and error handling

## Support

For issues related to:
- **NetCDF processing**: Check original misr_gui_app documentation
- **HDF processing**: Refer to MISR Toolkit documentation
- **GUI issues**: Check application logs and error messages

## Version History

- **v1.0**: Initial unified release combining NetCDF and HDF processing capabilities
- Based on proven processing pipelines from separate applications
- Maintains backward compatibility with existing configurations