#!/usr/bin/env python3
"""
Create MISR GUI Distribution Bundle
Packages the application with conda-pack for easy distribution.
"""

import subprocess
import shutil
import os
import sys
from pathlib import Path

def create_bundle():
    """Create the complete distribution bundle."""
    print("Creating MISR GUI Distribution Bundle...")
    
    # Get current directory
    current_dir = Path(__file__).parent.parent
    dist_dir = current_dir / "dist"
    
    # Step 1: Create the conda-pack bundle (already done)
    bundle_path = dist_dir / "misr-gui-full.tar.gz"
    if not bundle_path.exists():
        print("Error: Bundle not found. Please run conda-pack first.")
        return False
    
    # Step 2: Create extraction script
    extract_script = dist_dir / "extract_and_run.sh"
    
    script_content = '''#!/bin/bash
# MISR GUI Distribution - Extract and Run Script

echo "MISR GUI - Self-extracting bundle"
echo "================================="

# Create extraction directory
EXTRACT_DIR="misr-gui-full"
if [ -d "$EXTRACT_DIR" ]; then
    echo "Removing existing directory..."
    rm -rf "$EXTRACT_DIR"
fi

echo "Extracting bundle..."
tar -xzf misr-gui-full.tar.gz

echo "Copying application code..."
cp -r ../gui ../processing_core ../processing_hdf ../config ../utils ../main.py "$EXTRACT_DIR/"

echo "Creating launcher..."
cat > "$EXTRACT_DIR/run_misr_gui.sh" << 'EOF'
#!/bin/bash
# Activate the bundled environment and run the application
source bin/activate
python main.py
EOF

chmod +x "$EXTRACT_DIR/run_misr_gui.sh"

echo ""
echo "Setup complete! To run the application:"
echo "  cd $EXTRACT_DIR"
echo "  ./run_misr_gui.sh"
echo ""
'''
    
    with open(extract_script, 'w') as f:
        f.write(script_content)
    
    # Make script executable
    os.chmod(extract_script, 0o755)
    
    print(f"✅ Bundle created: {bundle_path}")
    print(f"✅ Extraction script: {extract_script}")
    print(f"📦 Bundle size: {bundle_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    return True

if __name__ == "__main__":
    success = create_bundle()
    if success:
        print("\n🎉 Distribution bundle ready!")
        print("Users can now download misr-gui-full.tar.gz and extract_and_run.sh")
    else:
        print("\n❌ Bundle creation failed!")
        sys.exit(1)