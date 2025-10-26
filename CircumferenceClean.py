#!/usr/bin/env python3
"""
CircumferenceClean - GUI application for cleaning circular parts using arc-based G-code
with reference point circle fitting for top and bottom positions.

Features:
- Geometry definition tab for outer/inner circles and cleaning parameters
- Main control tab with reference point capture and circle fitting
- G2/G3 arc-based cleaning with alternating direction passes
- Circle fitting using scipy.optimize.least_squares with fixed radius
- GRBL streaming protocol for smooth, continuous motion
- Interactive GUI with laser jogging controls and position capture
"""

VERSION = 1.0

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import serial
import serial.tools.list_ports
import threading
import time
import re
import json
import os
from datetime import datetime
from scipy.optimize import least_squares
import math


class CircumferenceClean:
    def __init__(self, root):
        self.root = root
        self.root.title(f"CircumferenceClean v{VERSION}")
        self.root.geometry("1200x800")

        # Initialize variables
        self.initialize_variables()

        # Create main interface
        self.create_main_interface()

    def initialize_variables(self):
        """Initialize all class variables"""
        # Geometry parameters
        self.outer_diameter = 17.643 * 25.4  # mm
        self.inner_diameter = 16.837 * 25.4  # mm
        self.outer_cleaning_offsets = [0.26, 0.18, 0.1]  # mm
        self.inner_cleaning_offsets = [-0.26, -0.18, -0.1]  # mm

        # Circle centers (start as expected values, become actual after fitting)
        self.top_center = [0, -50]  # Expected center for top
        self.bottom_center = [0, 50]  # Expected center for bottom

        # Reference points (in degrees from positive X-axis, always on outer circumference)
        self.top_reference_angles = [-30, 0, 45, 90, 135, 180, 210]  # degrees
        self.bottom_reference_angles = [150, 180, 225, 270, 315, 0, 30]  # degrees

        # Reference points (computed from angles)
        self.top_reference_points = []  # List of (x, y) tuples
        self.bottom_reference_points = []  # List of (x, y) tuples

        # Initialize reference points from angles
        self._compute_reference_points_from_angles()

        # G-code parameters
        self.laser_power = 100  # Default laser power level (0-100%)
        self.laser_power_max = 10000  # Maximum laser power value (full scale)
        self.targeting_power = 3  # Power level for targeting reference points (0-100%)
        self.feed_rate = 500  # mm/min

        # Cleaning angles
        self.top_start_angle = 0  # degrees
        self.top_end_angle = 180  # degrees
        self.bottom_start_angle = 0  # degrees
        self.bottom_end_angle = -180  # degrees

        # GRBL connection
        self.serial_connection = None
        self.is_connected = False
        self.serial_reader_thread = None
        self.grbl_state = "Disconnected"  # Tracks GRBL state (Idle, Run, etc.)
        self.status_query_active = False  # Controls periodic status queries

        # Current position
        self.work_pos = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.mpos = {"x": 0.0, "y": 0.0, "z": 0.0}  # Machine position
        self.wpos = {"x": 0.0, "y": 0.0, "z": 0.0}  # Work position

        # Laser state
        self.laser_on = False

        # Circle fitting results
        self.fitted_center = None
        self.fitted_radius = None
        self.circle_errors = []

        # G-code generation (will be added back for execution control)
        self.is_executing = False

        # Buffer management for G-code streaming
        self.gcode_buffer = []  # Queue of G-code lines to send
        self.buffer_size = 0  # Current commands in GRBL's buffer
        self.max_buffer_size = 4  # Conservative buffer size
        self.command_queue = []  # Track sent commands for ok matching

        # Current position selection
        self.current_position = "bottom"  # "top" or "bottom"

        # Plot visibility
        self.show_top = True
        self.show_bottom = True

        # Actual reference points captured from laser
        self.actual_points = {"top": {}, "bottom": {}}

    def _compute_reference_points_from_angles(self):
        """Compute X,Y reference points from angles on outer circumference, relative to circle centers"""
        radius = self.outer_diameter / 2

        # Convert top angles to X,Y points relative to top center
        self.top_reference_points = []
        for angle_deg in self.top_reference_angles:
            angle_rad = np.radians(angle_deg)
            x = self.top_center[0] + radius * np.cos(angle_rad)
            y = self.top_center[1] + radius * np.sin(angle_rad)
            self.top_reference_points.append((x, y))

        # Convert bottom angles to X,Y points relative to bottom center
        self.bottom_reference_points = []
        for angle_deg in self.bottom_reference_angles:
            angle_rad = np.radians(angle_deg)
            x = self.bottom_center[0] + radius * np.cos(angle_rad)
            y = self.bottom_center[1] + radius * np.sin(angle_rad)
            self.bottom_reference_points.append((x, y))

    def create_main_interface(self):
        """Create the main interface with tabs"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.create_geometry_tab()
        self.create_main_control_tab()
        self.create_gcode_tab()

        # Refresh ports on startup
        self.refresh_ports()

    def create_geometry_tab(self):
        """Create the geometry definition tab"""
        self.geometry_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.geometry_frame, text="Geometry Definition")

        # Create split view: controls on left, plot on right
        left_frame = ttk.Frame(self.geometry_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right_frame = ttk.Frame(self.geometry_frame)
        right_frame.pack(side="right", fill="y", padx=(5, 0))

        # Create scrollable frame for controls
        canvas = tk.Canvas(left_frame)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Outer Circle Section
        outer_frame = ttk.LabelFrame(scrollable_frame, text="Outer Circle", padding=10)
        outer_frame.pack(fill="x", pady=5)

        ttk.Label(outer_frame, text="Outer Diameter (mm):").pack(anchor="w")
        outer_diam_frame = ttk.Frame(outer_frame)
        outer_diam_frame.pack(anchor="w", pady=2, fill="x")
        self.outer_diameter_var = tk.StringVar(value=str(self.outer_diameter))
        self.outer_diameter_entry = ttk.Entry(
            outer_diam_frame, textvariable=self.outer_diameter_var, width=20
        )
        self.outer_diameter_entry.pack(side="left", padx=(0, 10))
        self.outer_diameter_entry.bind("<FocusOut>", self.update_geometry_from_ui)

        # Display inches equivalent
        self.outer_diameter_inches_label = ttk.Label(
            outer_diam_frame, text=f"({self.outer_diameter / 25.4:.4f} in)"
        )
        self.outer_diameter_inches_label.pack(side="left")

        ttk.Label(outer_frame, text="Cleaning Offsets (mm, comma-separated):").pack(
            anchor="w"
        )
        self.outer_offsets_var = tk.StringVar(
            value=", ".join(map(str, self.outer_cleaning_offsets))
        )
        self.outer_offsets_entry = ttk.Entry(
            outer_frame, textvariable=self.outer_offsets_var, width=20
        )
        self.outer_offsets_entry.pack(anchor="w", pady=2)
        self.outer_offsets_entry.bind("<FocusOut>", self.update_geometry_from_ui)

        # Inner Circle Section
        inner_frame = ttk.LabelFrame(scrollable_frame, text="Inner Circle", padding=10)
        inner_frame.pack(fill="x", pady=5)

        ttk.Label(inner_frame, text="Inner Diameter (mm):").pack(anchor="w")
        inner_diam_frame = ttk.Frame(inner_frame)
        inner_diam_frame.pack(anchor="w", pady=2, fill="x")
        self.inner_diameter_var = tk.StringVar(value=str(self.inner_diameter))
        self.inner_diameter_entry = ttk.Entry(
            inner_diam_frame, textvariable=self.inner_diameter_var, width=20
        )
        self.inner_diameter_entry.pack(side="left", padx=(0, 10))
        self.inner_diameter_entry.bind("<FocusOut>", self.update_geometry_from_ui)

        # Display inches equivalent
        self.inner_diameter_inches_label = ttk.Label(
            inner_diam_frame, text=f"({self.inner_diameter / 25.4:.4f} in)"
        )
        self.inner_diameter_inches_label.pack(side="left")

        ttk.Label(inner_frame, text="Cleaning Offsets (mm, comma-separated):").pack(
            anchor="w"
        )
        self.inner_offsets_var = tk.StringVar(
            value=", ".join(map(str, self.inner_cleaning_offsets))
        )
        self.inner_offsets_entry = ttk.Entry(
            inner_frame, textvariable=self.inner_offsets_var, width=20
        )
        self.inner_offsets_entry.pack(anchor="w", pady=2)
        self.inner_offsets_entry.bind("<FocusOut>", self.update_geometry_from_ui)

        # Reference Points Section
        ref_frame = ttk.LabelFrame(
            scrollable_frame,
            text="Reference Points (degrees, comma-separated)",
            padding=10,
        )
        ref_frame.pack(fill="x", pady=5)

        # Top reference points
        ttk.Label(ref_frame, text="Top Position Reference Angles:").pack(anchor="w")
        self.top_ref_angles_var = tk.StringVar(
            value=", ".join(map(str, self.top_reference_angles))
        )
        self.top_ref_angles_entry = ttk.Entry(
            ref_frame, textvariable=self.top_ref_angles_var, width=40
        )
        self.top_ref_angles_entry.pack(anchor="w", pady=2)
        self.top_ref_angles_entry.bind(
            "<FocusOut>", self.update_reference_angles_from_ui
        )

        # Bottom reference points
        ttk.Label(
            ref_frame,
            text="Bottom Position Reference Angles:",
        ).pack(anchor="w")
        self.bottom_ref_angles_var = tk.StringVar(
            value=", ".join(map(str, self.bottom_reference_angles))
        )
        self.bottom_ref_angles_entry = ttk.Entry(
            ref_frame, textvariable=self.bottom_ref_angles_var, width=40
        )
        self.bottom_ref_angles_entry.pack(anchor="w", pady=2)
        self.bottom_ref_angles_entry.bind(
            "<FocusOut>", self.update_reference_angles_from_ui
        )

        # Cleaning Angles Section
        angles_frame = ttk.LabelFrame(
            scrollable_frame, text="Cleaning Angles", padding=10
        )
        angles_frame.pack(fill="x", pady=5)

        # Top angles
        ttk.Label(angles_frame, text="Top Cleaning (degrees):").pack(anchor="w")
        top_angle_frame = ttk.Frame(angles_frame)
        top_angle_frame.pack(anchor="w", pady=2)
        ttk.Label(top_angle_frame, text="Start:").pack(side="left", padx=(0, 5))
        self.top_start_angle_var = tk.StringVar(value=str(self.top_start_angle))
        top_start_entry = ttk.Entry(
            top_angle_frame, textvariable=self.top_start_angle_var, width=8
        )
        top_start_entry.pack(side="left", padx=(0, 10))
        top_start_entry.bind("<FocusOut>", self.update_angles)
        ttk.Label(top_angle_frame, text="End:").pack(side="left", padx=(0, 5))
        self.top_end_angle_var = tk.StringVar(value=str(self.top_end_angle))
        top_end_entry = ttk.Entry(
            top_angle_frame, textvariable=self.top_end_angle_var, width=8
        )
        top_end_entry.pack(side="left")
        top_end_entry.bind("<FocusOut>", self.update_angles)

        # Bottom angles
        ttk.Label(angles_frame, text="Bottom Cleaning (degrees):").pack(
            anchor="w", pady=(5, 0)
        )
        bottom_angle_frame = ttk.Frame(angles_frame)
        bottom_angle_frame.pack(anchor="w", pady=2)
        ttk.Label(bottom_angle_frame, text="Start:").pack(side="left", padx=(0, 5))
        self.bottom_start_angle_var = tk.StringVar(value=str(self.bottom_start_angle))
        bottom_start_entry = ttk.Entry(
            bottom_angle_frame, textvariable=self.bottom_start_angle_var, width=8
        )
        bottom_start_entry.pack(side="left", padx=(0, 10))
        bottom_start_entry.bind("<FocusOut>", self.update_angles)
        ttk.Label(bottom_angle_frame, text="End:").pack(side="left", padx=(0, 5))
        self.bottom_end_angle_var = tk.StringVar(value=str(self.bottom_end_angle))
        bottom_end_entry = ttk.Entry(
            bottom_angle_frame, textvariable=self.bottom_end_angle_var, width=8
        )
        bottom_end_entry.pack(side="left")
        bottom_end_entry.bind("<FocusOut>", self.update_angles)

        # Save/Load buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill="x", pady=10)

        ttk.Button(
            button_frame, text="Save Configuration", command=self.save_configuration
        ).pack(side="left", padx=(0, 10))
        ttk.Button(
            button_frame, text="Load Configuration", command=self.load_configuration
        ).pack(side="left")

        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create geometry plot on the right side
        self.create_geometry_plot(right_frame)

    def create_geometry_plot(self, parent):
        """Create the geometry plot for the geometry tab"""
        # Create visibility controls
        visibility_frame = ttk.LabelFrame(parent, text="Show Paths", padding=5)
        visibility_frame.pack(fill="x", pady=(0, 5))

        self.show_top_var = tk.BooleanVar(value=True)
        self.show_bottom_var = tk.BooleanVar(value=True)

        self.show_top_check = ttk.Checkbutton(
            visibility_frame,
            text="Top (Blue/Purple)",
            variable=self.show_top_var,
            command=self.toggle_plot_visibility,
        )
        self.show_top_check.pack(side="left", padx=10)

        self.show_bottom_check = ttk.Checkbutton(
            visibility_frame,
            text="Bottom (Orange/Green)",
            variable=self.show_bottom_var,
            command=self.toggle_plot_visibility,
        )
        self.show_bottom_check.pack(side="left", padx=10)

        # Create toolbar first (before the plot)
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill="x", pady=(0, 5))

        # Create figure and axes
        self.geo_fig = Figure(figsize=(6, 8), dpi=100)
        self.geo_ax = self.geo_fig.add_subplot(111)

        # Create canvas
        self.geo_canvas = FigureCanvasTkAgg(self.geo_fig, parent)
        self.geo_canvas.get_tk_widget().pack(fill="both", expand=True)

        # Create toolbar with zoom and pan support
        self.geo_toolbar = NavigationToolbar2Tk(self.geo_canvas, toolbar_frame)

        # Enable zoom and pan
        from matplotlib.widgets import Cursor

        self.geo_cursor = Cursor(
            self.geo_ax, horizOn=True, vertOn=True, color="gray", linewidth=1
        )

        # Initialize plot
        self.update_geometry_plot()

    def toggle_plot_visibility(self):
        """Update plot visibility based on checkboxes"""
        self.update_geometry_plot()

    def update_geometry_plot(self):
        """Update the geometry plot with current settings"""
        # Store current view limits before clearing
        xlim = self.geo_ax.get_xlim()
        ylim = self.geo_ax.get_ylim()

        self.geo_ax.clear()
        self.geo_ax.set_xlabel("X (mm)")
        self.geo_ax.set_ylabel("Y (mm)")
        self.geo_ax.set_title("Geometry Preview")
        self.geo_ax.grid(True, alpha=0.3)
        self.geo_ax.set_aspect("equal")

        # Restore previous view limits if they were set
        if xlim[0] != 0 or xlim[1] != 1 or ylim[0] != 0 or ylim[1] != 1:
            self.geo_ax.set_xlim(xlim)
            self.geo_ax.set_ylim(ylim)

        # Get radii for calculations
        outer_radius = self.outer_diameter / 2
        inner_radius = self.inner_diameter / 2

        # Plot base outer circle for top (solid blue)
        if self.show_top_var.get():
            # Plot base outer circle (solid blue, no offset)
            start_rad = np.radians(self.top_start_angle)
            end_rad = np.radians(self.top_end_angle)
            if end_rad > start_rad:
                arc_theta = np.linspace(start_rad, end_rad, 50)
            else:
                arc_theta = np.linspace(start_rad, end_rad + 2 * np.pi, 50)
            arc_x = outer_radius * np.cos(arc_theta)
            arc_y = outer_radius * np.sin(arc_theta)
            self.geo_ax.plot(
                arc_x,
                arc_y,
                color="blue",
                linestyle="-",
                linewidth=2,
                alpha=0.8,
                label="Top Outer Base",
            )

            # Plot cleaning paths for top outer with offsets (dotted blue)
            # Top uses outer diameter with outer offsets, arc from top_start to top_end
            # Always add offset: positive = outward, negative = inward
            for i, offset in enumerate(self.outer_cleaning_offsets):
                clean_radius = outer_radius + offset
                # Convert degrees to radians
                start_rad = np.radians(self.top_start_angle)
                end_rad = np.radians(self.top_end_angle)

                # Create arc - always go from start to end (counterclockwise if end > start)
                if end_rad > start_rad:
                    arc_theta = np.linspace(start_rad, end_rad, 50)
                else:
                    # Handle wrap-around case
                    arc_theta = np.linspace(start_rad, end_rad + 2 * np.pi, 50)

                arc_x = clean_radius * np.cos(arc_theta)
                arc_y = clean_radius * np.sin(arc_theta)

                # Use dotted line for all cleaning passes
                linestyle = ":"

                self.geo_ax.plot(
                    arc_x,
                    arc_y,
                    color="blue",
                    linestyle=linestyle,
                    linewidth=2,
                    alpha=0.8,
                    label="Top Outer Clean" if i == 0 else "",
                )

            # Plot base inner circle for top (solid purple)
            start_rad = np.radians(self.top_start_angle)
            end_rad = np.radians(self.top_end_angle)
            if end_rad > start_rad:
                arc_theta = np.linspace(start_rad, end_rad, 50)
            else:
                arc_theta = np.linspace(start_rad, end_rad + 2 * np.pi, 50)
            arc_x = inner_radius * np.cos(arc_theta)
            arc_y = inner_radius * np.sin(arc_theta)
            self.geo_ax.plot(
                arc_x,
                arc_y,
                color="purple",
                linestyle="-",
                linewidth=2,
                alpha=0.8,
                label="Top Inner Base",
            )

            # Plot cleaning paths for inner diameter with inner offsets (shown in top plot)
            # This represents the inner cleaning that will be done from top position
            # Always add offset: positive = outward, negative = inward
            for i, offset in enumerate(
                self.inner_cleaning_offsets
            ):  # Using inner offsets for inner diameter
                clean_radius = inner_radius + offset
                start_rad = np.radians(self.top_start_angle)
                end_rad = np.radians(self.top_end_angle)

                if end_rad > start_rad:
                    arc_theta = np.linspace(start_rad, end_rad, 50)
                else:
                    arc_theta = np.linspace(start_rad, end_rad + 2 * np.pi, 50)

                arc_x = clean_radius * np.cos(arc_theta)
                arc_y = clean_radius * np.sin(arc_theta)

                linestyle = ":"

                self.geo_ax.plot(
                    arc_x,
                    arc_y,
                    color="purple",
                    linestyle=linestyle,
                    linewidth=2,
                    alpha=0.8,
                    label=(
                        f"Top Inner Clean {i+1} (R={clean_radius:.2f}mm)"
                        if i == 0
                        else ""
                    ),
                )

        # Plot cleaning paths for bottom - Outer (Orange) and Inner (Green)
        # Bottom uses outer diameter with outer offsets and inner diameter with inner offsets
        # Always add offset: positive = outward, negative = inward
        if self.show_bottom_var.get():
            # Plot base outer circle for bottom (solid orange, no offset)
            start_rad = np.radians(self.bottom_start_angle)
            end_rad = np.radians(self.bottom_end_angle)
            if end_rad < start_rad:
                arc_theta = np.linspace(start_rad, end_rad, 50)
            elif end_rad > start_rad:
                arc_theta = np.linspace(start_rad, end_rad - 2 * np.pi, 50)
            else:
                arc_theta = np.linspace(start_rad, end_rad, 50)
            arc_x = outer_radius * np.cos(arc_theta)
            arc_y = outer_radius * np.sin(arc_theta)
            self.geo_ax.plot(
                arc_x,
                arc_y,
                color="orange",
                linestyle="-",
                linewidth=2,
                alpha=0.8,
                label=f"Bottom Outer Base (R={outer_radius:.2f}mm)",
            )

            # Plot cleaning paths for bottom outer with offsets (dotted orange)
            for i, offset in enumerate(self.outer_cleaning_offsets):
                clean_radius = outer_radius + offset
                # Convert degrees to radians
                start_rad = np.radians(self.bottom_start_angle)
                end_rad = np.radians(self.bottom_end_angle)

                # For bottom, if end < start, we go clockwise (negative direction)
                if end_rad < start_rad:
                    arc_theta = np.linspace(start_rad, end_rad, 50)
                elif end_rad > start_rad:
                    # If end > start but we want clockwise, go the long way
                    arc_theta = np.linspace(start_rad, end_rad - 2 * np.pi, 50)
                else:
                    arc_theta = np.linspace(start_rad, end_rad, 50)

                arc_x = clean_radius * np.cos(arc_theta)
                arc_y = clean_radius * np.sin(arc_theta)

                linestyle = ":"

                self.geo_ax.plot(
                    arc_x,
                    arc_y,
                    color="orange",
                    linestyle=linestyle,
                    linewidth=2,
                    alpha=0.8,
                    label=(
                        f"Bottom Outer Clean {i+1} (R={clean_radius:.2f}mm)"
                        if i == 0
                        else ""
                    ),
                )

            # Plot base inner circle for bottom (solid green, no offset)
            start_rad = np.radians(self.bottom_start_angle)
            end_rad = np.radians(self.bottom_end_angle)
            if end_rad < start_rad:
                arc_theta = np.linspace(start_rad, end_rad, 50)
            elif end_rad > start_rad:
                arc_theta = np.linspace(start_rad, end_rad - 2 * np.pi, 50)
            else:
                arc_theta = np.linspace(start_rad, end_rad, 50)
            arc_x = inner_radius * np.cos(arc_theta)
            arc_y = inner_radius * np.sin(arc_theta)
            self.geo_ax.plot(
                arc_x,
                arc_y,
                color="green",
                linestyle="-",
                linewidth=2,
                alpha=0.8,
                label=f"Bottom Inner Base (R={inner_radius:.2f}mm)",
            )

            # Plot cleaning paths for bottom inner with offsets (dotted green)
            for i, offset in enumerate(self.inner_cleaning_offsets):
                clean_radius = inner_radius + offset
                # Convert degrees to radians
                start_rad = np.radians(self.bottom_start_angle)
                end_rad = np.radians(self.bottom_end_angle)

                # For bottom, if end < start, we go clockwise (negative direction)
                if end_rad < start_rad:
                    arc_theta = np.linspace(start_rad, end_rad, 50)
                elif end_rad > start_rad:
                    # If end > start but we want clockwise, go the long way
                    arc_theta = np.linspace(start_rad, end_rad - 2 * np.pi, 50)
                else:
                    arc_theta = np.linspace(start_rad, end_rad, 50)

                arc_x = clean_radius * np.cos(arc_theta)
                arc_y = clean_radius * np.sin(arc_theta)

                linestyle = ":"

                self.geo_ax.plot(
                    arc_x,
                    arc_y,
                    color="green",
                    linestyle=linestyle,
                    linewidth=2,
                    alpha=0.8,
                    label=(
                        f"Bottom Inner Clean {i+1} (R={clean_radius:.2f}mm)"
                        if i == 0
                        else ""
                    ),
                )

        # Plot reference points for both top and bottom (respect visibility toggles)
        # For the geometry plot, use circle centers of (0, 0) for both top and bottom
        # to see them overlapped on the same plot
        if self.show_top_var.get() and self.top_reference_angles:
            # Calculate top points relative to (0, 0) for plotting
            top_plot_points = []
            radius = self.outer_diameter / 2
            for angle_deg in self.top_reference_angles:
                angle_rad = np.radians(angle_deg)
                x = radius * np.cos(angle_rad)
                y = radius * np.sin(angle_rad)
                top_plot_points.append((x, y))

            top_points = np.array(top_plot_points)
            self.geo_ax.plot(
                top_points[:, 0],
                top_points[:, 1],
                "g^",
                markersize=10,
                label="Top Points",
            )
            for i, (x, y) in enumerate(top_plot_points):
                self.geo_ax.annotate(
                    f"T{i+1}", (x, y), xytext=(5, 5), textcoords="offset points"
                )

        if self.show_bottom_var.get() and self.bottom_reference_angles:
            # Calculate bottom points relative to (0, 0) for plotting
            bottom_plot_points = []
            radius = self.outer_diameter / 2
            for angle_deg in self.bottom_reference_angles:
                angle_rad = np.radians(angle_deg)
                x = radius * np.cos(angle_rad)
                y = radius * np.sin(angle_rad)
                bottom_plot_points.append((x, y))

            bottom_points = np.array(bottom_plot_points)
            self.geo_ax.plot(
                bottom_points[:, 0],
                bottom_points[:, 1],
                "bo",
                markersize=10,
                label="Bottom Points",
            )
            for i, (x, y) in enumerate(bottom_plot_points):
                self.geo_ax.annotate(
                    f"B{i+1}", (x, y), xytext=(5, 5), textcoords="offset points"
                )

        self.geo_ax.legend(fontsize=7, loc="center", framealpha=0.9)
        self.geo_canvas.draw()

    def create_main_control_tab(self):
        """Create the main control tab"""
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Laser Control")

        # Bind tab change event to update bottom cleaning plot
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Create main layout with adjustable divider
        paned_window = ttk.PanedWindow(self.main_frame, orient="horizontal")
        paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # Create left container frame
        left_container = ttk.Frame(paned_window)

        # Create scrollable canvas for left controls
        left_canvas = tk.Canvas(
            left_container, width=550
        )  # Increased width for better button spacing
        left_scrollbar_y = ttk.Scrollbar(
            left_container, orient="vertical", command=left_canvas.yview
        )
        left_scrollbar_x = ttk.Scrollbar(
            left_container, orient="horizontal", command=left_canvas.xview
        )
        left_scrollable_frame = ttk.Frame(left_canvas)

        left_scrollable_frame.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")),
        )

        left_canvas.create_window((0, 0), window=left_scrollable_frame, anchor="nw")
        left_canvas.configure(
            yscrollcommand=left_scrollbar_y.set, xscrollcommand=left_scrollbar_x.set
        )

        # Pack scrollbars and canvas in left container
        left_scrollbar_y.pack(side="right", fill="y")
        left_scrollbar_x.pack(side="bottom", fill="x")
        left_canvas.pack(side="left", fill="both", expand=True)

        right_frame = ttk.Frame(paned_window)

        # Add frames to paned window
        paned_window.add(left_container, weight=1)
        paned_window.add(right_frame, weight=2)  # Right side gets more space initially

        # Create control panels (left side) - now in scrollable frame
        self.create_control_panels(left_scrollable_frame)

        # Create plot area (right side)
        self.create_plot_area(right_frame)

    def create_gcode_tab(self):
        """Create the G-code editing tab"""
        self.gcode_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.gcode_frame, text="G-code")

        # Create scrollable canvas for the whole tab
        canvas = tk.Canvas(self.gcode_frame)
        scrollbar = ttk.Scrollbar(
            self.gcode_frame, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Configure canvas to update scroll region when contents change
        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", update_scroll_region)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Split into left (top) and right (bottom)
        left_frame = ttk.LabelFrame(
            scrollable_frame, text="Top Position G-code", padding=10
        )
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        right_frame = ttk.LabelFrame(
            scrollable_frame, text="Bottom Position G-code", padding=10
        )
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Create top side gcode text boxes
        self.create_gcode_editor_section(left_frame, "top")

        # Create bottom side gcode text boxes
        self.create_gcode_editor_section(right_frame, "bottom")

        # Generate initial G-code
        self.update_gcode_from_geometry()

    def create_gcode_editor_section(self, parent, position):
        """Create the three text boxes for preamble, cleaning, and postscript"""
        # Preamble
        preamble_frame = ttk.LabelFrame(parent, text="Preamble", padding=5)
        preamble_frame.pack(fill="both", expand=True, pady=2)

        preamble_text = tk.Text(preamble_frame, wrap="none", height=8, width=60)
        preamble_scroll_x = ttk.Scrollbar(
            preamble_frame, orient="horizontal", command=preamble_text.xview
        )
        preamble_scroll_y = ttk.Scrollbar(
            preamble_frame, orient="vertical", command=preamble_text.yview
        )
        preamble_text.configure(
            xscrollcommand=preamble_scroll_x.set, yscrollcommand=preamble_scroll_y.set
        )
        preamble_text.pack(side="left", fill="y")
        preamble_scroll_y.pack(side="right", fill="y")
        preamble_scroll_x.pack(side="bottom", fill="x")

        # Cleaning passes
        cleaning_frame = ttk.LabelFrame(parent, text="Cleaning Passes", padding=5)
        cleaning_frame.pack(fill="both", expand=True, pady=2)

        cleaning_text = tk.Text(cleaning_frame, wrap="none", height=24, width=60)
        cleaning_scroll_x = ttk.Scrollbar(
            cleaning_frame, orient="horizontal", command=cleaning_text.xview
        )
        cleaning_scroll_y = ttk.Scrollbar(
            cleaning_frame, orient="vertical", command=cleaning_text.yview
        )
        cleaning_text.configure(
            xscrollcommand=cleaning_scroll_x.set, yscrollcommand=cleaning_scroll_y.set
        )
        cleaning_text.pack(side="left", fill="y")
        cleaning_scroll_y.pack(side="right", fill="y")
        cleaning_scroll_x.pack(side="bottom", fill="x")

        # Postscript
        postscript_frame = ttk.LabelFrame(parent, text="Postscript", padding=5)
        postscript_frame.pack(fill="both", expand=True, pady=2)

        postscript_text = tk.Text(postscript_frame, wrap="none", height=8, width=60)
        postscript_scroll_x = ttk.Scrollbar(
            postscript_frame, orient="horizontal", command=postscript_text.xview
        )
        postscript_scroll_y = ttk.Scrollbar(
            postscript_frame, orient="vertical", command=postscript_text.yview
        )
        postscript_text.configure(
            xscrollcommand=postscript_scroll_x.set,
            yscrollcommand=postscript_scroll_y.set,
        )
        postscript_text.pack(side="left", fill="y")
        postscript_scroll_y.pack(side="right", fill="y")
        postscript_scroll_x.pack(side="bottom", fill="x")

        # Bind text change events to update plot
        preamble_text.bind("<KeyRelease>", self.on_gcode_text_change)
        cleaning_text.bind("<KeyRelease>", self.on_gcode_text_change)
        postscript_text.bind("<KeyRelease>", self.on_gcode_text_change)

        # Also bind for paste operations
        preamble_text.bind("<<Modified>>", self.on_gcode_text_change)
        cleaning_text.bind("<<Modified>>", self.on_gcode_text_change)
        postscript_text.bind("<<Modified>>", self.on_gcode_text_change)

        # Store references
        if position == "top":
            self.top_preamble_widget = preamble_text
            self.top_cleaning_widget = cleaning_text
            self.top_postscript_widget = postscript_text
        else:
            self.bottom_preamble_widget = preamble_text
            self.bottom_cleaning_widget = cleaning_text
            self.bottom_postscript_widget = postscript_text

    def create_plot_area(self, parent):
        """Create the matplotlib plot area with communication log and G-code execution"""
        # Create plot area with paned window for plot and log
        plot_frame = ttk.Frame(parent)
        plot_frame.pack(fill="both", expand=True)

        # Create paned window
        plot_paned = ttk.PanedWindow(plot_frame, orient="vertical")
        plot_paned.pack(fill="both", expand=True)

        # Top pane - plot (1/3 of space)
        plot_top_frame = ttk.Frame(plot_paned)
        plot_paned.add(plot_top_frame, weight=1)

        # Create toolbar first (before the plot)
        toolbar_frame = ttk.Frame(plot_top_frame)
        toolbar_frame.pack(fill="x", pady=(0, 5))

        # Create figure and axes
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Add position display text in upper right corner
        self.position_text = self.ax.text(
            0.98,
            0.98,
            "",
            transform=self.ax.transAxes,
            fontsize=10,
            ha="right",
            va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        )

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, plot_top_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Add laser position marker (green crosshair)
        self.laser_marker = self.ax.plot(
            [self.wpos["x"]],
            [self.wpos["y"]],
            marker="+",
            color="green",
            markersize=15,
            markeredgewidth=2,
            linestyle="None",
        )[0]

        # Initialize position display
        self.update_position_display_text()

        # Create toolbar with zoom and pan support
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)

        # Enable zoom and pan
        from matplotlib.widgets import Cursor

        self.cursor = Cursor(
            self.ax, horizOn=True, vertOn=True, color="gray", linewidth=1
        )

        # Bottom pane - G-code execute and communication log (2/3 of space)
        bottom_frame = ttk.Frame(plot_paned)
        plot_paned.add(bottom_frame, weight=2)

        # G-code execute field
        gcode_frame = ttk.LabelFrame(bottom_frame, text="G-code Execute", padding=5)
        gcode_frame.pack(fill="x", padx=5, pady=(5, 5))

        gcode_entry_frame = ttk.Frame(gcode_frame)
        gcode_entry_frame.pack(fill="x")

        ttk.Label(gcode_entry_frame, text="G-code:").pack(side="left", padx=(0, 5))
        self.gcode_cmd_var = tk.StringVar()
        self.gcode_cmd_entry = ttk.Entry(
            gcode_entry_frame, textvariable=self.gcode_cmd_var, width=30
        )
        self.gcode_cmd_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)

        # Bind Enter key to execute command
        self.gcode_cmd_entry.bind("<Return>", lambda e: self.execute_manual_gcode())

        ttk.Button(
            gcode_entry_frame,
            text="Execute",
            command=self.execute_manual_gcode,
            width=8,
        ).pack(side="right")

        # Communication log
        log_frame = ttk.LabelFrame(bottom_frame, text="Communication Log", padding=5)
        log_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(side="top", fill="x", pady=(0, 5))

        # Clear log button
        ttk.Button(
            log_controls, text="Clear Log", command=self.clear_comm_log, width=10
        ).pack(side="left", padx=5)

        # Auto-scroll checkbox
        self.log_autoscroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            log_controls, text="Auto-scroll", variable=self.log_autoscroll_var
        ).pack(side="left", padx=5)

        # Text widget with scrollbar for log
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill="both", expand=True)

        self.comm_log_text = tk.Text(
            log_text_frame,
            height=6,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Courier", 9),
        )
        log_scrollbar = ttk.Scrollbar(
            log_text_frame, orient="vertical", command=self.comm_log_text.yview
        )
        self.comm_log_text.configure(yscrollcommand=log_scrollbar.set)

        log_scrollbar.pack(side="right", fill="y")
        self.comm_log_text.pack(side="left", fill="both", expand=True)

        # Configure text tags for color coding
        self.comm_log_text.tag_config("sent", foreground="blue")
        self.comm_log_text.tag_config("received", foreground="green")
        self.comm_log_text.tag_config("error", foreground="red")

        # Initialize plot
        self.initialize_plot()

    def create_control_panels(self, parent):
        """Create the control panels"""
        # Create horizontal frame for Position and GRBL Connection side-by-side
        top_row = ttk.Frame(parent)
        top_row.pack(fill="x", pady=5)

        # Position selection (left side)
        pos_frame = ttk.LabelFrame(top_row, text="Position", padding=5)
        pos_frame.pack(side="left", padx=(0, 5))

        self.position_var = tk.StringVar(value="bottom")
        ttk.Radiobutton(
            pos_frame,
            text="Top",
            variable=self.position_var,
            value="top",
            command=self.on_position_change,
        ).pack(anchor="w")
        ttk.Radiobutton(
            pos_frame,
            text="Bottom",
            variable=self.position_var,
            value="bottom",
            command=self.on_position_change,
        ).pack(anchor="w")

        # GRBL Connection (right side)
        grbl_container = ttk.Frame(top_row)
        grbl_container.pack(side="left", fill="x", expand=True)
        self.create_grbl_controls(grbl_container)

        # Jogging controls
        self.create_jogging_controls(parent)

        # Reference points table
        self.create_reference_table(parent)

        # Calculation results
        self.create_calculation_results(parent)

        # Action buttons
        self.create_action_buttons(parent)

    def create_grbl_controls(self, parent):
        """Create GRBL connection controls"""
        grbl_frame = ttk.LabelFrame(parent, text="GRBL Connection", padding=5)
        grbl_frame.pack(fill="both", expand=True)

        # Port selection
        port_frame = ttk.Frame(grbl_frame)
        port_frame.pack(fill="x", pady=2)
        ttk.Label(port_frame, text="Port:").pack(side="left")
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(
            port_frame, textvariable=self.port_var, width=20, state="readonly"
        )
        self.port_combo.pack(side="left", padx=(5, 0))

        # Refresh ports button
        ttk.Button(port_frame, text="⟳", command=self.refresh_ports, width=3).pack(
            side="left", padx=(5, 0)
        )

        # Connect/Disconnect buttons
        button_frame = ttk.Frame(grbl_frame)
        button_frame.pack(fill="x", pady=2)
        self.connect_button = ttk.Button(
            button_frame, text="Connect", command=self.connect_grbl, width=8
        )
        self.connect_button.pack(side="left", padx=(0, 5))
        self.disconnect_button = ttk.Button(
            button_frame,
            text="Disconnect",
            command=self.disconnect_grbl,
            state="disabled",
            width=8,
        )
        self.disconnect_button.pack(side="left")

        # Status display
        self.status_label = ttk.Label(
            grbl_frame, text="Status: Disconnected", foreground="red"
        )
        self.status_label.pack(anchor="w", pady=2)

        # GRBL State display
        self.grbl_state_label = ttk.Label(
            grbl_frame, text="State: Disconnected", foreground="gray"
        )
        self.grbl_state_label.pack(anchor="w", pady=2)

        # Position display frame
        pos_display_frame = ttk.Frame(grbl_frame)
        pos_display_frame.pack(anchor="w", pady=2)

        # Work Position
        wpos_row = ttk.Frame(pos_display_frame)
        wpos_row.pack(side="top", anchor="w")
        ttk.Label(wpos_row, text="WPos:", font=("TkDefaultFont", 9, "bold")).pack(
            side="left", padx=(0, 5)
        )
        self.work_pos_label = ttk.Label(
            wpos_row, text="X: 0.00  Y: 0.00  Z: 0.00", font=("Courier", 9)
        )
        self.work_pos_label.pack(side="left")

        # Machine Position
        mpos_row = ttk.Frame(pos_display_frame)
        mpos_row.pack(side="top", anchor="w")
        ttk.Label(mpos_row, text="MPos:", font=("TkDefaultFont", 9, "bold")).pack(
            side="left", padx=(0, 5)
        )
        self.machine_pos_label = ttk.Label(
            mpos_row, text="X: 0.00  Y: 0.00  Z: 0.00", font=("Courier", 9)
        )
        self.machine_pos_label.pack(side="left")

        # Control buttons row (Home, Clear Errors, Reboot)
        control_row = ttk.Frame(grbl_frame)
        control_row.pack(fill="x", pady=(5, 0))

        self.home_button = ttk.Button(
            control_row, text="Home", command=self.home_machine, width=6
        )
        self.home_button.pack(side="left", padx=(0, 5))

        self.clear_errors_button = ttk.Button(
            control_row, text="Clear Errors", command=self.clear_errors, width=8
        )
        self.clear_errors_button.pack(side="left", padx=(0, 5))

        self.soft_reset_button = ttk.Button(
            control_row, text="Reboot GRBL", command=self.reboot_grbl, width=8
        )
        self.soft_reset_button.pack(side="left")

    def create_jogging_controls(self, parent):
        """Create jogging controls"""
        jog_frame = ttk.LabelFrame(
            parent, text="Jog Laser to Set Reference Points", padding=10
        )
        jog_frame.pack(fill="x", pady=(0, 10))

        # Set origin button
        origin_frame = ttk.Frame(jog_frame)
        origin_frame.pack(fill="x", pady=(0, 5))

        self.set_origin_button = ttk.Button(
            origin_frame,
            text="Set Origin",
            command=self.set_work_origin,
            width=8,
        )
        self.set_origin_button.pack(side="left", padx=(0, 5))

        self.auto_top_origin_button = ttk.Button(
            origin_frame,
            text="Top Origin",
            command=lambda: self.auto_origin("top"),
            width=8,
        )
        self.auto_top_origin_button.pack(side="left", padx=(0, 5))

        self.auto_bottom_origin_button = ttk.Button(
            origin_frame,
            text="Bottom Origin",
            command=lambda: self.auto_origin("bottom"),
            width=10,
        )
        self.auto_bottom_origin_button.pack(side="left")

        # Create main frame to hold jog buttons and controls side-by-side
        jog_main_frame = ttk.Frame(jog_frame)
        jog_main_frame.pack(pady=(5, 0))

        # Jog buttons in a grid (left side)
        jog_buttons_frame = ttk.Frame(jog_main_frame)
        jog_buttons_frame.pack(side="left", padx=(0, 10))

        # Step size and laser control (right side)
        right_controls_frame = ttk.Frame(jog_main_frame)
        right_controls_frame.pack(side="left")

        # Laser ON/OFF button on top
        self.laser_button = ttk.Button(
            right_controls_frame, text="Laser OFF", command=self.toggle_laser, width=8
        )
        self.laser_button.pack(pady=(0, 5))

        # Laser power level input
        power_frame = ttk.Frame(right_controls_frame)
        power_frame.pack(pady=(0, 5))

        ttk.Label(power_frame, text="Power:").pack(side="left", padx=(0, 2))
        # Create laser tab variables
        self.laser_power_var = tk.StringVar(value=str(self.laser_power))
        self.laser_power_entry = ttk.Entry(
            power_frame,
            textvariable=self.laser_power_var,
            width=6,
            justify="right",
        )
        self.laser_power_entry.pack(side="left", padx=(0, 2))
        ttk.Label(power_frame, text="%").pack(side="left")

        # Bind Enter key and focus out to update power level
        self.laser_power_entry.bind("<Return>", lambda e: self.update_laser_power())
        self.laser_power_entry.bind("<FocusOut>", lambda e: self.update_laser_power())

        # Laser max power input
        max_power_frame = ttk.Frame(right_controls_frame)
        max_power_frame.pack(pady=(0, 5))

        ttk.Label(max_power_frame, text="  Max:").pack(side="left", padx=(0, 2))
        # Create laser tab variables
        self.laser_power_max_var = tk.StringVar(value=str(self.laser_power_max))
        self.laser_power_max_entry = ttk.Entry(
            max_power_frame,
            textvariable=self.laser_power_max_var,
            width=6,
            justify="right",
        )
        self.laser_power_max_entry.pack(side="left", padx=(0, 2))

        # Bind Enter key and focus out to update max power level
        self.laser_power_max_entry.bind(
            "<Return>", lambda e: self.update_laser_power_max()
        )
        self.laser_power_max_entry.bind(
            "<FocusOut>", lambda e: self.update_laser_power_max()
        )

        # Targeting power input
        targeting_power_frame = ttk.Frame(right_controls_frame)
        targeting_power_frame.pack(pady=(0, 5))

        ttk.Label(targeting_power_frame, text="Target:").pack(side="left", padx=(0, 2))
        self.targeting_power_var = tk.StringVar(value=str(self.targeting_power))
        self.targeting_power_entry = ttk.Entry(
            targeting_power_frame,
            textvariable=self.targeting_power_var,
            width=6,
            justify="right",
        )
        self.targeting_power_entry.pack(side="left", padx=(0, 2))
        ttk.Label(targeting_power_frame, text="%").pack(side="left")

        # Bind Enter key and focus out to update targeting power level
        self.targeting_power_entry.bind(
            "<Return>", lambda e: self.update_targeting_power()
        )
        self.targeting_power_entry.bind(
            "<FocusOut>", lambda e: self.update_targeting_power()
        )

        # Step size below
        step_frame = ttk.Frame(right_controls_frame)
        step_frame.pack()

        ttk.Label(step_frame, text="Step:").pack(side="left", padx=(0, 2))
        self.jog_step_var = tk.StringVar(value="1")
        step_entry = ttk.Entry(
            step_frame,
            textvariable=self.jog_step_var,
            width=6,
            justify="right",
        )
        step_entry.pack(side="left", padx=(0, 2))
        ttk.Label(step_frame, text="mm").pack(side="left")

        # Feedrate input below step size
        feedrate_frame = ttk.Frame(right_controls_frame)
        feedrate_frame.pack(pady=(5, 0))

        ttk.Label(feedrate_frame, text="Feed:").pack(side="left", padx=(0, 2))
        self.feedrate_var = tk.StringVar(value="500")
        feedrate_entry = ttk.Entry(
            feedrate_frame,
            textvariable=self.feedrate_var,
            width=6,
            justify="right",
        )
        feedrate_entry.pack(side="left", padx=(0, 2))
        ttk.Label(feedrate_frame, text="mm/min").pack(side="left")

        # Bind Enter key and focus out to update feedrate
        feedrate_entry.bind("<Return>", lambda e: self.update_feedrate())
        feedrate_entry.bind("<FocusOut>", lambda e: self.update_feedrate())

        # Button styling - fixed width for consistent layout
        button_width = 6

        # Row 0: X-Y+ (diagonal), Y+, X+Y+ (diagonal)
        ttk.Button(
            jog_buttons_frame,
            text="↖ X-Y+",
            command=lambda: self.jog_move(-1, 1),
            width=button_width,
        ).grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        ttk.Button(
            jog_buttons_frame,
            text="↑ Y+",
            command=lambda: self.jog_move(0, 1),
            width=button_width,
        ).grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        ttk.Button(
            jog_buttons_frame,
            text="↗ X+Y+",
            command=lambda: self.jog_move(1, 1),
            width=button_width,
        ).grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        # Row 1: X-, Origin, X+
        ttk.Button(
            jog_buttons_frame,
            text="← X-",
            command=lambda: self.jog_move(-1, 0),
            width=button_width,
        ).grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        ttk.Button(
            jog_buttons_frame, text="⌂ Origin", command=self.go_home, width=button_width
        ).grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        ttk.Button(
            jog_buttons_frame,
            text="→ X+",
            command=lambda: self.jog_move(1, 0),
            width=button_width,
        ).grid(row=1, column=2, padx=2, pady=2, sticky="ew")

        # Row 2: X-Y- (diagonal), Y-, X+Y- (diagonal)
        ttk.Button(
            jog_buttons_frame,
            text="↙ X-Y-",
            command=lambda: self.jog_move(-1, -1),
            width=button_width,
        ).grid(row=2, column=0, padx=2, pady=2, sticky="ew")

        ttk.Button(
            jog_buttons_frame,
            text="↓ Y-",
            command=lambda: self.jog_move(0, -1),
            width=button_width,
        ).grid(row=2, column=1, padx=2, pady=2, sticky="ew")

        ttk.Button(
            jog_buttons_frame,
            text="↘ X+Y-",
            command=lambda: self.jog_move(1, -1),
            width=button_width,
        ).grid(row=2, column=2, padx=2, pady=2, sticky="ew")

        # Row 3: Z controls
        z_frame = ttk.Frame(jog_buttons_frame)
        z_frame.grid(row=3, column=0, columnspan=3, pady=(5, 0))

        ttk.Button(
            z_frame, text="Z+", command=lambda: self.jog_move_z(1), width=button_width
        ).pack(side="left", padx=2)
        ttk.Button(
            z_frame, text="Z-", command=lambda: self.jog_move_z(-1), width=button_width
        ).pack(side="left", padx=2)

        # Position display
        pos_frame = ttk.Frame(jog_frame)
        pos_frame.pack(fill="x", pady=(10, 2))
        self.position_label = ttk.Label(pos_frame, text="Position: X0.00 Y0.00 Z0.00")
        self.position_label.pack(anchor="w")

    def create_reference_table(self, parent):
        """Create reference points table"""
        ref_frame = ttk.LabelFrame(parent, text="Reference Points", padding=5)
        ref_frame.pack(fill="x", pady=5)

        # Buttons above the table
        button_frame = ttk.Frame(ref_frame)
        button_frame.pack(fill="x", pady=(0, 5))
        ttk.Button(button_frame, text="Goto", command=self.goto_position, width=8).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(
            button_frame, text="Set", command=self.capture_position, width=8
        ).pack(side="left")

        # Create treeview for table
        columns = ("Point", "Expected X", "Expected Y", "Actual X", "Actual Y")
        self.ref_tree = ttk.Treeview(
            ref_frame, columns=columns, show="headings", height=6
        )

        for col in columns:
            self.ref_tree.heading(col, text=col)
            self.ref_tree.column(col, width=80)

        # Scrollbar for table
        ref_scroll = ttk.Scrollbar(
            ref_frame, orient="vertical", command=self.ref_tree.yview
        )
        self.ref_tree.configure(yscrollcommand=ref_scroll.set)

        self.ref_tree.pack(side="left", fill="both", expand=True)
        ref_scroll.pack(side="right", fill="y")

    def create_calculation_results(self, parent):
        """Create calculation results display"""
        calc_frame = ttk.LabelFrame(parent, text="Calculation Results", padding=5)
        calc_frame.pack(fill="x", pady=5)

        self.calc_text = tk.Text(calc_frame, height=8, width=40)
        self.calc_text.pack(fill="both", expand=True)

    def create_action_buttons(self, parent):
        """Create action buttons"""
        action_frame = ttk.LabelFrame(parent, text="Actions", padding=5)
        action_frame.pack(fill="x", pady=5)

        # Row for Adjust and Reset buttons
        adjust_frame = ttk.Frame(action_frame)
        adjust_frame.pack(fill="x", pady=2)
        ttk.Button(adjust_frame, text="Adjust G-code", command=self.adjust_gcode).pack(
            side="left", fill="x", expand=True, padx=(0, 2)
        )
        ttk.Button(adjust_frame, text="Reset G-code", command=self.reset_gcode).pack(
            side="right", fill="x", expand=True, padx=(2, 0)
        )
        ttk.Button(action_frame, text="Run Cleaning", command=self.run_cleaning).pack(
            fill="x", pady=2
        )
        ttk.Button(action_frame, text="Stop", command=self.stop_execution).pack(
            fill="x", pady=2
        )

        # Execution status indicator
        status_frame = ttk.Frame(action_frame)
        status_frame.pack(fill="x", pady=(5, 0))
        ttk.Label(status_frame, text="Status:").pack(side="left")
        self.execution_status_label = ttk.Label(
            status_frame, text="Ready", foreground="green"
        )
        self.execution_status_label.pack(side="left", padx=(5, 0))

    def initialize_plot(self):
        """Initialize the plot"""
        # Call update_plot to initialize with actual data
        self.update_plot()

    def on_tab_changed(self, event=None):
        """Handle tab change - update geometry plot visibility based on tab"""
        # Get the currently selected tab index
        selected_tab = self.notebook.index(self.notebook.select())

        # Check if "Laser Control" tab is selected (index 1)
        if selected_tab == 1:
            # Switch to bottom view when entering Laser Control tab
            self.show_top_var.set(False)
            self.show_bottom_var.set(True)
            self.update_geometry_plot()
            # Update the laser control plot and reference points when switching to this tab
            self.update_reference_display()
            self.update_plot()

    def on_position_change(self):
        """Handle position change (top/bottom)"""
        self.current_position = self.position_var.get()
        self.update_reference_display()
        self.update_plot()

    def update_reference_display(self):
        """Update the reference points table"""
        # Initialize actual points storage if not exists
        if not hasattr(self, "actual_points"):
            self.actual_points = {"top": {}, "bottom": {}}

        # Clear existing items
        for item in self.ref_tree.get_children():
            self.ref_tree.delete(item)

        # Get current reference points
        if self.current_position == "top":
            ref_points = self.top_reference_points
            actual_points = self.actual_points.get("top", {})
        else:
            ref_points = self.bottom_reference_points
            actual_points = self.actual_points.get("bottom", {})

        # Add points to table
        for i, (x, y) in enumerate(ref_points):
            point_id = f"Pt{i+1}"
            actual_x = actual_points.get(point_id, {}).get("x", 0.0)
            actual_y = actual_points.get(point_id, {}).get("y", 0.0)

            self.ref_tree.insert(
                "",
                "end",
                values=(
                    point_id,
                    f"{x:.2f}",
                    f"{y:.2f}",
                    f"{actual_x:.2f}",
                    f"{actual_y:.2f}",
                ),
            )

    def update_plot(self):
        """Update the plot with G-code toolpath and reference points"""
        self.ax.clear()
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.set_title(f"Laser Control - {self.current_position.title()} Position")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect("equal")

        # Get cleaning G-code for the current position
        if self.current_position == "top":
            if hasattr(self, "top_cleaning_widget"):
                gcode_text = self.top_cleaning_widget.get("1.0", tk.END)
            else:
                gcode_text = self.generate_top_cleaning_gcode()
        else:
            if hasattr(self, "bottom_cleaning_widget"):
                gcode_text = self.bottom_cleaning_widget.get("1.0", tk.END)
            else:
                gcode_text = self.generate_bottom_cleaning_gcode()

        # Parse and plot G-code toolpath
        if gcode_text:
            self._plot_gcode_toolpath(gcode_text)

        # Plot reference points
        if self.current_position == "top":
            ref_points = self.top_reference_points
        else:
            ref_points = self.bottom_reference_points

        if ref_points:
            points = np.array(ref_points)
            self.ax.plot(
                points[:, 0], points[:, 1], "ro", markersize=8, label="Expected Points"
            )

        self.ax.legend()

        # Set axis limits
        self.ax.set_xlim(-400, 400)
        self.ax.set_ylim(-200, 200)

        self.canvas.draw()

    def _plot_gcode_toolpath(self, gcode_text):
        """Parse G-code and plot the toolpath with color coding"""
        lines = gcode_text.strip().split("\n")
        current_x, current_y = None, None

        for line in lines:
            line = line.strip()
            if not line or line.startswith(";"):
                continue

            # Parse G0, G1, G2, G3 commands
            if (
                line.startswith("G0")
                or line.startswith("G1")
                or line.startswith("G2")
                or line.startswith("G3")
            ):
                # Determine color based on command type
                line_color = None
                if line.startswith("G0"):
                    line_color = "green"  # G0 - rapid moves (green)
                else:
                    line_color = "red"  # G1/G2/G3 - cutting moves (red)

                # Extract X and Y coordinates
                x_match = re.search(r"X([+-]?\d+\.?\d*)", line)
                y_match = re.search(r"Y([+-]?\d+\.?\d*)", line)
                i_match = re.search(r"I([+-]?\d+\.?\d*)", line)
                j_match = re.search(r"J([+-]?\d+\.?\d*)", line)

                if x_match and y_match:
                    end_x = float(x_match.group(1))
                    end_y = float(y_match.group(1))

                    # Handle arcs (G2/G3) with I/J offsets
                    if (
                        (line.startswith("G2") or line.startswith("G3"))
                        and i_match
                        and j_match
                        and current_x is not None
                    ):
                        # Arc move: calculate center from I/J offsets
                        center_x = current_x + float(i_match.group(1))
                        center_y = current_y + float(j_match.group(1))

                        # Calculate start and end angles
                        start_angle = np.arctan2(
                            current_y - center_y, current_x - center_x
                        )
                        end_angle = np.arctan2(end_y - center_y, end_x - center_x)

                        # Determine direction (G2 = CW, G3 = CCW)
                        is_cw = line.startswith("G2")

                        # Generate arc points - trust the G2/G3 command direction
                        if is_cw:
                            # Clockwise: go from start to end, decreasing angle
                            if start_angle >= end_angle:
                                angles = np.linspace(start_angle, end_angle, 50)
                            else:
                                # Cross 0° boundary, go the long way around
                                angles = np.linspace(
                                    start_angle, end_angle - 2 * np.pi, 50
                                )
                        else:
                            # Counter-clockwise: go from start to end, increasing angle
                            if start_angle <= end_angle:
                                angles = np.linspace(start_angle, end_angle, 50)
                            else:
                                # Cross 0° boundary, go the long way around
                                angles = np.linspace(
                                    start_angle, end_angle + 2 * np.pi, 50
                                )

                        # Calculate radius
                        radius = np.sqrt(
                            (current_x - center_x) ** 2 + (current_y - center_y) ** 2
                        )

                        # Generate arc points
                        arc_x_points = []
                        arc_y_points = []
                        for angle in angles:
                            point_x = center_x + radius * np.cos(angle)
                            point_y = center_y + radius * np.sin(angle)
                            arc_x_points.append(point_x)
                            arc_y_points.append(point_y)

                        # Plot the arc as a single line
                        if arc_x_points and arc_y_points:
                            self.ax.plot(
                                arc_x_points,
                                arc_y_points,
                                color=line_color,
                                linewidth=1.5,
                                alpha=0.8,
                            )

                        # Update current position to the end of the arc
                        current_x, current_y = end_x, end_y
                    else:
                        # Linear move (G0, G1) or first position
                        if (
                            current_x is not None
                            and current_y is not None
                            and line_color
                        ):
                            self.ax.plot(
                                [current_x, end_x],
                                [current_y, end_y],
                                color=line_color,
                                linewidth=1.5 if line_color == "red" else 1.0,
                                alpha=0.8 if line_color == "red" else 0.5,
                            )

                        current_x, current_y = end_x, end_y

    def refresh_ports(self):
        """Scan and populate port dropdown"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]

        self.port_combo["values"] = port_list

        if port_list:
            if not self.port_var.get() or self.port_var.get() not in port_list:
                self.port_combo.current(0)
        else:
            self.port_var.set("")

    def connect_grbl(self):
        """Connect to GRBL controller"""
        port = self.port_var.get()

        if not port:
            messagebox.showerror("Error", "Please select a COM port!")
            return

        try:
            # Open serial connection (GRBL typically uses 115200 baud)
            self.serial_connection = serial.Serial(
                port=port, baudrate=115200, timeout=2, write_timeout=2
            )

            # Wait for GRBL to initialize
            self.root.after(2000, self.complete_connection)

            # Disable port selection while connecting
            self.port_combo.config(state="disabled")
            self.status_label.config(text="Status: Connecting...", foreground="orange")

        except serial.SerialException as e:
            messagebox.showerror(
                "Connection Error", f"Failed to connect to {port}:\n{str(e)}"
            )
            self.serial_connection = None

    def complete_connection(self):
        """Complete the connection after GRBL initializes"""
        if self.serial_connection and self.serial_connection.is_open:
            # Flush any startup messages
            self.serial_connection.reset_input_buffer()

            self.is_connected = True
            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
            self.status_label.config(text="Status: Connected", foreground="green")
            self.grbl_state = "Connecting"
            self.update_state_display()

            # Send wake-up command
            self.send_gcode("$X")

            # Start reader thread
            self.serial_reader_thread = threading.Thread(
                target=self.serial_reader, daemon=True
            )
            self.serial_reader_thread.start()

            # Start status queries
            self.start_status_queries()

        else:
            self.disconnect_grbl()
            messagebox.showerror("Error", "Connection timed out")

    def disconnect_grbl(self):
        """Disconnect from GRBL controller"""
        # If already disconnected, just update UI to be consistent
        if not self.is_connected and not self.serial_connection:
            # Force UI update in case of inconsistent state
            try:
                self.connect_button.config(state="normal")
                self.disconnect_button.config(state="disabled")
                self.status_label.config(text="Status: Disconnected", foreground="gray")
                self.grbl_state = "Disconnected"
                self.update_state_display()
                self.port_combo.config(state="readonly")
            except:
                pass
            return

        # Stop status queries first
        self.stop_status_queries()

        # Update state immediately to prevent new commands
        self.is_connected = False

        # Close serial connection
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except:
                pass
            self.serial_connection = None

        # Update UI
        try:
            self.connect_button.config(state="normal")
        except:
            pass

        try:
            self.disconnect_button.config(state="disabled")
        except:
            pass

        try:
            self.status_label.config(text="Status: Disconnected", foreground="gray")
        except:
            pass

        # Update GRBL state
        self.grbl_state = "Disconnected"
        try:
            self.update_state_display()
        except:
            pass

        try:
            self.port_combo.config(state="readonly")
        except:
            pass

        # Clear position display
        try:
            if hasattr(self, "work_pos_label"):
                self.work_pos_label.config(text="X: 0.00  Y: 0.00  Z: 0.00")
        except:
            pass

        try:
            if hasattr(self, "machine_pos_label"):
                self.machine_pos_label.config(text="X: 0.00  Y: 0.00  Z: 0.00")
        except:
            pass

        try:
            if hasattr(self, "position_text"):
                self.position_text.set_text("")
                self.canvas.draw_idle()
        except:
            pass

    def start_status_queries(self):
        """Start periodic status queries"""
        self.status_query_active = True
        self.query_status()

    def stop_status_queries(self):
        """Stop periodic status queries"""
        self.status_query_active = False

    def query_status(self):
        """Send status query to GRBL"""
        if self.is_connected and self.status_query_active:
            self.send_gcode("?")
            # Schedule next query in 100ms
            self.root.after(100, self.query_status)

    def send_gcode(self, command):
        """Send G-code command to GRBL"""
        if self.serial_connection and self.is_connected:
            self.serial_connection.write(f"{command}\n".encode())
            # Log sent command
            self.log_comm_message(f"> {command}", "sent")

    def serial_reader(self):
        """Read responses from GRBL"""
        consecutive_errors = 0
        while self.is_connected and self.serial_connection:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    line = (
                        self.serial_connection.readline()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )
                    if line:
                        # Log received response
                        self.log_comm_message(f"< {line}", "received")
                        self.parse_grbl_response(line)
                        consecutive_errors = 0  # Reset error counter on success
                else:
                    time.sleep(0.001)  # 1ms sleep when no data
            except (OSError, serial.SerialException) as e:
                # Check if this is a real disconnect error
                error_str = str(e).lower()
                is_disconnect = any(
                    [
                        "access is denied" in error_str,
                        "invalid handle" in error_str,
                        "device not configured" in error_str,
                        "device is not open" in error_str,
                        "i/o error" in error_str,
                        (
                            not self.serial_connection.is_open
                            if self.serial_connection
                            else True
                        ),
                    ]
                )

                if self.is_connected and is_disconnect:
                    consecutive_errors += 1
                    print(
                        f"Serial disconnect error (attempt {consecutive_errors}): {e}"
                    )

                    # After 3 consecutive errors, trigger disconnect
                    if consecutive_errors >= 3:
                        print("USB disconnect detected!")
                        # Schedule disconnect on main thread
                        self.root.after(10, self.handle_usb_disconnect)
                        break
                    time.sleep(0.1)  # Brief delay before retry
            except Exception as e:
                print(f"Unexpected error in serial reader: {e}")
                break

    def handle_usb_disconnect(self):
        """Handle unexpected USB disconnect"""
        # Prevent multiple simultaneous disconnect handlers
        if not self.is_connected:
            return

        print("\n⚠️ USB DISCONNECT DETECTED ⚠️")

        # Stop any ongoing operations
        if hasattr(self, "is_executing") and self.is_executing:
            print("Stopping execution due to disconnect...")
            self.stop_execution()

        # Disconnect
        self.disconnect_grbl()

        # Show user notification
        messagebox.showwarning(
            "USB Disconnected",
            "Lost connection to GRBL controller!\n\nPlease check the USB cable and reconnect.",
        )

    def parse_grbl_response(self, line):
        """Parse GRBL response and update position and state"""
        # Handle "ok" responses - command completed
        if line.strip().lower() == "ok":
            self.handle_grbl_ok()
            return

        # Handle error responses
        if "error" in line.lower():
            print(f"GRBL Error: {line}")
            self.grbl_state = "Error"
            self.update_state_display()
            return

        # Parse position updates and state
        if line.startswith("<"):
            # Extract GRBL state (first part before |)
            parts = line[1:-1].split("|")
            if parts:
                self.grbl_state = parts[0]
                # Update state display
                self.root.after(0, self.update_state_display)

            # Extract MPos from status report
            mpos_match = re.search(
                r"MPos:([+-]?\d+\.?\d*),([+-]?\d+\.?\d*),([+-]?\d+\.?\d*)", line
            )
            if mpos_match:
                self.mpos = {
                    "x": float(mpos_match.group(1)),
                    "y": float(mpos_match.group(2)),
                    "z": float(mpos_match.group(3)),
                }

            # Extract WPos from status report
            wpos_match = re.search(
                r"WPos:([+-]?\d+\.?\d*),([+-]?\d+\.?\d*),([+-]?\d+\.?\d*)", line
            )
            if wpos_match:
                self.wpos = {
                    "x": float(wpos_match.group(1)),
                    "y": float(wpos_match.group(2)),
                    "z": float(wpos_match.group(3)),
                }

            # Update position displays if we have both MPos and WPos
            if mpos_match and wpos_match:
                self.root.after(0, self.update_position_display)
                self.root.after(0, self.update_position_display_text)

    def handle_grbl_ok(self):
        """Handle GRBL 'ok' response - command completed"""
        # Command completed, reduce buffer count
        if self.command_queue:
            self.command_queue.pop(0)  # Remove completed command
            self.buffer_size = max(0, self.buffer_size - 1)
        else:
            # Safety: command_queue empty but got 'ok'
            if self.buffer_size > 0:
                self.buffer_size = max(0, self.buffer_size - 1)

        # If executing, try to send more commands
        if self.is_executing:
            self.stream_next_commands()

    def update_position_display(self):
        """Update position display in UI"""
        # Update position labels
        if hasattr(self, "work_pos_label"):
            self.work_pos_label.config(
                text=f"X: {self.wpos['x']:6.2f}  Y: {self.wpos['y']:6.2f}  Z: {self.wpos['z']:6.2f}"
            )
        if hasattr(self, "machine_pos_label"):
            self.machine_pos_label.config(
                text=f"X: {self.mpos['x']:6.2f}  Y: {self.mpos['y']:6.2f}  Z: {self.mpos['z']:6.2f}"
            )

        # Update laser marker position on plot (only if on Laser Control tab)
        if hasattr(self, "laser_marker") and hasattr(self, "canvas"):
            try:
                # Check if we're on the Laser Control tab
                selected_tab = self.notebook.index(self.notebook.select())
                if selected_tab == 1:  # Laser Control tab is index 1
                    self.laser_marker.set_data([self.wpos["x"]], [self.wpos["y"]])
                    # Use draw() instead of draw_idle() for immediate update
                    self.canvas.draw()
            except:
                pass

    def update_position_display_text(self):
        """Update position display text on the plot"""
        if hasattr(self, "position_text"):
            mpos_text = f"MPos: X{self.mpos['x']:.2f} Y{self.mpos['y']:.2f} Z{self.mpos['z']:.2f}"
            wpos_text = f"WPos: X{self.wpos['x']:.2f} Y{self.wpos['y']:.2f} Z{self.wpos['z']:.2f}"
            self.position_text.set_text(f"{mpos_text}\n{wpos_text}")
            self.canvas.draw_idle()

    def update_state_display(self):
        """Update GRBL state display in UI"""
        if hasattr(self, "grbl_state_label") and hasattr(self, "grbl_state"):
            color = "gray"
            if self.grbl_state == "Idle":
                color = "green"
            elif self.grbl_state in ["Run", "Jog"]:
                color = "blue"
            elif self.grbl_state == "Alarm":
                color = "red"
            elif self.grbl_state == "Hold":
                color = "orange"

            self.grbl_state_label.config(
                text=f"State: {self.grbl_state}", foreground=color
            )

    def jog_move(self, x_dir, y_dir):
        """Jog move in X and Y direction"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        try:
            step = float(self.jog_step_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid step size!")
            return

        x_move = x_dir * step
        y_move = y_dir * step

        # Use $J jog command (GRBL 1.1+) which is safer
        # Format: $J=G91 X10 Y10 F1000 (relative move at feed rate 1000 mm/min)
        jog_cmd = f"$J=G91 X{x_move:.3f} Y{y_move:.3f} F1000"
        self.send_gcode(jog_cmd)

    def jog_move_z(self, z_dir):
        """Jog move in Z direction"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        try:
            step = float(self.jog_step_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid step size!")
            return

        z_move = z_dir * step

        # Use $J jog command for Z axis
        jog_cmd = f"$J=G91 Z{z_move:.3f} F500"
        self.send_gcode(jog_cmd)

    def go_home(self):
        """Go to work coordinate origin (0,0,0)"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Confirm with user
        response = messagebox.askyesno(
            "Go to Origin",
            "Move to work coordinate origin (0, 0, 0)?\n\n"
            "This will execute:\n"
            "G90 (absolute positioning)\n"
            "G0 X0 Y0 Z0 (rapid move to origin)",
        )

        if response:
            # Send commands to go to origin
            self.send_gcode("G90")  # Absolute positioning mode
            self.send_gcode("G0 X0 Y0 Z0")  # Rapid move to origin

    def home_machine(self):
        """Send machine to home position (only if homing is enabled)"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Send homing cycle command
        response = messagebox.askyesno(
            "Home Machine",
            "This will run the homing cycle. Make sure the machine is clear!\n\nContinue?",
        )

        if response:
            self.send_gcode("$H")

    def clear_errors(self):
        """Clear GRBL errors, alarms, and reset buffers"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Send commands to clear errors and reset
        self.send_gcode("$X")  # Clear alarms and unlock
        messagebox.showinfo("Info", "Clear errors command sent to GRBL")

    def reboot_grbl(self):
        """Reboot GRBL by sending Ctrl-X (soft reset)"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        response = messagebox.askyesno(
            "Reboot GRBL",
            "This will reboot GRBL by sending a soft reset (Ctrl-X).\n\n"
            "All settings and position will be lost.\n\n"
            "Continue?",
        )

        if response:
            if self.serial_connection:
                self.serial_connection.write(b"\x18")  # Ctrl-X soft reset
            messagebox.showinfo(
                "Info",
                "Soft reset sent. Please wait a few seconds, then reconnect to GRBL.",
            )

    def set_work_origin(self):
        """Set the current position as the work coordinate origin (0,0,0)"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Confirm with user
        response = messagebox.askyesno(
            "Set Work Origin",
            f"Set current position as work origin (0, 0, 0)?\n\n"
            f"Current Position: X={self.work_pos['x']:.2f} Y={self.work_pos['y']:.2f} Z={self.work_pos['z']:.2f}\n\n"
            f"This will execute: G10 L20 P1 X0 Y0 Z0",
        )

        if response:
            # Send G10 command to set current position as origin for G54 coordinate system
            self.send_gcode("G10 L20 P1 X0 Y0 Z0")

    def auto_origin(self, position):
        """Execute automatic origin setting sequence for Top or Bottom position

        Args:
            position: 'top' or 'bottom' to determine Y coordinate
        """
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Set Y coordinate based on position
        y_coord = 100 if position == "top" else 200
        position_name = position.capitalize()

        # Confirm with user
        response = messagebox.askyesno(
            f"Auto {position_name} Origin",
            f"Execute automatic origin sequence for {position_name} position?\n\n"
            "This will:\n"
            "1. Home the machine ($H)\n"
            "2. Set origin at current position (G10 L20 P1 X0 Y0 Z0)\n"
            f"3. Move to X320 Y{y_coord} Z-60.1 (G0 X320 Y{y_coord} Z-60.1)\n"
            "4. Set origin at current position (G10 L20 P1 X0 Y0 Z0)",
        )

        if response:
            # Send commands in sequence - GRBL will execute them in order
            self.send_gcode("$H")
            self.send_gcode("G10 L20 P1 X0 Y0 Z0")
            self.send_gcode(f"G0 X320 Y{y_coord} Z-60.1")
            self.send_gcode("G10 L20 P1 X0 Y0 Z0")

    def toggle_laser(self):
        """Toggle laser on/off using targeting power"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        try:
            # Use targeting power for laser toggle (not full cleaning power)
            power = float(self.targeting_power_var.get())
            max_power = float(self.laser_power_max_var.get())

            if 0 <= power <= 100:
                self.targeting_power = power
                scaled_power = int((power / 100.0) * max_power)

                if self.laser_on:
                    self.send_gcode("M5")
                    self.laser_on = False
                    self.laser_button.config(text="Laser OFF")
                else:
                    self.send_gcode(f"M3 S{scaled_power}")
                    self.send_gcode("G1 F100")
                    self.laser_on = True
                    self.laser_button.config(text="Laser ON")
            else:
                messagebox.showwarning(
                    "Warning", "Targeting power must be between 0-100%"
                )
        except ValueError:
            messagebox.showwarning(
                "Warning", "Please enter valid targeting power value"
            )

    def execute_manual_gcode(self):
        """Execute a manually entered G-code command"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        command = self.gcode_cmd_var.get().strip()
        if not command:
            return

        # Send the command
        self.send_gcode(command)

        # Add to communication log
        self.log_comm_message(f"> {command}", "sent")

        # Clear the entry field after execution
        self.gcode_cmd_var.set("")

    def clear_comm_log(self):
        """Clear the communication log"""
        if hasattr(self, "comm_log_text"):
            self.comm_log_text.config(state=tk.NORMAL)
            self.comm_log_text.delete(1.0, tk.END)
            self.comm_log_text.config(state=tk.DISABLED)

    def log_comm_message(self, message, tag="sent"):
        """Log a message to the communication log"""
        if not hasattr(self, "comm_log_text"):
            return

        # Filter out status queries and responses to reduce log spam
        if tag == "sent" and message.strip() == "> ?":
            return  # Don't log status queries
        if tag == "received" and message.startswith("< <") and message.endswith(">"):
            return  # Don't log status responses
        # Filter out "ok" responses from status queries
        if tag == "received" and message.strip() == "< ok":
            return  # Don't log ok responses

        self.comm_log_text.config(state=tk.NORMAL)
        self.comm_log_text.insert(tk.END, message + "\n", tag)

        if self.log_autoscroll_var.get():
            self.comm_log_text.see(tk.END)

        self.comm_log_text.config(state=tk.DISABLED)

    def capture_position(self):
        """Capture current position for selected reference point"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Initialize actual points storage if not exists
        if not hasattr(self, "actual_points"):
            self.actual_points = {"top": {}, "bottom": {}}

        # Get selected item
        selection = self.ref_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a reference point!")
            return

        item = self.ref_tree.item(selection[0])
        values = list(item["values"])
        point_id = values[0]

        # Store actual position using correct wpos variable
        actual_x = self.wpos["x"]
        actual_y = self.wpos["y"]

        if self.current_position == "top":
            self.actual_points["top"][point_id] = {"x": actual_x, "y": actual_y}
        else:
            self.actual_points["bottom"][point_id] = {"x": actual_x, "y": actual_y}

        # Update table display with current position
        values[3] = f"{actual_x:.2f}"
        values[4] = f"{actual_y:.2f}"
        self.ref_tree.item(selection[0], values=values)

        print(
            f"Captured position for point {point_id}: X={actual_x:.2f}, Y={actual_y:.2f}"
        )

    def goto_position(self):
        """Move to selected reference point"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        selection = self.ref_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a reference point!")
            return

        item = self.ref_tree.item(selection[0])
        values = item["values"]

        try:
            x = float(values[1])  # Expected X
            y = float(values[2])  # Expected Y
            command = f"G0 X{x:.3f} Y{y:.3f}"
            self.send_gcode(command)
        except ValueError:
            messagebox.showerror("Error", "Invalid coordinates!")

    def adjust_gcode(self):
        """Perform circle fitting and generate G-code"""
        # Get reference points from table
        ref_points = []
        for item in self.ref_tree.get_children():
            values = self.ref_tree.item(item)["values"]
            try:
                x = float(values[3])  # Actual X
                y = float(values[4])  # Actual Y
                if x != 0.0 or y != 0.0:  # Skip unset points
                    ref_points.append((x, y))
            except ValueError:
                continue

        if len(ref_points) < 3:
            messagebox.showerror("Error", "Need at least 3 reference points!")
            return

        # Perform circle fitting
        try:
            if self.current_position == "top":
                radius = self.outer_diameter / 2
            else:
                radius = self.inner_diameter / 2

            self.fitted_center, self.circle_errors = self.fit_circle_fixed_radius(
                ref_points, radius
            )
            self.fitted_radius = radius

            # Update circle center based on fitted center
            if self.current_position == "top":
                self.top_center = list(self.fitted_center)
            else:
                self.bottom_center = list(self.fitted_center)

            # Display results
            self.display_calculation_results()

            # Regenerate G-code with new center
            self.update_gcode_from_geometry()

            # Update reference table with new expected positions
            self.update_reference_display()

            # Update plot
            self.update_plot()

            messagebox.showinfo("Success", "G-code adjusted with fitted circle center!")

        except Exception as e:
            messagebox.showerror("Error", f"Circle fitting failed: {str(e)}")

    def reset_gcode(self):
        """Reset circle centers to defaults and regenerate G-code"""
        # Reset centers to defaults
        self.top_center = [0, -50]
        self.bottom_center = [0, 50]

        # Recalculate reference points with new centers
        self._compute_reference_points_from_angles()

        # Regenerate G-code
        self.update_gcode_from_geometry()

        # Update reference table
        self.update_reference_display()

        # Update plot
        self.update_plot()

        # Clear calculation results
        self.calc_text.delete(1.0, tk.END)

        messagebox.showinfo("Success", "G-code reset to default center values!")

    def fit_circle_fixed_radius(self, points, radius):
        """Fit circle with fixed radius using least squares"""
        points = np.array(points)

        def residuals(center):
            distances = np.sqrt(
                (points[:, 0] - center[0]) ** 2 + (points[:, 1] - center[1]) ** 2
            )
            return distances - radius

        # Initial guess at center
        initial_center = np.mean(points, axis=0)

        # Fit circle
        result = least_squares(residuals, initial_center)
        fitted_center = result.x

        # Calculate errors
        distances = np.sqrt(
            (points[:, 0] - fitted_center[0]) ** 2
            + (points[:, 1] - fitted_center[1]) ** 2
        )
        errors = distances - radius

        return fitted_center, errors

    def display_calculation_results(self):
        """Display calculation results"""
        self.calc_text.delete(1.0, tk.END)

        results = f"""Circle Fitting Results
