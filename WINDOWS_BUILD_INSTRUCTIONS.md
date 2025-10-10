# Building Windows Executables

## Important Notice
**You CANNOT build Windows executables on macOS.** PyInstaller creates platform-specific binaries. To create Windows executables, you must build them on a Windows machine.

## Prerequisites (Windows Only)

1. **Windows 10 or later** (64-bit)
2. **Python 3.11 or later** installed from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
3. **Git** (optional, for cloning the repository)

## Step-by-Step Build Instructions

### 1. Get the Project Files on Windows

**Option A: Using Git**
```cmd
git clone [your-repository-url]
cd DXF2LASER
```

**Option B: Download ZIP**
- Download the project as a ZIP file
- Extract to a folder (e.g., `C:\Users\YourName\DXF2LASER`)
- Open Command Prompt and navigate to that folder

### 2. Create Virtual Environment

```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your command prompt.

### 3. Install Dependencies

```cmd
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```

### 4. Build the Executables

**Build DXF2Laser:**
```cmd
pyinstaller DXF2Laser.spec
```

**Build GCodeAdjuster:**
```cmd
pyinstaller GCodeAdjuster.spec
```

### 5. Locate the Executables

After building, the executables will be in:
```
dist/
  ├── DXF2Laser.exe
  └── GCodeAdjuster.exe
```

### 6. Test the Executables

```cmd
cd dist
DXF2Laser.exe
```

If it launches successfully, you're done!

### 7. Package for Distribution

Create a distribution folder with:
```
DXF2Laser_Windows/
  ├── DXF2Laser.exe
  ├── GCodeAdjuster.exe
  ├── logo.png
  ├── Run_DXF2Laser.bat
  ├── Run_GCodeAdjuster.bat
  └── README_EXECUTABLES.md
```

Copy these files from the project:
```cmd
mkdir DXF2Laser_Windows
copy dist\DXF2Laser.exe DXF2Laser_Windows\
copy dist\GCodeAdjuster.exe DXF2Laser_Windows\
copy logo.png DXF2Laser_Windows\
copy dist\Run_DXF2Laser.bat DXF2Laser_Windows\
copy dist\Run_GCodeAdjuster.bat DXF2Laser_Windows\
copy dist\README_EXECUTABLES.md DXF2Laser_Windows\
```

## Troubleshooting

### "python is not recognized"
- Python is not in your PATH
- Reinstall Python and check "Add Python to PATH"
- Or use full path: `C:\Python311\python.exe`

### "No module named 'tkinter'"
- Tkinter should be included with Python
- Reinstall Python and ensure "tcl/tk and IDLE" is checked

### Missing DLLs
- Ensure you're using Python from python.org (not Microsoft Store version)
- Install Visual C++ Redistributable if needed

### Build Fails
- Make sure all dependencies are installed: `pip list`
- Try cleaning build folders: `rmdir /s build dist`
- Rebuild: `pyinstaller DXF2Laser.spec`

### Executable Won't Run
- Check antivirus isn't blocking it
- Run from Command Prompt to see error messages
- Check console output for specific errors

## Alternative: Using a Windows Virtual Machine

If you don't have a Windows PC, you can:

1. **Use a Windows VM on Mac:**
   - Parallels Desktop (paid)
   - VMware Fusion (free for personal use)
   - VirtualBox (free)

2. **Use a Cloud Windows Instance:**
   - AWS EC2 Windows instance
   - Azure Windows VM
   - Google Cloud Windows instance

3. **Use GitHub Actions (Automated):**
   - Set up GitHub Actions to build Windows executables automatically
   - See `GITHUB_ACTIONS_BUILD.md` for instructions

## GitHub Actions Build (Automated)

If you push to GitHub, you can set up automated Windows builds. This is the easiest option if you don't have Windows access.

See the `GITHUB_ACTIONS_BUILD.md` file for complete instructions on setting up automated builds that will create Windows executables every time you push to GitHub.

## Notes

- Each executable is self-contained (~150-250 MB)
- They include Python runtime and all dependencies
- No installation required for end users
- Executables only work on Windows (you need to build on Mac for Mac executables)

## Current Build Status

The executables in the `dist/` and `windows_executables/` folders were built on **macOS** and will **NOT work on Windows**. You must rebuild on Windows using these instructions.

