; G Code for the 40% sized Carousel 3D printed part
; reference_point1 = (-79.2465, -21.234)
; reference_point2 = ( 79.2465, -21.234)
;
; preamble
G21 ; Set units to millimeters
G90 ; Absolute positioning
M4 S10 ; laser on at 1% power
; end preamble

G0 X-10 Y-10
G0 X-79.246 Y-21.234
G1 X-79.246 Y-21.234 F2000
G1 X-58.012 Y-58.012 F2000
G1 X-21.234 Y-79.246 F2000
G1 X21.234 Y-79.246 F2000
G1 X58.012 Y-58.012 F2000
G1 X79.246 Y-21.234 F2000
G1 X79.246 Y21.234 F2000
G1 X58.012 Y58.012 F2000
G1 X21.234 Y79.246 F2000
G1 X-21.234 Y79.246 F2000
G1 X-58.012 Y58.012 F2000
G1 X-79.246 Y21.234 F2000

; postscript
M5 ; Turn off laser
G0 X0.000000 Y100.000000 ; Send to unload position