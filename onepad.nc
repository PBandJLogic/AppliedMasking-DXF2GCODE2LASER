; preamble
; Cleaning G-code for Carousel - top: sections 1 and 3
; Reference points are the bottom outside corners of S3P1 and S1P16
; reference_point1 = (-199.2901, -152.4163)
; reference_point2 = (199.2901, -152.4163)
G21 ; Set units to millimeters
G90 ; Absolute positioning
M4 S0 ; laser on at zero power
; end preamble
; === ARC GEOMETRY ===
G0 X-205.791 Y-88.632 Z0.000
G1 X-205.791 Y-88.632 Z0.000 F1500  ; Settling move for arc
G3 X-199.290 Y-102.416 I205.791 J88.632 F1500 S10
; Optimized arc (reversed direction)
G2 X-205.791 Y-88.632 I199.290 J102.416 F1500 S10

; === ARC GEOMETRY ===
G0 X-196.527 Y-84.263 Z0.000
G1 X-196.527 Y-84.263 Z0.000 F1500  ; Settling move for arc
G3 X-190.026 Y-98.047 I196.527 J84.263 F1500 S10

; === LINE GEOMETRY ===
G1 X-199.290 Y-102.416 F1500 S10  ; Engrave line

; === LINE GEOMETRY ===
G1 X-190.026 Y-98.047 F1500 S10  ; Engrave line
; Optimized arc (reversed direction)
G2 X-196.527 Y-84.263 I190.026 J98.047 F1500 S10

; === LINE GEOMETRY ===
G1 X-205.791 Y-88.632 F1500 S10  ; Engrave line

; === LINE GEOMETRY ===
G1 X-196.527 Y-84.263 F1500 S10  ; Engrave line

; === ARC GEOMETRY ===
G0 X-196.476 Y-84.129 Z0.000
G1 X-196.476 Y-84.129 Z0.000 F1500  ; Settling move for arc
G3 X-189.890 Y-98.093 I196.476 J84.129 F1500 S10

; === LINE GEOMETRY ===
G0 X-196.476 Y-84.129 Z0.000
G1 X-205.921 Y-88.583 F1500 S10  ; Engrave line

; === ARC GEOMETRY ===
G3 X-199.335 Y-102.548 I205.921 J88.583 F1500 S10

; === LINE GEOMETRY ===
G1 X-189.890 Y-98.093 F1500 S10  ; Engrave line

; === ARC GEOMETRY ===
G0 X-196.425 Y-83.994 Z0.000
G1 X-196.425 Y-83.994 Z0.000 F1500  ; Settling move for arc
G3 X-189.753 Y-98.140 I196.425 J83.994 F1500 S10

; === LINE GEOMETRY ===
G1 X-199.380 Y-102.680 F1500 S10  ; Engrave line
; Optimized arc (reversed direction)
G2 X-206.051 Y-88.534 I199.380 J102.680 F1500 S10

; === LINE GEOMETRY ===
G1 X-196.425 Y-83.994 F1500 S10  ; Engrave line

; === ARC GEOMETRY ===
G0 X-196.374 Y-83.859 Z0.000
G1 X-196.374 Y-83.859 Z0.000 F1500  ; Settling move for arc
G3 X-189.617 Y-98.186 I196.374 J83.859 F1500 S10

; === LINE GEOMETRY ===
G0 X-196.374 Y-83.859 Z0.000
G1 X-206.181 Y-88.485 F1500 S10  ; Engrave line

; === ARC GEOMETRY ===
G3 X-199.424 Y-102.811 I206.181 J88.485 F1500 S10

; === LINE GEOMETRY ===
G1 X-189.617 Y-98.186 F1500 S10  ; Engrave line

; === ARC GEOMETRY ===
G0 X-196.323 Y-83.724 Z0.000
G1 X-196.323 Y-83.724 Z0.000 F1500  ; Settling move for arc
G3 X-189.480 Y-98.232 I196.323 J83.724 F1500 S10

; === LINE GEOMETRY ===
G1 X-199.469 Y-102.943 F1500 S10  ; Engrave line
; Optimized arc (reversed direction)
G2 X-206.311 Y-88.435 I199.469 J102.943 F1500 S10

; === LINE GEOMETRY ===
G1 X-196.323 Y-83.724 F1500 S10  ; Engrave line

; postscript
M5 ; Turn off laser