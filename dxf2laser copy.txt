#!/usr/bin/env python3
"""
Interactive DXF 2 Laser Editor
Allows loading DXF files, adjusting origin, and marking elements for engraving or removal.
Must install libraries: pip3 install matplotlib numpy ezdxf Pillow
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import ezdxf
import math
from typing import List, Tuple, Dict, Any
import threading


class DXFGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive DXF 2 Laser Editor")
        self.root.geometry("1400x900")

        # Data storage
        self.original_points = []  # Original DXF data
        self.current_points = []  # Current data after transformations
        self.origin_offset = (0.0, 0.0)
        self.removed_elements = set()  # Set of element IDs to remove
        self.engraved_elements = set()  # Set of element IDs to engrave
        self.clipped_elements = (
            set()
        )  # Set of element IDs that are clipped out of workspace

        # Element tracking
        self.element_counter = 0
        self.element_data = (
            {}
        )  # Maps element_id to (x, y, radius, geom_type, original_data)

        # Undo functionality
        self.undo_stack = []  # Store state before each action
        self.max_undo_steps = 20

        # G-code settings
        self.gcode_settings = {
            "preamble": "G21 ; Set units to millimeters\nG90 ; Absolute positioning\nG0 X0, Y0, Z-3 ; Go to zero position\nM4 S0 ; laser on at zero power\n",
            "postscript": "G0 Z-3 ; Raise Z\nM5 ; Turn off laser\nG0 X0 Y375 ; Send to unload position\n",
            "laser_power": 1000,
            "cutting_z": -30,
            "feedrate": 1500,
            "max_workspace_x": 800.0 - 10.0,
            "max_workspace_y": 400.0 - 10.0,
            "raise_laser_between_paths": False,
            "optimize_toolpath": True,  # Enable toolpath optimization by default
        }

        # Unit conversion settings
        self.dxf_units = "mm"  # Default to mm
        self.unit_conversion_factor = 1.0  # Factor to convert to mm

        self.setup_ui()

    def generate_and_display_gcode(self):
        """Generate G-code and show preview window"""
        if not self.current_points:
            messagebox.showwarning("Warning", "No DXF file loaded")
            return

        # Generate G-code
        gcode = self.generate_gcode(self.current_points)

        # Show preview window with both plot and G-code text
        self.show_gcode_preview(gcode)

    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel for controls
        control_frame = ttk.Frame(main_frame, width=300)
        control_frame.pack(side="left", fill="y", padx=(0, 10))
        control_frame.pack_propagate(False)

        # Right panel for plot and G-code
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        self.setup_controls(control_frame)
        self.setup_plot(right_panel)

        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for undo functionality"""
        # Bind Ctrl+Z (Windows/Linux) and Cmd+Z (macOS)
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Command-z>", lambda e: self.undo())

        # Bind Ctrl+R to refresh input fields (debug hotkey)
        self.root.bind("<Control-r>", lambda e: self.ensure_input_fields_active())

        # Focus the root window so keyboard events are captured
        self.root.focus_set()

    def setup_controls(self, parent):
        # Logo and title frame
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 20))

        # Logo
        try:
            from PIL import Image, ImageTk

            logo_image = Image.open("logo.png")
            # Resize logo to appropriate size
            logo_image = logo_image.resize((80, 80), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_image)

            logo_label = ttk.Label(header_frame, image=logo_photo)
            logo_label.image = logo_photo  # Keep a reference
            logo_label.pack(side="left", padx=(0, 10))
        except Exception as e:
            print(f"Could not load logo: {e}")

        # Title
        title_label = ttk.Label(
            header_frame, text="DXF to\nLaser\nEditor", font=("Arial", 16, "bold")
        )
        title_label.pack(side="left", pady=10)

        # File loading section
        file_frame = ttk.LabelFrame(parent, text="File Operations", padding="10")
        file_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(file_frame, text="Load DXF File", command=self.load_dxf_file).pack(
            fill="x", pady=(0, 5)
        )
        ttk.Button(file_frame, text="Export G-code", command=self.export_gcode).pack(
            fill="x", pady=(0, 5)
        )
        ttk.Button(file_frame, text="G-code Settings", command=self.open_settings).pack(
            fill="x"
        )

        # Origin adjustment section
        origin_frame = ttk.LabelFrame(parent, text="Origin Adjustment", padding="10")
        origin_frame.pack(fill="x", pady=(0, 10))

        # X offset
        x_frame = ttk.Frame(origin_frame)
        x_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(x_frame, text="X Offset (mm):").pack(side="left")
        self.x_offset_var = tk.StringVar(value="0.0")
        self.x_entry = ttk.Entry(x_frame, textvariable=self.x_offset_var, width=15)
        self.x_entry.pack(side="right")

        # Add event handlers to ensure proper focus
        self.x_entry.bind("<Button-1>", self.debug_input_field)
        self.x_entry.bind("<FocusIn>", lambda e: None)
        self.x_entry.bind("<FocusOut>", lambda e: None)

        # Y offset
        y_frame = ttk.Frame(origin_frame)
        y_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(y_frame, text="Y Offset (mm):").pack(side="left")
        self.y_offset_var = tk.StringVar(value="0.0")
        self.y_entry = ttk.Entry(y_frame, textvariable=self.y_offset_var, width=15)
        self.y_entry.pack(side="right")

        # Add event handlers to ensure proper focus
        self.y_entry.bind("<Button-1>", self.debug_input_field)
        self.y_entry.bind("<FocusIn>", lambda e: None)
        self.y_entry.bind("<FocusOut>", lambda e: None)

        ttk.Button(origin_frame, text="Apply Offset", command=self.apply_offset).pack(
            fill="x"
        )

        # Element selection section
        selection_frame = ttk.LabelFrame(parent, text="Element Selection", padding="10")
        selection_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            selection_frame, text="Click on elements in the plot to select them."
        ).pack(anchor="w")
        ttk.Label(selection_frame, text="Selected elements:").pack(
            anchor="w", pady=(10, 0)
        )

        # Selected element info
        self.selected_info_var = tk.StringVar(value="None")
        ttk.Label(
            selection_frame,
            textvariable=self.selected_info_var,
            font=("Arial", 10, "bold"),
        ).pack(anchor="w")

        # Action buttons - First row
        button_frame1 = ttk.Frame(selection_frame)
        button_frame1.pack(fill="x", pady=(10, 5))

        ttk.Button(
            button_frame1, text="Engrave Element", command=self.mark_engraving
        ).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame1, text="Reset All", command=self.reset_selection).pack(
            side="left"
        )

        # Action buttons - Second row
        button_frame2 = ttk.Frame(selection_frame)
        button_frame2.pack(fill="x", pady=(5, 5))

        ttk.Button(
            button_frame2, text="Remove Element", command=self.remove_element
        ).pack(side="left", padx=(0, 5))
        ttk.Button(
            button_frame2,
            text="Engrave All",
            command=self.select_all_for_engraving,
        ).pack(side="left")

        # Statistics section
        stats_frame = ttk.LabelFrame(parent, text="Statistics", padding="10")
        stats_frame.pack(fill="x", pady=(0, 10))

        self.stats_var = tk.StringVar(value="No file loaded")
        ttk.Label(stats_frame, textvariable=self.stats_var).pack(anchor="w")

        # Instructions
        instructions_frame = ttk.LabelFrame(parent, text="Instructions", padding="10")
        instructions_frame.pack(fill="both", expand=True)

        instructions = """
1. Load a DXF file using the button above
2. Adjust the origin by entering X,Y offsets
3. Click on elements in the plot to select them
4. Mark elements for engraving (red) or removal
5. Export G-code for the final design

Colors:
• Blue: Original elements
• Red: Marked for engraving
• Removed elements disappear
        """
        ttk.Label(instructions_frame, text=instructions, justify="left").pack(
            anchor="w"
        )

    def setup_plot(self, parent):
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_title("DXF Geometry - Click on elements to select")

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Add navigation toolbar for zoom and pan
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill="x", pady=(5, 0))

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Bind canvas events to ensure input fields can still receive focus
        self.canvas.mpl_connect("button_press_event", self.on_canvas_click)

        # Connect click event with higher priority
        self.canvas.mpl_connect("button_press_event", self.on_click)

        # Also connect to button_release_event for better interaction with toolbar
        self.canvas.mpl_connect("button_release_event", self.on_click_release)

        # Connect motion event for selection rectangle
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)

        # Selection rectangle variables
        self.selection_rect = None
        self.selection_start = None
        self.selection_mode = False

        # Currently selected elements (support multiple selection)
        self.selected_element_ids = set()

    def load_dxf_file(self):
        """Load and parse DXF file"""
        file_path = filedialog.askopenfilename(
            title="Select DXF file",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")],
        )

        if not file_path:
            return

        try:
            self.original_points = self.extract_geometry(file_path)
            self.current_points = self.original_points.copy()
            self.reset_selection()
            self.update_plot()
            self.update_statistics()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load DXF file:\n{str(e)}")

    def detect_dxf_units(self, doc):
        """Detect the units used in the DXF file and set conversion factor"""
        try:
            # Check the header section for units
            header = doc.header

            # Try to get units from INSUNITS (Drawing Units)
            insunits = None
            try:
                insunits = header["$INSUNITS"]
            except:
                pass

            if insunits is not None:
                unit_mapping = {
                    0: ("Unitless", 1.0),
                    1: ("Inches", 25.4),  # Convert inches to mm
                    2: ("Feet", 304.8),  # Convert feet to mm
                    3: ("Miles", 1609344.0),  # Convert miles to mm
                    4: ("Millimeters", 1.0),  # Already in mm
                    5: ("Centimeters", 10.0),  # Convert cm to mm
                    6: ("Meters", 1000.0),  # Convert meters to mm
                    7: ("Kilometers", 1000000.0),  # Convert km to mm
                    8: ("Microinches", 0.0000254),  # Convert microinches to mm
                    9: ("Mils", 0.0254),  # Convert mils to mm
                    10: ("Yards", 914.4),  # Convert yards to mm
                    11: ("Angstroms", 0.0000001),  # Convert angstroms to mm
                    12: ("Nanometers", 0.000001),  # Convert nanometers to mm
                    13: ("Microns", 0.001),  # Convert microns to mm
                    14: ("Decimeters", 100.0),  # Convert decimeters to mm
                    15: ("Decameters", 10000.0),  # Convert decameters to mm
                    16: ("Hectometers", 100000.0),  # Convert hectometers to mm
                    17: ("Gigameters", 1000000000.0),  # Convert gigameters to mm
                    18: ("Astronomical units", 149597870700000.0),  # Convert AU to mm
                    19: (
                        "Light years",
                        9460730472580800000000.0,
                    ),  # Convert light years to mm
                    20: ("Parsecs", 30856775814913673000000.0),  # Convert parsecs to mm
                }

                if insunits in unit_mapping:
                    unit_name, conversion_factor = unit_mapping[insunits]
                    self.dxf_units = unit_name
                    self.unit_conversion_factor = conversion_factor
                    print(
                        f"DXF Units detected from header: {unit_name} (conversion factor: {conversion_factor})"
                    )
                    return
                else:
                    print(f"Unknown INSUNITS value: {insunits}")

        except Exception as e:
            print(f"Could not detect DXF units from header: {e}")

        # Fallback: Try to detect units by analyzing geometry scale
        try:
            # Look for typical dimensions that might indicate units
            msp = doc.modelspace()
            max_coord = 0
            min_coord = float("inf")
            coord_count = 0

            for entity in msp:
                if entity.dxftype() in [
                    "LINE",
                    "CIRCLE",
                    "ARC",
                    "LWPOLYLINE",
                    "POLYLINE",
                    "ELLIPSE",
                    "SPLINE",
                ]:
                    if entity.dxftype() == "LINE":
                        start = entity.dxf.start
                        end = entity.dxf.end
                        coords = [start.x, start.y, end.x, end.y]
                    elif entity.dxftype() == "CIRCLE":
                        center = entity.dxf.center
                        radius = entity.dxf.radius
                        coords = [center.x, center.y, radius]
                    elif entity.dxftype() == "ARC":
                        center = entity.dxf.center
                        radius = entity.dxf.radius
                        coords = [center.x, center.y, radius]
                    elif entity.dxftype() == "LWPOLYLINE":
                        points = list(entity.get_points())
                        coords = []
                        for x, y, *_ in points:
                            coords.extend([x, y])

                    for coord in coords:
                        max_coord = max(max_coord, abs(coord))
                        if coord != 0:
                            min_coord = min(min_coord, abs(coord))
                        coord_count += 1

            print(
                f"Geometry analysis: max_coord={max_coord:.2f}, min_coord={min_coord:.2f}, coord_count={coord_count}"
            )

            # Improved heuristic: look for typical patterns
            # Based on test files: inches (max_coord=4), mm (max_coord=100), meters (max_coord=20)
            if max_coord > 0:
                if max_coord <= 10:  # Small values, likely inches or meters
                    # If very small (1-5), likely inches. If larger (5-10), could be meters
                    if max_coord <= 5:
                        self.dxf_units = "Inches (heuristic - small values)"
                        self.unit_conversion_factor = 25.4
                        print(
                            f"DXF Units detected: Inches (heuristic - max coord: {max_coord:.2f})"
                        )
                    else:
                        self.dxf_units = "Meters (heuristic - medium values)"
                        self.unit_conversion_factor = 1000.0
                        print(
                            f"DXF Units detected: Meters (heuristic - max coord: {max_coord:.2f})"
                        )
                elif max_coord <= 200:  # Medium values, likely millimeters
                    self.dxf_units = "Millimeters (heuristic - typical mm range)"
                    self.unit_conversion_factor = 1.0
                    print(
                        f"DXF Units detected: Millimeters (heuristic - max coord: {max_coord:.2f})"
                    )
                else:  # Large values, likely millimeters
                    self.dxf_units = "Millimeters (heuristic - large values)"
                    self.unit_conversion_factor = 1.0
                    print(
                        f"DXF Units detected: Millimeters (heuristic - max coord: {max_coord:.2f})"
                    )
            else:
                self.dxf_units = "Unknown (no geometry found)"
                self.unit_conversion_factor = 1.0
                print("DXF Units: Unknown (no geometry found)")

        except Exception as e:
            print(f"Could not detect units heuristically: {e}")
            self.dxf_units = "Unknown (assuming mm)"
            self.unit_conversion_factor = 1.0

    def convert_units(self, value):
        """Convert a value from DXF units to millimeters"""
        return value * self.unit_conversion_factor

    def get_element_start_point(self, element_id, element_info):
        """Get the starting point for an element (where the tool should move to)"""
        geom_type = element_info["geom_type"]
        points = element_info["points"]

        if geom_type == "LINE" and len(points) >= 2:
            return points[0]  # Start of line
        elif geom_type == "CIRCLE" and len(points) >= 1:
            # Start at 0 degrees (right side of circle)
            cx, cy = points[0]
            radius = element_info["radius"]
            return (cx + radius, cy)
        elif geom_type == "ARC" and len(points) >= 1:
            # Start at the arc's start angle
            cx, cy = points[0]
            radius = element_info["radius"]
            element_data = self.element_data.get(element_id)
            if element_data and len(element_data) >= 5:
                _, _, _, _, original_data = element_data
                if len(original_data) >= 6:
                    _, _, _, start_angle, _, _ = original_data
                    start_rad = math.radians(start_angle)
                    start_x = cx + radius * math.cos(start_rad)
                    start_y = cy + radius * math.sin(start_rad)
                    return (start_x, start_y)
            # Fallback to right side of arc
            return (cx + radius, cy)
        elif (
            geom_type in ["LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"]
            and len(points) >= 1
        ):
            return points[0]  # First point of polyline

        # Fallback
        return (0.0, 0.0)

    def get_element_end_point(self, element_id, element_info):
        """Get the end point of an element for path optimization"""
        geom_type = element_info["geom_type"]
        points = element_info["points"]
        radius = element_info["radius"]

        if geom_type == "LINE" and len(points) >= 2:
            return points[1]  # End of line
        elif geom_type == "CIRCLE" and len(points) >= 1:
            # Circle ends where it starts (full circle)
            cx, cy = points[0]
            return (cx + radius, cy)  # Right side of circle
        elif geom_type == "ARC" and len(points) >= 1:
            # End at the arc's end angle
            cx, cy = points[0]
            element_data = self.element_data.get(element_id)
            if element_data and len(element_data) >= 5:
                _, _, _, _, original_data = element_data
                if len(original_data) >= 6:
                    _, _, _, _, end_angle, _ = original_data
                    end_rad = math.radians(end_angle)
                    end_x = cx + radius * math.cos(end_rad)
                    end_y = cy + radius * math.sin(end_rad)
                    return (end_x, end_y)
            # Fallback
            return (cx + radius, cy)
        elif (
            geom_type in ["LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"]
            and len(points) >= 1
        ):
            return points[-1]  # Last point of polyline

        # Fallback
        return (0.0, 0.0)

    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def optimize_toolpath(self, elements_by_id, start_x, start_y):
        """Optimize toolpath using nearest neighbor algorithm with path reversal to minimize travel distance"""
        if not elements_by_id:
            return []

        # Convert to list for easier manipulation
        elements_list = list(elements_by_id.items())
        optimized = []
        remaining = elements_list.copy()
        current_pos = (start_x, start_y)

        print(f"Optimizing toolpath for {len(elements_list)} elements...")

        # Use nearest neighbor algorithm with path reversal consideration
        while remaining:
            # Find the element with the closest entry point (start or end) to current position
            min_distance = float("inf")
            closest_index = 0
            should_reverse = False

            for i, (element_id, element_info) in enumerate(remaining):
                geom_type = element_info["geom_type"]

                # Get start and end points
                start_point = self.get_element_start_point(element_id, element_info)
                end_point = self.get_element_end_point(element_id, element_info)

                # Calculate distance to start point
                distance_to_start = self.calculate_distance(current_pos, start_point)

                # For reversible elements, also consider distance to end point
                if geom_type in ["LINE", "LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"]:
                    distance_to_end = self.calculate_distance(current_pos, end_point)

                    # Choose the closer entry point
                    if distance_to_end < distance_to_start:
                        distance = distance_to_end
                        reverse = True
                    else:
                        distance = distance_to_start
                        reverse = False
                else:
                    # Circles and arcs - don't reverse (direction matters for G2/G3)
                    distance = distance_to_start
                    reverse = False

                if distance < min_distance:
                    min_distance = distance
                    closest_index = i
                    should_reverse = reverse

            # Add the closest element to optimized list
            closest_element = remaining.pop(closest_index)
            element_id, element_info = closest_element

            # Create a copy of element_info to avoid modifying shared data
            element_info = element_info.copy()

            # Mark if this element should be reversed and reverse points
            if should_reverse:
                element_info["_reverse_path"] = True
                geom_type = element_info["geom_type"]
                if geom_type in ["LINE", "LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"]:
                    # Reverse the points list in the copy
                    points = element_info["points"]
                    element_info["points"] = list(reversed(points))

            optimized.append((element_id, element_info))

            # Update current position using helper function
            current_pos = self.get_element_end_point(element_id, element_info)

        # Calculate total optimized travel distance
        optimized_distance = 0.0
        current_pos = (start_x, start_y)
        for element_id, element_info in optimized:
            start_point = self.get_element_start_point(element_id, element_info)
            optimized_distance += self.calculate_distance(current_pos, start_point)

            # Update current position to end of element (using modified points if reversed)
            current_pos = self.get_element_end_point(element_id, element_info)

        # Calculate unoptimized distance for comparison
        unoptimized_distance = 0.0
        current_pos = (start_x, start_y)
        for element_id, element_info in elements_list:
            start_point = self.get_element_start_point(element_id, element_info)
            unoptimized_distance += self.calculate_distance(current_pos, start_point)
            current_pos = self.get_element_end_point(element_id, element_info)

        savings = unoptimized_distance - optimized_distance
        savings_percent = (
            (savings / unoptimized_distance * 100) if unoptimized_distance > 0 else 0
        )

        print(
            f"Toolpath optimization complete:\n"
            f"  Original order travel: {unoptimized_distance:.2f} mm\n"
            f"  Optimized travel: {optimized_distance:.2f} mm\n"
            f"  Savings: {savings:.2f} mm ({savings_percent:.1f}%)"
        )

        return optimized

    def extract_geometry(self, file_path):
        """Extract geometry from DXF file (simplified version of the original function)"""
        doc = ezdxf.readfile(file_path)

        # Detect and set up unit conversion
        self.detect_dxf_units(doc)

        msp = doc.modelspace()
        all_points = []

        # Debug: Count entities
        entity_count = 0
        entity_types = {}

        for entity in msp:
            entity_type = entity.dxftype()
            entity_count += 1
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            if entity_type == "INSERT":
                block_name = entity.dxf.name
                block = doc.blocks.get(block_name)
                if not block:
                    continue

                insert_pos = entity.dxf.insert
                scale = (entity.dxf.xscale, entity.dxf.yscale, entity.dxf.zscale)
                rotation = entity.dxf.rotation if entity.dxf.hasattr("rotation") else 0

                print(
                    f"Processing INSERT block: {block_name} at ({insert_pos.x:.2f}, {insert_pos.y:.2f})"
                )
                print(f"  Scale factors: {scale}")

                for block_entity in block:
                    if block_entity.dxftype() == "LINE":
                        # Store line as start and end points with same element ID
                        start_pt = block_entity.dxf.start
                        end_pt = block_entity.dxf.end
                        start_x, start_y = self.transform_point(
                            start_pt.x, start_pt.y, insert_pos, scale, rotation
                        )
                        end_x, end_y = self.transform_point(
                            end_pt.x, end_pt.y, insert_pos, scale, rotation
                        )

                        # Convert units to mm
                        start_x = self.convert_units(start_x)
                        start_y = self.convert_units(start_y)
                        end_x = self.convert_units(end_x)
                        end_y = self.convert_units(end_y)

                        element_id = self.get_next_element_id()
                        # Store both points with the same element ID
                        all_points.append((start_x, start_y, 0, "LINE", element_id))
                        all_points.append((end_x, end_y, 0, "LINE", element_id))

                        # Store line data with both endpoints
                        self.element_data[element_id] = (
                            (start_x, end_x),  # X coordinates
                            (start_y, end_y),  # Y coordinates
                            0,
                            "LINE",
                            ((start_pt.x, start_pt.y), (end_pt.x, end_pt.y), "LINE"),
                        )

                    elif block_entity.dxftype() == "CIRCLE":
                        original_cx = block_entity.dxf.center.x
                        original_cy = block_entity.dxf.center.y
                        cx, cy = self.transform_point(
                            original_cx,
                            original_cy,
                            insert_pos,
                            scale,
                            rotation,
                        )
                        # Apply scale transformation to radius as well!
                        original_radius = block_entity.dxf.radius
                        scaled_radius = original_radius * scale[0]  # Use X scale factor

                        # Convert units to mm
                        cx = self.convert_units(cx)
                        cy = self.convert_units(cy)
                        scaled_radius = self.convert_units(scaled_radius)

                        print(
                            f"  Found CIRCLE: original_center=({original_cx:.2f}, {original_cy:.2f}), transformed_center=({cx:.2f}, {cy:.2f}), original_radius={original_radius:.2f}, scaled_radius={scaled_radius:.2f}"
                        )
                        element_id = self.get_next_element_id()
                        all_points.append((cx, cy, scaled_radius, "CIRCLE", element_id))
                        self.element_data[element_id] = (
                            cx,
                            cy,
                            scaled_radius,
                            "CIRCLE",
                            (
                                block_entity.dxf.center.x,
                                block_entity.dxf.center.y,
                                original_radius,
                                "CIRCLE",
                            ),
                        )

                    elif block_entity.dxftype() == "LWPOLYLINE":
                        polyline_points = self.extract_lwpolyline_geometry(
                            block_entity, insert_pos, scale, rotation
                        )
                        element_id = self.get_next_element_id()
                        # Store all polyline points with the same element ID
                        for tx, ty in polyline_points:
                            all_points.append((tx, ty, 0, "LWPOLYLINE", element_id))

                        # Store polyline data with all points
                        self.element_data[element_id] = (
                            [pt[0] for pt in polyline_points],  # X coordinates
                            [pt[1] for pt in polyline_points],  # Y coordinates
                            0,
                            "LWPOLYLINE",
                            polyline_points,
                        )

                    elif block_entity.dxftype() == "ARC":
                        original_cx = block_entity.dxf.center.x
                        original_cy = block_entity.dxf.center.y
                        cx, cy = self.transform_point(
                            original_cx,
                            original_cy,
                            insert_pos,
                            scale,
                            rotation,
                        )
                        # Apply scale transformation to radius as well!
                        original_radius = block_entity.dxf.radius
                        scaled_radius = original_radius * scale[0]  # Use X scale factor
                        start_angle = block_entity.dxf.start_angle
                        end_angle = block_entity.dxf.end_angle

                        # Convert units to mm
                        cx = self.convert_units(cx)
                        cy = self.convert_units(cy)
                        scaled_radius = self.convert_units(scaled_radius)

                        print(
                            f"  Found ARC: original_center=({original_cx:.2f}, {original_cy:.2f}), transformed_center=({cx:.2f}, {cy:.2f}), original_radius={original_radius:.2f}, scaled_radius={scaled_radius:.2f}, angles=({start_angle:.2f}, {end_angle:.2f})"
                        )
                        element_id = self.get_next_element_id()
                        all_points.append((cx, cy, scaled_radius, "ARC", element_id))
                        self.element_data[element_id] = (
                            cx,
                            cy,
                            scaled_radius,
                            "ARC",
                            (
                                block_entity.dxf.center.x,
                                block_entity.dxf.center.y,
                                original_radius,
                                start_angle,
                                end_angle,
                                "ARC",
                            ),
                        )

            elif entity_type == "LINE":
                # Store line as start and end points with same element ID
                start_pt = entity.dxf.start
                end_pt = entity.dxf.end
                element_id = self.get_next_element_id()

                # Convert units to mm
                start_x = self.convert_units(start_pt.x)
                start_y = self.convert_units(start_pt.y)
                end_x = self.convert_units(end_pt.x)
                end_y = self.convert_units(end_pt.y)

                all_points.append((start_x, start_y, 0, "LINE", element_id))
                all_points.append((end_x, end_y, 0, "LINE", element_id))

                self.element_data[element_id] = (
                    (start_x, end_x),  # X coordinates (converted)
                    (start_y, end_y),  # Y coordinates (converted)
                    0,
                    "LINE",
                    ((start_pt.x, start_pt.y), (end_pt.x, end_pt.y), "LINE"),
                )

            elif entity_type == "CIRCLE":
                center = entity.dxf.center
                radius = entity.dxf.radius
                element_id = self.get_next_element_id()

                # Convert units to mm
                cx = self.convert_units(center.x)
                cy = self.convert_units(center.y)
                radius_mm = self.convert_units(radius)

                all_points.append((cx, cy, radius_mm, "CIRCLE", element_id))
                self.element_data[element_id] = (
                    cx,
                    cy,
                    radius_mm,
                    "CIRCLE",
                    (center.x, center.y, radius, "CIRCLE"),
                )

            elif entity_type == "ARC":
                center = entity.dxf.center
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                element_id = self.get_next_element_id()

                # Convert units to mm
                cx = self.convert_units(center.x)
                cy = self.convert_units(center.y)
                radius_mm = self.convert_units(radius)

                all_points.append((cx, cy, radius_mm, "ARC", element_id))
                self.element_data[element_id] = (
                    cx,
                    cy,
                    radius_mm,
                    "ARC",
                    (center.x, center.y, radius, start_angle, end_angle, "ARC"),
                )

            elif entity_type == "LWPOLYLINE":
                # Extract LWPOLYLINE points (top-level, not in block)
                polyline_points = self.extract_lwpolyline_geometry(entity)
                element_id = self.get_next_element_id()

                # Store all polyline points with the same element ID
                for tx, ty in polyline_points:
                    all_points.append((tx, ty, 0, "LWPOLYLINE", element_id))

                # Store polyline data with all points
                self.element_data[element_id] = (
                    [pt[0] for pt in polyline_points],  # X coordinates
                    [pt[1] for pt in polyline_points],  # Y coordinates
                    0,
                    "LWPOLYLINE",
                    polyline_points,
                )

            elif entity_type == "POLYLINE":
                # POLYLINE (heavy polyline) - similar to LWPOLYLINE but legacy format
                polyline_points = []
                is_closed = entity.is_closed

                # Get vertices from the polyline
                for vertex in entity.vertices:
                    x, y = vertex.dxf.location.x, vertex.dxf.location.y
                    # Convert units to mm
                    x = self.convert_units(x)
                    y = self.convert_units(y)
                    polyline_points.append((x, y))

                # Close the polyline if needed
                if is_closed and len(polyline_points) > 2:
                    polyline_points.append(polyline_points[0])

                element_id = self.get_next_element_id()

                # Store all polyline points with the same element ID
                for tx, ty in polyline_points:
                    all_points.append((tx, ty, 0, "POLYLINE", element_id))

                # Store polyline data with all points
                self.element_data[element_id] = (
                    [pt[0] for pt in polyline_points],  # X coordinates
                    [pt[1] for pt in polyline_points],  # Y coordinates
                    0,
                    "POLYLINE",
                    polyline_points,
                )

            elif entity_type == "ELLIPSE":
                # Flatten ELLIPSE to polyline approximation
                try:
                    # Use ezdxf's flattening method to convert to line segments
                    flattened_points = []
                    for point in entity.flattening(distance=0.1):  # 0.1mm segments
                        x, y = point.x, point.y
                        # Convert units to mm
                        x = self.convert_units(x)
                        y = self.convert_units(y)
                        flattened_points.append((x, y))

                    element_id = self.get_next_element_id()

                    # Store all points with the same element ID
                    for tx, ty in flattened_points:
                        all_points.append((tx, ty, 0, "ELLIPSE", element_id))

                    # Store data with all points
                    self.element_data[element_id] = (
                        [pt[0] for pt in flattened_points],  # X coordinates
                        [pt[1] for pt in flattened_points],  # Y coordinates
                        0,
                        "ELLIPSE",
                        flattened_points,
                    )
                    print(f"  Converted ELLIPSE to {len(flattened_points)} segments")
                except Exception as e:
                    print(f"  WARNING: Could not process ELLIPSE: {e}")

            elif entity_type == "SPLINE":
                # Flatten SPLINE to polyline approximation
                try:
                    # Use ezdxf's flattening method to convert to line segments
                    flattened_points = []
                    for point in entity.flattening(distance=0.1):  # 0.1mm segments
                        x, y = point.x, point.y
                        # Convert units to mm
                        x = self.convert_units(x)
                        y = self.convert_units(y)
                        flattened_points.append((x, y))

                    element_id = self.get_next_element_id()

                    # Store all points with the same element ID
                    for tx, ty in flattened_points:
                        all_points.append((tx, ty, 0, "SPLINE", element_id))

                    # Store data with all points
                    self.element_data[element_id] = (
                        [pt[0] for pt in flattened_points],  # X coordinates
                        [pt[1] for pt in flattened_points],  # Y coordinates
                        0,
                        "SPLINE",
                        flattened_points,
                    )
                    print(f"  Converted SPLINE to {len(flattened_points)} segments")
                except Exception as e:
                    print(f"  WARNING: Could not process SPLINE: {e}")

            elif entity_type in ["TEXT", "MTEXT"]:
                # Convert TEXT/MTEXT to geometric primitives (vector paths)
                try:
                    from ezdxf.disassemble import to_primitives

                    # Get text properties for logging
                    if entity_type == "TEXT":
                        text_content = entity.dxf.get("text", "")
                        insert_point = entity.dxf.get("insert", None)
                    else:  # MTEXT
                        text_content = (
                            entity.text
                        )  # MTEXT uses .text property, not .dxf.text
                        insert_point = entity.dxf.get("insert", None)

                    pos_str = (
                        f"at ({insert_point.x:.2f}, {insert_point.y:.2f})"
                        if insert_point
                        else ""
                    )
                    print(
                        f"  Processing {entity_type}: '{text_content[:30]}...' {pos_str}"
                    )

                    # Convert text to primitive geometric paths
                    primitives = list(to_primitives([entity]))

                    if not primitives:
                        print(
                            f"    WARNING: Text '{text_content[:30]}' has no geometry (not exploded in CAD)"
                        )
                        # Store as a marker point so user knows text exists
                        if insert_point:
                            x = self.convert_units(insert_point.x)
                            y = self.convert_units(insert_point.y)
                            element_id = self.get_next_element_id()
                            all_points.append((x, y, 0, "TEXT_MARKER", element_id))
                            self.element_data[element_id] = (
                                x,
                                y,
                                0,
                                "TEXT_MARKER",
                                {"content": text_content, "type": entity_type},
                            )
                    else:
                        # Process each primitive from the text
                        primitives_processed = 0
                        for primitive in primitives:
                            if primitive.type == "line":
                                # Extract line geometry from text outline
                                start_x = self.convert_units(primitive.start.x)
                                start_y = self.convert_units(primitive.start.y)
                                end_x = self.convert_units(primitive.end.x)
                                end_y = self.convert_units(primitive.end.y)

                                element_id = self.get_next_element_id()
                                all_points.append(
                                    (start_x, start_y, 0, "LINE", element_id)
                                )
                                all_points.append((end_x, end_y, 0, "LINE", element_id))

                                self.element_data[element_id] = (
                                    (start_x, end_x),
                                    (start_y, end_y),
                                    0,
                                    "LINE",
                                    ((start_x, start_y), (end_x, end_y), "TEXT_LINE"),
                                )
                                primitives_processed += 1

                            elif primitive.type == "polyline":
                                # Extract polyline geometry from text outline
                                polyline_points = []
                                for vertex in primitive.vertices:
                                    x = self.convert_units(vertex.x)
                                    y = self.convert_units(vertex.y)
                                    polyline_points.append((x, y))

                                if len(polyline_points) >= 2:
                                    element_id = self.get_next_element_id()
                                    for tx, ty in polyline_points:
                                        all_points.append(
                                            (tx, ty, 0, "LWPOLYLINE", element_id)
                                        )

                                    self.element_data[element_id] = (
                                        [pt[0] for pt in polyline_points],
                                        [pt[1] for pt in polyline_points],
                                        0,
                                        "LWPOLYLINE",
                                        polyline_points,
                                    )
                                    primitives_processed += 1

                            elif primitive.type == "arc":
                                # Extract arc geometry from text outline
                                cx = self.convert_units(primitive.center.x)
                                cy = self.convert_units(primitive.center.y)
                                radius = self.convert_units(primitive.radius)
                                start_angle = primitive.start_angle
                                end_angle = primitive.end_angle

                                element_id = self.get_next_element_id()
                                all_points.append((cx, cy, radius, "ARC", element_id))
                                self.element_data[element_id] = (
                                    cx,
                                    cy,
                                    radius,
                                    "ARC",
                                    (
                                        cx,
                                        cy,
                                        radius,
                                        start_angle,
                                        end_angle,
                                        "TEXT_ARC",
                                    ),
                                )
                                primitives_processed += 1

                            elif primitive.type == "spline":
                                # Flatten spline from text outline
                                spline_points = []
                                for point in primitive.flattening(distance=0.1):
                                    x = self.convert_units(point.x)
                                    y = self.convert_units(point.y)
                                    spline_points.append((x, y))

                                if len(spline_points) >= 2:
                                    element_id = self.get_next_element_id()
                                    for tx, ty in spline_points:
                                        all_points.append(
                                            (tx, ty, 0, "SPLINE", element_id)
                                        )

                                    self.element_data[element_id] = (
                                        [pt[0] for pt in spline_points],
                                        [pt[1] for pt in spline_points],
                                        0,
                                        "SPLINE",
                                        spline_points,
                                    )
                                    primitives_processed += 1

                        print(
                            f"    Converted to {primitives_processed} geometric primitives"
                        )

                except Exception as e:
                    print(f"  WARNING: Could not process {entity_type}: {e}")
                    # Try to at least mark where the text is
                    try:
                        if entity_type == "TEXT":
                            insert_point = entity.dxf.get("insert", None)
                        else:
                            insert_point = entity.dxf.get("insert", None)

                        if insert_point:
                            x = self.convert_units(insert_point.x)
                            y = self.convert_units(insert_point.y)
                            element_id = self.get_next_element_id()
                            all_points.append((x, y, 0, "TEXT_MARKER", element_id))
                            self.element_data[element_id] = (
                                x,
                                y,
                                0,
                                "TEXT_MARKER",
                                {
                                    "content": "TEXT",
                                    "type": entity_type,
                                    "error": str(e),
                                },
                            )
                    except:
                        pass  # If even marker creation fails, just skip

        # Debug: Print entity information
        print(f"DXF File Analysis:")
        print(f"  Total entities found: {entity_count}")
        print(f"  Entity types: {entity_types}")
        print(f"  Points extracted: {len(all_points)}")

        if entity_count == 0:
            print("  WARNING: No entities found in DXF file!")
            print("  This suggests the file may be incomplete or corrupted.")
            print("  Expected to find ENTITIES section with geometry data.")

        return all_points

    def transform_point(self, x, y, insert_pos, scale, rotation):
        """Transform point coordinates using proper transformation matrix"""
        if insert_pos is not None and scale is not None:
            from ezdxf.math import Matrix44
            import math

            rotation_rad = math.radians(rotation)
            transform = (
                Matrix44.scale(scale[0], scale[1], scale[2])
                @ Matrix44.z_rotate(rotation_rad)
                @ Matrix44.translate(insert_pos.x, insert_pos.y, 0)
            )
            tx, ty, _ = transform.transform((x, y, 0))
            return tx, ty
        else:
            return x, y

    def extract_lwpolyline_geometry(
        self, entity, insert_pos=None, scale=None, rotation=None
    ):
        """Extract LWPOLYLINE points"""
        points = []
        polyline_points = list(entity.get_points())
        is_closed = entity.closed

        for x, y, *_ in polyline_points:
            if insert_pos and scale and rotation is not None:
                tx, ty = self.transform_point(x, y, insert_pos, scale, rotation)
            else:
                tx, ty = x, y

            # Convert units to mm
            tx = self.convert_units(tx)
            ty = self.convert_units(ty)

            points.append((tx, ty))

        if is_closed and len(points) > 2:
            points.append(points[0])

        return points

    def get_next_element_id(self):
        """Get next unique element ID"""
        self.element_counter += 1
        return self.element_counter

    def save_state(self):
        """Save current state for undo functionality"""
        state = {
            "removed_elements": self.removed_elements.copy(),
            "engraved_elements": self.engraved_elements.copy(),
            "origin_offset": self.origin_offset,
        }
        self.undo_stack.append(state)

        # Limit undo stack size
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)

    def undo(self):
        """Undo the last action"""
        if not self.undo_stack:
            return

        state = self.undo_stack.pop()
        self.removed_elements = state["removed_elements"]
        self.engraved_elements = state["engraved_elements"]
        self.origin_offset = state["origin_offset"]

        # Update UI
        self.update_plot()
        self.update_statistics()
        self.update_selection_info()

        # Clear selection
        self.selected_element_id = None

    def apply_offset(self):
        """Apply origin offset to all points"""
        try:
            x_offset = float(self.x_offset_var.get())
            y_offset = float(self.y_offset_var.get())

            self.origin_offset = (x_offset, y_offset)

            # Update current points with offset
            self.current_points = []
            for x, y, radius, geom_type, element_id in self.original_points:
                new_x = x + x_offset
                new_y = y + y_offset
                self.current_points.append(
                    (new_x, new_y, radius, geom_type, element_id)
                )

            self.update_plot()
            self.update_statistics()

            # Ensure input fields remain active after applying offset
            self.ensure_input_fields_active()

        except ValueError:
            messagebox.showerror(
                "Error", "Please enter valid numbers for X and Y offsets"
            )

    def on_click(self, event):
        """Handle mouse clicks on the plot - store position for click_release"""
        # Check if Ctrl/Cmd key is held for selection rectangle
        if event.button == 1:  # Left mouse button
            if event.key == "control" or event.key == "cmd":
                # Start selection rectangle mode
                if (
                    event.inaxes == self.ax
                    and event.xdata is not None
                    and event.ydata is not None
                ):
                    self.selection_mode = True
                    self.selection_start = (event.xdata, event.ydata)
                    self.last_click_pos = None  # Don't do single selection
                    return

        # Store click position for potential single selection
        if (
            event.inaxes == self.ax
            and event.xdata is not None
            and event.ydata is not None
        ):
            self.last_click_pos = (event.xdata, event.ydata)
            self.selection_mode = False
        else:
            self.last_click_pos = None
            self.selection_mode = False

    def on_motion(self, event):
        """Handle mouse motion for selection rectangle"""
        if not self.selection_mode or event.inaxes != self.ax:
            return

        if event.xdata is None or event.ydata is None:
            return

        # Update selection rectangle
        if self.selection_start:
            start_x, start_y = self.selection_start
            end_x, end_y = event.xdata, event.ydata

            # Remove previous rectangle
            if self.selection_rect:
                self.selection_rect.remove()

            # Create new rectangle
            from matplotlib.patches import Rectangle

            width = end_x - start_x
            height = end_y - start_y
            self.selection_rect = Rectangle(
                (start_x, start_y),
                width,
                height,
                fill=False,
                edgecolor="blue",
                linestyle="--",
                linewidth=2,
                alpha=0.7,
            )
            self.ax.add_patch(self.selection_rect)
            self.canvas.draw_idle()

    def on_click_release(self, event):
        """Handle mouse click release - this works better with navigation toolbar"""
        if event.inaxes != self.ax:
            # End selection mode if mouse leaves plot
            if self.selection_mode:
                self.selection_mode = False
                if self.selection_rect:
                    self.selection_rect.remove()
                    self.selection_rect = None
                    self.canvas.draw()
            return

        if event.xdata is None or event.ydata is None:
            return

        # Handle selection rectangle completion
        if self.selection_mode and self.selection_start:
            start_x, start_y = self.selection_start
            end_x, end_y = event.xdata, event.ydata

            # Clear previous selection
            self.selected_element_ids.clear()

            # Find elements within rectangle
            rect_left = min(start_x, end_x)
            rect_right = max(start_x, end_x)
            rect_bottom = min(start_y, end_y)
            rect_top = max(start_y, end_y)

            # Get unique elements for selection
            unique_elements = {}
            for x, y, radius, geom_type, element_id in self.current_points:
                if element_id not in unique_elements:
                    unique_elements[element_id] = {
                        "geom_type": geom_type,
                        "radius": radius,
                        "points": [],
                    }
                unique_elements[element_id]["points"].append((x, y))

            # Select elements within rectangle
            for element_id, element_info in unique_elements.items():
                if element_id in self.removed_elements:
                    continue

                geom_type = element_info["geom_type"]
                points = element_info["points"]

                # Check if element is within rectangle
                in_rect = False
                if geom_type == "CIRCLE" and len(points) >= 1:
                    center_x, center_y = points[0]
                    radius = element_info["radius"]
                    # Check if circle intersects with rectangle
                    in_rect = (
                        center_x - radius <= rect_right
                        and center_x + radius >= rect_left
                        and center_y - radius <= rect_top
                        and center_y + radius >= rect_bottom
                    )
                elif (
                    geom_type in ["LINE", "LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"]
                    and len(points) >= 1
                ):
                    # Check if any point is within rectangle
                    for point in points:
                        px, py = point
                        if (
                            rect_left <= px <= rect_right
                            and rect_bottom <= py <= rect_top
                        ):
                            in_rect = True
                            break

                if in_rect:
                    self.selected_element_ids.add(element_id)

            # Clean up selection rectangle
            if self.selection_rect:
                self.selection_rect.remove()
                self.selection_rect = None

            self.selection_mode = False
            self.update_plot_preserve_zoom()
            self.update_selection_info()
            return

        # Handle single click selection
        # Check if this was a simple click (not a drag)
        if hasattr(self, "last_click_pos") and self.last_click_pos:
            click_start_x, click_start_y = self.last_click_pos
            click_end_x, click_end_y = event.xdata, event.ydata

            # If mouse moved too much, it was a drag operation (pan/zoom)
            drag_distance = (
                (click_end_x - click_start_x) ** 2 + (click_end_y - click_start_y) ** 2
            ) ** 0.5
            if drag_distance > 2:  # 2mm tolerance for drag vs click
                return

        # Find the closest element to the click point
        click_x, click_y = event.xdata, event.ydata

        # Store candidates with priority system
        candidates = []

        # Get unique elements for click detection
        unique_elements = {}
        for x, y, radius, geom_type, element_id in self.current_points:
            if element_id not in unique_elements:
                unique_elements[element_id] = {
                    "geom_type": geom_type,
                    "radius": radius,
                    "points": [],
                }
            unique_elements[element_id]["points"].append((x, y))

        for element_id, element_info in unique_elements.items():
            if element_id in self.removed_elements:
                continue

            geom_type = element_info["geom_type"]
            radius = element_info["radius"]
            points = element_info["points"]

            if geom_type == "CIRCLE":
                if len(points) >= 1:
                    center_x, center_y = points[0]
                    # Calculate distance from click to circle center
                    distance = math.sqrt(
                        (click_x - center_x) ** 2 + (click_y - center_y) ** 2
                    )
                    # Use precise selection tolerance for circles
                    # Always use 3mm tolerance regardless of circle size
                    tolerance = 3.0

                    if distance <= tolerance:
                        # Circles have highest priority (1)
                        candidates.append((distance, 1, element_id))

            elif geom_type == "ARC":
                if len(points) >= 1:
                    center_x, center_y = points[0]
                    # Get arc parameters from element data
                    element_data = self.element_data.get(element_id)
                    if element_data and len(element_data) >= 5:
                        _, _, _, _, original_data = element_data
                        if len(original_data) >= 6:
                            _, _, _, start_angle, end_angle, _ = original_data

                            # Calculate distance from click to arc center
                            distance_to_center = math.sqrt(
                                (click_x - center_x) ** 2 + (click_y - center_y) ** 2
                            )

                            # Check if click is within arc radius tolerance
                            radius_tolerance = 3.0
                            if abs(distance_to_center - radius) <= radius_tolerance:
                                # Check if click is within arc angle range
                                click_angle = math.atan2(
                                    click_y - center_y, click_x - center_x
                                )
                                click_angle_deg = math.degrees(click_angle)

                                # Normalize angles to 0-360 range
                                start_angle_norm = start_angle % 360
                                end_angle_norm = end_angle % 360
                                click_angle_norm = click_angle_deg % 360

                                # Handle arc that crosses 0 degrees
                                if start_angle_norm > end_angle_norm:
                                    # Arc crosses 0 degrees
                                    in_arc = (
                                        click_angle_norm >= start_angle_norm
                                        or click_angle_norm <= end_angle_norm
                                    )
                                else:
                                    # Normal arc
                                    in_arc = (
                                        start_angle_norm
                                        <= click_angle_norm
                                        <= end_angle_norm
                                    )

                                if in_arc:
                                    # Arcs have same priority as circles (1)
                                    candidates.append(
                                        (
                                            abs(distance_to_center - radius),
                                            1,
                                            element_id,
                                        )
                                    )

            elif geom_type == "LINE":
                if len(points) >= 2:
                    # Check distance to line segment
                    for i in range(len(points) - 1):
                        p1 = points[i]
                        p2 = points[i + 1]
                        distance = self.point_to_line_distance(
                            (click_x, click_y), p1, p2
                        )
                        if distance < 2:  # Precise tolerance for lines (2mm)
                            # Lines have lower priority (2)
                            candidates.append((distance, 2, element_id))

            elif geom_type in ["LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"]:
                if len(points) >= 2:
                    # Check distance to polyline segments
                    for i in range(len(points) - 1):
                        p1 = points[i]
                        p2 = points[i + 1]
                        distance = self.point_to_line_distance(
                            (click_x, click_y), p1, p2
                        )
                        if distance < 2:  # Precise tolerance for polylines (2mm)
                            # Polylines have lower priority (2)
                            candidates.append((distance, 2, element_id))

        # Sort candidates by priority first, then by distance
        # Lower priority number = higher priority
        candidates.sort(key=lambda x: (x[1], x[0]))

        closest_element = candidates[0][2] if candidates else None

        if closest_element:
            # Check if Ctrl/Cmd key is held for multi-selection
            if event.key == "control" or event.key == "cmd":
                # Add to selection
                self.selected_element_ids.add(closest_element)
            else:
                # Single selection - clear others
                self.selected_element_ids.clear()
                self.selected_element_ids.add(closest_element)

            self.update_selection_info()
            self.update_plot_preserve_zoom()  # Redraw to show selection without resetting zoom
        else:
            # Deselect if clicking on empty space (only if not holding Ctrl/Cmd)
            if not (event.key == "control" or event.key == "cmd"):
                self.selected_element_ids.clear()
                self.update_selection_info()
                self.update_plot_preserve_zoom()

    def point_to_line_distance(self, point, line_start, line_end):
        """Calculate distance from point to line segment"""
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end

        # Calculate distance from point to line segment
        A = px - x1
        B = py - y1
        C = x2 - x1
        D = y2 - y1

        dot = A * C + B * D
        len_sq = C * C + D * D

        if len_sq == 0:
            # Line segment is actually a point
            return math.sqrt(A * A + B * B)

        param = dot / len_sq

        if param < 0:
            xx, yy = x1, y1
        elif param > 1:
            xx, yy = x2, y2
        else:
            xx = x1 + param * C
            yy = y1 + param * D

        dx = px - xx
        dy = py - yy

        return math.sqrt(dx * dx + dy * dy)

    def update_selection_info(self):
        """Update the selected element info display"""
        if self.selected_element_id is None:
            self.selected_info_var.set("None")
            return

        element_data = self.element_data.get(self.selected_element_id)
        if element_data:
            x, y, radius, geom_type, _ = element_data
            if geom_type == "CIRCLE":
                self.selected_info_var.set(
                    f"Circle: center=({x:.1f}, {y:.1f}), radius={radius:.1f}mm"
                )
            elif geom_type == "LINE":
                # For lines, x and y are tuples of start/end points
                start_x, end_x = x
                start_y, end_y = y
                self.selected_info_var.set(
                    f"Line: ({start_x:.1f}, {start_y:.1f}) to ({end_x:.1f}, {end_y:.1f})"
                )
            elif geom_type in ["LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"]:
                # For polylines and flattened curves, x and y are lists of coordinates
                if len(x) > 0:
                    type_name = {
                        "LWPOLYLINE": "LW Polyline",
                        "POLYLINE": "Polyline",
                        "ELLIPSE": "Ellipse",
                        "SPLINE": "Spline",
                    }.get(geom_type, geom_type)
                    self.selected_info_var.set(
                        f"{type_name}: {len(x)} points, first=({x[0]:.1f}, {y[0]:.1f})"
                    )
                else:
                    self.selected_info_var.set(f"{geom_type}: no points")
            elif geom_type == "ARC":
                # For arcs, x and y are center coordinates, radius is the radius
                # Get arc parameters from original data
                if len(element_data) >= 5:
                    _, _, _, _, original_data = element_data
                    if len(original_data) >= 6:
                        _, _, _, start_angle, end_angle, _ = original_data
                        self.selected_info_var.set(
                            f"Arc: center=({x:.1f}, {y:.1f}), radius={radius:.1f}mm, angles=({start_angle:.1f}°, {end_angle:.1f}°)"
                        )
                    else:
                        self.selected_info_var.set(
                            f"Arc: center=({x:.1f}, {y:.1f}), radius={radius:.1f}mm"
                        )
                else:
                    self.selected_info_var.set(
                        f"Arc: center=({x:.1f}, {y:.1f}), radius={radius:.1f}mm"
                    )
            elif geom_type == "TEXT_MARKER":
                # For text markers, show the text content
                if len(element_data) >= 5 and isinstance(element_data[4], dict):
                    text_content = element_data[4].get("content", "TEXT")
                    text_type = element_data[4].get("type", "TEXT")
                    self.selected_info_var.set(
                        f"{text_type} Marker: '{text_content[:30]}' at ({x:.1f}, {y:.1f}) [Not cuttable]"
                    )
                else:
                    self.selected_info_var.set(
                        f"Text Marker at ({x:.1f}, {y:.1f}) [Not cuttable]"
                    )
            else:
                # For other geometry types, just show the type
                self.selected_info_var.set(f"{geom_type}: selected")
        else:
            self.selected_info_var.set("Unknown element")

    def mark_engraving(self):
        """Mark selected elements for engraving"""
        if not self.selected_element_ids:
            messagebox.showwarning("Warning", "Please select elements first")
            return

        # Check for removed elements
        removed_selected = [
            eid for eid in self.selected_element_ids if eid in self.removed_elements
        ]
        if removed_selected:
            messagebox.showwarning(
                "Warning", "Cannot mark removed elements for engraving"
            )
            return

        # Save state before making changes
        self.save_state()

        # Mark all selected elements for engraving
        for element_id in self.selected_element_ids:
            self.engraved_elements.add(element_id)

        self.selected_element_ids.clear()  # Clear selection to show red engraving color
        self.update_plot_preserve_zoom()
        self.update_statistics()
        self.update_selection_info()

    def remove_element(self):
        """Remove selected element"""
        if self.selected_element_id is None:
            messagebox.showwarning("Warning", "Please select an element first")
            return

        # Save state before making changes
        self.save_state()

        self.removed_elements.add(self.selected_element_id)
        self.engraved_elements.discard(
            self.selected_element_id
        )  # Remove from engraving if it was there
        self.selected_element_id = None  # Clear selection since element is now removed
        self.update_plot_preserve_zoom()
        self.update_statistics()
        self.update_selection_info()

    def reset_selection(self):
        """Reset all selections and modifications"""
        self.removed_elements.clear()
        self.engraved_elements.clear()
        self.clipped_elements.clear()
        self.selected_element_id = None
        self.origin_offset = (0.0, 0.0)
        self.x_offset_var.set("0.0")
        self.y_offset_var.set("0.0")

        if self.original_points:
            self.current_points = self.original_points.copy()
            self.update_plot()
            self.update_statistics()
        else:
            self.update_selection_info()

    def select_all_for_engraving(self):
        """Mark all non-removed elements for engraving"""
        if not self.current_points:
            messagebox.showwarning("Warning", "No DXF file loaded")
            return

        # Get all unique element IDs that are not removed
        all_element_ids = set()
        for x, y, radius, geom_type, element_id in self.current_points:
            if element_id not in self.removed_elements:
                all_element_ids.add(element_id)

        # Add all non-removed elements to engraved set
        self.engraved_elements.update(all_element_ids)

        # Clear current selection
        self.selected_element_id = None

        # Update display
        self.update_plot()
        self.update_statistics()
        self.update_selection_info()

    def update_plot_preserve_zoom(self):
        """Update plot while preserving current zoom level"""
        # Store current axis limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # Update the plot
        self.update_plot()

        # Restore axis limits
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

        # Redraw canvas
        self.canvas.draw()

    def update_plot(self):
        """Update the matplotlib plot with original DXF geometry"""
        self.ax.clear()
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_title("DXF Geometry - Load file and click 'Generate G-code'")

        # Clear clipped elements before recalculating
        self.clipped_elements.clear()

        # Get unique elements (since lines/polylines have multiple points)
        unique_elements = {}
        for x, y, radius, geom_type, element_id in self.current_points:
            if element_id not in unique_elements:
                unique_elements[element_id] = {
                    "geom_type": geom_type,
                    "radius": radius,
                    "points": [],
                }
            unique_elements[element_id]["points"].append((x, y))

        # Check which elements are clipped (outside workspace)
        for element_id, element_info in unique_elements.items():
            geom_type = element_info["geom_type"]
            radius = element_info["radius"]
            points = element_info["points"]

            if geom_type == "LINE":
                if len(points) >= 2:
                    start_x, start_y = points[0]
                    end_x, end_y = points[1]
                    # Debug print removed for cleaner output
                    clipped_line = self.clip_line_to_workspace(
                        start_x, start_y, end_x, end_y
                    )
                    if not clipped_line:
                        self.clipped_elements.add(element_id)

            elif geom_type == "CIRCLE":
                if len(points) >= 1:
                    cx, cy = points[0]
                    max_x = self.gcode_settings["max_workspace_x"]
                    max_y = self.gcode_settings["max_workspace_y"]
                    # Debug print removed for cleaner output
                    circle_in_workspace = (
                        cx - radius <= max_x and cx + radius >= 0
                    ) and (cy - radius <= max_y and cy + radius >= 0)
                    if not circle_in_workspace:
                        self.clipped_elements.add(element_id)

            elif geom_type in ["LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"]:
                if len(points) >= 2:
                    polyline_in_workspace = False
                    for x, y in points:
                        if self.is_within_workspace(x, y):
                            polyline_in_workspace = True
                            break
                    if not polyline_in_workspace:
                        self.clipped_elements.add(element_id)
                        # Debug print removed for cleaner output

            elif geom_type == "ARC":
                if len(points) >= 1:
                    cx, cy = points[0]
                    max_x = self.gcode_settings["max_workspace_x"]
                    max_y = self.gcode_settings["max_workspace_y"]

                    # Check if arc intersects with workspace
                    # An arc intersects if its bounding box intersects with workspace
                    arc_in_workspace = self.arc_intersects_workspace(
                        cx, cy, radius, element_id
                    )
                    if not arc_in_workspace:
                        self.clipped_elements.add(element_id)

        # Debug prints removed for cleaner output

        # Plot each unique element
        for element_id, element_info in unique_elements.items():
            if element_id in self.removed_elements:
                continue

            geom_type = element_info["geom_type"]
            radius = element_info["radius"]
            points = element_info["points"]

            is_engraved = element_id in self.engraved_elements
            is_selected = element_id in self.selected_element_ids

            # Choose colors and styles
            if is_selected:
                # Selected elements get special highlighting
                line_color = "lime"  # Bright green for selection
                marker_color = "lime"
                line_width = 4
                alpha = 1.0  # Full opacity for selected
            elif element_id in self.clipped_elements:
                # Clipped elements (outside workspace) - gray/dashed
                line_color = "gray"
                marker_color = "gray"
                line_width = 1
                alpha = 0.5
            elif is_engraved:
                line_color = "red"
                marker_color = "red"
                line_width = 3
                alpha = 0.8
            else:
                line_color = "blue"
                marker_color = "blue"
                line_width = 2
                alpha = 0.7

            if geom_type == "LINE":
                if len(points) >= 2:
                    x_coords = [p[0] for p in points]
                    y_coords = [p[1] for p in points]
                    # Draw line segment
                    linestyle = "--" if element_id in self.clipped_elements else "-"
                    self.ax.plot(
                        x_coords,
                        y_coords,
                        color=line_color,
                        linewidth=line_width,
                        alpha=alpha,
                        linestyle=linestyle,
                    )
                    # Draw markers at endpoints
                    marker_size = 15 if is_selected else 5
                    self.ax.scatter(
                        x_coords,
                        y_coords,
                        c=marker_color,
                        s=marker_size,
                        marker="o",
                        alpha=alpha,
                    )

            elif geom_type == "CIRCLE":
                if len(points) >= 1:
                    center_x, center_y = points[0]
                    # Draw circle
                    circle = plt.Circle(
                        (center_x, center_y),
                        radius,
                        color=line_color,
                        fill=False,
                        linewidth=line_width,
                        alpha=alpha,
                    )
                    self.ax.add_patch(circle)

            elif geom_type == "ARC":
                if len(points) >= 1:
                    center_x, center_y = points[0]
                    # Get arc parameters from element data
                    element_data = self.element_data.get(element_id)
                    if element_data and len(element_data) >= 5:
                        _, _, _, _, original_data = element_data
                        if len(original_data) >= 6:
                            _, _, _, start_angle, end_angle, _ = original_data
                            # Convert angles from degrees to radians if needed
                            # DXF angles are typically in degrees
                            start_rad = math.radians(start_angle)
                            end_rad = math.radians(end_angle)

                            # Calculate arc span
                            arc_span = end_rad - start_rad
                            if arc_span < 0:
                                arc_span += 2 * math.pi

                            # Draw arc using matplotlib Arc
                            from matplotlib.patches import Arc

                            arc = Arc(
                                (center_x, center_y),
                                2 * radius,  # width
                                2 * radius,  # height
                                angle=0,  # rotation
                                theta1=math.degrees(
                                    start_rad
                                ),  # start angle in degrees
                                theta2=math.degrees(end_rad),  # end angle in degrees
                                color=line_color,
                                linewidth=line_width,
                                alpha=alpha,
                            )
                            self.ax.add_patch(arc)

            elif geom_type in ["LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"]:
                if len(points) >= 2:
                    x_coords = [p[0] for p in points]
                    y_coords = [p[1] for p in points]
                    # Draw connected polyline
                    linestyle = "--" if element_id in self.clipped_elements else "-"
                    self.ax.plot(
                        x_coords,
                        y_coords,
                        color=line_color,
                        linewidth=line_width,
                        alpha=alpha,
                        linestyle=linestyle,
                    )
                    # Draw markers at vertices
                    marker_size = 15 if is_selected else 5
                    marker_shape = (
                        "s" if geom_type in ["LWPOLYLINE", "POLYLINE"] else "o"
                    )
                    self.ax.scatter(
                        x_coords,
                        y_coords,
                        c=marker_color,
                        s=marker_size,
                        marker=marker_shape,
                        alpha=alpha,
                    )

            elif geom_type == "TEXT_MARKER":
                # Render text markers for text that couldn't be exploded
                if len(points) >= 1:
                    x, y = points[0]
                    # Draw an X marker
                    self.ax.plot(
                        x,
                        y,
                        "x",
                        color="orange",
                        markersize=12,
                        markeredgewidth=2,
                        alpha=0.8,
                    )
                    # Add text label if available
                    element_data = self.element_data.get(element_id)
                    if (
                        element_data
                        and len(element_data) >= 5
                        and isinstance(element_data[4], dict)
                    ):
                        text_content = element_data[4].get("content", "TEXT")
                        # Truncate long text
                        if len(text_content) > 20:
                            text_content = text_content[:17] + "..."
                        self.ax.text(
                            x,
                            y + 1,
                            text_content,
                            fontsize=7,
                            color="orange",
                            alpha=0.7,
                            ha="center",
                        )

        # Set equal aspect ratio and auto-scale
        self.ax.set_aspect("equal")
        self.canvas.draw()

        # Ensure input fields remain interactive after plot updates
        self.ensure_input_fields_active()

    def on_canvas_click(self, event):
        """Handle canvas clicks to ensure input fields can still receive focus"""
        # This method is called when the matplotlib canvas is clicked
        # It helps ensure that input fields can still receive focus
        pass

    def debug_input_field(self, event):
        """Debug function to check input field state when clicked"""
        widget = event.widget
        try:
            state = widget.cget("state")
            focus_widget = self.root.focus_get()
            # Debug information removed for cleaner output

            # Force the field to be active and focused
            widget.configure(state="normal")
            # Use after_idle to ensure focus is set after the click event
            self.root.after_idle(lambda: widget.focus_set())
            # Also select all text for easy editing
            self.root.after_idle(lambda: widget.select_range(0, tk.END))

        except Exception as e:
            # Debug error removed for cleaner output
            pass

    def ensure_input_fields_active(self):
        """Ensure input fields remain active and responsive"""
        try:
            # Re-enable input fields if they somehow got disabled
            if hasattr(self, "x_entry"):
                self.x_entry.configure(state="normal")
                # Ensure the entry can receive focus
                self.root.after_idle(
                    lambda: (
                        self.x_entry.focus_set()
                        if self.x_entry.winfo_exists()
                        else None
                    )
                )
            if hasattr(self, "y_entry"):
                self.y_entry.configure(state="normal")
                # Ensure the entry can receive focus
                self.root.after_idle(
                    lambda: (
                        self.y_entry.focus_set()
                        if self.y_entry.winfo_exists()
                        else None
                    )
                )

            # Ensure the root window can receive focus
            self.root.focus_set()
        except Exception as e:
            print(f"Warning: Could not ensure input fields are active: {e}")

    def update_statistics(self):
        """Update statistics display"""
        if not self.original_points:
            self.stats_var.set("No file loaded")
            return

        total_elements = len(self.original_points)
        removed_count = len(self.removed_elements)
        engraved_count = len(self.engraved_elements)
        clipped_count = len(self.clipped_elements)
        remaining_count = total_elements - removed_count

        stats_text = f"""Total elements: {total_elements}
Removed: {removed_count}
Engraved: {engraved_count}
Clipped (outside workspace): {clipped_count}
Remaining: {remaining_count}
Origin offset: ({self.origin_offset[0]:.1f}, {self.origin_offset[1]:.1f})
DXF Units: {self.dxf_units}"""

        self.stats_var.set(stats_text)

    def export_gcode(self):
        """Export G-code for the current design"""
        if not self.current_points:
            messagebox.showwarning("Warning", "No DXF file loaded")
            return

        # Filter points for engraving only
        engraving_points = []
        for x, y, radius, geom_type, element_id in self.current_points:
            if (
                element_id in self.engraved_elements
                and element_id not in self.removed_elements
            ):
                engraving_points.append((x, y, radius, geom_type))

        if not engraving_points:
            messagebox.showwarning("Warning", "No elements marked for engraving")
            return

        # Generate G-code
        gcode = self.generate_gcode(engraving_points)

        # Show preview window
        self.show_gcode_preview(gcode)

    def generate_gcode(self, points):
        """Generate G-code from points"""
        gcode = []

        # Add preamble
        preamble_lines = self.gcode_settings["preamble"].strip().split("\n")
        gcode.append("; preamble")
        gcode.extend(preamble_lines)
        gcode.append("; end preamble")

        # Group points by element_id to get complete geometry
        elements_by_id = {}
        for x, y, radius, geom_type, element_id in self.current_points:
            if (
                element_id in self.engraved_elements
                and element_id not in self.removed_elements
            ):
                if element_id not in elements_by_id:
                    elements_by_id[element_id] = {
                        "geom_type": geom_type,
                        "radius": radius,
                        "points": [],
                    }
                elements_by_id[element_id]["points"].append((x, y))

        # Track current position for G0 moves between elements
        current_x, current_y = 0.0, 0.0
        last_engraved_x, last_engraved_y = 0.0, 0.0

        # Optimize toolpath by sorting elements to minimize travel distance (if enabled)
        if self.gcode_settings.get("optimize_toolpath", True):
            optimized_elements = self.optimize_toolpath(
                elements_by_id, current_x, current_y
            )
        else:
            optimized_elements = list(elements_by_id.items())
            print("Toolpath optimization disabled - using original element order")

        # Generate G-code for each element in optimized order
        for element_id, element_info in optimized_elements:
            geom_type = element_info["geom_type"]
            radius = element_info["radius"]

            if geom_type == "LINE":
                # Use the offset coordinates from current_points (already includes X/Y offsets)
                line_points = element_info["points"]
                if len(line_points) >= 2:
                    start_x, start_y = line_points[0]
                    end_x, end_y = line_points[1]

                    # Clip line to workspace using intersection logic
                    clipped_line = self.clip_line_to_workspace(
                        start_x, start_y, end_x, end_y
                    )

                    if clipped_line:
                        # Only add header if we're actually going to engrave
                        gcode.append("; === LINE GEOMETRY ===")
                        (
                            clipped_start_x,
                            clipped_start_y,
                            clipped_end_x,
                            clipped_end_y,
                        ) = clipped_line

                        # G0 move to start point if not already there
                        if (current_x, current_y) != (clipped_start_x, clipped_start_y):
                            gcode.append(
                                f"G0 X{clipped_start_x:.3f} Y{clipped_start_y:.3f} Z{self.gcode_settings['cutting_z']:.3f}"
                            )

                        # Engrave to clipped end point combined laser power into move
                        gcode.append(
                            f"G1 X{clipped_end_x:.3f} Y{clipped_end_y:.3f} F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Engrave line"
                        )

                        # Update current position
                        current_x, current_y = clipped_end_x, clipped_end_y
                        last_engraved_x, last_engraved_y = clipped_end_x, clipped_end_y

                        # Conditionally raise Z between paths
                        if self.gcode_settings["raise_laser_between_paths"]:
                            gcode.append("G0 Z-5.0 ; Raise laser between paths")

                        gcode.append("")  # Blank line between elements
                    else:
                        # Line is completely outside workspace - no G-code generated
                        # Update position for next element but don't generate any G-code
                        current_x, current_y = end_x, end_y

            elif geom_type == "CIRCLE":
                # Use the offset coordinates from current_points (already includes X/Y offsets)
                circle_points = element_info["points"]
                if len(circle_points) >= 1:
                    cx, cy = circle_points[0]
                    radius = element_info["radius"]

                    # Check if circle intersects with workspace
                    max_x = self.gcode_settings["max_workspace_x"]
                    max_y = self.gcode_settings["max_workspace_y"]
                    circle_in_workspace = (
                        cx - radius <= max_x and cx + radius >= 0
                    ) and (cy - radius <= max_y and cy + radius >= 0)

                    if circle_in_workspace:
                        # Only add header if we're actually going to engrave
                        gcode.append("; === CIRCLE GEOMETRY ===")
                        # Position to circle start point (0 degrees - right side of circle) with Z at cutting height
                        start_x = cx + radius
                        start_y = cy
                        clipped_start_x, clipped_start_y = self.clip_to_workspace(
                            start_x, start_y
                        )

                        # G0 move to start point if not already there
                        if (current_x, current_y) != (clipped_start_x, clipped_start_y):
                            gcode.append(
                                f"G0 X{clipped_start_x:.3f} Y{clipped_start_y:.3f} Z{self.gcode_settings['cutting_z']:.3f}"
                            )

                        # Generate full circle using two 180-degree G3 arcs (CCW)
                        # A full circle requires two semicircular arcs because most controllers
                        # can't handle a full 360-degree arc in one command

                        # First semicircle: 0° to 180° (right side to left side)
                        halfway_x = cx - radius  # Left side of circle
                        halfway_y = cy

                        # Second semicircle endpoint (back to start)
                        end_x = cx + radius
                        end_y = cy

                        # Check if circle is entirely within workspace
                        # Simple check: if center +/- radius is within bounds
                        circle_fully_inside = (
                            self.is_within_workspace(cx + radius, cy)
                            and self.is_within_workspace(cx - radius, cy)
                            and self.is_within_workspace(cx, cy + radius)
                            and self.is_within_workspace(cx, cy - radius)
                        )

                        if circle_fully_inside:
                            # Entire circle is inside - use two clean G3 arcs
                            # First semicircle: start -> halfway (0° to 180°)
                            i_offset1 = (
                                cx - start_x
                            )  # -radius (going from right to center)
                            j_offset1 = cy - start_y  # 0
                            gcode.append(
                                f"G3 X{halfway_x:.3f} Y{halfway_y:.3f} I{i_offset1:.3f} J{j_offset1:.3f} "
                                f"F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Circle 1st half"
                            )

                            # Second semicircle: halfway -> end (180° to 360°)
                            i_offset2 = (
                                cx - halfway_x
                            )  # radius (going from left to center)
                            j_offset2 = cy - halfway_y  # 0
                            gcode.append(
                                f"G3 X{end_x:.3f} Y{end_y:.3f} I{i_offset2:.3f} J{j_offset2:.3f} "
                                f"F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Circle 2nd half"
                            )
                        else:
                            # Circle partially outside workspace - use segmented arcs
                            # Break into 45-degree arc segments for better clipping
                            num_segments = 8  # 45 degrees each
                            angle_step = 2 * math.pi / num_segments

                            prev_x, prev_y = start_x, start_y
                            for i in range(1, num_segments + 1):
                                angle = i * angle_step
                                seg_end_x = cx + radius * math.cos(angle)
                                seg_end_y = cy + radius * math.sin(angle)

                                prev_inside = self.is_within_workspace(prev_x, prev_y)
                                end_inside = self.is_within_workspace(
                                    seg_end_x, seg_end_y
                                )

                                if prev_inside and end_inside:
                                    # Both inside - use G3 arc
                                    i_seg = cx - prev_x
                                    j_seg = cy - prev_y
                                    gcode.append(
                                        f"G3 X{seg_end_x:.3f} Y{seg_end_y:.3f} I{i_seg:.3f} J{j_seg:.3f} "
                                        f"F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Circle segment"
                                    )
                                elif prev_inside and not end_inside:
                                    # Exits workspace
                                    i_seg = cx - prev_x
                                    j_seg = cy - prev_y
                                    gcode.append(
                                        f"G3 X{seg_end_x:.3f} Y{seg_end_y:.3f} I{i_seg:.3f} J{j_seg:.3f} "
                                        f"F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Circle to boundary"
                                    )
                                elif not prev_inside and end_inside:
                                    # Enters workspace
                                    gcode.append(
                                        f"G0 X{prev_x:.3f} Y{prev_y:.3f} "
                                        f"Z{self.gcode_settings['cutting_z']:.3f} ; Move to entry"
                                    )
                                    i_seg = cx - prev_x
                                    j_seg = cy - prev_y
                                    gcode.append(
                                        f"G3 X{seg_end_x:.3f} Y{seg_end_y:.3f} I{i_seg:.3f} J{j_seg:.3f} "
                                        f"F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Circle from boundary"
                                    )

                                prev_x, prev_y = seg_end_x, seg_end_y

                        # Update current position to end of circle
                        end_angle = math.radians(360)
                        end_x = cx + radius * math.cos(end_angle)
                        end_y = cy + radius * math.sin(end_angle)
                        current_x, current_y = end_x, end_y
                        last_engraved_x, last_engraved_y = end_x, end_y

                        # Conditionally raise Z between paths
                        if self.gcode_settings["raise_laser_between_paths"]:
                            gcode.append("G0 Z-5.0 ; Raise laser between paths")

                        gcode.append("")  # Blank line between elements
                    else:
                        # Circle is completely outside workspace - no G-code generated
                        # Update position for next element but don't generate any G-code
                        current_x, current_y = cx, cy

            elif geom_type == "ARC":
                # Use the offset coordinates from current_points (already includes X/Y offsets)
                arc_points = element_info["points"]
                if len(arc_points) >= 1:
                    cx, cy = arc_points[0]
                    radius = element_info["radius"]

                    # Get arc parameters from element data
                    element_data = self.element_data.get(element_id)
                    if element_data and len(element_data) >= 5:
                        _, _, _, _, original_data = element_data
                        if len(original_data) >= 6:
                            _, _, _, start_angle, end_angle, _ = original_data

                            # Check if arc intersects with workspace
                            arc_in_workspace = self.arc_intersects_workspace(
                                cx, cy, radius, element_id
                            )

                            if arc_in_workspace:
                                # Convert angles to radians
                                start_rad = math.radians(start_angle)
                                end_rad = math.radians(end_angle)

                                # Calculate start and end points of arc
                                start_x = cx + radius * math.cos(start_rad)
                                start_y = cy + radius * math.sin(start_rad)
                                end_x = cx + radius * math.cos(end_rad)
                                end_y = cy + radius * math.sin(end_rad)

                                # Check if start and end points are both outside workspace
                                start_outside = not self.is_within_workspace(
                                    start_x, start_y
                                )
                                end_outside = not self.is_within_workspace(end_x, end_y)

                                # If both start and end points are outside workspace, check if any arc segment is inside
                                if start_outside and end_outside:
                                    # Sample points along the arc to see if any part is within workspace
                                    arc_span = end_rad - start_rad
                                    if arc_span < 0:
                                        arc_span += 2 * math.pi

                                    num_samples = max(
                                        10, int(arc_span / math.radians(5))
                                    )
                                    angle_step = arc_span / num_samples
                                    any_point_inside = False

                                    for i in range(num_samples + 1):
                                        angle = start_rad + i * angle_step
                                        x = cx + radius * math.cos(angle)
                                        y = cy + radius * math.sin(angle)
                                        if self.is_within_workspace(x, y):
                                            any_point_inside = True
                                            break

                                    # If no part of the arc is within workspace, skip G-code generation
                                    if not any_point_inside:
                                        current_x, current_y = end_x, end_y
                                        continue

                                # Only add header if we're actually going to engrave
                                gcode.append("; === ARC GEOMETRY ===")

                                # G0 move to start point if not already there and start point is accessible
                                if (current_x, current_y) != (start_x, start_y):
                                    # If start point is outside workspace, move to intersection instead
                                    if start_outside:
                                        # Find intersection point with workspace boundary
                                        intersection = (
                                            self.find_line_workspace_intersection(
                                                current_x,
                                                current_y,
                                                start_x,
                                                start_y,
                                                start_x,
                                                start_y,
                                            )
                                        )
                                        if intersection:
                                            gcode.append(
                                                f"G0 X{intersection[0]:.3f} Y{intersection[1]:.3f} Z{self.gcode_settings['cutting_z']:.3f}"
                                            )
                                        else:
                                            # No valid intersection, skip this arc
                                            current_x, current_y = end_x, end_y
                                            continue
                                    else:
                                        gcode.append(
                                            f"G0 X{start_x:.3f} Y{start_y:.3f} Z{self.gcode_settings['cutting_z']:.3f}"
                                        )

                                # Generate G2/G3 arc command instead of linear segments
                                # DXF arcs are always counterclockwise (CCW), use G3
                                # G3 format: G3 X[end] Y[end] I[dx to center] J[dy to center]

                                # Calculate arc span and check if it's a full circle
                                arc_span = end_rad - start_rad
                                if arc_span < 0:
                                    arc_span += 2 * math.pi

                                # Check if arc needs to be split for workspace clipping
                                # For now, if entire arc is within workspace, use single G3
                                start_in = self.is_within_workspace(start_x, start_y)
                                end_in = self.is_within_workspace(end_x, end_y)

                                # Calculate I and J offsets from start point to center
                                i_offset = cx - start_x
                                j_offset = cy - start_y

                                if start_in and end_in:
                                    # Both endpoints inside - simple G3 arc
                                    gcode.append(
                                        f"G3 X{end_x:.3f} Y{end_y:.3f} I{i_offset:.3f} J{j_offset:.3f} "
                                        f"F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Arc CCW"
                                    )
                                else:
                                    # Arc crosses workspace boundary - need to handle clipping
                                    # For complex cases, fall back to segmented approach
                                    # This ensures proper handling of arcs that partially exit workspace

                                    # Use smaller segments for clipped arcs (10-degree steps)
                                    num_segments = max(
                                        1, int(arc_span / math.radians(10))
                                    )
                                    angle_step = arc_span / num_segments

                                    prev_x, prev_y = start_x, start_y
                                    for i in range(1, num_segments + 1):
                                        angle = start_rad + i * angle_step
                                        seg_end_x = cx + radius * math.cos(angle)
                                        seg_end_y = cy + radius * math.sin(angle)

                                        # Check if segment endpoints are in workspace
                                        prev_inside = self.is_within_workspace(
                                            prev_x, prev_y
                                        )
                                        end_inside = self.is_within_workspace(
                                            seg_end_x, seg_end_y
                                        )

                                        if prev_inside and end_inside:
                                            # Both inside - use G3 arc segment
                                            i_seg = cx - prev_x
                                            j_seg = cy - prev_y
                                            gcode.append(
                                                f"G3 X{seg_end_x:.3f} Y{seg_end_y:.3f} I{i_seg:.3f} J{j_seg:.3f} "
                                                f"F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Arc segment"
                                            )
                                        elif prev_inside and not end_inside:
                                            # Exits workspace - use G3 to approximate boundary
                                            i_seg = cx - prev_x
                                            j_seg = cy - prev_y
                                            gcode.append(
                                                f"G3 X{seg_end_x:.3f} Y{seg_end_y:.3f} I{i_seg:.3f} J{j_seg:.3f} "
                                                f"F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Arc to boundary"
                                            )
                                        elif not prev_inside and end_inside:
                                            # Enters workspace - move to start then arc
                                            gcode.append(
                                                f"G0 X{prev_x:.3f} Y{prev_y:.3f} "
                                                f"Z{self.gcode_settings['cutting_z']:.3f} ; Move to entry"
                                            )
                                            i_seg = cx - prev_x
                                            j_seg = cy - prev_y
                                            gcode.append(
                                                f"G3 X{seg_end_x:.3f} Y{seg_end_y:.3f} I{i_seg:.3f} J{j_seg:.3f} "
                                                f"F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Arc from boundary"
                                            )

                                        prev_x, prev_y = seg_end_x, seg_end_y

                                # Update current position to end of arc
                                current_x, current_y = end_x, end_y
                                last_engraved_x, last_engraved_y = end_x, end_y

                                # Conditionally raise Z between paths
                                if self.gcode_settings["raise_laser_between_paths"]:
                                    gcode.append("G0 Z-5.0 ; Raise laser between paths")

                                gcode.append("")  # Blank line between elements
                            else:
                                # Arc is completely outside workspace - no G-code generated
                                # Update position for next element but don't generate any G-code
                                current_x, current_y = cx, cy

            elif geom_type in ["LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"]:
                # Use the offset coordinates from current_points (already includes X/Y offsets)
                polyline_points = element_info["points"]
                if len(polyline_points) >= 2:
                    # Check if any part of polyline is within workspace
                    polyline_in_workspace = False
                    for x, y in polyline_points:
                        if self.is_within_workspace(x, y):
                            polyline_in_workspace = True
                            break

                    if polyline_in_workspace:
                        # Only add header if we're actually going to engrave
                        gcode.append(f"; === {geom_type} GEOMETRY ===")
                        # Process polyline segments with proper clipping
                        first_x, first_y = polyline_points[0]

                        # G0 move to start point if not already there
                        if (current_x, current_y) != (first_x, first_y):
                            gcode.append(
                                f"G0 X{first_x:.3f} Y{first_y:.3f} Z{self.gcode_settings['cutting_z']:.3f}"
                            )

                        # Engrave polyline segments with proper clipping
                        for i in range(1, len(polyline_points)):
                            prev_x, prev_y = polyline_points[i - 1]
                            curr_x, curr_y = polyline_points[i]

                            # Clip line segment to workspace
                            clipped_line = self.clip_line_to_workspace(
                                prev_x, prev_y, curr_x, curr_y
                            )

                            if clipped_line:
                                (
                                    clipped_start_x,
                                    clipped_start_y,
                                    clipped_end_x,
                                    clipped_end_y,
                                ) = clipped_line

                                # Engrave to clipped end point
                                gcode.append(
                                    f"G1 X{clipped_end_x:.3f} Y{clipped_end_y:.3f} F{self.gcode_settings['feedrate']} S{self.gcode_settings['laser_power']}  ; Engrave polyline"
                                )

                        # Update current position to end of polyline
                        last_x, last_y = polyline_points[-1]
                        current_x, current_y = last_x, last_y
                        last_engraved_x, last_engraved_y = last_x, last_y

                        # Conditionally raise Z between paths
                        if self.gcode_settings["raise_laser_between_paths"]:
                            gcode.append("G0 Z-5.0 ; Raise laser between paths")

                        gcode.append("")  # Blank line between elements
                    else:
                        # Polyline is completely outside workspace - no G-code generated
                        # Update position for next element but don't generate any G-code
                        last_x, last_y = polyline_points[-1]
                        current_x, current_y = last_x, last_y

        # Add postscript
        postscript_lines = self.gcode_settings["postscript"].strip().split("\n")
        gcode.append("; postscript")
        gcode.extend(postscript_lines)

        return "\n".join(gcode)

    def is_within_workspace(self, x, y):
        """Check if a point is within workspace limits"""
        max_x = self.gcode_settings["max_workspace_x"]
        max_y = self.gcode_settings["max_workspace_y"]

        return 0.0 <= x <= max_x and 0.0 <= y <= max_y

    def arc_intersects_workspace(self, cx, cy, radius, element_id):
        """Check if an arc intersects with the workspace"""
        max_x = self.gcode_settings["max_workspace_x"]
        max_y = self.gcode_settings["max_workspace_y"]

        # Get arc parameters
        element_data = self.element_data.get(element_id)
        if not element_data or len(element_data) < 5:
            return False

        _, _, _, _, original_data = element_data
        if len(original_data) < 6:
            return False

        _, _, _, start_angle, end_angle, _ = original_data

        # Convert angles to radians
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)

        # First check if the arc's bounding box intersects with workspace
        # This is a quick rejection test
        if not (
            cx - radius <= max_x
            and cx + radius >= 0
            and cy - radius <= max_y
            and cy + radius >= 0
        ):
            return False

        # Check if any part of the arc intersects with workspace boundaries
        # Sample points along the arc and check if any are within workspace
        arc_span = end_rad - start_rad
        if arc_span < 0:
            arc_span += 2 * math.pi

        # Use more samples for better accuracy
        num_samples = max(20, int(arc_span / math.radians(2)))  # 2-degree steps
        angle_step = arc_span / num_samples

        for i in range(num_samples + 1):
            angle = start_rad + i * angle_step
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)

            if self.is_within_workspace(x, y):
                return True

        # If no sampled points are within workspace, the arc doesn't intersect
        return False

    def clip_to_workspace(self, x, y):
        """Clip coordinates to workspace limits"""
        max_x = self.gcode_settings["max_workspace_x"]
        max_y = self.gcode_settings["max_workspace_y"]

        clipped_x = max(0.0, min(x, max_x))
        clipped_y = max(0.0, min(y, max_y))

        return clipped_x, clipped_y

    def clip_line_to_workspace(self, start_x, start_y, end_x, end_y):
        """Clip a line segment to workspace boundaries using intersection logic"""
        max_x = self.gcode_settings["max_workspace_x"]
        max_y = self.gcode_settings["max_workspace_y"]

        # Check if both points are outside workspace
        start_out = not self.is_within_workspace(start_x, start_y)
        end_out = not self.is_within_workspace(end_x, end_y)

        if start_out and end_out:
            # Both points outside - check if line intersects workspace
            if not self.line_intersects_workspace(start_x, start_y, end_x, end_y):
                return None  # No intersection, skip this line

        # Find intersection points with workspace boundaries
        clipped_start_x, clipped_start_y = start_x, start_y
        clipped_end_x, clipped_end_y = end_x, end_y

        # Clip start point if outside
        if start_out:
            intersection = self.find_line_workspace_intersection(
                start_x, start_y, end_x, end_y, start_x, start_y
            )
            if intersection:
                clipped_start_x, clipped_start_y = intersection
            else:
                return None  # No valid intersection

        # Clip end point if outside
        if end_out:
            intersection = self.find_line_workspace_intersection(
                start_x, start_y, end_x, end_y, end_x, end_y
            )
            if intersection:
                clipped_end_x, clipped_end_y = intersection
            else:
                return None  # No valid intersection

        return (clipped_start_x, clipped_start_y, clipped_end_x, clipped_end_y)

    def line_intersects_workspace(self, x1, y1, x2, y2):
        """Check if a line segment intersects with the workspace rectangle"""
        max_x = self.gcode_settings["max_workspace_x"]
        max_y = self.gcode_settings["max_workspace_y"]

        # Check if line intersects with any of the four workspace boundaries
        boundaries = [
            (0, 0, max_x, 0),  # Bottom edge
            (0, max_y, max_x, max_y),  # Top edge
            (0, 0, 0, max_y),  # Left edge
            (max_x, 0, max_x, max_y),  # Right edge
        ]

        for bx1, by1, bx2, by2 in boundaries:
            if self.line_segments_intersect(x1, y1, x2, y2, bx1, by1, bx2, by2):
                return True
        return False

    def find_line_workspace_intersection(self, x1, y1, x2, y2, target_x, target_y):
        """Find intersection of line with workspace boundary closest to target point"""
        max_x = self.gcode_settings["max_workspace_x"]
        max_y = self.gcode_settings["max_workspace_y"]

        intersections = []

        # Check intersections with all four boundaries
        boundaries = [
            (0, 0, max_x, 0),  # Bottom edge
            (0, max_y, max_x, max_y),  # Top edge
            (0, 0, 0, max_y),  # Left edge
            (max_x, 0, max_x, max_y),  # Right edge
        ]

        for bx1, by1, bx2, by2 in boundaries:
            intersection = self.line_segment_intersection(
                x1, y1, x2, y2, bx1, by1, bx2, by2
            )
            if intersection:
                intersections.append(intersection)

        if not intersections:
            return None

        # Return intersection closest to target point
        closest = min(
            intersections, key=lambda p: (p[0] - target_x) ** 2 + (p[1] - target_y) ** 2
        )
        return closest

    def line_segments_intersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """Check if two line segments intersect"""

        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        A, B, C, D = (x1, y1), (x2, y2), (x3, y3), (x4, y4)
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    def line_segment_intersection(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """Find intersection point of two line segments, if it exists"""
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None  # Lines are parallel

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return (x, y)

        return None

    def show_gcode_preview(self, gcode, file_path=None):
        """Show G-code preview window with visual toolpath plot and G-code text"""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("G-code Toolpath Preview")
        preview_window.geometry("1000x800")
        preview_window.transient(self.root)
        preview_window.grab_set()

        # Store gcode in the window for access by nested functions
        preview_window.gcode_content = gcode

        # Main frame
        main_frame = ttk.Frame(preview_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(
            main_frame, text="G-code Toolpath Preview", font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Toolpath Plot Tab
        plot_frame = ttk.Frame(notebook)
        notebook.add(plot_frame, text="Toolpath Plot")

        # Legend removed as requested

        # Create matplotlib figure for toolpath visualization
        from matplotlib.backends.backend_tkagg import (
            FigureCanvasTkAgg,
            NavigationToolbar2Tk,
        )
        from matplotlib.figure import Figure
        import matplotlib.pyplot as plt

        fig = Figure(figsize=(8, 5), dpi=100)
        ax = fig.add_subplot(111)

        # Parse G-code and create toolpath visualization
        self.plot_gcode_toolpath(gcode, ax)

        # Embed plot in tkinter
        canvas = FigureCanvasTkAgg(fig, plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, pady=(0, 10))

        # Add navigation toolbar for zoom/pan functionality
        toolbar = NavigationToolbar2Tk(canvas, plot_frame)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")

        # Note: Removed focus event bindings that were interfering with matplotlib zoom/pan functionality

        # G-code Text Tab
        gcode_frame = ttk.Frame(notebook)
        notebook.add(gcode_frame, text="G-code Text")

        # G-code text widget with scrollbar
        text_frame = ttk.Frame(gcode_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        gcode_text = tk.Text(
            text_frame, wrap=tk.WORD, font=("Courier", 9), height=25, width=80
        )
        gcode_text.pack(side="left", fill="both", expand=True)

        # Scrollbar for G-code text
        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=gcode_text.yview
        )
        gcode_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Insert G-code into text widget
        gcode_text.insert(1.0, gcode)

        # Apply focus fixes to the G-code text widget
        def ensure_text_focus():
            """Ensure text widget maintains focus"""
            try:
                gcode_text.focus_set()
            except Exception as e:
                print(f"Warning: Could not ensure text focus: {e}")

        # Bind focus events to the text widget
        gcode_text.bind("<Button-1>", lambda e: ensure_text_focus())
        gcode_text.bind("<FocusIn>", lambda e: ensure_text_focus())

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")

        def save_gcode():
            """Save G-code to file automatically"""
            import os
            from datetime import datetime

            # Generate automatic filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dxf_gcode_{timestamp}.nc"
            save_file_path = os.path.join(os.getcwd(), filename)

            print(f"Attempting to save G-code to: {save_file_path}")
            print(
                f"G-code content length: {len(preview_window.gcode_content)} characters"
            )

            try:
                with open(save_file_path, "w") as f:
                    f.write(preview_window.gcode_content)
                print(f"Successfully saved G-code to: {save_file_path}")
                messagebox.showinfo("Success", f"G-code exported to:\n{save_file_path}")
                preview_window.destroy()
            except Exception as e:
                print(f"Error saving G-code: {str(e)}")
                messagebox.showerror("Error", f"Failed to save G-code:\n{str(e)}")

        def copy_gcode():
            """Copy G-code to clipboard"""
            preview_window.clipboard_clear()
            preview_window.clipboard_append(preview_window.gcode_content)
            messagebox.showinfo("Success", "G-code copied to clipboard")

        ttk.Button(button_frame, text="Copy G-code", command=copy_gcode).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(button_frame, text="Save G-code", command=save_gcode).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(button_frame, text="Close", command=preview_window.destroy).pack(
            side="right"
        )

    def plot_gcode_toolpath(self, gcode, ax):
        """Plot the G-code toolpath with color-coded moves"""
        lines = gcode.split("\n")

        current_x = 0.0
        current_y = 0.0
        last_x = 0.0
        last_y = 0.0

        positioning_lines = []
        engraving_lines = []

        for line in lines:
            line_upper = line.upper().strip()

            # Skip comments and empty lines
            if not line_upper or line_upper.startswith(";"):
                continue

            # Parse G0 (positioning) moves
            if line_upper.startswith("G0"):
                x_pos = None
                y_pos = None

                # Extract X and Y coordinates (handle commas)
                parts = line_upper.replace(",", " ").split()
                for part in parts:
                    if part.startswith("X"):
                        x_pos = float(part[1:])
                    elif part.startswith("Y"):
                        y_pos = float(part[1:])

                if x_pos is not None:
                    current_x = x_pos
                if y_pos is not None:
                    current_y = y_pos

                # Draw positioning move
                positioning_lines.append([(last_x, last_y), (current_x, current_y)])
                last_x = current_x
                last_y = current_y

            # Parse G1 (engraving) moves
            elif line_upper.startswith("G1"):
                x_pos = None
                y_pos = None

                # Extract X and Y coordinates (handle commas)
                parts = line_upper.replace(",", " ").split()
                for part in parts:
                    if part.startswith("X"):
                        x_pos = float(part[1:])
                    elif part.startswith("Y"):
                        y_pos = float(part[1:])

                if x_pos is not None:
                    current_x = x_pos
                if y_pos is not None:
                    current_y = y_pos

                # Draw engraving move
                engraving_lines.append([(last_x, last_y), (current_x, current_y)])
                last_x = current_x
                last_y = current_y

            # Parse G2 (clockwise arc) and G3 (counterclockwise arc) moves
            elif line_upper.startswith("G2") or line_upper.startswith("G3"):
                x_pos = None
                y_pos = None
                i_offset = None
                j_offset = None

                # Extract X, Y, I, J coordinates (handle commas)
                parts = line_upper.replace(",", " ").split()
                for part in parts:
                    if part.startswith("X"):
                        x_pos = float(part[1:])
                    elif part.startswith("Y"):
                        y_pos = float(part[1:])
                    elif part.startswith("I"):
                        i_offset = float(part[1:])
                    elif part.startswith("J"):
                        j_offset = float(part[1:])

                if x_pos is not None:
                    current_x = x_pos
                if y_pos is not None:
                    current_y = y_pos

                # Calculate arc if we have I and J offsets
                if i_offset is not None and j_offset is not None:
                    # Calculate center of arc
                    center_x = last_x + i_offset
                    center_y = last_y + j_offset

                    # Calculate start and end angles
                    start_angle = math.atan2(last_y - center_y, last_x - center_x)
                    end_angle = math.atan2(current_y - center_y, current_x - center_x)

                    # Calculate radius
                    radius = math.sqrt(i_offset**2 + j_offset**2)

                    # Determine arc direction (G2 = CW, G3 = CCW)
                    is_ccw = line_upper.startswith("G3")

                    # Calculate arc span
                    if is_ccw:
                        # Counterclockwise
                        if end_angle <= start_angle:
                            end_angle += 2 * math.pi
                        arc_span = end_angle - start_angle
                    else:
                        # Clockwise
                        if end_angle >= start_angle:
                            end_angle -= 2 * math.pi
                        arc_span = start_angle - end_angle

                    # Break arc into segments for visualization (use 5-degree steps)
                    num_segments = max(8, int(abs(arc_span) / math.radians(5)))
                    angle_step = (end_angle - start_angle) / num_segments

                    # Generate arc segments
                    prev_arc_x = last_x
                    prev_arc_y = last_y

                    for i in range(1, num_segments + 1):
                        angle = start_angle + i * angle_step
                        arc_x = center_x + radius * math.cos(angle)
                        arc_y = center_y + radius * math.sin(angle)

                        # Add segment to engraving lines
                        engraving_lines.append(
                            [(prev_arc_x, prev_arc_y), (arc_x, arc_y)]
                        )

                        prev_arc_x = arc_x
                        prev_arc_y = arc_y
                else:
                    # No I/J offsets, treat as straight line (fallback)
                    engraving_lines.append([(last_x, last_y), (current_x, current_y)])

                last_x = current_x
                last_y = current_y

        # Plot positioning moves in green with arrows
        for i, line_segment in enumerate(positioning_lines):
            start, end = line_segment
            ax.plot(
                [start[0], end[0]], [start[1], end[1]], "g-", linewidth=2, alpha=0.8
            )

            # Add arrow only every few segments for circles (reduce clutter)
            # For short segments (likely circles), show arrows every 8th segment
            segment_length = (
                (end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2
            ) ** 0.5
            if segment_length < 5:  # Likely a circle segment
                if i % 8 != 0:  # Skip most arrows for circles
                    continue
            else:  # Regular line segments - show all arrows
                pass

            # Add arrow in the middle of the line segment
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2

            # Calculate arrow direction
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = (dx**2 + dy**2) ** 0.5

            if length > 0:
                # Normalize direction vector
                dx_norm = dx / length
                dy_norm = dy / length

                # Arrow length (proportional to line length, scaled for small circles)
                arrow_length = max(0.3, length * 0.15)

                # If this is part of a circle (short segments), scale arrow length down
                if length < 5:  # Likely a circle segment
                    arrow_length = max(
                        0.2, length * 0.3
                    )  # Shorter arrows for small segments

                # Draw arrow
                ax.annotate(
                    "",
                    xy=(
                        mid_x + dx_norm * arrow_length / 2,
                        mid_y + dy_norm * arrow_length / 2,
                    ),
                    xytext=(
                        mid_x - dx_norm * arrow_length / 2,
                        mid_y - dy_norm * arrow_length / 2,
                    ),
                    arrowprops=dict(arrowstyle="->", color="green", lw=1.5, alpha=0.8),
                )

        # Plot engraving moves in red with arrows
        for i, line_segment in enumerate(engraving_lines):
            start, end = line_segment
            ax.plot(
                [start[0], end[0]], [start[1], end[1]], "r-", linewidth=2, alpha=0.8
            )

            # Add arrow only every few segments for circles (reduce clutter)
            # For short segments (likely circles), show arrows every 8th segment
            segment_length = (
                (end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2
            ) ** 0.5
            if segment_length < 5:  # Likely a circle segment
                if i % 8 != 0:  # Skip most arrows for circles
                    continue
            else:  # Regular line segments - show all arrows
                pass

            # Add arrow in the middle of the line segment
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2

            # Calculate arrow direction
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = (dx**2 + dy**2) ** 0.5

            if length > 0:
                # Normalize direction vector
                dx_norm = dx / length
                dy_norm = dy / length

                # Arrow length (proportional to line length, scaled for small circles)
                arrow_length = max(0.3, length * 0.15)

                # If this is part of a circle (short segments), scale arrow length down
                if length < 5:  # Likely a circle segment
                    arrow_length = max(
                        0.2, length * 0.3
                    )  # Shorter arrows for small segments

                # Draw arrow
                ax.annotate(
                    "",
                    xy=(
                        mid_x + dx_norm * arrow_length / 2,
                        mid_y + dy_norm * arrow_length / 2,
                    ),
                    xytext=(
                        mid_x - dx_norm * arrow_length / 2,
                        mid_y - dy_norm * arrow_length / 2,
                    ),
                    arrowprops=dict(arrowstyle="->", color="red", lw=1.5, alpha=0.8),
                )

        # Set up the plot
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_title("G-code Toolpath Preview")
        ax.grid(True, alpha=0.3)
        ax.set_aspect("equal")

        # Add start point marker
        if positioning_lines or engraving_lines:
            ax.plot(0, 0, "go", markersize=8)

    def open_settings(self):
        """Open the G-code settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("G-code Settings")
        settings_window.geometry("600x500")
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Main frame
        main_frame = ttk.Frame(settings_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Variables for the form
        preamble_var = tk.StringVar(value=self.gcode_settings["preamble"])
        postscript_var = tk.StringVar(value=self.gcode_settings["postscript"])
        laser_power_var = tk.IntVar(value=self.gcode_settings["laser_power"])
        cutting_z_var = tk.DoubleVar(value=self.gcode_settings["cutting_z"])
        feedrate_var = tk.IntVar(value=self.gcode_settings["feedrate"])
        max_x_var = tk.DoubleVar(value=self.gcode_settings["max_workspace_x"])
        max_y_var = tk.DoubleVar(value=self.gcode_settings["max_workspace_y"])

        # Preamble section
        ttk.Label(main_frame, text="G-code Preamble:", font=("Arial", 10, "bold")).pack(
            anchor="w", pady=(0, 5)
        )
        preamble_text = tk.Text(main_frame, height=4, width=70)
        preamble_text.pack(fill="x", pady=(0, 10))
        preamble_text.insert("1.0", preamble_var.get())

        # Postscript section
        ttk.Label(
            main_frame, text="G-code Postscript:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))
        postscript_text = tk.Text(main_frame, height=4, width=70)
        postscript_text.pack(fill="x", pady=(0, 10))
        postscript_text.insert("1.0", postscript_var.get())

        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Laser Settings", padding="10")
        settings_frame.pack(fill="x", pady=(0, 20))

        # Laser Power
        power_frame = ttk.Frame(settings_frame)
        power_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(power_frame, text="Laser Power (0-255):").pack(side="left")
        power_spinbox = ttk.Spinbox(
            power_frame, from_=0, to=255, width=10, textvariable=laser_power_var
        )
        power_spinbox.pack(side="right")

        # Cutting Z Height
        z_frame = ttk.Frame(settings_frame)
        z_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(z_frame, text="Cutting Z Height (mm):").pack(side="left")
        z_spinbox = ttk.Spinbox(
            z_frame,
            from_=-10.0,
            to=0.0,
            increment=0.1,
            width=10,
            textvariable=cutting_z_var,
        )
        z_spinbox.pack(side="right")

        # Feedrate
        feedrate_frame = ttk.Frame(settings_frame)
        feedrate_frame.pack(fill="x")
        ttk.Label(feedrate_frame, text="Feedrate (mm/min):").pack(side="left")
        feedrate_spinbox = ttk.Spinbox(
            feedrate_frame,
            from_=100,
            to=5000,
            increment=100,
            width=10,
            textvariable=feedrate_var,
        )
        feedrate_spinbox.pack(side="right")

        # Max Workspace X
        max_x_frame = ttk.Frame(settings_frame)
        max_x_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(max_x_frame, text="Max Workspace X (mm):").pack(side="left")
        max_x_spinbox = ttk.Spinbox(
            max_x_frame,
            from_=50.0,
            to=1000.0,
            increment=10.0,
            width=10,
            textvariable=max_x_var,
        )
        max_x_spinbox.pack(side="right")

        # Max Workspace Y
        max_y_frame = ttk.Frame(settings_frame)
        max_y_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(max_y_frame, text="Max Workspace Y (mm):").pack(side="left")
        max_y_spinbox = ttk.Spinbox(
            max_y_frame,
            from_=50.0,
            to=1000.0,
            increment=10.0,
            width=10,
            textvariable=max_y_var,
        )
        max_y_spinbox.pack(side="right")

        # Raise laser between paths checkbox
        raise_laser_var = tk.BooleanVar(
            value=self.gcode_settings.get("raise_laser_between_paths", False)
        )
        ttk.Checkbutton(
            settings_frame, text="Raise laser between paths", variable=raise_laser_var
        ).pack(anchor="w", pady=(5, 0))

        # Optimize toolpath checkbox
        optimize_toolpath_var = tk.BooleanVar(
            value=self.gcode_settings.get("optimize_toolpath", True)
        )
        ttk.Checkbutton(
            settings_frame,
            text="Optimize toolpath (reduce travel distance)",
            variable=optimize_toolpath_var,
        ).pack(anchor="w", pady=(5, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))

        def save_settings():
            """Save the settings and close the window"""
            self.gcode_settings["preamble"] = preamble_text.get("1.0", "end-1c")
            self.gcode_settings["postscript"] = postscript_text.get("1.0", "end-1c")
            self.gcode_settings["laser_power"] = laser_power_var.get()
            self.gcode_settings["cutting_z"] = cutting_z_var.get()
            self.gcode_settings["feedrate"] = feedrate_var.get()
            self.gcode_settings["max_workspace_x"] = max_x_var.get()
            self.gcode_settings["max_workspace_y"] = max_y_var.get()
            self.gcode_settings["raise_laser_between_paths"] = raise_laser_var.get()
            self.gcode_settings["optimize_toolpath"] = optimize_toolpath_var.get()
            settings_window.destroy()

        ttk.Button(button_frame, text="Save", command=save_settings).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(
            side="right"
        )


def main():
    root = tk.Tk()
    app = DXFGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
