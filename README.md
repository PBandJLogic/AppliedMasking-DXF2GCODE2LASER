
# ReadMe file for the DXF2Laser Files

## Key Files

 - DXF2Gcode.py - this program can take a DXF file and generate g code to laser engrave. It works well for simple files but for complex files like the Carousel cleaning paths, it generates too many moves.
 - GenerateCarouselGcode.py - this program allows you to create an optimal G code laser cleaning program. It minimizes the moves and allows any number of cleaning passes at specified spacing. It can generate g code for any sequencce of pads you want. The defaults are the top - sections 1 and 3 or the bottom section 2.
 - Gcode2Laser.py - this program takes a g code file and drives the laser. it has built in alignment steps for fine submillimeter aligning of the gcode to the work piece.

## Key notes
DXF files can have arcs and the Laser system GRBL controller is very picky about the coordinates being exact. The carousel which has very shallow short arcs with very long radii was generating errors so Carousel cleaning shifted to using G1 linear approximations which are within 0.016mm of the arc, so good enough.

Section1and3noarcs.gcode and section2noarcs.gcode is the code that this generates for 5 passes of cleaning, each with a 0.08mm spacing.

The *.spec files are used to create the windows executive versions of the python programs.

gcode_adjuster.py is a program to adjust g code using a manual process of getting the translation and rotation of a work piece. It is included just in case there is a problem Gcode2Laser.py can't handle.

