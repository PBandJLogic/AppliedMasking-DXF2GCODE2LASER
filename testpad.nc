; Cleaning G-code for Carousel - top: sections 1 and 3
; Reference points are the bottom outside corners of S3P1 and S1P16
; reference_point1 = (-199.2901, -152.4163)
; reference_point2 = (199.2901, -152.4163)
; preamble
G21 ; Set units to millimeters
G90 ; Absolute positioning
M4 S0 ; laser on at zero power
; end preamble
; === ARC GEOMETRY ===
G0 X25.654 Y161.883 Z0.000
G3 X9.669 Y163.211 I-25.654 J-211.883 F1500 S1000

; === LINE GEOMETRY ===
G1 X10.583 Y174.216 F1500 S1000  ; Engrave line
; Optimized arc (reversed direction)
G2 X26.568 Y172.888 I-10.583 J-224.216 F1500 S1000

; === LINE GEOMETRY ===
G1 X25.654 Y161.883 F1500 S1000  ; Engrave line

; === LINE GEOMETRY ===
G0 X25.563 Y161.994 Z0.000
G1 X26.461 Y172.800 F1500 S1000  ; Engrave line

; === ARC GEOMETRY ===
G3 X10.675 Y174.112 I-26.461 J-222.800 F1500 S1000

; === LINE GEOMETRY ===
G1 X9.777 Y163.306 F1500 S1000  ; Engrave line
; Optimized arc (reversed direction)
G2 X25.563 Y161.994 I-9.777 J-213.306 F1500 S1000

; === ARC GEOMETRY ===
G0 X25.472 Y162.106 Z0.000
G3 X9.885 Y163.401 I-25.472 J-212.106 F1500 S1000

; === LINE GEOMETRY ===
G1 X10.767 Y174.008 F1500 S1000  ; Engrave line
; Optimized arc (reversed direction)
G2 X26.353 Y172.712 I-10.767 J-224.008 F1500 S1000

; === LINE GEOMETRY ===
G1 X25.472 Y162.106 F1500 S1000  ; Engrave line

; === LINE GEOMETRY ===
G0 X25.289 Y162.329 Z0.000
G1 X26.138 Y172.536 F1500 S1000  ; Engrave line

; === LINE GEOMETRY ===
G1 X25.289 Y162.329 F1500 S1000  ; Engrave line

; === ARC GEOMETRY ===
G0 X49.475 Y157.616 Z0.000
G3 X33.743 Y160.746 I-49.475 J-207.616 F1500 S1000

; === LINE GEOMETRY ===
G1 X35.897 Y171.577 F1500 S1000  ; Engrave line
; Optimized arc (reversed direction)
G2 X51.629 Y168.448 I-35.897 J-221.577 F1500 S1000

; === LINE GEOMETRY ===
G1 X49.475 Y157.616 F1500 S1000  ; Engrave line

; === LINE GEOMETRY ===
G0 X49.397 Y157.738 Z0.000
G1 X51.512 Y168.373 F1500 S1000  ; Engrave line

; === ARC GEOMETRY ===
G3 X35.977 Y171.463 I-51.512 J-218.373 F1500 S1000

; === LINE GEOMETRY ===
G1 X33.861 Y160.828 F1500 S1000  ; Engrave line
; Optimized arc (reversed direction)
G2 X49.397 Y157.738 I-33.861 J-210.828 F1500 S1000

