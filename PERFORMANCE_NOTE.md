# Performance Note - iCloud Sync Issue

## Issue
The application may take 30-60 seconds to start because the project folder is stored in iCloud Drive, which causes slow Python package imports (scipy, numpy, matplotlib).

## Why This Happens
- Virtual environment (`venv/`) is in iCloud-synced folder
- Python must read thousands of files from iCloud
- Each import triggers iCloud download/verification
- Scipy/numpy have many large binary files

## Solutions (Choose One)

### Solution 1: Just Wait (Simplest)
**The application WILL start**, it just takes time.
- First run: 30-60 seconds
- Subsequent runs: May be faster if files are cached
- Run with: `./run_circumference.sh`

### Solution 2: Build Standalone Executable (Recommended)
This bundles everything into a single app with fast startup:

```bash
./build_circumference.sh
```

Then run:
```bash
./dist/CircumferenceClean
```

**Benefits:**
- Fast startup (no imports)
- No iCloud delays
- Can distribute to other machines
- Professional deployment

### Solution 3: Move Project to Local Folder
Copy the entire project to a non-iCloud location:

```bash
# Create local copy
cp -r "/Users/brad/Library/Mobile Documents/com~apple~CloudDocs/Lori&BradShared/Brad Work/AppliedAnodized/DXF2LASER" ~/Desktop/DXF2LASER

# Work from local copy
cd ~/Desktop/DXF2LASER
./run_circumference.sh
```

**Benefits:**
- Fast imports
- No network dependencies
- Better development experience

**Note:** Remember to copy changes back to iCloud if you want them synced.

### Solution 4: Recreate venv Locally
Keep project in iCloud but venv local:

```bash
# Remove iCloud venv
rm -rf venv

# Create local venv in /tmp (fast but temporary)
python3 -m venv /tmp/dxf2laser_venv
source /tmp/dxf2laser_venv/bin/activate
pip install -r requirements.txt

# Run with local venv
python CircumferenceClean.py
```

**Note:** /tmp venv is deleted on reboot - need to recreate.

## Recommended Approach

For **development**: Use Solution 1 (wait) or Solution 3 (local copy)
For **production use**: Use Solution 2 (standalone executable)

## Current Status

You can run the application with:
```bash
./run_circumference.sh
```

Just be patient during the initial import phase. Once running, the application is fast and responsive.