====================

Fitted Center: ({self.fitted_center[0]:.4f}, {self.fitted_center[1]:.4f}) mm
Radius: {self.fitted_radius:.4f} mm

Point Errors:
"""

        for i, error in enumerate(self.circle_errors):
            status = "⚠ HIGH ERROR" if abs(error) > 0.1 else ""
            results += f"Point {i+1}: {error:+.4f} mm{status}\n"

        rms_error = np.sqrt(np.mean(self.circle_errors**2))
        max_error = np.max(np.abs(self.circle_errors))

        results += f"""
RMS Error: {rms_error:.4f} mm
Max Error: {max_error:.4f} mm
Status: {'✓ Excellent' if max_error <= 0.05 else '✓ Good' if max_error <= 0.1 else '✗ Poor - Check alignment'}
"""

        self.calc_text.insert(1.0, results)

    def run_cleaning(self):
        """Run the cleaning G-code with proper buffer management"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Check if G-code widgets exist
        if not hasattr(self, "top_preamble_widget") or not hasattr(
            self, "top_cleaning_widget"
        ):
            messagebox.showwarning("Warning", "G-code tab not initialized!")
            return

        # Get G-code based on current position
        if self.current_position == "top":
            preamble = self.top_preamble_widget.get("1.0", tk.END).strip()
            cleaning = self.top_cleaning_widget.get("1.0", tk.END).strip()
            postscript = self.top_postscript_widget.get("1.0", tk.END).strip()
        else:
            preamble = self.bottom_preamble_widget.get("1.0", tk.END).strip()
            cleaning = self.bottom_cleaning_widget.get("1.0", tk.END).strip()
            postscript = self.bottom_postscript_widget.get("1.0", tk.END).strip()

        # Combine G-code sections
        combined_gcode = []
        if preamble:
            combined_gcode.extend(preamble.split("\n"))
        if cleaning:
            combined_gcode.extend(cleaning.split("\n"))
        if postscript:
            combined_gcode.extend(postscript.split("\n"))

        # Filter out empty lines and comments
        filtered_gcode = []
        for line in combined_gcode:
            line = line.strip()
            if line and not line.startswith(";"):
                filtered_gcode.append(line)

        if not filtered_gcode:
            messagebox.showwarning("Warning", "No G-code to execute!")
            return

        # Clear buffers
        self.gcode_buffer = filtered_gcode.copy()
        self.command_queue.clear()
        self.buffer_size = 0

        # Set execution flag
        self.is_executing = True

        # Update status indicator
        if hasattr(self, "execution_status_label"):
            self.execution_status_label.config(text="Running", foreground="orange")

        print(f"Starting execution of {len(filtered_gcode)} G-code commands")

        # Start streaming
        self.stream_next_commands()

    def stream_next_commands(self):
        """Send as many commands as buffer allows (event-driven)"""
        if not self.is_executing or not self.gcode_buffer:
            # Check if execution is complete
            if self.is_executing and not self.gcode_buffer and self.buffer_size == 0:
                self.finish_execution()
            return

        # Send multiple commands if buffer has space
        while self.gcode_buffer and self.buffer_size < self.max_buffer_size:
            # Get next command
            line = self.gcode_buffer.pop(0)

            # Send it
            if not self.send_gcode_buffered(line):
                self.stop_execution()
                return

        # Check if done sending (but buffer may still have commands executing)
        if not self.gcode_buffer:
            # Schedule a check for completion
            self.root.after(100, self.check_execution_complete)

    def send_gcode_buffered(self, command):
        """Send G-code command with buffer tracking"""
        if not self.serial_connection or not self.is_connected:
            return False

        try:
            # Send command
            self.serial_connection.write(f"{command}\n".encode())

            # Log sent command
            self.log_comm_message(f"> {command}", "sent")

            # Track command in buffer
            self.buffer_size += 1
            self.command_queue.append(command)

            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False

    def check_execution_complete(self):
        """Check if execution is complete (buffer empty)"""
        if not self.is_executing:
            return

        # If buffer is empty and all commands sent, wait for machine to finish moving
        if self.buffer_size <= 0 and not self.gcode_buffer:
            # Wait a bit longer to ensure machine has stopped moving
            # Query position to get final state
            if self.is_connected:
                self.send_gcode("?")
            # Schedule final completion after delay
            self.root.after(500, self.finish_execution)
        else:
            # Check again in 100ms
            self.root.after(100, self.check_execution_complete)

    def finish_execution(self):
        """Complete the execution process"""
        # Double-check buffer is really empty and we're still executing
        if self.buffer_size > 0 or self.gcode_buffer:
            # Not really done yet, check again
            self.root.after(100, self.check_execution_complete)
            return

        self.is_executing = False

        # Clear buffers
        self.gcode_buffer.clear()
        self.command_queue.clear()
        self.buffer_size = 0

        # Update status indicator
        if hasattr(self, "execution_status_label"):
            self.execution_status_label.config(text="Complete", foreground="green")

        print("Execution complete!")
        messagebox.showinfo("Complete", "G-code execution completed successfully!")

    def stop_execution(self):
        """Stop G-code execution"""
        if self.is_connected:
            # Set flag to stop sending more commands
            self.is_executing = False

            # Clear pending commands
            self.gcode_buffer.clear()

            # Send feed hold (pause)
            if self.serial_connection:
                try:
                    self.serial_connection.write(b"!")
                except:
                    pass

            # Clear alarm
            self.send_gcode("$X")

            # Clear buffers
            self.command_queue.clear()
            self.buffer_size = 0

            # Display message
            messagebox.showinfo(
                "Execution Stopped", "G-code execution has been stopped."
            )

            # Update status indicator
            if hasattr(self, "execution_status_label"):
                self.execution_status_label.config(text="Stopped", foreground="red")
        else:
            messagebox.showwarning("Warning", "Not connected to GRBL")

    def save_configuration(self):
        """Save configuration to file"""
        config = {
            # Geometry parameters
            "outer_diameter": self.outer_diameter,
            "inner_diameter": self.inner_diameter,
            "outer_cleaning_offsets": self.outer_cleaning_offsets,
            "inner_cleaning_offsets": self.inner_cleaning_offsets,
            # Center points
            "top_center": self.top_center,
            "bottom_center": self.bottom_center,
            # Reference angles (stored instead of computed points)
            "top_reference_angles": self.top_reference_angles,
            "bottom_reference_angles": self.bottom_reference_angles,
            # Cleaning arc angles
            "top_start_angle": self.top_start_angle,
            "top_end_angle": self.top_end_angle,
            "bottom_start_angle": self.bottom_start_angle,
            "bottom_end_angle": self.bottom_end_angle,
            # Laser parameters
            "laser_power": self.laser_power,
            "laser_power_max": self.laser_power_max,
            "targeting_power": self.targeting_power,
            "feed_rate": self.feed_rate,
        }

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if filename:
            with open(filename, "w") as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Success", f"Configuration saved to:\n{filename}")

    def load_configuration(self):
        """Load configuration from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, "r") as f:
                    config = json.load(f)

                # Update geometry variables
                self.outer_diameter = config.get("outer_diameter", 100.0)
                self.inner_diameter = config.get("inner_diameter", 50.0)
                self.outer_cleaning_offsets = config.get(
                    "outer_cleaning_offsets", [0, 1, 2, 3]
                )
                self.inner_cleaning_offsets = config.get(
                    "inner_cleaning_offsets", [0, -1, -2, -3]
                )

                # Update center points
                self.top_center = config.get("top_center", [0, -50])
                self.bottom_center = config.get("bottom_center", [0, 50])

                # Update reference angles
                self.top_reference_angles = config.get(
                    "top_reference_angles", [-30, 0, 45, 90, 135, 180, 210]
                )
                self.bottom_reference_angles = config.get(
                    "bottom_reference_angles", [150, 180, 225, 270, 315, 0, 30]
                )

                # Recompute reference points from angles
                self._compute_reference_points_from_angles()

                # Update cleaning arc angles
                self.top_start_angle = config.get("top_start_angle", 0)
                self.top_end_angle = config.get("top_end_angle", 180)
                self.bottom_start_angle = config.get("bottom_start_angle", 0)
                self.bottom_end_angle = config.get("bottom_end_angle", -180)

                # Update laser parameters
                self.laser_power = config.get("laser_power", 100)
                self.laser_power_max = config.get("laser_power_max", 10000)
                self.targeting_power = config.get("targeting_power", 3)
                self.feed_rate = config.get("feed_rate", 500)

                # Update UI - Geometry tab
                self.outer_diameter_var.set(str(self.outer_diameter))
                self.inner_diameter_var.set(str(self.inner_diameter))
                self.outer_offsets_var.set(
                    ", ".join(map(str, self.outer_cleaning_offsets))
                )
                self.inner_offsets_var.set(
                    ", ".join(map(str, self.inner_cleaning_offsets))
                )
                self.top_ref_angles_var.set(
                    ", ".join(map(str, self.top_reference_angles))
                )
                self.bottom_ref_angles_var.set(
                    ", ".join(map(str, self.bottom_reference_angles))
                )

                # Update UI - Laser tab
                if hasattr(self, "laser_power_var"):
                    self.laser_power_var.set(str(self.laser_power))
                if hasattr(self, "laser_power_max_var"):
                    self.laser_power_max_var.set(str(self.laser_power_max))
                if hasattr(self, "targeting_power_var"):
                    self.targeting_power_var.set(str(self.targeting_power))
                if hasattr(self, "feed_rate_var"):
                    self.feed_rate_var.set(str(self.feed_rate))

                # Update reference points display and plot
                self.update_reference_display()
                self.update_plot()
                
                # Regenerate G-code with new parameters
                self.update_gcode_from_geometry()

                messagebox.showinfo(
                    "Success", f"Configuration loaded from:\n{filename}"
                )

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")

    def update_geometry_from_ui(self, event=None):
        """Update geometry variables from UI"""
        try:
            self.outer_diameter = float(self.outer_diameter_var.get())
            self.inner_diameter = float(self.inner_diameter_var.get())

            # Update inch labels
            self.outer_diameter_inches_label.config(
                text=f"({self.outer_diameter / 25.4:.4f} in)"
            )
            self.inner_diameter_inches_label.config(
                text=f"({self.inner_diameter / 25.4:.4f} in)"
            )

            # Parse offsets
            outer_offsets_str = self.outer_offsets_var.get()
            self.outer_cleaning_offsets = [
                float(x.strip()) for x in outer_offsets_str.split(",") if x.strip()
            ]

            inner_offsets_str = self.inner_offsets_var.get()
            self.inner_cleaning_offsets = [
                float(x.strip()) for x in inner_offsets_str.split(",") if x.strip()
            ]

            # Update geometry plot
            self.update_geometry_plot()

            # Recalculate reference points with new diameters
            self._compute_reference_points_from_angles()

            # Update reference points display if on Laser Control tab
            selected_tab = self.notebook.index(self.notebook.select())
            if selected_tab == 1:  # Laser Control tab
                self.update_reference_display()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid geometry values: {str(e)}")

        # Update G-code when geometry changes
        self.update_gcode_from_geometry()

    def update_gcode_from_geometry(self):
        """Generate G-code from current geometry settings"""
        # Default preamble and postscript from DXF2Gcode.py
        scaled_power = int((self.laser_power / 100.0) * self.laser_power_max)

        # Top preamble with circle center
        top_preamble = (
            f"; Circle Center: X{self.top_center[0]:.4f} Y{self.top_center[1]:.4f}\n"
        )
        top_preamble += "G21 ; Set units to millimeters\nG90 ; Absolute positioning\nG54 ; Use work coordinate system\nG0 X0 Y0 Z0 ; Go to zero position\n"
        top_preamble += f"M4 S{scaled_power} ; laser on\n"

        # Bottom preamble with circle center
        bottom_preamble = f"; Circle Center: X{self.bottom_center[0]:.4f} Y{self.bottom_center[1]:.4f}\n"
        bottom_preamble += "G21 ; Set units to millimeters\nG90 ; Absolute positioning\nG54 ; Use work coordinate system\nG0 X0 Y0 Z0 ; Go to zero position\n"
        bottom_preamble += f"M4 S{scaled_power} ; laser on\n"

        postscript = "M5 ; Turn off laser\nG0 X0 Y0 ; Send to unload position\n"

        # Generate cleaning G-code for top
        top_cleaning = self.generate_top_cleaning_gcode()

        # Generate cleaning G-code for bottom
        bottom_cleaning = self.generate_bottom_cleaning_gcode()

        # Update text widgets if they exist
        if hasattr(self, "top_preamble_widget"):
            self.top_preamble_widget.delete("1.0", tk.END)
            self.top_preamble_widget.insert("1.0", top_preamble)
            self.top_cleaning_widget.delete("1.0", tk.END)
            self.top_cleaning_widget.insert("1.0", top_cleaning)
            self.top_postscript_widget.delete("1.0", tk.END)
            self.top_postscript_widget.insert("1.0", postscript)

            self.bottom_preamble_widget.delete("1.0", tk.END)
            self.bottom_preamble_widget.insert("1.0", bottom_preamble)
            self.bottom_cleaning_widget.delete("1.0", tk.END)
            self.bottom_cleaning_widget.insert("1.0", bottom_cleaning)
            self.bottom_postscript_widget.delete("1.0", tk.END)
            self.bottom_postscript_widget.insert("1.0", postscript)

    def update_laser_power(self):
        """Update laser power from UI and refresh plot"""
        try:
            power = float(self.laser_power_var.get())
            if 0 <= power <= 100:
                self.laser_power = power
                # Update G-code when power changes
                self.update_gcode_from_geometry()
                # Update plot if on Laser Control tab
                selected_tab = self.notebook.index(self.notebook.select())
                if selected_tab == 1:  # Laser Control tab
                    self.update_plot()
            else:
                messagebox.showwarning("Warning", "Power level must be between 0-100%")
        except ValueError:
            messagebox.showwarning(
                "Warning", "Please enter a valid number for power level"
            )

    def update_laser_power_max(self):
        """Update max laser power from UI and refresh plot"""
        try:
            max_power = float(self.laser_power_max_var.get())
            if max_power > 0:
                self.laser_power_max = max_power
                # Update G-code when max power changes
                self.update_gcode_from_geometry()
                # Update plot if on Laser Control tab
                selected_tab = self.notebook.index(self.notebook.select())
                if selected_tab == 1:  # Laser Control tab
                    self.update_plot()
            else:
                messagebox.showwarning("Warning", "Max power must be greater than 0")
        except ValueError:
            messagebox.showwarning(
                "Warning", "Please enter a valid number for max power"
            )

    def update_targeting_power(self):
        """Update targeting power from UI and refresh plot"""
        try:
            power = float(self.targeting_power_var.get())
            if 0 <= power <= 100:
                self.targeting_power = power
                # Update plot if on Laser Control tab
                selected_tab = self.notebook.index(self.notebook.select())
                if selected_tab == 1:  # Laser Control tab
                    self.update_plot()
            else:
                messagebox.showwarning(
                    "Warning", "Targeting power level must be between 0-100%"
                )
        except ValueError:
            messagebox.showwarning(
                "Warning", "Please enter a valid number for targeting power level"
            )

    def update_feedrate(self):
        """Update feedrate from UI and refresh G-code"""
        try:
            feedrate = float(self.feedrate_var.get())
            if feedrate > 0:
                self.feed_rate = feedrate
                # Update G-code when feedrate changes
                self.update_gcode_from_geometry()
                # Update plot if on Laser Control tab
                selected_tab = self.notebook.index(self.notebook.select())
                if selected_tab == 1:  # Laser Control tab
                    self.update_plot()
            else:
                messagebox.showwarning("Warning", "Feedrate must be greater than 0")
        except ValueError:
            messagebox.showwarning(
                "Warning", "Please enter a valid number for feedrate"
            )

    def generate_top_cleaning_gcode(self):
        """Generate cleaning G-code for top position"""
        lines = []
        scaled_power = int((self.laser_power / 100.0) * self.laser_power_max)

        # Get center and radius for top
        center = self.top_center
        outer_radius = self.outer_diameter / 2
        inner_radius = self.inner_diameter / 2

        # Convert angles to radians
        start_rad = np.radians(self.top_start_angle)
        end_rad = np.radians(self.top_end_angle)

        # Outer passes - alternating CCW/CW
        for i, offset in enumerate(self.outer_cleaning_offsets):
            clean_radius = outer_radius + offset
            # if an even pass go start to end, if an odd pass go end to start
            if i % 2 == 0:
                start_rad = np.radians(self.top_start_angle)
                end_rad = np.radians(self.top_end_angle)
            else:
                start_rad = np.radians(self.top_end_angle)
                end_rad = np.radians(self.top_start_angle)

            clean_start_x = center[0] + clean_radius * np.cos(start_rad)
            clean_start_y = center[1] + clean_radius * np.sin(start_rad)
            clean_end_x = center[0] + clean_radius * np.cos(end_rad)
            clean_end_y = center[1] + clean_radius * np.sin(end_rad)

            # I/J offsets
            i_offset = center[0] - clean_start_x
            j_offset = center[1] - clean_start_y

            # G0 fast to position, then G1 move in place to get exact position
            lines.append(f"G0 X{clean_start_x:.4f} Y{clean_start_y:.4f}")
            lines.append(
                f"G1 X{clean_start_x:.4f} Y{clean_start_y:.4f} F{self.feed_rate}"
            )
            # now do the arc
            # Alternate direction: even passes CCW (G3), odd passes CW (G2)
            if i % 2 == 0:
                # Even passes: Start angle → End angle (CCW)
                lines.append(
                    f"G3 X{clean_end_x:.4f} Y{clean_end_y:.4f} I{i_offset:.4f} J{j_offset:.4f} F{self.feed_rate}"
                )
            else:
                # Odd passes: End angle → Start angle (CW)
                lines.append(
                    f"G2 X{clean_end_x:.4f} Y{clean_end_y:.4f} I{i_offset:.4f} J{j_offset:.4f} F{self.feed_rate}"
                )

        # Inner passes - alternating CCW/CW
        for i, offset in enumerate(self.inner_cleaning_offsets):
            clean_radius = inner_radius + offset
            if i % 2 == 0:
                start_rad = np.radians(self.top_start_angle)
                end_rad = np.radians(self.top_end_angle)
            else:
                start_rad = np.radians(self.top_end_angle)
                end_rad = np.radians(self.top_start_angle)

            clean_start_x = center[0] + clean_radius * np.cos(start_rad)
            clean_start_y = center[1] + clean_radius * np.sin(start_rad)
            clean_end_x = center[0] + clean_radius * np.cos(end_rad)
            clean_end_y = center[1] + clean_radius * np.sin(end_rad)

            # I/J offsets
            i_offset = center[0] - clean_start_x
            j_offset = center[1] - clean_start_y

            # G0 fast to position, then G1 move in place to get exact position
            lines.append(f"G0 X{clean_start_x:.4f} Y{clean_start_y:.4f}")
            lines.append(
                f"G1 X{clean_start_x:.4f} Y{clean_start_y:.4f} F{self.feed_rate}"
            )
            # now do the arc
            # Alternate direction: even passes CCW (G3), odd passes CW (G2)
            if i % 2 == 0:
                # Even passes: Start angle → End angle (CCW)
                lines.append(
                    f"G3 X{clean_end_x:.4f} Y{clean_end_y:.4f} I{i_offset:.4f} J{j_offset:.4f} F{self.feed_rate}"
                )
            else:
                # Odd passes: End angle → Start angle (CW)
                lines.append(
                    f"G2 X{clean_end_x:.4f} Y{clean_end_y:.4f} I{i_offset:.4f} J{j_offset:.4f} F{self.feed_rate}"
                )

        return "\n".join(lines)

    def generate_bottom_cleaning_gcode(self):
        """Generate cleaning G-code for bottom position"""
        lines = []
        scaled_power = int((self.laser_power / 100.0) * self.laser_power_max)

        # Get center and radius for bottom
        center = self.bottom_center
        outer_radius = self.outer_diameter / 2
        inner_radius = self.inner_diameter / 2

        # Convert angles to radians
        start_rad = np.radians(self.bottom_start_angle)
        end_rad = np.radians(self.bottom_end_angle)

        # Outer passes - first pass CW
        for i, offset in enumerate(self.outer_cleaning_offsets):
            clean_radius = outer_radius + offset
            if i % 2 == 0:
                start_rad = np.radians(self.bottom_start_angle)
                end_rad = np.radians(self.bottom_end_angle)
            else:
                start_rad = np.radians(self.bottom_end_angle)
                end_rad = np.radians(self.bottom_start_angle)

            clean_start_x = center[0] + clean_radius * np.cos(start_rad)
            clean_start_y = center[1] + clean_radius * np.sin(start_rad)
            clean_end_x = center[0] + clean_radius * np.cos(end_rad)
            clean_end_y = center[1] + clean_radius * np.sin(end_rad)

            # I/J offsets
            i_offset = center[0] - clean_start_x
            j_offset = center[1] - clean_start_y

            # G0 fast to position, then G1 move in place to get exact position
            lines.append(f"G0 X{clean_start_x:.4f} Y{clean_start_y:.4f}")
            lines.append(
                f"G1 X{clean_start_x:.4f} Y{clean_start_y:.4f} F{self.feed_rate}"
            )
            # now do the arc
            if i % 2 == 0:
                # Even passes: Start angle → End angle (CW)
                lines.append(
                    f"G2 X{clean_end_x:.4f} Y{clean_end_y:.4f} I{i_offset:.4f} J{j_offset:.4f} F{self.feed_rate}"
                )
            else:
                # Odd passes: End angle → Start angle (CCW)
                lines.append(
                    f"G3 X{clean_end_x:.4f} Y{clean_end_y:.4f} I{i_offset:.4f} J{j_offset:.4f} F{self.feed_rate}"
                )

        # Inner passes - alternating CW/CCW
        for i, offset in enumerate(self.inner_cleaning_offsets):
            clean_radius = inner_radius + offset
            if i % 2 == 0:
                start_rad = np.radians(self.bottom_start_angle)
                end_rad = np.radians(self.bottom_end_angle)
            else:
                start_rad = np.radians(self.bottom_end_angle)
                end_rad = np.radians(self.bottom_start_angle)

            clean_start_x = center[0] + clean_radius * np.cos(start_rad)
            clean_start_y = center[1] + clean_radius * np.sin(start_rad)
            clean_end_x = center[0] + clean_radius * np.cos(end_rad)
            clean_end_y = center[1] + clean_radius * np.sin(end_rad)

            # I/J offsets
            i_offset = center[0] - clean_start_x
            j_offset = center[1] - clean_start_y

            # G0 fast to position, then G1 move in place to get exact position
            lines.append(f"G0 X{clean_start_x:.4f} Y{clean_start_y:.4f}")
            lines.append(
                f"G1 X{clean_start_x:.4f} Y{clean_start_y:.4f} F{self.feed_rate}"
            )
            # now do the arc
            if i % 2 == 0:
                # Even passes: Start angle → End angle (CW)
                lines.append(
                    f"G2 X{clean_end_x:.4f} Y{clean_end_y:.4f} I{i_offset:.4f} J{j_offset:.4f} F{self.feed_rate}"
                )
            else:
                # Odd passes: End angle → Start angle (CCW)
                lines.append(
                    f"G3 X{clean_end_x:.4f} Y{clean_end_y:.4f} I{i_offset:.4f} J{j_offset:.4f} F{self.feed_rate}"
                )
        return "\n".join(lines)

    def update_reference_angles_from_ui(self, event=None):
        """Update reference angles from UI and compute X,Y points from them"""
        try:
            # Parse top reference angles
            top_text = self.top_ref_angles_var.get().strip()
            if top_text:
                self.top_reference_angles = [
                    float(angle.strip()) for angle in top_text.split(",")
                ]
            else:
                self.top_reference_angles = []

            # Parse bottom reference angles
            bottom_text = self.bottom_ref_angles_var.get().strip()
            if bottom_text:
                self.bottom_reference_angles = [
                    float(angle.strip()) for angle in bottom_text.split(",")
                ]
            else:
                self.bottom_reference_angles = []

            # Convert angles to X,Y coordinates on outer circumference
            self._compute_reference_points_from_angles()

            # Update geometry plot
            self.update_geometry_plot()

            # Update G-code
            self.update_gcode_from_geometry()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid reference angle format: {str(e)}")

    def update_angles(self, event=None):
        """Update cleaning angles from UI"""
        try:
            self.top_start_angle = float(self.top_start_angle_var.get())
            self.top_end_angle = float(self.top_end_angle_var.get())
            self.bottom_start_angle = float(self.bottom_start_angle_var.get())
            self.bottom_end_angle = float(self.bottom_end_angle_var.get())

            # Update geometry plot
            self.update_geometry_plot()

            # Update G-code
            self.update_gcode_from_geometry()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid angle values: {str(e)}")

    def on_gcode_text_change(self, event=None):
        """Handle G-code text changes - update plot if on Laser Control tab"""
        # Only update plot if we're currently on the Laser Control tab
        try:
            selected_tab = self.notebook.index(self.notebook.select())
            if selected_tab == 1:  # Laser Control tab is index 1
                self.update_plot()
        except:
            pass  # Ignore errors if notebook not ready yet


def main():
    root = tk.Tk()
    app = CircumferenceClean(root)
    root.mainloop()


if __name__ == "__main__":
    main()
