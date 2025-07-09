# PyInstaller spec file for MISR GUI Windows executable

import sys
import os
from pathlib import Path

# Get the main application directory
spec_dir = Path(os.path.abspath(SPECPATH))
app_dir = spec_dir.parent

a = Analysis(
    [str(app_dir / 'main.py')],
    pathex=[str(app_dir)],
    binaries=[],
    datas=[
        # Include GUI components
        (str(app_dir / 'gui'), 'gui'),
        # Include processing modules
        (str(app_dir / 'processing_core'), 'processing_core'),
        (str(app_dir / 'processing_hdf'), 'processing_hdf'),
        # Include configuration files
        (str(app_dir / 'config'), 'config'),
        # Include utilities
        (str(app_dir / 'utils'), 'utils'),
        # Include requirements for reference
        (str(app_dir / 'requirements.txt'), '.'),
    ],
    hiddenimports=[
        # Core dependencies
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
        # Scientific libraries
        'numpy', 'scipy', 'matplotlib', 'PIL',
        # Geospatial libraries
        'rasterio', 'rioxarray', 'geopandas', 'fiona', 'shapely', 'pyproj',
        # NetCDF libraries
        'xarray', 'netCDF4', 'h5py',
        # MISR Toolkit (if available)
        'MisrToolkit',
        # Additional hidden imports
        'matplotlib.backends.backend_tkagg',
        'pkg_resources.py2_warn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib.tests',
        'numpy.tests',
        'scipy.tests',
        'pandas.tests',
        'PIL.tests',
        'tkinter.test',
        # Exclude unused backends
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_gtk3agg',
        'PySide2', 'PyQt5', 'PyQt6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filter out unnecessary files
a.binaries = [x for x in a.binaries if not x[0].startswith('api-ms-win-')]
a.datas = [x for x in a.datas if not x[0].endswith('.pyc')]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='misr_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path if available
)