# CircumferenceClean Program Plan

## Overview
Build a standalone program for cleaning circular parts (top/bottom positions) using G2/G3 arc commands with circle fitting based on reference points.

## Architecture

### 1. Main Window Structure
- Tabbed interface with two tabs:
  - **Geometry Definition Tab**: Define cleaning parameters
  - **Main Control Tab**: Jogging, reference point capture, adjustment, and execution

### 2. Geometry Definition Tab Components

**Outer Circle Section:**
- Outer diameter input field
- Cleaning offsets list (comma-separated, e.g., "0, 1, 2, 3")
- Reference points list for top position (X,Y pairs, 3-10 points)
- Reference points list for bottom position (X,Y pairs, 3-10 points)

**Inner Circle Section:**
- Inner diameter input field
- Cleaning offsets list (negative values, e.g., "0, -1, -2, -3")

**G-code Parameters:**
- Laser power (%) input
- Max laser power (full scale) input
- Feed rate input (mm/min)

**Save/Load buttons** for geometry configuration

### 3. Main Control Tab Components

**Position Selection:**
- Radio buttons: Top / Bottom
- Displays appropriate reference points and arc based on selection

**Plot Area:**
- Shows ideal circle arc (blue) based on geometry
- Shows adjusted circle arc (green) after calculation
- Reference point markers with arrows (expected: blue, actual: green)
- Start/stop point markers (draggable on circle)
- Arc segment highlighted between start/stop

**Reference Point Panel:**
- Table showing all reference points for selected position (top/bottom)
- Columns: Point#, Expected X, Expected Y, Actual X, Actual Y
- "Capture" button for each point to record current laser position
- "Goto" button to move laser to expected position

**Jogging Controls:**
- Copy from Gcode2Laser.py: X/Y/Z jog buttons, step size, laser on/off

**GRBL Connection:**
- Copy from Gcode2Laser.py: Port selection, connect/disconnect, status display

**Calculation Results:**
- Show fitted circle center (X, Y)
- Show radius error for each reference point
- Highlight outliers > 0.1mm in red
- RMS error and max error display

**Action Buttons:**
- "Adjust G-code" - Perform circle fitting and generate G-code
- "Run Cleaning" - Execute the generated G-code
- "Stop" - Emergency stop

## Implementation Details

### 4. Circle Fitting Algorithm

Use `scipy.optimize.least_squares` with fixed radius:
```python
def circle_fit_fixed_radius(points, known_radius):
    # Objective: minimize distance from points to circle with known radius
    # Variables: center_x, center_y
    # Constraint: radius = known_radius
    def residuals(center):
        distances = np.sqrt((points[:, 0] - center[0])**2 + (points[:, 1] - center[1])**2)
        return distances - known_radius
    
    initial_center = np.mean(points, axis=0)
    result = least_squares(residuals, initial_center)
    return result.x  # fitted center
```

Apply separately for outer and inner circles based on their reference points.

### 5. G-code Generation Pattern

For each cleaning offset:
1. **First pass (even index)**: G0 to start point at current radius, G2/G3 clockwise arc to stop point
2. **Next pass (odd index)**: G0 to stop point at next radius, G3/G2 counter-clockwise arc to start point
3. Alternate direction each pass to minimize travel moves

**G-code structure:**
```gcode
G21 ; mm mode
G90 ; absolute positioning
M3 S<scaled_power> ; laser on

; For each offset in cleaning_offsets:
G0 X<start_x> Y<start_y> ; rapid to start at radius + offset
G2/G3 X<end_x> Y<end_y> I<i_offset> J<j_offset> F<feedrate> ; arc cleaning

M5 ; laser off
```

Arc parameters calculated from fitted center, radius, start angle, and stop angle.

### 6. Key Files to Reference/Copy

**From Gcode2Laser.py:**
- GRBL connection methods (lines ~2500-3500)
- Serial communication thread
- Jogging controls (lines ~640-720)
- Position capture and display
- Laser on/off controls
- Plot management with matplotlib
- Status monitoring

**New calculations:**
- Circle fitting with scipy
- Arc G-code generation (G2/G3 with I/J offsets)
- Start/stop angle to X/Y conversion
- Draggable plot markers for start/stop adjustment

### 7. Implementation Steps

1. Create CircumferenceClean.py skeleton with Tkinter window
2. Implement Geometry Definition Tab with all input fields
3. Implement Main Control Tab with tabbed interface
4. Copy GRBL connection code from Gcode2Laser.py
5. Copy jogging controls and laser on/off functionality
6. Implement circle fitting algorithm with scipy
7. Implement plot with draggable start/stop markers
8. Implement reference point capture and table display
9. Implement G-code generation for arc cleaning pattern
10. Implement calculation results display with error highlighting
11. Implement G-code execution with streaming
12. Add configuration save/load functionality
13. Testing and refinement

## Key Technical Considerations

- Use `scipy.optimize.least_squares` for robust circle fitting
- Validate reference points form proper arc coverage
- Handle both G2 (clockwise) and G3 (counter-clockwise) commands
- Calculate I/J offsets relative to current position for arc commands
- Implement draggable matplotlib artists for start/stop point adjustment
- Maintain separate reference point lists for top/bottom positions
- Stream G-code with proper 'ok' response handling from GRBL

## TODO List

- [ ] Create CircumferenceClean.py with basic Tkinter window and tab structure
- [ ] Implement Geometry Definition Tab with all input fields and validation
- [ ] Implement Main Control Tab UI layout with plot area and controls
- [ ] Copy and adapt GRBL connection code from Gcode2Laser.py
- [ ] Copy jogging controls and laser on/off functionality
- [ ] Implement matplotlib plot with circle arc visualization
- [ ] Add draggable start/stop point markers on plot
- [ ] Implement reference point table with capture/goto buttons
- [ ] Implement scipy-based circle fitting with fixed radius
- [ ] Implement G2/G3 arc-based G-code generation
- [ ] Implement calculation results with error highlighting
- [ ] Implement G-code streaming and execution control
- [ ] Add configuration save/load functionality
- [ ] Test with actual GRBL controller and refine
