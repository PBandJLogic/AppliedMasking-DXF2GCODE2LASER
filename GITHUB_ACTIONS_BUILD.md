# Automated Windows Builds with GitHub Actions

This guide shows you how to set up automatic Windows executable builds using GitHub Actions, so you can build Windows executables from your Mac without needing Windows.

## How It Works

GitHub Actions provides free Windows virtual machines. When you push code to GitHub, it automatically:
1. Sets up a Windows environment
2. Installs Python and dependencies
3. Builds the Windows executables
4. Makes them available for download

## Setup Instructions

### Step 1: Create GitHub Actions Workflow

Create a file at `.github/workflows/build-windows.yml` in your repository:

```yaml
name: Build Windows Executables

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:  # Allows manual triggering

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build DXF2Laser
      run: pyinstaller DXF2Laser.spec
    
    - name: Build GCodeAdjuster
      run: pyinstaller GCodeAdjuster.spec
    
    - name: Create distribution package
      run: |
        mkdir release
        copy dist\DXF2Laser.exe release\
        copy dist\GCodeAdjuster.exe release\
        copy logo.png release\
        copy dist\Run_DXF2Laser.bat release\
        copy dist\Run_GCodeAdjuster.bat release\
        copy dist\README_EXECUTABLES.md release\
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      with:
        name: windows-executables
        path: release/
        retention-days: 30

    - name: Create Release (on tag)
      if: startsWith(github.ref, 'refs/tags/')
      uses: softprops/action-gh-release@v1
      with:
        files: release/*
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Step 2: Commit and Push

From your Mac:

```bash
mkdir -p .github/workflows
# Create the file above, then:
git add .github/workflows/build-windows.yml
git commit -m "Add Windows build automation"
git push
```

### Step 3: Monitor the Build

1. Go to your GitHub repository
2. Click on the "Actions" tab
3. You should see the build running
4. Wait for it to complete (usually 5-10 minutes)

### Step 4: Download the Executables

1. Once the build completes, click on the workflow run
2. Scroll down to "Artifacts"
3. Download "windows-executables.zip"
4. Extract the ZIP file to get your Windows executables

## Usage

### Automatic Builds
Every time you push to `main` or `master` branch, a new build will automatically run.

### Manual Builds
You can manually trigger a build:
1. Go to Actions tab
2. Click "Build Windows Executables"
3. Click "Run workflow"
4. Select branch and click "Run workflow"

### Creating Releases
To create a versioned release:

```bash
# Tag your version
git tag v1.0.0
git push origin v1.0.0
```

This will:
- Trigger the build
- Create a GitHub Release
- Attach the executables to the release
- Users can download from the Releases page

## Troubleshooting

### Build Fails

**Check the logs:**
1. Go to Actions tab
2. Click on the failed workflow
3. Click on the failed job
4. Review the error messages

**Common issues:**
- Missing dependencies in `requirements.txt`
- Syntax errors in the workflow file (must be valid YAML)
- PyInstaller spec file issues

### No Artifacts Available

- Make sure the build completed successfully
- Artifacts are only available for 30 days (configurable)
- Check you're looking at the correct workflow run

## Cost

GitHub Actions is **FREE** for public repositories with unlimited minutes.

For private repositories:
- Free tier: 2,000 minutes/month
- Each build takes ~5-10 minutes
- That's ~200-400 builds/month for free

## Advanced: Release Strategy

### Semantic Versioning

```bash
# Patch release (bug fixes): 1.0.0 -> 1.0.1
git tag v1.0.1 -m "Fix coordinate validation bug"

# Minor release (new features): 1.0.1 -> 1.1.0
git tag v1.1.0 -m "Add arc support"

# Major release (breaking changes): 1.1.0 -> 2.0.0
git tag v2.0.0 -m "New UI with improved workflow"

git push origin --tags
```

### Pre-releases

For beta versions:

```bash
git tag v1.1.0-beta.1 -m "Beta release for testing"
git push origin v1.1.0-beta.1
```

## Benefits of This Approach

✅ **No Windows PC needed** - Build from your Mac
✅ **Automated** - No manual build steps
✅ **Consistent** - Same environment every time
✅ **Version control** - Track what went into each build
✅ **Easy distribution** - Download links for users
✅ **Free** - No cost for public repositories

## Alternative: Build on Multiple Platforms

You can also build for Windows, Mac, and Linux simultaneously:

```yaml
strategy:
  matrix:
    os: [windows-latest, macos-latest, ubuntu-latest]
runs-on: ${{ matrix.os }}
```

This creates executables for all three platforms automatically!

## Next Steps

1. Set up the workflow using this guide
2. Push to GitHub and verify the build works
3. Create your first release tag
4. Share the Release page URL with Windows users
5. They can download the latest version anytime

## Testing the Windows Build

Since you're on Mac, you can test using:
1. **Windows VM** (Parallels, VMware, VirtualBox)
2. **Remote Windows PC** (friend, colleague, remote desktop)
3. **Wine** (might work, but not recommended for testing)

The best option is to have at least one Windows user test the executables before distributing widely.

