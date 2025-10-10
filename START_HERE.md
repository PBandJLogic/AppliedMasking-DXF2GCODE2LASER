# 🚀 Quick Start Guide

## Choose Your Path

### 🪟 Windows Users

**The executables in this repository won't work on Windows** (they're built for Mac).

**Pick one:**

1. **📦 Build Windows executables** (takes 15-20 min)
   - Follow: [WINDOWS_BUILD_INSTRUCTIONS.md](WINDOWS_BUILD_INSTRUCTIONS.md)
   - Best if you have Windows PC

2. **🤖 Use automated builds** (easiest, no Windows needed)
   - Follow: [GITHUB_ACTIONS_BUILD.md](GITHUB_ACTIONS_BUILD.md)
   - Set up once, get executables automatically

3. **🐍 Run from Python** (if you have Python)
   ```bash
   pip install -r requirements.txt
   python dxf2laser.py
   ```

4. **🌐 Use web version** (any browser)
   - Follow: [DEPLOYMENT.md](DEPLOYMENT.md)

### 🍎 macOS Users (You're Ready!)

**Your executables are already built! Just run them:**

```bash
cd dist/
./DXF2Laser
# or
./GCodeAdjuster
```

Or double-click the files in Finder.

### 🐧 Linux Users

Same as Windows - you need to build on Linux or run from source.

## Need More Help?

See [PLATFORM_COMPATIBILITY.md](PLATFORM_COMPATIBILITY.md) for detailed explanations.

## What These Apps Do

### DXF2Laser
Converts DXF drawing files → G-code for laser cutting/engraving

### GCodeAdjuster
Adjusts G-code based on actual vs expected positions for precision correction

---

**Having trouble?** Check [WINDOWS_USERS_READ_THIS.txt](WINDOWS_USERS_READ_THIS.txt) for common issues.

