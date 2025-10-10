# Platform Compatibility Guide

## The Problem

PyInstaller creates **platform-specific executables**. This means:

- ✅ Mac executables work **only on Mac**
- ✅ Windows executables work **only on Windows**  
- ✅ Linux executables work **only on Linux**
- ❌ You **cannot** run a Mac executable on Windows
- ❌ You **cannot** run a Windows executable on Mac

## Current Status

The executables in this repository (in `dist/` and `windows_executables/` folders) were built on **macOS** and will only work on Mac.

## Solutions by Platform

### For Mac Users

✅ **The current executables work for you!**

Simply double-click:
- `dist/DXF2Laser`
- `dist/GCodeAdjuster`

### For Windows Users

❌ **The current executables will NOT work**

Choose one of these solutions:

#### Solution 1: Build on Windows (Recommended)
**Best if:** You have access to a Windows computer

📖 **See:** [WINDOWS_BUILD_INSTRUCTIONS.md](WINDOWS_BUILD_INSTRUCTIONS.md)

Takes ~15-20 minutes. Gives you full control over the build process.

#### Solution 2: GitHub Actions (Easiest)
**Best if:** You don't have Windows but want automated builds

📖 **See:** [GITHUB_ACTIONS_BUILD.md](GITHUB_ACTIONS_BUILD.md)

- Build automatically when you push to GitHub
- Free for public repositories
- Creates downloadable releases
- No Windows PC needed

#### Solution 3: Run from Python Source
**Best if:** You're comfortable with Python

📖 **See:** [README.md](README.md) - Installation Options section

```bash
# On your Windows PC:
pip install -r requirements.txt
python dxf2laser.py
# or
python gcode_adjuster.py
```

#### Solution 4: Web Version
**Best if:** You want browser-based access

📖 **See:** [DEPLOYMENT.md](DEPLOYMENT.md)

Deploy to Replit or any Python web host. Access from any browser.

### For Linux Users

Similar to Windows users - you need to build on Linux or run from source.

## Quick Decision Tree

```
Do you have Windows?
├─ YES → Build on Windows (WINDOWS_BUILD_INSTRUCTIONS.md)
└─ NO
   ├─ Have Python installed? 
   │  └─ YES → Run from source (README.md)
   └─ Want automated builds?
      └─ YES → GitHub Actions (GITHUB_ACTIONS_BUILD.md)
   └─ Want web version?
      └─ YES → Deploy to Replit (DEPLOYMENT.md)
```

## Error Messages You Might See

If you try to run the wrong platform's executable:

**On Windows:**
- "This app can't run on your PC"
- "Unsupported 16-bit application"  
- "Not a valid Win32 application"

**On Mac:**
- "Bad CPU type in executable"
- "'DXF2Laser.exe' cannot be opened"

**On Linux:**
- "cannot execute binary file: Exec format error"

These all mean: **wrong platform executable**.

## Why Can't We Create Universal Binaries?

PyInstaller bundles:
- Platform-specific Python runtime
- Platform-specific system libraries
- Platform-specific executable format

This is why each platform needs its own build. There's no way around this limitation.

## Recommended Distribution Strategy

### Option A: Multiple Builds
Build separately on each platform and provide:
- `DXF2Laser-macOS.zip`
- `DXF2Laser-Windows.zip`
- `DXF2Laser-Linux.zip`

### Option B: Automated Releases
Use GitHub Actions to automatically build for all platforms:
- Push code once
- Get builds for Windows, Mac, Linux
- Automatic release creation

### Option C: Source Distribution
Distribute as Python source code:
- Users install Python
- Users run `pip install -r requirements.txt`
- Users run `python dxf2laser.py`

### Option D: Web Application
Deploy as web app:
- Works on any platform with a browser
- No installation needed
- Easiest for end users

## FAQs

**Q: Can I use Wine to run Windows executables on Mac?**  
A: Theoretically yes, but not recommended. Better to build natively.

**Q: Can I cross-compile for Windows on Mac?**  
A: No, PyInstaller doesn't support cross-compilation.

**Q: How big are the executables?**  
A: Typically 150-250 MB each (includes Python + all libraries).

**Q: Do I need different code for different platforms?**  
A: No, the Python code is the same. Only the compiled executables differ.

**Q: Can I make them smaller?**  
A: Yes, but it's complex. See PyInstaller optimization docs.

## Getting Help

If you're stuck:

1. Check the error message - it usually indicates wrong platform
2. Verify your OS matches the executable's target platform
3. Try the "Run from Source" option (works on all platforms)
4. See the detailed guides linked above

## Summary

| Platform | Current Executables | Action Needed |
|----------|-------------------|---------------|
| macOS | ✅ Work | None - just run them |
| Windows | ❌ Don't work | Build on Windows or use alternatives |
| Linux | ❌ Don't work | Build on Linux or use alternatives |

Choose your solution from the options above based on your needs and resources.

