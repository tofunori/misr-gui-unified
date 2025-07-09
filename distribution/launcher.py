#!/usr/bin/env python3
"""
MISR GUI Launcher for Conda-Pack Distribution
Calls the main application from the bundled environment.
"""

import sys
import os
from pathlib import Path

# Get the directory containing this launcher
launcher_dir = Path(__file__).parent
app_dir = launcher_dir.parent

# Add the main app directory to Python path
sys.path.insert(0, str(app_dir))

# Import and run the main application
try:
    from main import main
    main()
except Exception as e:
    print(f"Error launching MISR GUI: {e}")
    print("Please ensure the bundle was extracted correctly.")
    sys.exit(1)