# DXF2Laser and GCodeAdjuster - Windows Executables

## Overview
These are standalone Windows executables for the DXF2Laser and GCodeAdjuster applications. They include all necessary dependencies and can run on Windows systems without requiring Python installation.

## Files Included
- **DXF2Laser.exe** - DXF to G-code conversion tool
- **GCodeAdjuster.exe** - G-code adjustment and correction tool
- **logo.png** - Application logo (included in both executables)

## System Requirements
- Windows 64-bit (Windows 10 or later recommended)
- No additional software installation required
- At least 100MB free disk space for each executable

## DXF2Laser.exe
### Purpose
Converts DXF (Drawing Exchange Format) files to G-code for laser cutting/engraving.

### Features
- Load DXF files with visual preview
- Convert to G-code with customizable settings
- Preview toolpath with zoom and pan capabilities
- Save G-code files with user-defined names
- Copy G-code to clipboard

### Usage
1. Double-click `DXF2Laser.exe` to launch
2. Click "Load DXF File" to select your DXF file
3. Adjust settings as needed
4. Click "Convert to G-code" to generate G-code
5. Use "Save G-code" to export the file

## GCodeAdjuster.exe
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
1. Double-click `GCodeAdjuster.exe` to launch
2. Click "Load G-code File" to select your G-code file
3. Enter expected target coordinates (left and right points)
4. Enter actual measured coordinates
5. Click "Adjust G-code" to calculate corrections
6. Review the results and validation status
7. Use "Save Adjusted G-code" to export the corrected file

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
- Includes Python 3.13.2 runtime
- Includes matplotlib, numpy, ezdxf, and Pillow libraries
- Target architecture: Windows 64-bit

---
*These executables were created from the DXF2Laser project for easy distribution to Windows users.*
