# DXF2TEMPLATE - Laser Engraving G-code Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A web application that converts DXF files to G-code for laser engraving machines. All elements are automatically processed for engraving with configurable settings.

## Features

- **DXF File Processing**: Load and process DXF files with automatic geometry extraction
- **Automatic Element Processing**: All elements are automatically marked for engraving
- **Origin Offset**: Adjust the origin position with X,Y offsets
- **G-code Generation**: Generate G-code with configurable settings:
  - Laser power control
  - Cutting depth (Z-axis)
  - Feedrate settings
  - Workspace limits
  - Custom preamble and postscript
- **Visual Preview**: Interactive plot showing original and processed elements
- **G-code Preview**: Text and graphical preview of generated G-code

## Quick Start

1. **Load DXF File**: Click "Choose File" and select your DXF file
2. **Adjust Origin** (optional): Set X,Y offsets if needed
3. **Configure Settings**: Adjust laser power, feedrate, and other G-code settings
4. **Preview G-code**: Click "Preview G-code" to see the generated code
5. **Export**: Download the G-code file for your laser engraver

## G-code Settings

- **Laser Power**: Power level for the laser (0-100%)
- **Cutting Z**: Z-axis depth for cutting/engraving
- **Feedrate**: Movement speed in mm/min
- **Max Workspace X/Y**: Maximum workspace dimensions
- **Preamble**: Custom G-code commands before the main program
- **Postscript**: Custom G-code commands after the main program

## Color Legend

- **Blue**: Original DXF elements
- **Red**: Elements marked for engraving

## Technical Details

- **Backend**: Flask (Python)
- **Frontend**: HTML/CSS/JavaScript
- **DXF Processing**: ezdxf library
- **Plotting**: Matplotlib
- **G-code Generation**: Custom implementation with workspace clamping

## Installation Options

### Option 1: Desktop Applications (Standalone Executables)

**Windows Users:**
- Download pre-built Windows executables (see Releases page)
- Or build from source on Windows - see [WINDOWS_BUILD_INSTRUCTIONS.md](WINDOWS_BUILD_INSTRUCTIONS.md)
- **Note:** Executables are platform-specific. Mac-built executables will NOT work on Windows

**Mac Users:**
- Build from source on Mac using PyInstaller (see build instructions)

**Automated Builds:**
- Set up GitHub Actions for automatic Windows/Mac builds - see [GITHUB_ACTIONS_BUILD.md](GITHUB_ACTIONS_BUILD.md)

### Option 2: Web Application (Replit)

This application is configured for Replit deployment with the following files:
- `main.py`: Entry point for Replit
- `app.py`: Main Flask application
- `requirements.txt`: Python dependencies
- `.replit`: Replit configuration
- `replit.nix`: Replit environment setup

See [DEPLOYMENT.md](DEPLOYMENT.md) for web deployment instructions.

### Option 3: Run from Source

```bash
# Clone the repository
git clone [your-repo-url]
cd DXF2LASER

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run DXF2Laser GUI
python dxf2laser.py

# Or run G-code Adjuster GUI
python gcode_adjuster.py

# Or run web version
python main.py
```

## Usage Notes

- All elements in the DXF file are automatically processed
- G-code coordinates are clamped to the specified workspace limits
- The application maintains equal aspect ratio for accurate geometry representation
- Offset adjustments automatically update the plot scale to show all elements

## File Structure

```
├── main.py              # Replit entry point
├── app.py               # Main Flask application
├── requirements.txt     # Python dependencies
├── .replit             # Replit configuration
├── replit.nix          # Replit environment
├── .gitignore          # Git ignore file
├── templates/
│   └── index.html      # Web interface
├── LICENSE             # MIT License
└── README.md           # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you find this project helpful, please consider giving it a star! ⭐