# Windows Build Setup Instructions

## ⚠️ Important: Avoid WSL Path Issues

The build script cannot run directly from WSL paths due to Windows CMD limitations.

## 🚀 Correct Setup Steps:

### 1. Clone to Windows Directory
```cmd
# Run this in Windows Command Prompt (not WSL)
cd C:\
git clone https://github.com/tofunori/misr-gui-unified.git
cd misr-gui-unified
```

### 2. Run Build Script
```cmd
# Navigate to distribution folder
cd distribution

# Run the build script
build_windows.bat
```

### 3. Alternative: Copy from WSL to Windows
```cmd
# If you already have files in WSL, copy them:
robocopy "\\wsl.localhost\ubuntu\home\tofunori\Projects\misr_reproject\misr_gui_unified" "C:\misr-gui-unified" /E
cd C:\misr-gui-unified\distribution
build_windows.bat
```

## 🛠️ Manual Build (if script fails):

```cmd
# Navigate to main directory
cd C:\misr-gui-unified

# Install dependencies
pip install pyinstaller
pip install -r requirements.txt
pip install numpy
pip install MisrToolkit

# Build executable
cd distribution
pyinstaller --clean misr_gui.spec
```

## 📁 Expected Output:
- **Location:** `distribution\dist\misr_gui.exe`
- **Size:** ~50-100MB
- **Ready to distribute:** Single executable file

## 🆘 Troubleshooting:

**"UNC paths not supported":**
- Don't run from WSL path (`\\wsl.localhost\...`)
- Copy files to Windows directory first

**"requirements.txt not found":**
- Make sure you're in the main project directory
- The script navigates automatically now

**"MISR Toolkit failed":**
- Install numpy first: `pip install numpy`
- Then try: `pip install MisrToolkit`
- NetCDF processing will still work without it

**"PyInstaller failed":**
- Don't run from C:\Windows directory
- Navigate to your project folder first
- Make sure all dependencies are installed

## ✅ Success Indicators:
- No error messages during build
- `dist\misr_gui.exe` file exists
- File size is reasonable (50-100MB)
- Double-clicking launches the GUI