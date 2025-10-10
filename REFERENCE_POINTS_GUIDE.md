# Reference Points Feature Guide

## Overview

The G-code Adjuster now supports automatic loading of reference points from G-code comments. This allows for both 2-point (circle-based) and 3-point (planar) transformations.

## G-code Comment Format

Add these comments to the beginning of your G-code file:

### For 2-Point Transformation (Circle-based)

```gcode
; number_of_reference_points = 2
; reference_point1 = (-79.2465, -21.234)
; reference_point2 = ( 79.2465, -21.234)
```

**Use when:** Your reference points are on the circumference of a circle, with point 1 on the left and point 2 on the right.

### For 3-Point Transformation (Planar)

```gcode
; number_of_reference_points = 3
; reference_point1 = (-79.2465, -21.234)
; reference_point2 = ( 79.2465, -21.234)
; reference_point3 = (  0.0000,  50.000)
```

**Use when:** Your reference points are on a plane (not necessarily on a circle).

## How It Works

### 1. Load G-code File

When you load a G-code file with reference point comments:
- The application automatically detects the number of reference points
- Expected coordinates are extracted from the comments
- Actual coordinates are initialized to match the expected values
- The GUI updates to show the correct number of reference points

### 2. Reference Points Display

The left panel will show:
- **Number of Reference Points**: 2 or 3
- **For each point:**
  - **Expected X, Y** (orange text): The ideal coordinates from G-code comments
  - **Actual X, Y** (black text): The measured coordinates (editable)

### 3. Update Actual Coordinates

After measuring your physical reference points:
1. Update the "Actual X, Y" values for each point
2. The expected values remain as loaded from the G-code
3. Click "Adjust G-code" to calculate the transformation

### 4. Transformation Calculation

**2-Point Mode:**
- Assumes points are on a circle
- Calculates translation and rotation
- Validates that actual points maintain expected radius
- Shows error metrics for each point

**3-Point Mode:**
- Uses affine transformation (translation + rotation + optional scaling)
- Calculates optimal transformation using SVD (Singular Value Decomposition)
- Shows error for all three points
- Displays average and maximum errors

## Example Workflow

### Scenario: 2-Point Circle Reference

```gcode
; number_of_reference_points = 2
; reference_point1 = (-222.959, -22.250)
; reference_point2 = ( 222.959, -22.250)
; 
; (rest of G-code)
G0 X0 Y0
G1 X10 Y10
...
```

1. Load this G-code file
2. GUI shows 2 reference points:
   - Point 1: Expected (-222.959, -22.250)
   - Point 2: Expected (222.959, -22.250)
3. Measure actual positions and update:
   - Point 1: Actual (-223.150, -22.100)
   - Point 2: Actual (222.800, -22.300)
4. Click "Adjust G-code"
5. View transformation results and error metrics
6. Save adjusted G-code

### Scenario: 3-Point Planar Reference

```gcode
; number_of_reference_points = 3
; reference_point1 = (-100.000, -50.000)
; reference_point2 = ( 100.000, -50.000)
; reference_point3 = (   0.000,  50.000)
;
; (rest of G-code)
...
```

1. Load this G-code file
2. GUI shows 3 reference points (triangle pattern)
3. Measure and update actual positions for all three points
4. Click "Adjust G-code"
5. Algorithm calculates best-fit transformation
6. View results showing error for each point plus summary statistics

## Technical Details

### 2-Point Algorithm
- **Method**: Circle-based transformation
- **Assumptions**: Points lie on a circle centered at origin
- **Calculates**: 
  - Circle center position
  - Rotation angle to align chord
- **Best for**: Cylindrical parts, carousel systems

### 3-Point Algorithm
- **Method**: Affine transformation using SVD
- **Process**:
  1. Calculate centroids of expected and actual points
  2. Center both sets of points
  3. Use SVD to find optimal rotation matrix
  4. Calculate translation vector
  5. Optionally calculate scale factor
- **Best for**: Flat parts, general planar transformations

## Comment Syntax Rules

