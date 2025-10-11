# DXF2Gcode User Guide

## Overview

**DXF2Gcode** is an interactive DXF to G-code conversion tool specifically designed for laser engraving. It allows you to load CAD drawings (DXF files), visualize the design, selectively choose which elements to engrave or remove, adjust positioning, and generate optimized G-code for your laser engraver.

## Key Features

- **Interactive DXF Visualization**: View your CAD designs with zoom and pan
- **Element Selection**: Click to select/deselect individual elements for engraving
- **Smart Element Removal**: Remove unwanted elements (construction lines, dimensions, etc.)
- **Origin Adjustment**: Set custom origin points for precise positioning
- **Workspace Validation**: Automatic detection and handling of out-of-bounds elements
- **Toolpath Optimization**: Minimizes travel time between cuts
- **Unit Conversion**: Automatic handling of mm, inches, and other DXF units
- **Reference Point Embedding**: Add alignment points for downstream correction
- **G-code Preview**: Review generated toolpaths before saving
- **Settings Management**: Save and load machine-specific configurations

## Installation

### Requirements
- Python 3.8 or higher
- Virtual environment (recommended)

### Setup

1. **Clone or download the repository**
2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Mac/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install matplotlib numpy ezdxf Pillow
   ```

4. **Run the application:**
   ```bash
   python DXF2Gcode.py
   ```

## Workflow

### 1. Load DXF File

**Button: "Load DXF"**

1. Click **"Load DXF"** button
2. Select your `.dxf` file
3. The application will:
   - Parse all geometric elements (lines, arcs, circles, polylines, splines)
   - Auto-detect units from DXF file
   - Display the design in the main canvas
   - Color all elements in blue (ready for engraving)

**Unit Detection:**
- DXF files may specify units (mm, inches, feet, etc.)
- DXF2Gcode automatically converts everything to millimeters
- If no units specified, assumes millimeters

### 2. Review and Select Elements

**Canvas Interaction:**

The canvas displays your DXF design with color coding:
- **Blue**: Elements marked for engraving
- **Red**: Elements marked for removal (won't be engraved)
- **Yellow**: Elements clipped (outside workspace boundaries)

**Element Selection:**
1. **Click on any element** to select it
   - Selected elements show a small circle at their center
   - Element info appears in the info panel
   
2. **Mark for Engraving** (default):
   - Click **"Mark for Engraving"** button
   - Element turns blue
   
3. **Mark for Removal**:
   - Click **"Mark for Removal"** button
   - Element turns red and won't be included in G-code

4. **Clear Selection**:
   - Click **"Clear Selection"** to deselect all

**Tip**: Use removal to exclude:
- Construction lines
- Dimension annotations
- Reference geometry
- Hidden layer elements

### 3. Set Origin (Optional)

**Purpose**: Define where (0,0) should be on your workpiece

**Button: "Set Origin"**

1. Click **"Set Origin"**
2. Click on the canvas at desired origin point
3. All coordinates will be adjusted relative to this point
4. Visual crosshair shows current origin

**Common Origin Points:**
- Bottom-left corner (most common)
- Center of design
- Specific hole or feature location
- Edge of workpiece

**Button: "Reset Origin"**
- Returns origin to (0,0) in original DXF coordinates

### 4. Add Reference Points (Optional)

**Purpose**: Embed reference points for alignment in Gcode2Laser

**Button: "Add Reference Points"**

Reference points help correct for workpiece misalignment:
1. Click **"Add Reference Points"**
2. Click on TWO points in your design
   - Points should be on a circle's circumference
   - Point 1 should be LEFT of Point 2
   - Far apart is better for accuracy
3. Points are embedded as comments in G-code header:
   ```gcode
   ; reference_point1 = (-79.2465, -21.234)
   ; reference_point2 = (79.2465, -21.234)
   ```

**Best Practices:**
- Use tooling holes when available
- Choose easily identifiable features
- Ensure points will be accessible for measurement

**Button: "Clear Reference Points"**
- Removes reference points if you want to start over

### 5. Check Workspace Validation

**Panel: "Clipped Elements"**

Shows elements that fall outside your machine's workspace:
- Red count indicates how many elements are clipped
- These elements will be automatically excluded from G-code
- Review and adjust origin if needed to fit design

**Workspace Limits** (default):
- X: 0 to 794 mm
- Y: 0 to 394 mm
- Configured in settings (adjustable for your machine)

### 6. Generate G-code

**Button: "Generate G-code"**

1. Click **"Generate G-code"**
2. G-code preview window appears showing:
   - Complete G-code text
   - Statistics (total moves, rapid moves, cut moves)
   - Estimated dimensions

**G-code Structure:**
```gcode
; Preamble (machine setup)
G21 ; Set units to millimeters
G90 ; Absolute positioning
M4 S0 ; Laser on at zero power

