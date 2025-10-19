# Generate Carousel G-code Program
# Converted from LaserCleanCarousel.py - removes serial communication, adds JSON settings
VERSION = 2.1

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import numpy as np

# Configure matplotlib for better toolbar display
matplotlib.rcParams["figure.autolayout"] = True
import json
import os
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.geometry.base import JOIN_STYLE
from PIL import Image, ImageTk

matplotlib.use("TkAgg")

####################################################################
# === Key Laser Information ===
ZLASER = 0  # height for laser to clean with 0.4mm spot size
PLASER = 8000  # power level for laser 8000/10000 = 80%
FEEDRATE = 1500  # feedrate for cleaning 1500mm/min or 25mm/sec

####################################################################
DEBUG = False


def debug_print(msg):
    if DEBUG:
        print(msg)


####################################################################
# === Carousel Geometry Information ===
section1and3 = [
    "3-1",
    "3-2",
    "3-3",
    "3-4",
    "3-5",
    "3-6",
    "3-7",
    "3-8",
    "3-9",
    "3-10",
    "3-11",
    "3-12",
    "3-13",
    "3-14",
    "3-15",
    "3-16",
    "1-1",
    "1-2",
    "1-3",
    "1-4",
    "1-5",
    "1-6",
    "1-7",
    "1-8",
    "1-9",
    "1-10",
    "1-11",
    "1-12",
    "1-13",
    "1-14",
    "1-15",
    "1-16",
]
section2 = [
    "2-1",
    "2-2",
    "2-3",
    "2-4",
    "2-5",
    "2-6",
    "2-7",
    "2-8",
    "2-9",
    "2-10",
    "2-11",
    "2-12",
    "2-13",
    "2-14",
    "2-15",
    "2-16",
]
yaw_from_origin = {
    "0-0": 0.00,
    "1-1": 85.25,
    "1-2": 78.75,
    "1-3": 71.25,
    "1-4": 63.75,
    "1-5": 56.25,
    "1-6": 48.75,
    "1-7": 41.25,
    "1-8": 33.75,
    "1-9": 26.25,
    "1-10": 18.75,
    "1-11": 11.25,
    "1-12": 3.75,
    "1-13": -3.75,
    "1-14": -11.25,
    "1-15": -18.75,
    "1-16": -25.25,
    "2-1": -34.75,
    "2-2": -41.25,
    "2-3": -48.75,
    "2-4": -56.25,
    "2-5": -63.75,
    "2-6": -71.25,
    "2-7": -78.75,
    "2-8": -86.25,
    "2-9": -93.75,
    "2-10": -101.25,
    "2-11": -108.75,
    "2-12": -116.25,
    "2-13": -123.75,
    "2-14": -131.25,
    "2-15": -138.75,
    "2-16": -145.25,
    "3-1": -154.75,
    "3-2": -161.25,
    "3-3": -168.75,
    "3-4": -176.25,
    "3-5": -183.75,
    "3-6": -191.25,
    "3-7": -198.75,
    "3-8": -206.25,
    "3-9": -213.75,
    "3-10": -221.25,
    "3-11": -228.75,
    "3-12": -236.25,
    "3-13": -243.75,
    "3-14": -251.25,
    "3-15": -258.75,
    "3-16": -265.25,
}

"""
# definition of the pad using arcs but GRBL has trouble with arcs
# if the math coordinates are not exact so using linear segments instead
G2 X223.94 Y-7.62 R224.066 ; CW arc pt1->pt2
G1 X213.69 Y-7.62 ; Linear pt2->pt3
G3 X213.69 Y7.62 R213.83 ; CCW arc pt3->pt4
G1 X223.94 Y7.62 ; Linear pt4->pt1
"pad_gcode_template": [
    {"type": "G2", "X": 223.94, "Y": -7.62, "R": 224.066, ...},  # CW arc pt1->pt2
    {"type": "G1", "X": 213.69, "Y": -7.62, ...},               # Linear pt2->pt3
    {"type": "G3", "X": 213.69, "Y": 7.62, "R": 213.83, ...},   # CCW arc pt3->pt4
    {"type": "G1", "X": 223.94, "Y": 7.62, ...},                # Linear pt4->pt1
],

# linear segments are:
G0 X223.94 Y7.62        ; pt1
G1 X224.0336 Y3.8105    ; G2 arc approx.
G1 X224.0660 Y0.0000
G1 X224.0336 Y-3.8105
G1 X223.94 Y-7.62       ; pt2
G1 X213.69 Y-7.62       ; Linear pt2->pt3
G1 X213.7960 Y-3.8107   ; G3 arc approx.
G1 X213.8300 Y0.0000
G1 X213.7960 Y3.8107
G1 X213.69 Y7.62
G1 X223.94 Y7.62        ; Linear pt4->pt1

"""

# === Geometry Functions ===


def expand_polygon(points, offset):
    """Expand polygon by offset amount"""
    poly = Polygon(points)
    poly = orient(poly, sign=1.0)
    expanded = poly.buffer(offset, join_style=JOIN_STYLE.mitre)
    coords = np.round(expanded.exterior.coords, 3)
    return [pt.tolist() for pt in coords]


def get_default_settings():
    """Return default settings dictionary"""
    return {
        "section_1_3_origin": [0, -50],
        "section_2_origin": [0, 50],
        "section_1_3_preamble": "; Cleaning G-code for Carousel - top: sections 1 and 3\n; Reference points are the bottom outside corners of S3P1 and S1P16\n; reference_point1 = (-199.2901, -152.4163)\n; reference_point2 = (199.2901, -152.4163)\nG90 ; absolute coordinates\nG21 ; metric units\nG17 ; arcs in XY plane\n",
        "section_2_preamble": "; Cleaning G-code for Carousel - bottom: section 2\n; Reference points are the bottom outside corners of S3P1 and S1P16\n; reference_point1 = (-199.2901, -52.4163)\n; reference_point2 = (199.2901, -52.4163)G90 ; absolute coordinates\nG21 ; metric units\nG17 ; arcs in XY plane\n",
        "section_1_3_postscript": "M5\nG0 X0 Y0 Z0",
        "section_2_postscript": "M5\nG0 X0 Y0 Z0",
        "section_1_3_laser_power": 10,
        "section_2_laser_power": 10,
        "section_1_3_feedrate": 1500,
        "section_2_feedrate": 1500,
        "cleaning_pass_spacings": [0.10, 0.18, 0.26, 0.34, 0.42],
        "calculated_cleaning_passes": [],
        "section_1_3_origin": [0, -50],
        "section_2_origin": [0, 50],
        "section_1_3_pads": "3-16,3-15,3-14,3-13,3-12,3-11,3-10,3-9,3-8,3-7,3-6,3-5,3-4,3-3,3-2,3-1,1-1,1-2,1-3,1-4,1-5,1-6,1-7,1-8,1-9,1-10,1-11,1-12,1-13,1-14,1-15,1-16",
        "section_2_pads": "2-1,2-2,2-3,2-4,2-5,2-6,2-7,2-8,2-9,2-10,2-11,2-12,2-13,2-14,2-15,2-16",
        "zlaser": 0,
        "center": [300, 100],
        "table_dimensions": {"lower_left": [-400, -200], "upper_right": [400, 200]},
        "pad_gcode_template": [
            {"type": "G1", "X": 224.0336, "Y": 3.8105, "comment": "G2 arc approx."},
            {"type": "G1", "X": 224.0660, "Y": 0.0000, "comment": ""},
            {"type": "G1", "X": 224.0336, "Y": -3.8105, "comment": ""},
            {"type": "G1", "X": 223.94, "Y": -7.62, "comment": "pt2"},
            {"type": "G1", "X": 213.69, "Y": -7.62, "comment": "Linear pt2->pt3"},
            {"type": "G1", "X": 213.7960, "Y": -3.8107, "comment": "G3 arc approx."},
            {"type": "G1", "X": 213.8300, "Y": 0.0000, "comment": ""},
            {"type": "G1", "X": 213.7960, "Y": 3.8107, "comment": ""},
            {"type": "G1", "X": 213.69, "Y": 7.62, "comment": ""},
            {"type": "G1", "X": 223.94, "Y": 7.62, "comment": "Linear pt4->pt1"},
        ],
        "yaw_from_origin": yaw_from_origin,
    }


