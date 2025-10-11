# Gcode2Laser User Guide

## Overview

**Gcode2Laser** is a precision G-code adjustment and laser engraving control application. It corrects for workpiece misalignment using a 2-point reference system, allowing you to accurately engrave on parts that aren't perfectly positioned on your laser bed.

## Key Features

- **2-Point Reference Alignment**: Correct for translation and rotation errors
- **Real-time G-code Adjustment**: Apply transformations to compensate for misalignment
- **GRBL Integration**: Direct control of laser via serial connection
- **Live Position Tracking**: See laser position update in real-time
- **Single-Step Mode**: Debug G-code execution line by line
- **Path Visualization**: Plot original and adjusted toolpaths
- **Emergency Stop**: Immediately halt operations for safety

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
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python Gcode2Laser.py
   ```

## Understanding the 2-Point Reference System

### What is it?
The 2-point reference system uses two precisely known locations on your G-code design to correct for workpiece misalignment. These points:
- Must lie on the circumference of a circle (for proper rotation calculation)
- Point 1 should be to the LEFT of Point 2
- Are typically tooling holes, corners, or other easily identifiable features

### How it Works
1. **Expected Points**: The ideal XY coordinates from your CAD design
2. **Actual Points**: The measured XY coordinates on your physical workpiece
3. **Transformation**: The app calculates rotation and translation needed to map expected → actual

## Workflow

### 1. Connect to GRBL

**Panel: GRBL Connection**

1. Select your serial port from the dropdown
2. Click **"Connect"**
3. Wait for connection confirmation
4. Status will show **"Connected to GRBL"**

### 2. Load G-code File

**Panel: File Operations**

1. Click **"Load G-code File"**
2. Select your `.nc` or `.gcode` file
3. The app will:
   - Parse reference points from comments (if present)
   - Display original toolpath in green (G0) and red (G1)
   - Show reference points in the left panel

### 3. Set Reference Points

**Panel: Reference Points**

The app shows two reference points with Expected and Actual coordinates.

#### Using the GUI:

1. **Check Expected Values**: Verify they match your CAD design
   - If loading a file with embedded reference points, these auto-populate
   - Otherwise, manually enter the expected X,Y coordinates

2. **Measure Actual Values**: Use laser jogging to find actual positions
   - Use **Jog buttons** to move laser (X+/X-/Y+/Y-/Z+/Z-)
   - Adjust **Step** size (default 1.0mm) for fine control
   - Navigate to reference point 1 location on workpiece
   - Click **"Set"** button next to Point 1 Actual to capture current position
   - Repeat for reference point 2

3. **Verify Positions**: 
   - **"Goto"** buttons will move laser to expected coordinates
   - Use this to verify your reference points are correct

### 4. Adjust G-code

**Panel: File Operations**

1. Click **"Adjust G-code"**
2. Review the **Calculation Results** display showing:
   - Translation values (X, Y in mm)
   - Rotation angle (in degrees)
   - Scale factor (for verification)
   - Validation error (should be ≤0.01mm for good alignment)
3. The adjusted toolpath appears in blue (G0) and orange (G1)
4. Use **"Show Original G-code"** checkbox to toggle original path visibility

### 5. Save Adjusted G-code (Optional)

**Panel: File Operations**

1. Click **"Save Adjusted G-code"**
2. Choose save location
3. Filename auto-includes timestamp: `[originalname]_adjusted_YYYYMMDD_HHMMSS.nc`
4. Saved file includes:
   - Updated reference points (set to actual values)
   - All transformed G-code coordinates
   - All G0 rapid positioning moves preserved

### 6. Run G-code

**Panel: Laser Job Controls**

#### Normal Streaming Mode:
1. Click **"Run"** button
2. Confirm the safety checklist dialog
3. G-code streams continuously to GRBL
4. Progress window shows:
   - Current line number
   - Lines sent / total lines
   - Real-time laser position on plot

#### Single-Step Mode (for debugging):
1. Click **"Step"** button
2. First command executes, then pauses
3. Click **"Next"** to execute each subsequent command
4. Great for:
   - Verifying alignment before full run
   - Debugging unexpected behavior
   - Learning what each G-code command does

#### Emergency Stop:
- Click **"STOP"** at any time to:
  - Send `Ctrl-X` to GRBL (immediate halt)
  - Turn off laser (`M5`)
  - Clear GRBL buffer
  - Stop streaming

## GUI Panels Reference

### Left Panel

#### GRBL Connection
- **Port Selector**: Choose serial port
- **Connect/Disconnect**: Toggle connection
- **Status**: Current connection state

#### File Operations
- **Load G-code File**: Import G-code
- **Adjust G-code**: Apply transformation
- **Save Adjusted G-code**: Export corrected file

#### Reference Points
Shows 2 reference points:
- **Pt1/Pt2 Label**: Point identifier
- **Exp**: Expected X,Y coordinates (from design)
- **Act**: Actual X,Y coordinates (measured on workpiece)
- **Goto**: Move laser to expected position
- **Set**: Capture current position as actual

#### Laser Jog Controls
- **Jog Buttons**: Move laser (X+/X-/Y+/Y-/Z+/Z-)
- **Step**: Distance per jog (mm)
- **Set G54 Origin**: Set current position as work origin (G10 L20 P1)
- **Home**: Return to machine home
- **Go Home**: Return to work origin (0,0)
- **Laser ON/OFF**: Toggle laser (M3/M5 at 10% power)
- **Clear Errors**: Reset GRBL alarm state

#### Laser Job Controls
- **Run**: Stream entire G-code
- **Step**: Enable single-step mode
- **Next**: Execute next line (in single-step)
- **STOP**: Emergency stop (red button)

#### Position Display
- **MPos**: Machine position (absolute)
- **WPos**: Work position (relative to G54 origin)
- Updates in real-time during jogging and execution

#### Calculation Results
Shows transformation math after "Adjust G-code":
- Reference point values
- Translation vector
- Rotation angle
- Scale factor
- Validation results

### Right Panel

#### Plot Controls
- **Show Original G-code**: Checkbox to toggle original path display
- **Navigation Toolbar**: Zoom, pan, reset view

#### Toolpath Visualization
- **Green lines**: Rapid positioning moves (G0) - original
- **Red lines**: Cutting moves (G1/G2/G3) - original
- **Blue lines**: Rapid positioning moves (G0) - adjusted
- **Orange lines**: Cutting moves (G1/G2/G3) - adjusted
- **Purple line**: Current execution path (during run)
- **Yellow circle**: Current laser position

## G-code Comment Format

To embed reference points in your G-code files for automatic loading:

```gcode
; reference_point1 = (-79.2465, -21.234)
; reference_point2 = (79.2465, -21.234)
```

Place these comments near the top of your file. The app will:
- Parse these values automatically
- Set them as expected reference points
- Initialize actual points to match (you'll update actual via jogging)

## Tips and Best Practices

### Reference Point Selection
- **Choose points far apart**: Increases accuracy of rotation calculation
- **Use tooling holes**: Provide precise, repeatable locations
- **On circle circumference**: Ensures proper 2-point transformation math
- **Easy to locate**: Corners, holes, or engraved marks work well

### Workflow Tips
1. **Test first**: Use single-step mode on first run
2. **Verify scale**: Scale factor should be very close to 1.000
3. **Check validation error**: Should be ≤0.01mm for good alignment
4. **Low power testing**: Use laser ON/OFF at 10% to verify path before full power
5. **Save settings**: Save adjusted G-code with updated reference points for repeatability

### Troubleshooting

**Problem**: Large validation error (>0.01mm)
- **Solution**: Re-measure actual reference points carefully

**Problem**: Rotation angle is very large (>5°)
- **Solution**: Verify reference points are correct, may indicate measurement error

**Problem**: Scale factor not close to 1.0
- **Solution**: Check that expected and actual units match (both should be mm)

**Problem**: G0 commands missing in saved file
- **Solution**: Ensure you're using the latest version of Gcode2Laser.py

**Problem**: Reference points not updating in saved file
- **Solution**: This is a known issue - verify actual values are displayed correctly in GUI before adjusting

**Problem**: GRBL not responding
- **Solutions**:
  - Click "Clear Errors"
  - Disconnect and reconnect
  - Check USB cable connection
  - Restart GRBL controller

**Problem**: Laser won't turn on/off
- **Solution**: Verify GRBL laser mode setting: `$32=1`

## Safety Reminders

⚠️ **IMPORTANT SAFETY NOTES** ⚠️

1. **Always wear laser safety glasses** appropriate for your laser wavelength
2. **Never leave laser unattended** during operation
3. **Test with low power first** (10% via Laser ON/OFF button)
4. **Keep fire extinguisher nearby**
5. **Ensure proper ventilation** for fumes/smoke
6. **Use the STOP button** if anything looks wrong
7. **Verify work area is clear** before running G-code
8. **Double-check workpiece position** won't cause collisions

## Advanced Features

### Manual G-code Entry
- Located below Laser Job Controls
- Enter any G-code command
- Click "Execute" to send immediately
- Useful for:
  - Custom positioning commands
  - GRBL configuration ($$ commands)
  - Testing specific moves

### Keyboard Shortcuts
- Currently no keyboard shortcuts implemented
- Future enhancement opportunity

### Custom GRBL Settings
The app sets `$10=3` (status report mask) automatically for position tracking.

## Technical Details

### Transformation Method
Uses 2-point vector-based transformation:
1. Calculate vectors between reference points (expected and actual)
2. Compute rotation angle from vector orientations
3. Compute scale from vector lengths (should be ~1.0)
4. Compute translation to align rotated expected point 1 with actual point 1
5. Apply: `transformed_point = rotation(expected_point) + translation`

### GRBL Streaming Protocol
- Sends commands continuously to keep GRBL buffer full
- Monitors `ok` responses to manage flow control
- Requests position updates every 100ms during execution
- Throttles plot updates to maintain GUI responsiveness

### Coordinate Systems
- **Machine Coordinates (MPos)**: Absolute position from home
- **Work Coordinates (WPos)**: Relative to G54 work origin
- **Relationship**: `WPos = MPos - WCO` (Work Coordinate Offset)

## Support and Development

### File Issues
If you encounter bugs or have feature requests, document:
- Steps to reproduce
- Expected vs actual behavior
- G-code file (if relevant)
- GRBL version and settings

### Version History
See git commit history for detailed changes.

### License
See LICENSE file in repository.

---

**Gcode2Laser** - Precision laser engraving through intelligent G-code transformation