; Reference points (if added)
; reference_point1 = (x, y)
; reference_point2 = (x, y)

; Toolpath commands
G0 X... Y... ; Rapid moves (laser off)
G1 X... Y... F1500 ; Cut moves (laser on)

; Postscript (shutdown)
M5 ; Turn off laser
G0 X0 Y375 ; Move to unload position
```

**Preview Window:**
- Review G-code before saving
- Check for any unexpected movements
- Verify coordinates are within expected range

### 7. Save G-code

**Button: "Save G-code" (in preview window)**

1. Click **"Save G-code"**
2. Choose filename and location
3. File saved with `.nc` extension (standard G-code format)

**Filename Convention:**
- `dxf_gcode_YYYYMMDD_HHMMSS.nc`
- Timestamp prevents accidental overwrites

## GUI Reference

### Left Panel

#### File Operations
- **Load DXF**: Import DXF file
- **Save Settings**: Save current machine settings to JSON
- **Load Settings**: Load previously saved settings

#### Element Marking
- **Mark for Engraving**: Include selected element in G-code (blue)
- **Mark for Removal**: Exclude selected element from G-code (red)
- **Clear Selection**: Deselect all elements

#### Transform
- **Set Origin**: Click to set new origin point on canvas
- **Reset Origin**: Return to original DXF coordinates
- **Undo Last Action**: Revert last change (up to 20 steps)

#### Reference Points
- **Add Reference Points**: Click twice on canvas to set alignment points
- **Clear Reference Points**: Remove reference points

#### Generate
- **Generate G-code**: Create G-code and show preview window
- **Show Statistics**: Display element count and workspace info

#### Info Panel
Shows information about selected element:
- Element ID
- Geometry type (LINE, ARC, CIRCLE, etc.)
- Center coordinates
- Radius (for circles/arcs)
- Current state (Engraved/Removed)

#### Clipped Elements
- Shows count of elements outside workspace
- Auto-updated as you transform the design

### Right Panel (Canvas)

#### Navigation
- **Zoom**: Mouse wheel or toolbar zoom buttons
- **Pan**: Click and drag to move view
- **Reset View**: Home button on toolbar
- **Save Image**: Export current view as PNG

#### Display
- Blue elements: Marked for engraving
- Red elements: Marked for removal
- Yellow elements: Clipped (out of bounds)
- Green circle: Selected element
- Red crosshair: Current origin (if set)
- Green "X" marks: Reference points (if set)

## Settings Management

### Save Settings

**Button: "Save Settings"**

Saves current configuration to JSON file:
- Machine workspace limits
- G-code preamble/postscript
- Laser power settings
- Feed rates
- Coordinate system settings (WPos/MPos)

**Default file**: `settings.json`

### Load Settings

**Button: "Load Settings"**

Loads previously saved configuration:
- Restores all machine parameters
- Does not affect current DXF file or selections

### Settings File Format

```json
{
  "preamble": "G21 ; Set units to millimeters\n...",
  "postscript": "M5 ; Turn off laser\n...",
  "laser_power": 1000,
  "cutting_z": -30,
  "feedrate": 1500,
  "max_travel_x": 794.0,
  "max_travel_y": 394.0,
  "wpos_home_x": -519.0,
  "wpos_home_y": -396.1,
  "optimize_toolpath": true,
  "raise_laser_between_paths": false
}
```

## Advanced Features

### Toolpath Optimization

**Setting**: `optimize_toolpath` (default: true)

When enabled:
- Minimizes total travel distance
- Finds nearest uncut element for next move
- Can significantly reduce job time
- Especially helpful for designs with many disconnected elements

**Trade-offs:**
- Optimized path may not follow logical design order
- May be harder to predict tool movement visually

### Raise Laser Between Paths

**Setting**: `raise_laser_between_paths` (default: false)

When enabled:
- Raises Z-axis during rapid moves between cuts
- Prevents accidental marking during rapid moves
- Slower but safer for sensitive materials

When disabled:
- Keeps Z-axis constant
- Faster job execution
- Relies on laser power control (M4/M5) for safety

### Unit Conversion

**Automatic Detection:**
DXF2Gcode automatically detects and converts DXF units:
- Inches → millimeters (×25.4)
- Feet → millimeters (×304.8)
- Centimeters → millimeters (×10)
- Other units supported via ezdxf library

**Override:**
If auto-detection fails, you can manually specify units in DXF file metadata.

### Coordinate Systems

**Machine Position (MPos):**
- Absolute coordinates from machine home
- Where machine physically is
- Set by homing cycle

**Work Position (WPos):**
- Relative coordinates from work origin (G54)
- Where you want to cut
- Set by work coordinate system offset

**Conversion:**
- `MPos = WPos + WPos_Home`
- `WPos = MPos - WPos_Home`

DXF2Gcode generates G-code in WPos (G54 system).

## Tips and Best Practices

### DXF File Preparation

1. **Clean up CAD file before export:**
   - Remove dimensions and annotations
   - Delete construction geometry
   - Flatten all layers you want to engrave
   - Close all polylines (no gaps)

2. **Use appropriate units:**
   - Explicitly set units in CAD software
   - Verify scale by checking known dimensions

3. **Organize by layers (optional):**
   - Can help identify what to engrave vs remove
   - Not required, but makes review easier

### Workspace Planning

1. **Test fit before engraving:**
   - Generate G-code
   - Check max X/Y values in preview
   - Verify against actual workpiece size

2. **Origin placement:**
   - Consider clamping locations
   - Ensure entire design stays in positive coordinates
   - Account for material thickness if using Z-moves

3. **Reference points:**
   - Place at known, easily measured features
   - Use tooling holes when available
   - Verify they're in positive coordinates

### G-code Validation

Before running on machine:
1. **Check coordinates** in preview
2. **Verify element count** matches expectations
3. **Review rapid moves** for unexpected behavior
4. **Confirm laser power** setting is appropriate
5. **Test with low power first** (1-10%) to verify path

## Troubleshooting

### Problem: DXF file won't load
**Solutions:**
- Verify file is valid DXF format (AutoCAD R12 or newer)
- Check for corrupted file (try opening in CAD software)
- Ensure file contains geometric entities (not just text/dimensions)
- Try exporting from CAD with different DXF version

### Problem: Elements appear at wrong scale
**Solutions:**
- Check DXF file units in CAD software
- DXF2Gcode should auto-detect, but verify in preview
- If in inches, should see ~25x coordinate values
- Re-export DXF with explicit units set

### Problem: Nothing appears on canvas after loading
**Solutions:**
- Check if design is very small (zoom in)
- Check if design is very large (zoom out / reset view)
- Verify DXF contains visible geometry (not just blocks/text)
- Look at terminal/console for error messages

### Problem: Elements show as clipped (yellow)
**Solutions:**
- Adjust origin to move design into workspace
- Check workspace limits in settings
- Verify design fits within machine travel
- Scale down design if too large for machine

### Problem: Generated G-code missing elements
**Solutions:**
- Check if elements are marked for removal (red)
- Verify elements aren't clipped (yellow)
- Ensure elements are marked for engraving (blue)
- Check element type is supported (LINE, ARC, CIRCLE, POLYLINE, SPLINE)

### Problem: Can't click on small elements
**Solutions:**
- Zoom in on area
- Use "Show Statistics" to verify element exists
- Check if element is behind another element
- Try selecting nearby and using Mark for Engraving/Removal buttons

### Problem: Undo doesn't work as expected
**Solutions:**
- Undo only tracks origin and element marking changes
- File load operations can't be undone
- Maximum 20 undo steps (older changes are lost)
- Reload DXF file to completely reset

## Supported DXF Entities

DXF2Gcode supports the following geometric entities:

### Fully Supported:
- **LINE**: Straight line segments
- **ARC**: Circular arcs (converted to G2/G3)
- **CIRCLE**: Full circles
- **LWPOLYLINE**: Lightweight polylines
- **POLYLINE**: Legacy polylines
- **SPLINE**: Cubic splines (linearized)

### Approximated:
- **ELLIPSE**: Converted to polyline approximation
- **SPLINE**: Linearized into small line segments

### Not Supported:
- TEXT: Text entities (use outline/explode in CAD)
- MTEXT: Multiline text
- DIMENSION: Dimension annotations
- HATCH: Hatch patterns
- BLOCK: Block instances (explode in CAD first)
- IMAGE: Raster images

**Tip**: Explode blocks and convert text to outlines in your CAD software before exporting to DXF.

## G-code Output Format

### Header
```gcode
; G-code generated from DXF file
; Generated: YYYY-MM-DD HH:MM:SS
; Total elements: XX
; reference_point1 = (x, y)  ; If added
; reference_point2 = (x, y)  ; If added
```

### Preamble (customizable)
```gcode
G21 ; Set units to millimeters
G90 ; Absolute positioning
G54 ; Use work coordinate system
G0 X0 Y0 Z-3 ; Go to zero position
M4 S0 ; Laser on at zero power
```

### Toolpath
```gcode
G0 X10.5 Y20.3 ; Rapid move to start
G1 X15.7 Y25.1 F1500 ; Cut move
G2 X20.0 Y30.0 I5.0 J0.0 F1500 ; Arc cut
```

### Postscript (customizable)
```gcode
G0 Z-3 ; Raise Z
M5 ; Turn off laser
G0 X0 Y375 ; Send to unload position
```

## Safety Reminders

⚠️ **IMPORTANT SAFETY NOTES** ⚠️

1. **Always verify G-code** before running on machine
2. **Test with low laser power** first (1-10%)
3. **Check workspace limits** match your machine
4. **Ensure proper ventilation** for laser engraving
5. **Wear laser safety glasses** appropriate for your wavelength
6. **Never leave machine unattended** during operation
7. **Keep fire extinguisher nearby**
8. **Verify material is laser-safe** (no PVC, vinyl, etc.)

## Integration with Gcode2Laser

DXF2Gcode works seamlessly with Gcode2Laser:

1. **Generate G-code** in DXF2Gcode with reference points
2. **Load G-code** in Gcode2Laser
3. **Adjust for workpiece alignment** using reference points
4. **Run on laser** with real-time position tracking

This workflow provides:
- Accurate DXF → G-code conversion
- Compensation for workpiece misalignment
- Real-time laser control and monitoring

## Technical Details

### Coordinate System
- Origin: Bottom-left by default
- Positive X: Right
- Positive Y: Up
- Units: Millimeters

### Precision
- Coordinates: 6 decimal places
- Arc approximation: 0.1mm tolerance
- Spline linearization: 1mm segments

### Arc Conversion
- DXF arcs → G2/G3 commands
- Counter-clockwise: G3
- Clockwise: G2
- IJ format: Relative to arc start point

## Support and Development

### File Issues
Document:
- DXF file (if possible)
- Steps to reproduce
- Expected vs actual behavior
- Python version
- Operating system

### Contributing
- Report bugs via issues
- Suggest features
- Submit pull requests
- Share example DXF files

---

**DXF2Gcode** - Transforming CAD designs into laser-ready G-code

