# Cross-Platform Development Setup

This document explains the cross-platform development setup for the AAI project, which supports both macOS and Windows development with shared source code.

## Directory Structure

```
AAI/
├── venv/              # macOS virtual environment for Windows builds
├── venv_mac/          # macOS virtual environment for development
├── DXF2Gcode.py       # Main DXF to G-code converter
├── Gcode2Laser.py     # G-code to laser control application
├── requirements.txt   # Python dependencies
└── README_CROSSDEVEL.md
```

## Virtual Environment Setup

### macOS Development Environment (`venv_mac/`)
- **Purpose**: Regular development and testing on macOS
- **Platform**: Native macOS virtual environment
- **Activation**: `source venv_mac/bin/activate`
- **Usage**: For running Python scripts during development

### Windows Build Environment (`venv/`)
- **Purpose**: Building Windows executables using PyInstaller
- **Platform**: macOS virtual environment with cross-compilation capabilities
- **Activation**: `source venv/bin/activate`
- **Usage**: For creating Windows `.exe` files from macOS

## Development Workflow

### On macOS

#### For Development and Testing:
```bash
# Activate macOS development environment
source venv_mac/bin/activate

# Run applications
python DXF2Gcode.py
python Gcode2Laser.py
```

#### For Building Windows Executables:
```bash
# Activate Windows build environment
source venv/bin/activate

# Build Windows executables
pyinstaller --onefile DXF2Gcode.py
pyinstaller --onefile Gcode2Laser.py

# Executables will be created in dist/ directory
```

### On Windows PC

When working on Windows, create a Windows-specific virtual environment:

```cmd
# Create Windows virtual environment
python -m venv venv_windows

# Activate Windows environment
venv_windows\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run applications
python DXF2Gcode.py
python Gcode2Laser.py
```

## Dependencies

All environments use the same `requirements.txt` file:
- matplotlib
- numpy
- ezdxf
- Pillow
- pyserial
- pyinstaller (for build environment only)

## Git Synchronization

- **Source code**: Synchronized between macOS and Windows via git
- **Virtual environments**: NOT synchronized (each platform creates its own)
- **Build artifacts**: `dist/` directory contains built executables

## Best Practices

1. **Always activate the correct virtual environment** for your task
2. **Use `venv_mac` for development** on macOS
3. **Use `venv` for building Windows executables** on macOS
4. **Create separate virtual environments** on Windows PC
5. **Don't commit virtual environments** to git (they're in `.gitignore`)
6. **Test on both platforms** before releasing

## Troubleshooting

### Virtual Environment Issues
- **Problem**: Virtual environment won't activate
- **Solution**: Ensure you're using the correct activation command for your platform

### Cross-Platform Compatibility
- **Problem**: Code works on one platform but not the other
- **Solution**: Test thoroughly on both platforms and check for platform-specific dependencies

### Build Issues
- **Problem**: Windows executables won't build
- **Solution**: Ensure PyInstaller is installed in the build environment (`venv`)

## File Synchronization

This setup is designed to work with cloud storage (OneDrive) that syncs between macOS and Windows:

- **Source files**: Automatically synchronized
- **Virtual environments**: Platform-specific, not synchronized
- **Build outputs**: Can be synchronized if needed

## Notes

- The `venv/` directory is optimized for cross-compilation to Windows
- The `venv_mac/` directory is optimized for native macOS development
- Both environments contain the same core dependencies but may have different build tools
- PyInstaller on macOS can create Windows executables without needing a Windows machine