- Comments must start with semicolon (`;`)
- Keywords are case-insensitive
- Whitespace is flexible
- Coordinate format: `(x, y)` with optional spaces
- Numbers can be positive, negative, with or without decimals

**Valid examples:**
```gcode
; NUMBER_OF_REFERENCE_POINTS = 2
; number_of_reference_points=2
;number_of_reference_points = 2

; REFERENCE_POINT1 = (-79.2465, -21.234)
; reference_point1=(-79.2465,-21.234)
;reference_point1 = ( -79.2465 , -21.234 )
```

## Error Interpretation

### Validation Status

**✓ Valid** - Error ≤ 0.01mm
- Transformation is accurate
- Safe to proceed

**✗ Error > 0.01mm** - Error exceeds tolerance
- Check actual coordinate measurements
- Verify reference point positions
- Consider re-measuring or adjusting tolerance

### Common Issues

1. **Large errors in 2-point mode**
   - Points may not be on the expected circle
   - Consider using 3-point mode instead

2. **Large errors in 3-point mode**
   - Measurement errors in actual coordinates
   - Non-planar deformation (warping)
   - Points may be nearly collinear (bad geometry)

3. **No reference points detected**
   - Check comment syntax
   - Verify comments are at start of file
   - Manually enter coordinates using old method

## Backwards Compatibility

If no reference point comments are found:
- GUI shows traditional "Left Target" and "Right Target" interface
- Works exactly as before
- 2-point circle-based transformation

## Tips for Best Results

### Reference Point Placement

**2-Point Mode:**
- Place points far apart (maximize distance)
- Keep points at same Y coordinate if possible
- Ensure points are accurately on circle perimeter

**3-Point Mode:**
- Avoid collinear points (don't place in a straight line)
- Form a large triangle for better accuracy
- Distribute points around the work area

### Measurement

- Use precise measurement tools (dial indicator, edge finder)
- Measure multiple times and average
- Account for tool offset/diameter
- Verify machine repeatability first

## Integration with DXF2Laser

To generate G-code with reference points:

1. **Option A**: Manually add comments to generated G-code
```gcode
; number_of_reference_points = 2
; reference_point1 = (-222.959, -22.250)
; reference_point2 = ( 222.959, -22.250)
```

2. **Option B**: Modify DXF2Laser to include reference points
   - Add reference point layer in DXF
   - Parse and output as comments
   - (Feature enhancement for future)

## Example G-code Template

```gcode
; ===================================
; Reference Points for Adjustment
; ===================================
; number_of_reference_points = 2
; reference_point1 = (-222.959, -22.250)
; reference_point2 = ( 222.959, -22.250)
; ===================================
; Generated: 2025-10-10
; ===================================

G21 ; Set units to mm
G90 ; Absolute positioning
G0 Z5.000 ; Raise to safe height
G0 X0 Y0 ; Move to origin

; (Your engraving paths here)
G1 X10 Y10 F1000
G1 X20 Y10
...

M5 ; Laser off
G0 Z5.000 ; Safe height
G0 X0 Y0 ; Return to origin
M2 ; Program end
```

## Future Enhancements

Potential improvements:
- Support for 4+ reference points
- Automatic reference point generation in DXF2Laser
- Visual overlay of reference points on plot
- Reference point library/templates
- Tolerance configuration
- Export transformation matrix

## Troubleshooting

### Problem: Reference points not loading

**Check:**
- Comments are at beginning of file
- Syntax matches exactly
- No typos in keywords
- Parentheses around coordinates

### Problem: Large transformation errors

**Try:**
- Re-measure actual coordinates
- Switch between 2-point and 3-point modes
- Verify expected coordinates are correct
- Check for mechanical issues with machine

### Problem: Program crashes on adjust

**Check:**
- All coordinate fields have valid numbers
- G-code file was loaded successfully
- At least 2 reference points defined

## Support

For issues or questions:
1. Check this guide
2. Review console output for error messages
3. Verify G-code comment syntax
4. Test with example template above

