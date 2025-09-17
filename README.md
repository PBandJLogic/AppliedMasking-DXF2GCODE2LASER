# DXF2TEMPLATE - Web Version

A Flask web application for viewing, editing, and processing DXF files for laser engraving/cutting.

## Features

- **DXF File Upload**: Load and parse DXF files through a web interface
- **Interactive Visualization**: View DXF geometry with matplotlib plots
- **Origin Adjustment**: Set X/Y offsets for positioning
- **Element Selection**: Click to select elements for processing
- **Engraving Marking**: Mark elements for engraving (displayed in red)
- **Element Removal**: Remove unwanted elements
- **G-code Export**: Generate G-code for laser engraving/cutting
- **Statistics**: Real-time statistics of elements and modifications

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:8080
```

## Usage

1. **Load DXF File**: Click "Load DXF File" and select a .dxf file
2. **Adjust Origin**: Enter X and Y offset values and click "Apply Offset"
3. **Select Elements**: Click on elements in the plot to select them
4. **Mark for Engraving**: Click "Mark for Engraving" to mark selected elements (they'll turn red)
5. **Remove Elements**: Click "Remove Elements" to remove selected elements
6. **Export G-code**: Click "Export G-code" to download the generated G-code file

## Supported DXF Elements

- **Lines**: Individual line segments
- **Circles**: Circular geometry
- **Polylines**: Connected line segments
- **Blocks/Inserts**: Complex geometry with transformations

## G-code Settings

The application includes configurable G-code settings:
- Laser power (0-255)
- Cutting Z height
- Feedrate (mm/min)
- Workspace dimensions
- Custom preamble and postscript

## File Structure

```
DXF2TEMPLATE/
├── app.py                 # Main Flask application
├── dxf2template.py        # Original desktop GUI version
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Web interface template
└── README.md             # This file
```

## For Replit Deployment

This Flask application is designed to work on Replit:

1. Upload all files to your Replit project
2. Replit will automatically install dependencies from `requirements.txt`
3. Run the application - it will start on the default Replit port
4. The web interface will be available at your Replit URL

## Technical Details

- **Backend**: Flask with matplotlib for plotting
- **Frontend**: HTML/CSS/JavaScript with responsive design
- **DXF Processing**: ezdxf library for DXF file parsing
- **Plot Generation**: matplotlib with base64 encoding for web display
- **File Handling**: Temporary file processing for DXF uploads

## Browser Compatibility

- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge

## Notes

- Maximum file size: 16MB
- Supported DXF versions: R12, R2000, R2004, R2007, R2010, R2013, R2018
- The web version maintains the same functionality as the desktop version
- All processing is done server-side for security and performance