def load_settings_from_json(filepath):
    """Load settings from JSON file"""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load settings: {e}")
        return None


def save_settings_to_json(filepath, settings):
    """Save settings to JSON file"""
    try:
        with open(filepath, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save settings: {e}")
        return False


####################################################################
# === GUI APPLICATION ===


class GenerateCarouselGcodeApp:
    def __init__(self, root):
        self.root = root
        self.settings = get_default_settings()
        self.setup_ui()
        self.load_default_settings()

    def setup_ui(self):
        self.root.title(f"Applied Masking - Generate Carousel G-Code v{VERSION}")
        # Don't set fixed geometry - let it size to content

        # Create main scrollable frame with both horizontal and vertical scrolling
        main_canvas = tk.Canvas(self.root)
        v_scrollbar = ttk.Scrollbar(
            self.root, orient="vertical", command=main_canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            self.root, orient="horizontal", command=main_canvas.xview
        )
        scrollable_frame = ttk.Frame(main_canvas)

        # Set minimum width to enable horizontal scrolling
        scrollable_frame.configure(width=1400)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")),
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        main_canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")

        # --- Control Frame ---
        control_frame = ttk.Frame(scrollable_frame, padding="10")
        control_frame.pack(fill="x")

        # Left side: Load/Save buttons
        left_controls = ttk.Frame(control_frame)
        left_controls.pack(side="left")

        ttk.Button(
            left_controls, text="Load Settings", command=self.load_settings
        ).pack(side="left", padx=(0, 5))
        ttk.Button(
            left_controls, text="Save Settings", command=self.save_settings
        ).pack(side="left", padx=(0, 5))

        # Center: Tab selector
        self.settings_file_var = tk.StringVar(value="No file loaded")
        settings_label = ttk.Label(control_frame, textvariable=self.settings_file_var)
        settings_label.pack(side="left", padx=20)

        # Tab selector (notebook) in control frame
        notebook = ttk.Notebook(control_frame)
        notebook.pack(side="left", padx=20)

        # Right side: Quit button
        right_controls = ttk.Frame(control_frame)
        right_controls.pack(side="right")

        ttk.Button(right_controls, text="Quit", command=self.on_close).pack(
            side="right"
        )

        # --- Settings Panel ---
        settings_panel = ttk.Frame(scrollable_frame, padding="10")
        settings_panel.pack(fill="x", padx=10, pady=5)

        # Create notebook for tab content in settings panel
        content_notebook = ttk.Notebook(settings_panel)
        content_notebook.pack(fill="x")

        # Tab 1: Geometry
        geometry_frame = ttk.Frame(content_notebook)
        content_notebook.add(geometry_frame, text="Geometry")

        # Pad G-code template
        ttk.Label(geometry_frame, text="Pad G-code Template:").grid(
            row=0, column=0, sticky="nw", padx=5, pady=2
        )
        self.pad_gcode_text = tk.Text(geometry_frame, height=6, wrap="none")
        self.pad_gcode_text.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        # Cleaning pass spacings
        ttk.Label(geometry_frame, text="Pass Spacings (comma-separated):").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.pass_spacings_var = tk.StringVar(value="0.1, 0.08, 0.06")
        ttk.Entry(geometry_frame, textvariable=self.pass_spacings_var, width=30).grid(
            row=1, column=1, sticky="ew", padx=5, pady=2
        )

        # Calculate button
        ttk.Button(
            geometry_frame,
            text="Calculate Cleaning Passes",
            command=self.calculate_cleaning_passes,
        ).grid(row=2, column=0, columnspan=2, pady=10)

        # Split view for calculated passes and visualization
        split_frame = ttk.Frame(geometry_frame)
        split_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=5)

        # Left side: Calculated passes text (reduced width)
        left_frame = ttk.LabelFrame(split_frame, text="Calculated Passes")
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 5))
        left_frame.configure(width=300)

        self.calculated_passes_text = tk.Text(
            left_frame, wrap="none", font=("Courier", 9)
        )
        passes_scrollbar_v = ttk.Scrollbar(
            left_frame, orient="vertical", command=self.calculated_passes_text.yview
        )
        passes_scrollbar_h = ttk.Scrollbar(
            left_frame, orient="horizontal", command=self.calculated_passes_text.xview
        )
        self.calculated_passes_text.configure(
            yscrollcommand=passes_scrollbar_v.set, xscrollcommand=passes_scrollbar_h.set
        )

        self.calculated_passes_text.pack(side="left", fill="both", expand=True)
        passes_scrollbar_v.pack(side="right", fill="y")
        passes_scrollbar_h.pack(side="bottom", fill="x")

        # Right side: Visualization
        right_frame = ttk.LabelFrame(split_frame, text="Visualization")
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Create a frame for the plot and toolbar
        plot_frame = ttk.Frame(right_frame)
        plot_frame.pack(fill="both", expand=True)

        # Matplotlib canvas for geometry visualization
        self.geometry_fig, self.geometry_ax = plt.subplots(figsize=(5, 3.5))
        self.geometry_canvas = FigureCanvasTkAgg(self.geometry_fig, master=plot_frame)
        self.geometry_canvas.get_tk_widget().pack(fill="both", expand=True)

        # Add navigation toolbar for zoom/pan controls
        self.geometry_toolbar = NavigationToolbar2Tk(self.geometry_canvas, plot_frame)
        self.geometry_toolbar.pack(side="top", fill="x")
        self.geometry_toolbar.update()

        # Configure column weights for proper resizing
        geometry_frame.columnconfigure(1, weight=1)
        geometry_frame.rowconfigure(3, weight=1)

        # Tab 2: Layout
        layout_frame = ttk.Frame(content_notebook)
        content_notebook.add(layout_frame, text="Layout")

        # Section selector and table dimensions on same row
        selector_frame = ttk.Frame(layout_frame)
        selector_frame.pack(fill="x", padx=5, pady=5)

        # Left side: Section selector
        ttk.Label(selector_frame, text="Select Section:").pack(
            side="left", padx=(0, 10)
        )
        self.layout_section_var = tk.StringVar(value="Section 1&3")
        self.layout_section_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.layout_section_var,
            values=["Section 1&3", "Section 2"],
            state="readonly",
            width=15,
        )
        self.layout_section_combo.pack(side="left", padx=(0, 20))
        self.layout_section_combo.bind(
            "<<ComboboxSelected>>", self.on_layout_section_change
        )

        # Right side: Table dimensions (compact)
        ttk.Label(selector_frame, text="Table:").pack(side="left", padx=(0, 5))

        ttk.Label(selector_frame, text="Lower left:").pack(side="left", padx=(0, 2))
        self.table_lower_left_var = tk.StringVar(value="-400, -200")
        ttk.Entry(
            selector_frame, textvariable=self.table_lower_left_var, width=10
        ).pack(side="left", padx=(0, 10))

        ttk.Label(selector_frame, text="Upper right:").pack(side="left", padx=(0, 2))
        self.table_upper_right_var = tk.StringVar(value="400, 200")
        ttk.Entry(
            selector_frame, textvariable=self.table_upper_right_var, width=10
        ).pack(side="left", padx=(0, 20))

        # Offset controls (dynamic based on section selection)
        ttk.Label(selector_frame, text="Offset:").pack(side="left", padx=(0, 2))
        self.section_1_3_origin_var = tk.StringVar(value="0, -50")
        self.section_2_origin_var = tk.StringVar(value="0, 50")
        self.current_offset_var = tk.StringVar(value="0, -50")
        self.offset_entry = ttk.Entry(
            selector_frame, textvariable=self.current_offset_var, width=10
        )
        self.offset_entry.pack(side="left", padx=(0, 5))
        self.offset_entry.bind("<KeyRelease>", self.on_offset_change)

        # Main layout frame (will contain either section 1&3 or section 2)
        self.main_layout_frame = ttk.Frame(layout_frame)
        self.main_layout_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Section 1&3 Layout
        self.section_1_3_layout_frame = ttk.LabelFrame(
            self.main_layout_frame, text="Section 1&3"
        )
        self.section_1_3_layout_frame.pack(fill="both", expand=True)

        # Section 1&3 Pads
        ttk.Label(self.section_1_3_layout_frame, text="Pads (comma-separated):").grid(
            row=0, column=0, sticky="nw", padx=5, pady=2
        )
        self.section_1_3_pads_text = tk.Text(
            self.section_1_3_layout_frame, height=3, wrap="word", width=40
        )
        self.section_1_3_pads_text.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.section_1_3_pads_text.bind("<KeyRelease>", self.on_section_1_3_pads_change)

        # Section 1&3 Visualization
        ttk.Label(self.section_1_3_layout_frame, text="Visualization:").grid(
            row=1, column=0, sticky="nw", padx=5, pady=2
        )

        # Generate Plot button and view selector for Section 1&3
        plot_controls_frame = ttk.Frame(self.section_1_3_layout_frame)
        plot_controls_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Button(
            plot_controls_frame,
            text="Generate Plot",
            command=self.generate_section_1_3_plot,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            plot_controls_frame,
            text="Save Section 1&3",
            command=self.save_section_1_3_gcode,
        ).pack(side="left", padx=(0, 10))

        self.section_1_3_view_var = tk.StringVar(value="Plot View")
        view_combo_1_3 = ttk.Combobox(
            plot_controls_frame,
            textvariable=self.section_1_3_view_var,
            values=["Plot View", "G-code Text"],
            state="readonly",
            width=15,
        )
        view_combo_1_3.pack(side="left")
        view_combo_1_3.bind("<<ComboboxSelected>>", self.on_section_1_3_view_change)

        # Create frame for plot and toolbar
        self.section_1_3_plot_frame = ttk.Frame(self.section_1_3_layout_frame)
        self.section_1_3_plot_frame.grid(row=2, column=1, sticky="nsew", padx=2, pady=1)

        # Create toolbar frame at top
        self.section_1_3_toolbar_frame = ttk.Frame(self.section_1_3_plot_frame)
        self.section_1_3_toolbar_frame.pack(side="top", fill="x")

        # Create canvas frame
        self.section_1_3_canvas_frame = ttk.Frame(self.section_1_3_plot_frame)
        self.section_1_3_canvas_frame.pack(fill="both", expand=True)

        self.section_1_3_fig, self.section_1_3_ax = plt.subplots(figsize=(7, 5))
        self.section_1_3_canvas = FigureCanvasTkAgg(
            self.section_1_3_fig, master=self.section_1_3_canvas_frame
        )
        self.section_1_3_canvas.get_tk_widget().pack(fill="both", expand=True)

        # Initialize plot with table dimensions
        self.initialize_section_1_3_plot()

        # Add navigation toolbar for Section 1&3 plot
        self.section_1_3_toolbar = NavigationToolbar2Tk(
            self.section_1_3_canvas, self.section_1_3_toolbar_frame
        )
        self.section_1_3_toolbar.pack(fill="x")
        self.section_1_3_toolbar.update()

        # Text widget for G-code display (initially hidden)
        self.section_1_3_text_frame = ttk.Frame(self.section_1_3_layout_frame)
        self.section_1_3_text_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=2)
        self.section_1_3_gcode_text = tk.Text(
            self.section_1_3_text_frame, wrap="none", font=("Courier", 9)
        )
        scrollbar_v_1_3 = ttk.Scrollbar(
            self.section_1_3_text_frame,
            orient="vertical",
            command=self.section_1_3_gcode_text.yview,
        )
        scrollbar_h_1_3 = ttk.Scrollbar(
            self.section_1_3_text_frame,
            orient="horizontal",
            command=self.section_1_3_gcode_text.xview,
        )
        self.section_1_3_gcode_text.configure(
            yscrollcommand=scrollbar_v_1_3.set, xscrollcommand=scrollbar_h_1_3.set
        )
        self.section_1_3_gcode_text.pack(side="left", fill="both", expand=True)
        scrollbar_v_1_3.pack(side="right", fill="y")
        scrollbar_h_1_3.pack(side="bottom", fill="x")

        # Initially hide the text frame
        self.section_1_3_text_frame.grid_remove()

        # Configure Section 1&3 layout weights
        self.section_1_3_layout_frame.columnconfigure(1, weight=1)
        self.section_1_3_layout_frame.rowconfigure(3, weight=1)

        # Section 2 Layout
        self.section_2_layout_frame = ttk.LabelFrame(
            self.main_layout_frame, text="Section 2"
        )
        self.section_2_layout_frame.pack(fill="both", expand=True)

        # Section 2 Pads
        ttk.Label(self.section_2_layout_frame, text="Pads (comma-separated):").grid(
            row=0, column=0, sticky="nw", padx=5, pady=2
        )
        self.section_2_pads_text = tk.Text(
            self.section_2_layout_frame, height=3, wrap="word", width=40
        )
        self.section_2_pads_text.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.section_2_pads_text.bind("<KeyRelease>", self.on_section_2_pads_change)

        # Section 2 Visualization
        ttk.Label(self.section_2_layout_frame, text="Visualization:").grid(
            row=1, column=0, sticky="nw", padx=5, pady=2
        )

        # Generate Plot button and view selector for Section 2
        plot_controls_frame_2 = ttk.Frame(self.section_2_layout_frame)
        plot_controls_frame_2.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Button(
            plot_controls_frame_2,
            text="Generate Plot",
            command=self.generate_section_2_plot,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            plot_controls_frame_2,
            text="Save Section 2",
            command=self.save_section_2_gcode,
        ).pack(side="left", padx=(0, 10))

        self.section_2_view_var = tk.StringVar(value="Plot View")
        view_combo_2 = ttk.Combobox(
            plot_controls_frame_2,
            textvariable=self.section_2_view_var,
            values=["Plot View", "G-code Text"],
            state="readonly",
            width=15,
        )
        view_combo_2.pack(side="left")
        view_combo_2.bind("<<ComboboxSelected>>", self.on_section_2_view_change)

        # Create frame for plot and toolbar
        self.section_2_plot_frame = ttk.Frame(self.section_2_layout_frame)
        self.section_2_plot_frame.grid(row=2, column=1, sticky="nsew", padx=2, pady=1)

        # Create toolbar frame at top
        self.section_2_toolbar_frame = ttk.Frame(self.section_2_plot_frame)
        self.section_2_toolbar_frame.pack(side="top", fill="x")

        # Create canvas frame
        self.section_2_canvas_frame = ttk.Frame(self.section_2_plot_frame)
        self.section_2_canvas_frame.pack(fill="both", expand=True)

        self.section_2_fig, self.section_2_ax = plt.subplots(figsize=(7, 5))
        self.section_2_canvas = FigureCanvasTkAgg(
            self.section_2_fig, master=self.section_2_canvas_frame
        )
        self.section_2_canvas.get_tk_widget().pack(fill="both", expand=True)

        # Initialize plot with table dimensions
        self.initialize_section_2_plot()

        # Add navigation toolbar for Section 2 plot
        self.section_2_toolbar = NavigationToolbar2Tk(
            self.section_2_canvas, self.section_2_toolbar_frame
        )
        self.section_2_toolbar.pack(fill="x")
        self.section_2_toolbar.update()

        # Text widget for G-code display (initially hidden)
        self.section_2_text_frame = ttk.Frame(self.section_2_layout_frame)
        self.section_2_text_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=2)
        self.section_2_gcode_text = tk.Text(
            self.section_2_text_frame, wrap="none", font=("Courier", 9)
        )
        scrollbar_v_2 = ttk.Scrollbar(
            self.section_2_text_frame,
            orient="vertical",
            command=self.section_2_gcode_text.yview,
        )
        scrollbar_h_2 = ttk.Scrollbar(
            self.section_2_text_frame,
            orient="horizontal",
            command=self.section_2_gcode_text.xview,
        )
        self.section_2_gcode_text.configure(
            yscrollcommand=scrollbar_v_2.set, xscrollcommand=scrollbar_h_2.set
        )
        self.section_2_gcode_text.pack(side="left", fill="both", expand=True)
        scrollbar_v_2.pack(side="right", fill="y")
        scrollbar_h_2.pack(side="bottom", fill="x")

        # Initially hide the text frame
        self.section_2_text_frame.grid_remove()

        # Configure Section 2 layout weights
        self.section_2_layout_frame.columnconfigure(1, weight=1)
        self.section_2_layout_frame.rowconfigure(3, weight=1)

        # Initially show Section 1&3, hide Section 2
        self.section_2_layout_frame.pack_forget()

        # Tab 3: G-code Settings
        gcode_frame = ttk.Frame(content_notebook)
        content_notebook.add(gcode_frame, text="G-code Settings")

        # Laser Settings
        laser_settings_frame = ttk.LabelFrame(gcode_frame, text="Laser Settings")
        laser_settings_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5
        )

        ttk.Label(laser_settings_frame, text="Section 1&3 Power:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.section_1_3_power_var = tk.StringVar(value="800")
        ttk.Entry(
            laser_settings_frame, textvariable=self.section_1_3_power_var, width=10
        ).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(laser_settings_frame, text="Section 1&3 Feedrate:").grid(
            row=0, column=2, sticky="w", padx=5, pady=2
        )
        self.section_1_3_feedrate_var = tk.StringVar(value="1500")
        ttk.Entry(
            laser_settings_frame, textvariable=self.section_1_3_feedrate_var, width=10
        ).grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(laser_settings_frame, text="Section 2 Power:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.section_2_power_var = tk.StringVar(value="800")
        ttk.Entry(
            laser_settings_frame, textvariable=self.section_2_power_var, width=10
        ).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(laser_settings_frame, text="Section 2 Feedrate:").grid(
            row=1, column=2, sticky="w", padx=5, pady=2
        )
        self.section_2_feedrate_var = tk.StringVar(value="1500")
        ttk.Entry(
            laser_settings_frame, textvariable=self.section_2_feedrate_var, width=10
        ).grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(laser_settings_frame, text="Z Laser Height:").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )
        self.zlaser_var = tk.StringVar(value="-28")
        ttk.Entry(laser_settings_frame, textvariable=self.zlaser_var, width=10).grid(
            row=2, column=1, padx=5, pady=2
        )

        # G-code Templates
        templates_frame = ttk.LabelFrame(gcode_frame, text="G-code Templates")
        templates_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # Section 1&3 preamble/postscript
        ttk.Label(templates_frame, text="Section 1&3 Preamble:").grid(
            row=0, column=0, sticky="nw", padx=5, pady=2
        )
        self.section_1_3_preamble_text = tk.Text(templates_frame, height=4)
        self.section_1_3_preamble_text.grid(
            row=0, column=1, sticky="ew", padx=5, pady=2
        )

        ttk.Label(templates_frame, text="Section 1&3 Postscript:").grid(
            row=1, column=0, sticky="nw", padx=5, pady=2
        )
        self.section_1_3_postscript_text = tk.Text(templates_frame, height=4)
        self.section_1_3_postscript_text.grid(
            row=1, column=1, sticky="ew", padx=5, pady=2
        )

        # Section 2 preamble/postscript
        ttk.Label(templates_frame, text="Section 2 Preamble:").grid(
            row=2, column=0, sticky="nw", padx=5, pady=2
        )
        self.section_2_preamble_text = tk.Text(templates_frame, height=4)
        self.section_2_preamble_text.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(templates_frame, text="Section 2 Postscript:").grid(
            row=3, column=0, sticky="nw", padx=5, pady=2
        )
        self.section_2_postscript_text = tk.Text(templates_frame, height=4)
        self.section_2_postscript_text.grid(
            row=3, column=1, sticky="ew", padx=5, pady=2
        )

        # Configure column weights for proper resizing
        gcode_frame.columnconfigure(1, weight=1)
        templates_frame.columnconfigure(1, weight=1)

        # Auto-size window to fit content
        self.auto_size_window()

    def load_default_settings(self):
        """Load default settings into GUI fields"""
        self.section_1_3_origin_var.set(
            f"{self.settings['section_1_3_origin'][0]}, {self.settings['section_1_3_origin'][1]}"
        )
        self.section_2_origin_var.set(
            f"{self.settings['section_2_origin'][0]}, {self.settings['section_2_origin'][1]}"
        )
        self.section_1_3_power_var.set(str(self.settings["section_1_3_laser_power"]))
        self.section_2_power_var.set(str(self.settings["section_2_laser_power"]))
        self.section_1_3_feedrate_var.set(str(self.settings["section_1_3_feedrate"]))
        self.section_2_feedrate_var.set(str(self.settings["section_2_feedrate"]))
        self.zlaser_var.set(str(self.settings["zlaser"]))
        self.pass_spacings_var.set(
            ", ".join(map(str, self.settings["cleaning_pass_spacings"]))
        )

        # Load pad G-code template
        self.pad_gcode_text.delete(1.0, tk.END)
        if "pad_gcode_template" in self.settings:
            gcode_lines = []
            for cmd in self.settings["pad_gcode_template"]:
                line = f"{cmd['type']} X{cmd['X']} Y{cmd['Y']}"
                if "R" in cmd:
                    line += f" R{cmd['R']}"
                if "comment" in cmd:
                    line += f" ; {cmd['comment']}"
                gcode_lines.append(line)
            self.pad_gcode_text.insert(1.0, "\n".join(gcode_lines))

        self.section_1_3_preamble_text.delete(1.0, tk.END)
        self.section_1_3_preamble_text.insert(
            1.0, self.settings["section_1_3_preamble"]
        )
        self.section_1_3_postscript_text.delete(1.0, tk.END)
        self.section_1_3_postscript_text.insert(
            1.0, self.settings["section_1_3_postscript"]
        )
        self.section_2_preamble_text.delete(1.0, tk.END)
        self.section_2_preamble_text.insert(1.0, self.settings["section_2_preamble"])
        self.section_2_postscript_text.delete(1.0, tk.END)
        self.section_2_postscript_text.insert(
            1.0, self.settings["section_2_postscript"]
        )

        # Load section pads from arrays
        self.section_1_3_pads_text.delete(1.0, tk.END)
        self.section_1_3_pads_text.insert(1.0, ", ".join(section1and3))
        self.section_2_pads_text.delete(1.0, tk.END)
        self.section_2_pads_text.insert(1.0, ", ".join(section2))

        # Load table dimensions
        if "table_dimensions" in self.settings:
            table_dims = self.settings["table_dimensions"]
            self.table_lower_left_var.set(
                f"{table_dims['lower_left'][0]}, {table_dims['lower_left'][1]}"
            )
            self.table_upper_right_var.set(
                f"{table_dims['upper_right'][0]}, {table_dims['upper_right'][1]}"
            )

    def auto_size_window(self):
        """Automatically size the window to fit its content"""
        # Update the window to calculate required size
        self.root.update_idletasks()
        self.root.update()

        # Get the required size from the main canvas
        main_canvas = self.root.winfo_children()[0]  # First child is the main canvas
        req_width = main_canvas.winfo_reqwidth()
        req_height = main_canvas.winfo_reqheight()

        # Add some padding for the window frame
        padding = 10
        window_width = req_width + padding
        window_height = req_height + padding

        # Set minimum and maximum reasonable sizes
        min_width, min_height = 1400, 800
        max_width, max_height = 1800, 1200

        # Clamp to reasonable bounds
        window_width = max(min_width, min(window_width, max_width))
        window_height = max(min_height, min(window_height, max_height))

        # Set the geometry
        self.root.geometry(f"{window_width}x{window_height}")

        # Center the window on screen
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def load_settings(self):
        """Load settings from JSON file"""
        filepath = filedialog.askopenfilename(
            title="Load Settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if filepath:
            settings = load_settings_from_json(filepath)
            if settings:
                self.settings = settings
                self.load_default_settings()
                self.settings_file_var.set(os.path.basename(filepath))

                # Update global arrays from loaded settings
                global section1and3, section2
                if "section_1_3_pads" in settings:
                    section1and3 = [
                        pad.strip()
                        for pad in settings["section_1_3_pads"].split(",")
                        if pad.strip()
                    ]
                if "section_2_pads" in settings:
                    section2 = [
                        pad.strip()
                        for pad in settings["section_2_pads"].split(",")
                        if pad.strip()
                    ]

    def save_settings(self):
        """Save current settings to JSON file"""
        filepath = filedialog.asksaveasfilename(
            title="Save Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if filepath:
            settings = self.get_current_settings()
            if save_settings_to_json(filepath, settings):
                self.settings_file_var.set(os.path.basename(filepath))

    def calculate_cleaning_passes(self):
        """Calculate cleaning passes from pad template and spacings"""
        try:
            # Parse pad template
            pad_template = []
            gcode_text = self.pad_gcode_text.get(1.0, tk.END).strip()
            if gcode_text:
                for line in gcode_text.split("\n"):
                    line = line.strip()
                    if line and not line.startswith(";"):
                        parts = line.split()
                        if len(parts) >= 3:
                            cmd = {"type": parts[0]}
                            for part in parts[1:]:
                                if part.startswith("X"):
                                    cmd["X"] = float(part[1:])
                                elif part.startswith("Y"):
                                    cmd["Y"] = float(part[1:])
                                elif part.startswith("R"):
                                    cmd["R"] = float(part[1:])
                            if ";" in line:
                                cmd["comment"] = line.split(";", 1)[1].strip()
                            pad_template.append(cmd)

            # Parse spacings
            spacings = [
                float(x.strip()) for x in self.pass_spacings_var.get().split(",")
            ]

            # Calculate offset passes using shapely polygon buffering
            calculated_passes = []
            if pad_template:
                # Convert G-code to polygon
                original_polygon = self.gcode_to_polygon(pad_template)

                for spacing in spacings:
                    # Buffer the polygon by the offset amount
                    buffered_polygon = original_polygon.buffer(spacing, join_style=2)

                    # Convert back to G-code commands
                    pass_gcode = self.polygon_to_gcode(
                        buffered_polygon, pad_template, spacing
                    )

                    calculated_passes.append({"offset": spacing, "gcode": pass_gcode})

            # Update display
            self.update_calculated_passes_display(calculated_passes)
            self.update_geometry_visualization(pad_template, calculated_passes)

            # Store in settings
            self.settings["calculated_cleaning_passes"] = calculated_passes

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate cleaning passes: {e}")

    def update_calculated_passes_display(self, calculated_passes):
        """Update the calculated passes text display"""
        self.calculated_passes_text.delete(1.0, tk.END)

        text_content = ""
        for i, pass_data in enumerate(calculated_passes):
            text_content += f"Pass {i+1} (offset {pass_data['offset']}):\n"
            for cmd in pass_data["gcode"]:
                line = f"{cmd['type']} X{cmd['X']} Y{cmd['Y']}"
                if "R" in cmd:
                    line += f" R{cmd['R']}"
                if "comment" in cmd:
                    line += f" ; {cmd['comment']}"
                text_content += line + "\n"
            text_content += "\n"

        self.calculated_passes_text.insert(1.0, text_content)

    def update_geometry_visualization(self, pad_template, calculated_passes):
        """Update the geometry visualization plot"""
        self.geometry_ax.clear()

        # Plot original pad in green
        if pad_template:
            self.plot_gcode_path_on_ax(
                self.geometry_ax, pad_template, "Original Pad", "green"
            )

        # Plot cleaning passes in orange
        for i, pass_data in enumerate(calculated_passes):
            self.plot_gcode_path_on_ax(
                self.geometry_ax,
                pass_data["gcode"],
                f"Pass {i+1} ({pass_data['offset']})",
                "orange",
            )

        self.geometry_ax.set_title("Pad Geometry and Cleaning Passes")
        self.geometry_ax.set_aspect("equal")
        self.geometry_ax.grid(True)
        self.geometry_ax.legend()
        self.geometry_canvas.draw()

    def plot_gcode_path_on_ax(
        self, ax, gcode_commands, label, color, center_offset=None, is_layout_plot=False
    ):
        """Plot G-code commands on the given axes with proper arc rendering"""
        import numpy as np

        if not gcode_commands:
            return

        # Track current position - different starting points for different plot types
        if is_layout_plot:
            # Layout plot: start from origin to plot all commands in sequence
            current_x, current_y = 0, 0
        else:
            # Cleaning visualization: start from the last point (closing the polygon)
            if gcode_commands and len(gcode_commands) > 0:
                # Find the last command to get the starting point
                last_cmd = gcode_commands[-1]
                if "X" in last_cmd and "Y" in last_cmd:
                    current_x, current_y = last_cmd["X"], last_cmd["Y"]
                else:
                    current_x, current_y = 0, 0
            else:
                current_x, current_y = 0, 0

        for i, cmd in enumerate(gcode_commands):
            if "X" in cmd and "Y" in cmd:
                target_x, target_y = cmd["X"], cmd["Y"]

                if cmd["type"] == "G0":
                    # Rapid move - different colors for layout vs cleaning passes
                    if is_layout_plot:
                        ax.plot(
                            [current_x, target_x],
                            [current_y, target_y],
                            color="green",
                            linewidth=1,
                            alpha=0.7,
                        )
                    else:
                        # For cleaning passes visualization, use the passed color
                        ax.plot(
                            [current_x, target_x],
                            [current_y, target_y],
                            color=color,
                            linewidth=1,
                            alpha=0.7,
                        )
                elif cmd["type"] == "G1":
                    # Linear move - different colors for layout vs cleaning passes
                    if is_layout_plot:
                        ax.plot(
                            [current_x, target_x],
                            [current_y, target_y],
                            color="orange",
                            linewidth=2,
                            alpha=0.7,
                        )
                    else:
                        # For cleaning passes visualization, use the passed color
                        ax.plot(
                            [current_x, target_x],
                            [current_y, target_y],
                            color=color,
                            linewidth=2,
                            alpha=0.7,
                        )

                elif cmd["type"] in ["G2", "G3"] and "R" in cmd:
                    # Arc move - draw actual arc using step-by-step method
                    radius = cmd["R"]

                    # Step 1: Define start and end points
                    start_x, start_y = current_x, current_y
                    end_x, end_y = target_x, target_y

                    # Step 2: Calculate center for R-format arcs using GRBL method
                    # Use GRBL-style calculation for both layout plot and cleaning visualization
                    import math

                    # Distance from start to end (chord length)
                    dx = end_x - start_x
                    dy = end_y - start_y
                    chord_length = math.sqrt(dx * dx + dy * dy)

                    # Check if arc is geometrically possible
                    if chord_length > 2 * radius:
                        # Arc is impossible - draw straight line instead
                        if is_layout_plot:
                            ax.plot(
                                [start_x, end_x],
                                [start_y, end_y],
                                color="orange",
                                linewidth=2,
                                alpha=0.7,
                            )
                        else:
                            ax.plot(
                                [start_x, end_x],
                                [start_y, end_y],
                                color=color,
                                linewidth=2,
                                alpha=0.7,
                            )
                        continue

                    # Calculate center using GRBL method
                    # Midpoint of chord
                    mid_x = (start_x + end_x) / 2
                    mid_y = (start_y + end_y) / 2

                    # Distance from midpoint to center
                    h = math.sqrt(radius * radius - (chord_length / 2) ** 2)

                    # Perpendicular vector to chord (normalized)
                    perp_x = -dy / chord_length
                    perp_y = dx / chord_length

                    # There are two possible centers - choose based on arc direction
                    # For G2 (CW): use one side, for G3 (CCW): use the other
                    if cmd["type"] == "G2":
                        # G2 (CW) - use the center that makes the arc sweep clockwise
                        center_x = mid_x - h * perp_x
                        center_y = mid_y - h * perp_y
                    else:  # G3 (CCW)
                        # G3 (CCW) - use the center that makes the arc sweep counter-clockwise
                        center_x = mid_x + h * perp_x
                        center_y = mid_y + h * perp_y

                    # Step 3: Convert points to polar coordinates
                    start_angle = np.arctan2(start_y - center_y, start_x - center_x)
                    end_angle = np.arctan2(end_y - center_y, end_x - center_x)

                    # Step 4: Generate arc points
                    if cmd["type"] == "G2":
                        # G2 (CW) - sweep from start to end in reverse
                        if end_angle > start_angle:
                            end_angle -= 2 * np.pi
                        angles = np.linspace(start_angle, end_angle, 50)
                    else:
                        # G3 (CCW) - sweep from start to end forward
                        if end_angle < start_angle:
                            end_angle += 2 * np.pi
                        angles = np.linspace(start_angle, end_angle, 50)

                    # Generate arc points
                    arc_x = center_x + radius * np.cos(angles)
                    arc_y = center_y + radius * np.sin(angles)

                    # Plot the arc - different colors for layout vs cleaning passes
                    if is_layout_plot:
                        ax.plot(arc_x, arc_y, color="orange", linewidth=2, alpha=0.7)
                    else:
                        # For cleaning passes visualization, use the passed color
                        ax.plot(arc_x, arc_y, color=color, linewidth=2, alpha=0.7)

                # Update current position
                current_x, current_y = target_x, target_y

        # Add markers at key points
        for cmd in gcode_commands:
            if "X" in cmd and "Y" in cmd:
                ax.plot(cmd["X"], cmd["Y"], "o", color=color, markersize=4, alpha=0.8)

        # Add label for legend
        ax.plot([], [], color=color, linewidth=2, label=label, alpha=0.7)

    def gcode_to_polygon(self, gcode_commands):
        """Convert G-code commands to shapely Polygon"""
        from shapely.geometry import Polygon

        points = []
        for cmd in gcode_commands:
            if "X" in cmd and "Y" in cmd:
                # Round coordinates to 3 significant digits
                x = round(cmd["X"], 3)
                y = round(cmd["Y"], 3)
                points.append((x, y))

        if len(points) >= 3:
            return Polygon(points)
        return None

    def polygon_to_gcode(self, buffered_polygon, original_commands, offset_amount):
        """Convert buffered polygon back to G-code commands matching original structure"""
        if buffered_polygon is None or buffered_polygon.is_empty:
            return []

        # Get exterior coordinates (excluding the last duplicate point)
        coords = list(buffered_polygon.exterior.coords)[:-1]

        # Create new commands with same types but new coordinates
        new_commands = []
        for i, cmd in enumerate(original_commands):
            if i < len(coords):
                new_cmd = cmd.copy()
                # Round coordinates to 3 significant digits
                new_cmd["X"] = round(coords[i][0], 3)
                new_cmd["Y"] = round(coords[i][1], 3)

                # For arcs, adjust radius based on offset direction
                if cmd["type"] in ["G2", "G3"] and "R" in cmd:
                    original_radius = cmd["R"]

                    # For outward expansion (positive offset):
                    # G2 arcs: increase radius (arc gets larger)
                    # G3 arcs: decrease radius (arc gets smaller)
                    if cmd["type"] == "G2":
                        # G2: increase radius for outward expansion
                        new_cmd["R"] = round(original_radius + offset_amount, 3)
                    else:  # G3
                        # G3: decrease radius for outward expansion
                        new_cmd["R"] = round(original_radius - offset_amount, 3)

                new_commands.append(new_cmd)

        return new_commands

    def transform_gcode_command(self, cmd, yaw_angle, translation):
        """Transform G-code command with rotation and translation"""
        import math

        if "X" in cmd and "Y" in cmd:
            # Rotate coordinates
            x = cmd["X"]
            y = cmd["Y"]
            cos_yaw = math.cos(math.radians(yaw_angle))
            sin_yaw = math.sin(math.radians(yaw_angle))

            rotated_x = x * cos_yaw - y * sin_yaw
            rotated_y = x * sin_yaw + y * cos_yaw

            # Translate
            transformed_cmd = cmd.copy()
            # Round coordinates to 3 significant digits
            transformed_cmd["X"] = round(rotated_x + translation[0], 3)
            transformed_cmd["Y"] = round(rotated_y + translation[1], 3)

            # For R-format arcs, also transform the center (0,0) -> translation offset
            if cmd["type"] in ["G2", "G3"] and "R" in cmd:
                # The center in the original coordinate system is (0,0)
                # After rotation and translation, it becomes the translation offset
                transformed_cmd["center_x"] = translation[0]
                transformed_cmd["center_y"] = translation[1]

            return transformed_cmd
        return cmd

    def save_section_1_3_gcode(self):
        """Save Section 1&3 G-code to file"""
        try:
            # Generate G-code directly
            settings = self.get_current_settings()
            gcode_data = self.generate_section_plot_data(
                settings["section_1_3_pads"].split(","),
                settings["section_1_3_origin"],
                settings["calculated_cleaning_passes"],
                settings,
                "1&3",
            )
            gcode = "\n".join(gcode_data["lines"])

            filepath = filedialog.asksaveasfilename(
                title="Save Section 1&3 G-code",
                defaultextension=".gcode",
                filetypes=[("G-code files", "*.gcode"), ("All files", "*.*")],
            )
            if filepath:
                with open(filepath, "w") as f:
                    f.write(gcode)
                messagebox.showinfo("Success", f"G-code saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate/save G-code: {e}")

    def save_section_2_gcode(self):
        """Save Section 2 G-code to file"""
        try:
            # Generate G-code directly
            settings = self.get_current_settings()
            gcode_data = self.generate_section_plot_data(
                settings["section_2_pads"].split(","),
                settings["section_2_origin"],
                settings["calculated_cleaning_passes"],
                settings,
                "2",
            )
            gcode = "\n".join(gcode_data["lines"])

            filepath = filedialog.asksaveasfilename(
                title="Save Section 2 G-code",
                defaultextension=".gcode",
                filetypes=[("G-code files", "*.gcode"), ("All files", "*.*")],
            )
            if filepath:
                with open(filepath, "w") as f:
                    f.write(gcode)
                messagebox.showinfo("Success", f"G-code saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate/save G-code: {e}")

    def get_current_settings(self):
        """Get current settings from GUI fields"""
        try:
            pass_spacings = [
                float(x.strip()) for x in self.pass_spacings_var.get().split(",")
            ]
        except ValueError:
            pass_spacings = [0.1, 0.08, 0.06]

        # Parse pad G-code template from text
        pad_gcode_template = []
        try:
            gcode_text = self.pad_gcode_text.get(1.0, tk.END).strip()
            if gcode_text:
                for line in gcode_text.split("\n"):
                    line = line.strip()
                    if line and not line.startswith(";"):
                        parts = line.split()
                        if len(parts) >= 3:
                            cmd = {"type": parts[0]}
                            for part in parts[1:]:
                                if part.startswith("X"):
                                    cmd["X"] = float(part[1:])
                                elif part.startswith("Y"):
                                    cmd["Y"] = float(part[1:])
                                elif part.startswith("R"):
                                    cmd["R"] = float(part[1:])

                            # Add center information for arc commands
                            if cmd["type"] in ["G2", "G3"] and "R" in cmd:
                                cmd["center_x"] = 0
                                cmd["center_y"] = 0

                            if ";" in line:
                                cmd["comment"] = line.split(";", 1)[1].strip()
                            pad_gcode_template.append(cmd)
        except Exception:
            # Fall back to default if parsing fails
            pad_gcode_template = self.settings.get("pad_gcode_template", [])

        # Parse origin coordinates
        try:
            section_1_3_origin = [
                float(x.strip()) for x in self.section_1_3_origin_var.get().split(",")
            ]
            if len(section_1_3_origin) != 2:
                raise ValueError("Section 1&3 origin must have exactly 2 values")
        except (ValueError, IndexError):
            section_1_3_origin = [0, -50]

        try:
            section_2_origin = [
                float(x.strip()) for x in self.section_2_origin_var.get().split(",")
            ]
            if len(section_2_origin) != 2:
                raise ValueError("Section 2 origin must have exactly 2 values")
        except (ValueError, IndexError):
            section_2_origin = [0, 50]

        # Parse table dimensions
        try:
            table_lower_left = [
                float(x.strip()) for x in self.table_lower_left_var.get().split(",")
            ]
            if len(table_lower_left) != 2:
                raise ValueError("Table lower left must have exactly 2 values")
        except (ValueError, IndexError):
            table_lower_left = [-400, -200]

        try:
            table_upper_right = [
                float(x.strip()) for x in self.table_upper_right_var.get().split(",")
            ]
            if len(table_upper_right) != 2:
                raise ValueError("Table upper right must have exactly 2 values")
        except (ValueError, IndexError):
            table_upper_right = [400, 200]

        return {
            "section_1_3_origin": section_1_3_origin,
            "section_2_origin": section_2_origin,
            "section_1_3_pads": self.section_1_3_pads_text.get(1.0, tk.END).strip(),
            "section_2_pads": self.section_2_pads_text.get(1.0, tk.END).strip(),
            "section_1_3_preamble": self.section_1_3_preamble_text.get(
                1.0, tk.END
            ).strip(),
            "section_2_preamble": self.section_2_preamble_text.get(1.0, tk.END).strip(),
            "section_1_3_postscript": self.section_1_3_postscript_text.get(
                1.0, tk.END
            ).strip(),
            "section_2_postscript": self.section_2_postscript_text.get(
                1.0, tk.END
            ).strip(),
            "section_1_3_laser_power": int(self.section_1_3_power_var.get()),
            "section_2_laser_power": int(self.section_2_power_var.get()),
            "section_1_3_feedrate": int(self.section_1_3_feedrate_var.get()),
            "section_2_feedrate": int(self.section_2_feedrate_var.get()),
            "cleaning_pass_spacings": pass_spacings,
            "calculated_cleaning_passes": self.settings.get(
                "calculated_cleaning_passes", []
            ),
            "zlaser": float(self.zlaser_var.get()),
            "center": [300, 100],
            "table_dimensions": {
                "lower_left": table_lower_left,
                "upper_right": table_upper_right,
            },
            "pad_gcode_template": pad_gcode_template,
            "yaw_from_origin": yaw_from_origin,
        }

    def on_layout_section_change(self, event=None):
        """Handle layout section change"""
        selected_section = self.layout_section_var.get()

        if selected_section == "Section 1&3":
            # Show Section 1&3, hide Section 2
            self.section_1_3_layout_frame.pack(fill="both", expand=True)
            self.section_2_layout_frame.pack_forget()
            # Update offset control to show Section 1&3 offset
            self.current_offset_var.set(self.section_1_3_origin_var.get())
        else:  # Section 2
            # Show Section 2, hide Section 1&3
            self.section_2_layout_frame.pack(fill="both", expand=True)
            self.section_1_3_layout_frame.pack_forget()
            # Update offset control to show Section 2 offset
            self.current_offset_var.set(self.section_2_origin_var.get())

    def on_offset_change(self, event=None):
        """Handle offset entry change"""
        selected_section = self.layout_section_var.get()
        new_offset = self.current_offset_var.get()

        if selected_section == "Section 1&3":
            self.section_1_3_origin_var.set(new_offset)
        else:  # Section 2
            self.section_2_origin_var.set(new_offset)

    def on_section_1_3_pads_change(self, event=None):
        """Handle Section 1&3 pads text change"""
        try:
            text_content = self.section_1_3_pads_text.get(1.0, tk.END).strip()
            if text_content:
                # Parse comma-separated values and update global section1and3 array
                global section1and3
                section1and3 = [
                    pad.strip() for pad in text_content.split(",") if pad.strip()
                ]
        except Exception as e:
            print(f"Error updating section 1&3 pads: {e}")

    def on_section_2_pads_change(self, event=None):
        """Handle Section 2 pads text change"""
        try:
            text_content = self.section_2_pads_text.get(1.0, tk.END).strip()
            if text_content:
                # Parse comma-separated values and update global section2 array
                global section2
                section2 = [
                    pad.strip() for pad in text_content.split(",") if pad.strip()
                ]
        except Exception as e:
            print(f"Error updating section 2 pads: {e}")

    def generate_section_1_3_plot(self):
        """Generate plot for Section 1&3 with rotated/translated cleaning G-code"""
        try:
            settings = self.get_current_settings()
            self.section_1_3_gcode_data = self.generate_section_plot_data(
                settings["section_1_3_pads"].split(","),
                settings["section_1_3_origin"],
                settings["calculated_cleaning_passes"],
                settings,
                "1&3",
            )
            self.update_section_1_3_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Section 1&3 plot: {e}")

    def generate_section_2_plot(self):
        """Generate plot for Section 2 with rotated/translated cleaning G-code"""
        try:
            settings = self.get_current_settings()
            self.section_2_gcode_data = self.generate_section_plot_data(
                settings["section_2_pads"].split(","),
                settings["section_2_origin"],
                settings["calculated_cleaning_passes"],
                settings,
                "2",
            )
            self.update_section_2_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Section 2 plot: {e}")

    def generate_section_plot_data(
        self, pads, offset, cleaning_passes, settings, section_name
    ):
        """Generate G-code data for a section with rotated/translated cleaning passes"""
        all_gcode_commands = []
        all_gcode_lines = []

        # Add preamble
        preamble_key = f"section_{section_name.replace('&', '_')}_preamble"
        if preamble_key in settings:
            all_gcode_lines.extend(settings[preamble_key].split("\n"))

        # Add laser power commands
        laser_power = settings.get(
            f"section_{section_name.replace('&', '_')}_laser_power", 0
        )
        all_gcode_lines.append(f"M4 S{laser_power}")
        all_gcode_lines.append(f"G0 X0.0000 Y0.0000 Z{settings['zlaser']:.4f}")

        for pad_idx, pad_id in enumerate(pads):
            pad_id = pad_id.strip()
            if not pad_id or pad_id not in settings["yaw_from_origin"]:
                print(f"Pad {pad_id} not found in yaw_from_origin")
                continue

            yaw_angle = settings["yaw_from_origin"][pad_id]
            feedrate = settings.get(
                f"section_{section_name.replace('&', '_')}_feedrate", 1500
            )

            # Generate G-code for each cleaning pass
            for pass_idx, pass_data in enumerate(cleaning_passes):
                # Calculate the actual starting point of the first arc
                # The first command is a G2 arc, so we need to find where it starts from
                # For the first pass, start from the original pad position
                # For subsequent passes, start from the end of the previous pass
                # For all passes: get starting point from THIS pass's last command
                # (which is pt1 of this expanded polygon)
                last_cmd = pass_data["gcode"][-1]
                last_transformed = self.transform_gcode_command(
                    last_cmd, yaw_angle, offset
                )
                x_start, y_start = last_transformed["X"], last_transformed["Y"]

                # Add G0 rapid move to start position
                all_gcode_lines.append(f"G0 X{x_start:.4f} Y{y_start:.4f}")

                # No G1 settling move needed since all commands are now G1 linear moves

                for cmd_idx, cmd in enumerate(pass_data["gcode"]):
                    # Transform the command with rotation and translation
                    transformed_cmd = self.transform_gcode_command(
                        cmd, yaw_angle, offset
                    )

                    # Store command dictionary for plotting
                    all_gcode_commands.append(transformed_cmd)

                    # Format G-code line with 4 decimal precision
                    gcode_line = f"{transformed_cmd['type']} X{transformed_cmd['X']:.4f} Y{transformed_cmd['Y']:.4f}"

                    # Add feedrate to all move commands
                    gcode_line += f" F{feedrate}"

                    # Add radius for arcs
                    if "R" in transformed_cmd:
                        gcode_line += f" R{transformed_cmd['R']:.4f}"

                    # Add comment for first command (G2) with pad and offset info
                    if cmd_idx == 0:
                        gcode_line += f" ; pad {pad_id}, offset {pass_data['offset']}"
                    elif "comment" in transformed_cmd:
                        gcode_line += f" ; {transformed_cmd['comment']}"

                    all_gcode_lines.append(gcode_line)

        # Add postscript
        postscript_key = f"section_{section_name.replace('&', '_')}_postscript"
        if postscript_key in settings:
            all_gcode_lines.extend(settings[postscript_key].split("\n"))

        # Parse the G-code lines back into commands for plotting
        # This ensures the plot shows exactly what's in the G-code text
        plot_commands = self.parse_gcode_lines_to_commands(all_gcode_lines)

        # Return both formats: commands for plotting, lines for text display
        return {"commands": plot_commands, "lines": all_gcode_lines}

    def parse_gcode_lines_to_commands(self, gcode_lines):
        """Parse G-code lines back into command dictionaries for plotting"""
        commands = []
        errors = []

        for line_num, line in enumerate(gcode_lines, 1):
            line = line.strip()
            if not line or line.startswith(";"):
                continue

            # Parse G-code commands - be more specific to avoid G17 being treated as G1
            if (
                line.startswith("G0 ")
                or line.startswith("G1 ")
                or line.startswith("G2 ")
                or line.startswith("G3 ")
            ):
                parts = line.split()
                if len(parts) < 2:
                    errors.append(
                        f"Line {line_num}: Invalid G-code format - missing coordinates: {line}"
                    )
                    continue

                cmd = {"type": parts[0]}

                for part in parts[1:]:
                    if not part:  # Skip empty parts
                        continue
                    try:
                        if part.startswith("X"):
                            cmd["X"] = float(part[1:])
                        elif part.startswith("Y"):
                            cmd["Y"] = float(part[1:])
                        elif part.startswith("Z"):
                            cmd["Z"] = float(part[1:])
                        elif part.startswith("R"):
                            cmd["R"] = float(part[1:])
                        elif part.startswith("F"):
                            cmd["F"] = float(part[1:])
                    except ValueError as e:
                        errors.append(
                            f"Line {line_num}: Invalid coordinate '{part}' in '{line}' - {str(e)}"
                        )
                        continue

                # Validate required coordinates for move commands
                if cmd["type"] in ["G1", "G2", "G3"] and (
                    "X" not in cmd or "Y" not in cmd
                ):
                    errors.append(
                        f"Line {line_num}: Missing X or Y coordinates for {cmd['type']} command: {line}"
                    )
                    continue

                # Validate arc commands have radius
                if cmd["type"] in ["G2", "G3"] and "R" not in cmd:
                    errors.append(
                        f"Line {line_num}: Missing radius (R) for {cmd['type']} arc command: {line}"
                    )
                    continue

                # Add comment if present
                if ";" in line:
                    cmd["comment"] = line.split(";", 1)[1].strip()

                commands.append(cmd)

        # Show errors if any
        if errors:
            error_message = "G-code parsing errors:\n\n" + "\n".join(errors)
            messagebox.showerror("G-code Parsing Errors", error_message)
            return []  # Return empty list on errors

        return commands

    def update_section_1_3_display(self):
        """Update Section 1&3 display based on current view"""
        if self.section_1_3_view_var.get() == "Plot View":
            self.section_1_3_plot_frame.grid()
            self.section_1_3_text_frame.grid_remove()
            self.plot_section_1_3_data()
            # Ensure toolbar is visible
            self.section_1_3_toolbar.update()
            # print("Section 1&3 toolbar should be visible")
        else:
            self.section_1_3_plot_frame.grid_remove()
            self.section_1_3_text_frame.grid()
            self.display_section_1_3_gcode()

    def update_section_2_display(self):
        """Update Section 2 display based on current view"""
        if self.section_2_view_var.get() == "Plot View":
            self.section_2_plot_frame.grid()
            self.section_2_text_frame.grid_remove()
            self.plot_section_2_data()
            # Ensure toolbar is visible
            self.section_2_toolbar.update()
            # print("Section 2 toolbar should be visible")
        else:
            self.section_2_plot_frame.grid_remove()
            self.section_2_text_frame.grid()
            self.display_section_2_gcode()

    def plot_section_1_3_data(self):
        """Plot Section 1&3 G-code data"""
        if not hasattr(self, "section_1_3_gcode_data"):
            return

        self.section_1_3_ax.clear()

        # Set axis limits based on table dimensions
        settings = self.get_current_settings()
        if "table_dimensions" in settings:
            table_dims = settings["table_dimensions"]
            self.section_1_3_ax.set_xlim(
                table_dims["lower_left"][0], table_dims["upper_right"][0]
            )
            self.section_1_3_ax.set_ylim(
                table_dims["lower_left"][1], table_dims["upper_right"][1]
            )

        # Plot the G-code paths using commands
        self.plot_gcode_path_on_ax(
            self.section_1_3_ax,
            self.section_1_3_gcode_data["commands"],
            "Section 1&3",
            "blue",
            is_layout_plot=True,
        )
        self.section_1_3_ax.set_title("Section 1&3 Layout")
        self.section_1_3_ax.set_aspect("equal")
        self.section_1_3_ax.grid(True)
        self.section_1_3_canvas.draw()

    def plot_section_2_data(self):
        """Plot Section 2 G-code data"""
        if not hasattr(self, "section_2_gcode_data"):
            return

        self.section_2_ax.clear()

        # Set axis limits based on table dimensions
        settings = self.get_current_settings()
        if "table_dimensions" in settings:
            table_dims = settings["table_dimensions"]
            self.section_2_ax.set_xlim(
                table_dims["lower_left"][0], table_dims["upper_right"][0]
            )
            self.section_2_ax.set_ylim(
                table_dims["lower_left"][1], table_dims["upper_right"][1]
            )

        # Plot the G-code paths using commands
        self.plot_gcode_path_on_ax(
            self.section_2_ax,
            self.section_2_gcode_data["commands"],
            "Section 2",
            "red",
            is_layout_plot=True,
        )
        self.section_2_ax.set_title("Section 2 Layout")
        self.section_2_ax.set_aspect("equal")
        self.section_2_ax.grid(True)
        self.section_2_canvas.draw()

    def display_section_1_3_gcode(self):
        """Display Section 1&3 G-code in text widget"""
        if hasattr(self, "section_1_3_gcode_data"):
            self.section_1_3_gcode_text.delete(1.0, tk.END)
            self.section_1_3_gcode_text.insert(
                1.0, "\n".join(self.section_1_3_gcode_data["lines"])
            )

    def display_section_2_gcode(self):
        """Display Section 2 G-code in text widget"""
        if hasattr(self, "section_2_gcode_data"):
            self.section_2_gcode_text.delete(1.0, tk.END)
            self.section_2_gcode_text.insert(
                1.0, "\n".join(self.section_2_gcode_data["lines"])
            )

    def on_section_1_3_view_change(self, event=None):
        """Handle Section 1&3 view change"""
        self.update_section_1_3_display()

    def on_section_2_view_change(self, event=None):
        """Handle Section 2 view change"""
        self.update_section_2_display()

    def initialize_section_1_3_plot(self):
        """Initialize Section 1&3 plot with table dimensions"""
        # Use default table dimensions during initialization
        table_dims = self.settings.get(
            "table_dimensions", {"lower_left": [-400, -200], "upper_right": [400, 200]}
        )
        self.section_1_3_ax.set_xlim(
            table_dims["lower_left"][0], table_dims["upper_right"][0]
        )
        self.section_1_3_ax.set_ylim(
            table_dims["lower_left"][1], table_dims["upper_right"][1]
        )

        self.section_1_3_ax.set_title("Section 1&3 Layout")
        self.section_1_3_ax.set_aspect("equal")
        self.section_1_3_ax.grid(True)
        self.section_1_3_canvas.draw()

    def initialize_section_2_plot(self):
        """Initialize Section 2 plot with table dimensions"""
        # Use default table dimensions during initialization
        table_dims = self.settings.get(
            "table_dimensions", {"lower_left": [-400, -200], "upper_right": [400, 200]}
        )
        self.section_2_ax.set_xlim(
            table_dims["lower_left"][0], table_dims["upper_right"][0]
        )
        self.section_2_ax.set_ylim(
            table_dims["lower_left"][1], table_dims["upper_right"][1]
        )

        self.section_2_ax.set_title("Section 2 Layout")
        self.section_2_ax.set_aspect("equal")
        self.section_2_ax.grid(True)
        self.section_2_canvas.draw()

    def on_close(self):
        """Handle application close"""
        plt.close("all")
        self.root.destroy()


def main():
    root = tk.Tk()
    app = GenerateCarouselGcodeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
