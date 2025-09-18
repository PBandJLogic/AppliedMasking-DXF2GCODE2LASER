#!/usr/bin/env python3
"""
Interactive DXF Viewer and Editor
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
        self.root.title("Interactive DXF 2 Template Editor")
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
            "preamble": "G21 ; Set units to millimeters\nG90 ; Absolute positioning\nG0 X0, Y0, Z-5 ; Go to zero position\n",
            "postscript": "G0 Z-5 ; Raise Z\nM5 ; Turn off laser\nG0 X0 Y0 ; Return to origin\n",
            "laser_power": 1000,
            "cutting_z": -30,
            "feedrate": 1500,
            "max_workspace_x": 800.0 - 10.0,
            "max_workspace_y": 400.0 - 10.0,
            "raise_laser_between_paths": False,
        }

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
            header_frame, text="DXF to\nTemplate\nEditor", font=("Arial", 16, "bold")
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
        self.x_entry.bind("<FocusIn>", lambda e: print("X entry focused"))
        self.x_entry.bind("<FocusOut>", lambda e: print("X entry lost focus"))

        # Y offset
        y_frame = ttk.Frame(origin_frame)
        y_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(y_frame, text="Y Offset (mm):").pack(side="left")
        self.y_offset_var = tk.StringVar(value="0.0")
        self.y_entry = ttk.Entry(y_frame, textvariable=self.y_offset_var, width=15)
        self.y_entry.pack(side="right")

        # Add event handlers to ensure proper focus
        self.y_entry.bind("<Button-1>", self.debug_input_field)
        self.y_entry.bind("<FocusIn>", lambda e: print("Y entry focused"))
        self.y_entry.bind("<FocusOut>", lambda e: print("Y entry lost focus"))

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

    def extract_geometry(self, file_path):
        """Extract geometry from DXF file (simplified version of the original function)"""
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        all_points = []

        for entity in msp:
            entity_type = entity.dxftype()

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

            elif entity_type == "LINE":
                # Store line as start and end points with same element ID
                start_pt = entity.dxf.start
                end_pt = entity.dxf.end
                element_id = self.get_next_element_id()

                all_points.append((start_pt.x, start_pt.y, 0, "LINE", element_id))
                all_points.append((end_pt.x, end_pt.y, 0, "LINE", element_id))

                self.element_data[element_id] = (
                    (start_pt.x, end_pt.x),  # X coordinates
                    (start_pt.y, end_pt.y),  # Y coordinates
                    0,
                    "LINE",
                    ((start_pt.x, start_pt.y), (end_pt.x, end_pt.y), "LINE"),
                )

            elif entity_type == "CIRCLE":
                center = entity.dxf.center
                radius = entity.dxf.radius
                element_id = self.get_next_element_id()
                all_points.append((center.x, center.y, radius, "CIRCLE", element_id))
                self.element_data[element_id] = (
                    center.x,
                    center.y,
                    radius,
                    "CIRCLE",
                    (center.x, center.y, radius, "CIRCLE"),
                )

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
                elif geom_type in ["LINE", "LWPOLYLINE"] and len(points) >= 1:
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

            elif geom_type == "LWPOLYLINE":
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
            elif geom_type == "LWPOLYLINE":
                # For polylines, x and y are lists of coordinates
                if len(x) > 0:
                    self.selected_info_var.set(
                        f"Polyline: {len(x)} points, first=({x[0]:.1f}, {y[0]:.1f})"
                    )
                else:
                    self.selected_info_var.set("Polyline: no points")
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
                    print(
                        f"Debug: Checking line {element_id}: ({start_x:.1f}, {start_y:.1f}) to ({end_x:.1f}, {end_y:.1f})"
                    )
                    clipped_line = self.clip_line_to_workspace(
                        start_x, start_y, end_x, end_y
                    )
                    if not clipped_line:
                        self.clipped_elements.add(element_id)
                        print(f"Debug: Line {element_id} clipped (outside workspace)")

            elif geom_type == "CIRCLE":
                if len(points) >= 1:
                    cx, cy = points[0]
                    max_x = self.gcode_settings["max_workspace_x"]
                    max_y = self.gcode_settings["max_workspace_y"]
                    print(
                        f"Debug: Checking circle {element_id}: center=({cx:.1f}, {cy:.1f}), radius={radius:.1f}"
                    )
                    circle_in_workspace = (
                        cx - radius <= max_x and cx + radius >= 0
                    ) and (cy - radius <= max_y and cy + radius >= 0)
                    if not circle_in_workspace:
                        self.clipped_elements.add(element_id)
                        print(f"Debug: Circle {element_id} clipped (outside workspace)")

            elif geom_type == "LWPOLYLINE":
                if len(points) >= 2:
                    polyline_in_workspace = False
                    for x, y in points:
                        if self.is_within_workspace(x, y):
                            polyline_in_workspace = True
                            break
                    if not polyline_in_workspace:
                        self.clipped_elements.add(element_id)
                        print(
                            f"Debug: Polyline {element_id} clipped (outside workspace)"
                        )

        print(
            f"Debug: Workspace bounds: X=0 to {self.gcode_settings['max_workspace_x']}, Y=0 to {self.gcode_settings['max_workspace_y']}"
        )
        print(
            f"Debug: Found {len(self.clipped_elements)} clipped elements: {list(self.clipped_elements)}"
        )

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

            elif geom_type == "LWPOLYLINE":
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
                    self.ax.scatter(
                        x_coords,
                        y_coords,
                        c=marker_color,
                        s=marker_size,
                        marker="s",
                        alpha=alpha,
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
            print(f"Debug: Input field clicked")
            print(f"  Widget state: {state}")
            print(f"  Current focus: {focus_widget}")
            print(f"  Widget focus: {widget == focus_widget}")

            # Force the field to be active and focused
            widget.configure(state="normal")
            # Use after_idle to ensure focus is set after the click event
            self.root.after_idle(lambda: widget.focus_set())
            # Also select all text for easy editing
            self.root.after_idle(lambda: widget.select_range(0, tk.END))

        except Exception as e:
            print(f"Debug error: {e}")

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
Origin offset: ({self.origin_offset[0]:.1f}, {self.origin_offset[1]:.1f})"""

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

        # Generate G-code for each element
        for element_id, element_info in elements_by_id.items():
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

                        # Turn on laser
                        gcode.append(
                            f"M3 S{self.gcode_settings['laser_power']} ; Turn on laser"
                        )

                        # Engrave to clipped end point
                        gcode.append(
                            f"G1 X{clipped_end_x:.3f} Y{clipped_end_y:.3f} F{self.gcode_settings['feedrate']} ; Engrave line"
                        )

                        # Turn off laser
                        gcode.append("M5 ; Turn off laser")

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

                        # Turn on laser
                        gcode.append(
                            f"M3 S{self.gcode_settings['laser_power']} ; Turn on laser"
                        )

                        # Generate circular path (360 degrees in 5-degree steps for precision)
                        # Start at 0 degrees (right side of circle) and go to 355 degrees, then add 360 to close
                        angles = list(range(0, 360, 5))  # [0, 5, 10, ..., 355]
                        angles.append(
                            360
                        )  # Add 360 degrees (same as 0 degrees) to close the circle

                        # Generate circle segments with proper intersection-based clipping
                        # Start from the actual 0-degree point, not the clipped position
                        prev_x, prev_y = (
                            start_x,
                            start_y,
                        )  # Use actual 0-degree point, not clipped
                        for i in angles:
                            angle = math.radians(i)
                            x = cx + radius * math.cos(angle)
                            y = cy + radius * math.sin(angle)

                            # Check if the original segment intersects the workspace
                            clipped_line = self.clip_line_to_workspace(
                                prev_x, prev_y, x, y
                            )

                            if clipped_line:
                                (
                                    seg_start_x,
                                    seg_start_y,
                                    seg_end_x,
                                    seg_end_y,
                                ) = clipped_line

                                # Determine the intersection case based on original segment points
                                start_inside = self.is_within_workspace(prev_x, prev_y)
                                end_inside = self.is_within_workspace(x, y)

                                if not start_inside and end_inside:
                                    # Start outside, end inside: G0 to intersection, then G1 to end
                                    gcode.append(
                                        f"G0 X{seg_start_x:.3f} Y{seg_start_y:.3f} Z{self.gcode_settings['cutting_z']:.3f} ; Move to intersection"
                                    )
                                    gcode.append(
                                        f"G1 X{seg_end_x:.3f} Y{seg_end_y:.3f} F{self.gcode_settings['feedrate']} ; Engrave circle"
                                    )
                                elif start_inside and not end_inside:
                                    # Start inside, end outside: G1 to intersection, then move to next segment
                                    gcode.append(
                                        f"G1 X{seg_end_x:.3f} Y{seg_end_y:.3f} F{self.gcode_settings['feedrate']} ; Engrave to boundary"
                                    )
                                elif start_inside and end_inside:
                                    # Both inside: normal G1 engraving
                                    gcode.append(
                                        f"G1 X{seg_end_x:.3f} Y{seg_end_y:.3f} F{self.gcode_settings['feedrate']} ; Engrave circle"
                                    )
                                # If both outside, no G-code is generated (clipped_line would be None)

                            # Update previous point for next segment
                            prev_x, prev_y = x, y

                        # Turn off laser
                        gcode.append("M5 ; Turn off laser")

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

            elif geom_type == "LWPOLYLINE":
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
                        gcode.append("; === POLYLINE GEOMETRY ===")
                        # Process polyline segments with proper clipping
                        first_x, first_y = polyline_points[0]

                        # G0 move to start point if not already there
                        if (current_x, current_y) != (first_x, first_y):
                            gcode.append(
                                f"G0 X{first_x:.3f} Y{first_y:.3f} Z{self.gcode_settings['cutting_z']:.3f}"
                            )

                        # Turn on laser
                        gcode.append(
                            f"M3 S{self.gcode_settings['laser_power']} ; Turn on laser"
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
                                    f"G1 X{clipped_end_x:.3f} Y{clipped_end_y:.3f} F{self.gcode_settings['feedrate']} ; Engrave polyline"
                                )

                        # Turn off laser
                        gcode.append("M5 ; Turn off laser")

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
