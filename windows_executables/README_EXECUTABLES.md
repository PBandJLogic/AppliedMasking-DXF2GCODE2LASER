# DXF2Laser and GCodeAdjuster - Executables

## ⚠️ IMPORTANT PLATFORM NOTICE

**The executables in this folder were built on macOS and will ONLY work on Mac.**

**If you need Windows executables:**
1. You MUST build them on a Windows computer - see [WINDOWS_BUILD_INSTRUCTIONS.md](../WINDOWS_BUILD_INSTRUCTIONS.md)
2. OR use GitHub Actions for automated builds - see [GITHUB_ACTIONS_BUILD.md](../GITHUB_ACTIONS_BUILD.md)
3. OR run the Python scripts directly (see main README.md)

**Why?** PyInstaller creates platform-specific binaries. A Mac executable cannot run on Windows, and vice versa.

## Overview
These are standalone executables for the DXF2Laser and GCodeAdjuster applications. They include all necessary dependencies and can run without requiring Python installation.

## Files Included
- **DXF2Laser** (or DXF2Laser.exe on Windows) - DXF to G-code conversion tool
- **GCodeAdjuster** (or GCodeAdjuster.exe on Windows) - G-code adjustment and correction tool
- **logo.png** - Application logo (included in both executables)

## System Requirements
- **macOS**: 64-bit (macOS 10.15 or later recommended) for executables in this folder
- **Windows**: Must build on Windows (see build instructions)
- No additional software installation required
- At least 100MB free disk space for each executable

## DXF2Laser
### Purpose
Converts DXF (Drawing Exchange Format) files to G-code for laser cutting/engraving.

### Features
- Load DXF files with visual preview
- Convert to G-code with customizable settings
- Preview toolpath with zoom and pan capabilities
- Save G-code files with user-defined names
- Copy G-code to clipboard

### Usage
**On Mac:** Double-click `DXF2Laser` to launch
**On Windows:** Double-click `DXF2Laser.exe` to launch (must be built on Windows)

1. Click "Load DXF File" to select your DXF file
2. Adjust settings as needed
3. Click "Convert to G-code" to generate G-code
4. Use "Save G-code" to export the file

## GCodeAdjuster
### Purpose
Adjusts G-code files based on actual vs expected target positions for precision correction.

### Features
- Load G-code files with visual toolpath display
- Input expected and actual target coordinates
- Automatic calculation of translation and rotation corrections
- Real-time validation of coordinate accuracy
- Preview original and adjusted toolpaths
- Export corrected G-code files

### Usage
**On Mac:** Double-click `GCodeAdjuster` to launch
**On Windows:** Double-click `GCodeAdjuster.exe` to launch (must be built on Windows)

1. Click "Load G-code File" to select your G-code file
2. Enter expected target coordinates (left and right points)
3. Enter actual measured coordinates
4. Click "Adjust G-code" to calculate corrections
5. Review the results and validation status
6. Use "Save Adjusted G-code" to export the corrected file

## Important Notes

### Console Output
Both executables include console output for debugging purposes. If you encounter issues:
- Check the console window for error messages
- The console will show file loading progress and validation results

### File Paths
- Use absolute file paths or place files in the same directory as the executable
- Avoid file paths with special characters or spaces when possible

### Performance
- First launch may be slower as the executable extracts embedded files
- Subsequent launches will be faster
- Large G-code files may take time to process and display

## Troubleshooting

### Common Issues
1. **"File not found" errors**: Ensure file paths are correct and files exist
2. **Slow performance**: Close other applications to free up memory
3. **Display issues**: Try running as administrator if GUI elements don't appear

### Error Messages
- Check the console window for detailed error information
- Most errors are related to file access or invalid input data

## Support
For issues or questions about these executables:
1. Check the console output for error details
2. Verify input files are valid DXF or G-code format
3. Ensure coordinate values are numeric and reasonable

## Version Information
- Built with PyInstaller 6.16.0
- Includes Python 3.13 runtime
- Includes matplotlib, numpy, ezdxf, and Pillow libraries
- **Current executables:** macOS 64-bit

## Building for Windows

The executables in this folder were built on macOS. To create Windows executables:

1. **Use a Windows PC** - See [WINDOWS_BUILD_INSTRUCTIONS.md](../WINDOWS_BUILD_INSTRUCTIONS.md)
2. **Use GitHub Actions** - Automated builds for all platforms - See [GITHUB_ACTIONS_BUILD.md](../GITHUB_ACTIONS_BUILD.md)
3. **Use a Windows VM** - Run Windows in Parallels/VMware/VirtualBox on your Mac

You cannot build Windows executables from macOS - PyInstaller only creates executables for the platform it runs on.

---
*These executables were created from the DXF2Laser project for easy distribution.*

