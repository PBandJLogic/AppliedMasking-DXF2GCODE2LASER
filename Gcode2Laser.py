#!/usr/bin/env python3
"""
G-code Adjuster - GUI application for adjusting G-code toolpaths
based on actual vs expected reference point positions.

Features:
- Uses 3 reference points for rigid transformation (rotation + translation)
- Reference points can be embedded in G-code comments or entered manually
- GRBL streaming protocol for smooth, continuous motion
- Single-step mode for debugging
- Emergency stop with buffer clearing
- Real-time position updates every 250ms
- Interactive GUI with laser jogging controls and position capture
- Assumes Z height is consistent across all cleaned parts

Note: Does not validate against laser table limits - use caution with G-code generation.
"""
VERSION = 2.3

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import os
from datetime import datetime
import re
import serial
import serial.tools.list_ports
import time
import threading
import queue
from datetime import datetime


class SerialReaderThread(threading.Thread):
    """
    Background thread for reading from serial port.
    Continuously reads responses and puts them in a queue for processing.
    """

    def __init__(self, serial_connection, response_queue, disconnect_callback=None):
        super().__init__(daemon=True)
        self.serial_connection = serial_connection
        self.response_queue = response_queue
        self.disconnect_callback = disconnect_callback
        self.running = True
        self.consecutive_errors = 0

    def run(self):
        """Continuously read from serial and queue responses"""
        while self.running:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    response = (
                        self.serial_connection.readline()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )
                    if response:
                        self.response_queue.put(response)
                    self.consecutive_errors = 0  # Reset error counter on success
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

                if self.running and is_disconnect:
                    self.consecutive_errors += 1
                    print(
                        f"Serial disconnect error (attempt {self.consecutive_errors}): {e}"
                    )

                    # If we get multiple consecutive disconnect errors, USB is disconnected
                    if self.consecutive_errors >= 3:
                        print("Serial connection lost - USB disconnected")
                        if self.disconnect_callback:
                            # Signal disconnect to main thread
                            self.response_queue.put("__DISCONNECTED__")
                        self.running = False
                        break
                elif self.running:
                    # Non-disconnect error (e.g., timeout) - just log and continue
                    print(f"Serial error (non-fatal): {e}")
                    self.consecutive_errors = (
                        0  # Reset counter for non-disconnect errors
                    )

                time.sleep(0.01)
            except Exception as e:
                if self.running:  # Only log if not shutting down
                    print(f"Unexpected serial error: {e}")
                    import traceback

                    traceback.print_exc()
                time.sleep(0.01)

    def stop(self):
        """Stop the reading thread"""
        self.running = False


class GRBLSettings:
    """Class to store GRBL settings"""

    def __init__(self):
        self.settings = {}  # Dictionary to store all settings
        self.descriptions = {
            0: "Step pulse time (microseconds)",
            1: "Step idle delay (milliseconds)",
            2: "Step pulse invert (mask)",
            3: "Step direction invert (mask)",
            4: "Invert step enable pin",
            5: "Invert limit pins",
            6: "Invert probe pin",
            10: "Status report options",
            11: "Junction deviation (mm)",
            12: "Arc tolerance (mm)",
            13: "Report in inches",
            20: "Soft limits enable",
            21: "Hard limits enable",
            22: "Homing cycle enable",
            23: "Homing direction invert (mask)",
            24: "Homing locate feed rate (mm/min)",
            25: "Homing search seek rate (mm/min)",
            26: "Homing switch debounce delay (ms)",
            27: "Homing switch pull-off distance (mm)",
            30: "Maximum spindle speed (RPM)",
            31: "Minimum spindle speed (RPM)",
            32: "Laser-mode enable",
            100: "X-axis steps per mm",
            101: "Y-axis steps per mm",
            102: "Z-axis steps per mm",
            110: "X-axis max rate (mm/min)",
            111: "Y-axis max rate (mm/min)",
            112: "Z-axis max rate (mm/min)",
            120: "X-axis acceleration (mm/sec^2)",
            121: "Y-axis acceleration (mm/sec^2)",
            122: "Z-axis acceleration (mm/sec^2)",
            130: "X-axis max travel (mm)",
            131: "Y-axis max travel (mm)",
            132: "Z-axis max travel (mm)",
        }

    def set(self, setting_num, value):
        """Store a setting value"""
        self.settings[setting_num] = value

    def get(self, setting_num, default=None):
        """Get a setting value"""
        return self.settings.get(setting_num, default)

    def get_description(self, setting_num):
        """Get the description of a setting"""
        return self.descriptions.get(setting_num, "Unknown setting")

    def __str__(self):
        """String representation of all settings"""
        output = "GRBL Settings:\n"
        for num in sorted(self.settings.keys()):
            desc = self.get_description(num)
            output += f"  ${num}={self.settings[num]} ({desc})\n"
        return output


class GCodeAdjuster:
    def __init__(self, root):
        self.root = root
        self.root.title(
            f"Applied Masking - Gcode2Laser for Precision G-code Alignment v{VERSION}"
        )
        self.root.geometry("1400x900")

        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(icon_path):
                self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except Exception as e:
            print(f"Could not load window icon: {e}")

        # Data storage
        self.original_gcode = ""
        self.adjusted_gcode = ""
        self.original_positioning_lines = []
        self.original_engraving_lines = []
        self.adjusted_positioning_lines = []
        self.adjusted_engraving_lines = []

        # Reference point data from G-code comments
        self.num_reference_points = 3  # Use 3 points for rigid transform
        # Initialize with 3 zero points
        self.reference_points_expected = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
        self.reference_points_actual = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]

        # Serial connection
        self.serial_connection = None
        self.is_connected = False
        self.serial_reader_thread = None
        self.response_queue = queue.Queue()
        self.processing_responses = False

        # Position tracking
        self.machine_pos = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.work_pos = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.wco = {"x": 0.0, "y": 0.0, "z": 0.0}

        # Modal position tracking for arc conversion
        self.current_modal_x = 0.0
        self.current_modal_y = 0.0

        # GRBL state tracking
        self.grbl_state = "Disconnected"  # Tracks GRBL state (Idle, Run, Alarm, etc.)

        # Plot auto-scale settings
        self.auto_scale_enabled = True  # Toggle for auto-scaling to laser position

        # Communication log
        self.comm_log_enabled = True  # Toggle for logging
        self.comm_log_max_lines = 1000  # Maximum log entries
        self.comm_log_entries = []  # Store log entries
        self.log_status_queries = False  # Toggle for logging status queries
        self.log_update_buffer = []  # Buffer for batched log updates
        self.log_update_timer = None  # Timer for batched updates

        # Position display batching
        self.position_update_pending = False  # Flag for pending position update
        self.last_position_update = 0  # Timestamp of last position label update

        # Modal units (G20/G21) detected from file; default None -> will inject G21 if absent
        self.modal_units = None

        # Smart polling
        self.last_command_time = 0  # Track when last command was sent

        # Buffer management for manual commands
        self.manual_command_queue = []  # Queue of manual commands waiting to be sent
        self.waiting_for_ok = (
            False  # Track if we're waiting for an 'ok' response (manual commands only)
        )

        # Laser state
        self.laser_on = False
        self.laser_power = 3  # Default laser power level (0-100%)
        self.laser_power_max = 10000  # Maximum laser power value (full scale)

        # GRBL settings
        self.grbl_settings = GRBLSettings()
        self.homing_enabled = False

        # Execution tracking
        self.execution_path = []  # List of (x, y) tuples for execution trace
        self.is_executing = False

        # GRBL streaming - simplified command counting
        self.gcode_buffer = []  # Queue of G-code lines to send
        self.buffer_size = (
            0  # Current commands in GRBL's buffer (command count, not bytes)
        )
        self.max_buffer_size = (
            4  # Conservative buffer (was 15, reduced to prevent arc errors)
        )
        self.streaming = False
        self.status_update_id = None  # Timer ID for status updates
        self.command_queue = []  # Track sent commands for proper ok matching
        self.sent_lines = 0  # Track progress
        self.total_lines = 0
        self._last_plot_update = 0  # Throttle plot updates

        # Single-step mode
        self.single_step_mode = False
        self.step_paused = False
        self.current_line_text = ""

        # GUI setup
        self.setup_gui()

        # Configure font for LabelFrame headers to match button text (bold)
        style = ttk.Style()
        style.configure("TLabelframe.Label", font=("TkDefaultFont", 10, "bold"))

    def setup_gui(self):
        """Set up the GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel container with scrollbar
        left_container = ttk.Frame(main_frame, width=580)
        left_container.pack(side="left", fill="both", padx=(0, 10))
        left_container.pack_propagate(False)

        # Create canvas and scrollbar for left panel
        left_canvas = tk.Canvas(left_container, width=560, highlightthickness=0)
        left_scrollbar = ttk.Scrollbar(
            left_container, orient="vertical", command=left_canvas.yview
        )

        # Create a frame inside the canvas to hold all controls
        left_panel = ttk.Frame(left_canvas)

        # Configure canvas
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        # Pack scrollbar and canvas
        left_scrollbar.pack(side="right", fill="y")
        left_canvas.pack(side="left", fill="both", expand=True)

        # Create window in canvas
        canvas_frame = left_canvas.create_window((0, 0), window=left_panel, anchor="nw")

        # Configure scroll region when frame changes size
        def configure_scroll_region(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        left_panel.bind("<Configure>", configure_scroll_region)

        # Bind mousewheel to scroll
        def on_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        left_canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Store canvas reference for cleanup
        self.left_canvas = left_canvas

        # Right panel for plot
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)

    def setup_left_panel(self, parent):
        """Set up the left control panel"""
        # Logo and title header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 10))

        try:
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                # Create horizontal layout for logo and title
                logo_title_frame = ttk.Frame(header_frame)
                logo_title_frame.pack(fill="x", pady=5)

                # Load and display logo (50% smaller - from 25% to 12.5%)
                logo_image = tk.PhotoImage(file=logo_path)
                logo_image = logo_image.subsample(
                    8, 8
                )  # Makes it 12.5% size (50% of previous 25%)
                logo_label = ttk.Label(logo_title_frame, image=logo_image)
                logo_label.image = logo_image  # Keep a reference!
                logo_label.pack(side="left", padx=(0, 10))

                # Add title to the right of logo
                title_label = ttk.Label(
                    logo_title_frame, text="Gcode2Laser", font=("Arial", 14, "bold")
                )
                title_label.pack(side="left")
        except Exception as e:
            # If logo fails, just show title
            title_label = ttk.Label(
                header_frame, text="Gcode2Laser", font=("Arial", 14, "bold")
            )
            title_label.pack(pady=5)

        # GRBL Connection section
        grbl_frame = ttk.LabelFrame(parent, text="GRBL Connection", padding=10)
        grbl_frame.pack(fill="x", pady=(0, 10))

        # COM port selection row
        com_port_row = ttk.Frame(grbl_frame)
        com_port_row.pack(fill="x", pady=(0, 5))

        # COM port dropdown
        ttk.Label(com_port_row, text="COM Port:").pack(side="left", padx=(0, 5))
        self.com_port_var = tk.StringVar()
        self.com_port_combo = ttk.Combobox(
            com_port_row, textvariable=self.com_port_var, width=12, state="readonly"
        )
        self.com_port_combo.pack(side="left", padx=(0, 5))

        # Refresh COM ports button
        ttk.Button(
            com_port_row, text="⟳", command=self.refresh_com_ports, width=3
        ).pack(side="left", padx=(0, 5))

        # Connect/Disconnect button row
        connect_row = ttk.Frame(grbl_frame)
        connect_row.pack(fill="x")

        self.connect_button = ttk.Button(
            connect_row, text="Connect", command=self.toggle_connection, width=12
        )
        self.connect_button.pack(side="left", padx=(0, 5))

        # Connection status label
        self.status_label = ttk.Label(
            connect_row,
            text="Disconnected",
            foreground="red",
            font=("Arial", 9, "bold"),
        )
        self.status_label.pack(side="left")

        # GRBL State display (moved up for more space)
        self.grbl_state_label = ttk.Label(
            connect_row,
            text="State: Disconnected",
            font=("TkDefaultFont", 9, "bold"),
            foreground="gray",
        )
        self.grbl_state_label.pack(side="left", padx=(10, 0))

        # Control buttons row (Home and Clear Errors)
        control_row = ttk.Frame(grbl_frame)
        control_row.pack(fill="x", pady=(5, 0))

        self.home_button = ttk.Button(
            control_row, text="Home", command=self.home_machine, width=12
        )
        self.home_button.pack(side="left", padx=(0, 5))

        self.clear_errors_button = ttk.Button(
            control_row, text="Clear Errors", command=self.clear_errors, width=12
        )
        self.clear_errors_button.pack(side="left", padx=(0, 5))

        self.soft_reset_button = ttk.Button(
            control_row, text="Reboot GRBL", command=self.reboot_grbl, width=12
        )
        self.soft_reset_button.pack(side="left")

        # Refresh COM ports on startup
        self.refresh_com_ports()

        # File operations
        file_frame = ttk.LabelFrame(parent, text="File Operations", padding=10)
        file_frame.pack(fill="x", pady=(0, 10))

        # Create a row frame for the two buttons
        file_buttons_frame = ttk.Frame(file_frame)
        file_buttons_frame.pack(fill="x")

        ttk.Button(
            file_buttons_frame,
            text="Load G-code File",
            command=self.load_gcode_file,
            width=20,
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            file_buttons_frame,
            text="Save Adjusted G-code",
            command=self.save_adjusted_gcode,
            width=20,
        ).pack(side="left")

        # G-code Execution section
        execution_frame = ttk.LabelFrame(parent, text="G-code Execution", padding=10)
        execution_frame.pack(fill="x", pady=(0, 10))

        # Run, Step, Next, and STOP buttons
        buttons_frame = ttk.Frame(execution_frame)
        buttons_frame.pack(fill="x")

        # Run button
        ttk.Button(
            buttons_frame, text="Run", command=self.run_adjusted_gcode, width=8
        ).pack(side="left", padx=(0, 3))

        # Step button
        ttk.Button(
            buttons_frame, text="Step", command=self.run_single_step, width=8
        ).pack(side="left", padx=(0, 3))

        # Next Step button (for paused single-step mode)
        self.next_step_button = ttk.Button(
            buttons_frame,
            text="Next",
            command=self.continue_step,
            width=8,
            state="disabled",
        )
        self.next_step_button.pack(side="left", padx=(0, 10))

        # STOP button (red background)
        self.stop_button = tk.Button(
            buttons_frame,
            text="STOP",
            command=self.emergency_stop,
            bg="red",
            fg="white",
            font=("TkDefaultFont", 10, "bold"),
            relief="raised",
            bd=3,
            width=6,
            state="disabled",  # Disabled until streaming starts
        )
        self.stop_button.pack(side="left", padx=(0, 0))

        # Laser Jog Controls section
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
            width=15,
        )
        self.set_origin_button.pack(side="left", padx=(0, 5))

        self.auto_origin_button = ttk.Button(
            origin_frame,
            text="Auto Origin",
            command=self.auto_origin,
            width=15,
        )
        self.auto_origin_button.pack(side="left")

        # G-code command entry
        gcode_cmd_frame = ttk.Frame(jog_frame)
        gcode_cmd_frame.pack(fill="x", pady=(5, 5))

        ttk.Label(gcode_cmd_frame, text="G-code:").pack(side="left", padx=(0, 5))
        self.gcode_cmd_var = tk.StringVar()
        self.gcode_cmd_entry = ttk.Entry(
            gcode_cmd_frame,
            textvariable=self.gcode_cmd_var,
            width=20,
        )
        self.gcode_cmd_entry.pack(side="left", padx=(0, 5))

        # Bind Enter key to execute command
        self.gcode_cmd_entry.bind("<Return>", lambda e: self.execute_manual_gcode())

        ttk.Button(
            gcode_cmd_frame,
            text="Execute",
            command=self.execute_manual_gcode,
            width=8,
        ).pack(side="left")

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
            right_controls_frame, text="Laser OFF", command=self.toggle_laser, width=12
        )
        self.laser_button.pack(pady=(0, 5))

        # Laser power level input
        power_frame = ttk.Frame(right_controls_frame)
        power_frame.pack(pady=(0, 5))

        ttk.Label(power_frame, text="Power:").pack(side="left", padx=(0, 2))
        self.laser_power_var = tk.StringVar(value="3")
        self.laser_power_entry = ttk.Entry(
            power_frame,
            textvariable=self.laser_power_var,
            width=6,
            justify="right",
        )
        self.laser_power_entry.pack(side="left", padx=(0, 2))
        ttk.Label(power_frame, text="%").pack(side="left")

        # Bind Enter key to update power level
        self.laser_power_entry.bind("<Return>", lambda e: self.update_laser_power())

        # Laser max power input
        max_power_frame = ttk.Frame(right_controls_frame)
        max_power_frame.pack(pady=(0, 5))

        ttk.Label(max_power_frame, text="Max:").pack(side="left", padx=(0, 2))
        self.laser_power_max_var = tk.StringVar(value="10000")
        self.laser_power_max_entry = ttk.Entry(
            max_power_frame,
            textvariable=self.laser_power_max_var,
            width=6,
            justify="right",
        )
        self.laser_power_max_entry.pack(side="left", padx=(0, 2))
        ttk.Label(max_power_frame, text="(full scale)").pack(side="left")

        # Bind Enter key to update max power level
        self.laser_power_max_entry.bind(
            "<Return>", lambda e: self.update_laser_power_max()
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

        # Button styling - fixed width for consistent layout
        button_width = 8

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

        # Store reference to parent for dynamic updates
        self.targets_parent = parent

        # Create initial reference points display
        self.update_reference_points_display()

        # Adjust button
        ttk.Button(
            parent, text="Adjust G-code", command=self.adjust_gcode, width=20
        ).pack(pady=(0, 10))

        # Results display
        results_frame = ttk.LabelFrame(parent, text="Calculation Results", padding=10)
        results_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.results_text = tk.Text(results_frame, height=20, width=40, wrap=tk.WORD)
        results_text_scroll = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.results_text.yview
        )
        self.results_text.configure(yscrollcommand=results_text_scroll.set)
        self.results_text.pack(side="left", fill="both", expand=True)
        results_text_scroll.pack(side="right", fill="y")

    def update_reference_points_display(self):
        """Update the reference points display based on loaded data"""
        # Destroy the old targets container
        if hasattr(self, "targets_container") and self.targets_container.winfo_exists():
            self.targets_container.destroy()

        # Create new targets container - pack before adjust button
        self.targets_container = ttk.LabelFrame(
            self.targets_parent, text="Reference Points", padding=10
        )
        # Find adjust button and pack before it
        children = self.targets_parent.winfo_children()
        # The adjust button should be near the end
        for i, child in enumerate(children):
            if isinstance(child, ttk.Button):
                try:
                    if "Adjust" in child.cget("text"):
                        self.targets_container.pack(
                            fill="x", pady=(0, 10), before=child
                        )
                        break
                except:
                    pass
        else:
            # Fallback if we can't find the button
            self.targets_container.pack(fill="x", pady=(0, 10))

        # Always use 3 reference points
        num_points = 3

        # Store entry variables for each point
        self.ref_point_expected_vars = []
        self.ref_point_actual_vars = []

        # Create compact rows for each reference point
        for i in range(num_points):
            point_num = i + 1
            expected_point = (
                self.reference_points_expected[i]
                if i < len(self.reference_points_expected)
                else (0.0, 0.0)
            )
            actual_point = (
                self.reference_points_actual[i]
                if i < len(self.reference_points_actual)
                else expected_point
            )

            # Create a single row for this point with all info
            point_frame = ttk.Frame(self.targets_container)
            point_frame.pack(fill="x", pady=2)

            # Point label
            ttk.Label(
                point_frame,
                text=f"Pt{point_num}:",
                font=("TkDefaultFont", 9, "bold"),
            ).pack(side="left", padx=(0, 2))

            # Expected label and entry
            ttk.Label(
                point_frame, text="Exp:", foreground="black", font=("TkDefaultFont", 9)
            ).pack(side="left", padx=(0, 2))

            # Expected X, Y in single entry
            expected_combined = tk.StringVar(
                value=f"{expected_point[0]:.2f}, {expected_point[1]:.2f}"
            )
            # Store both X and Y vars for compatibility
            expected_x_var = tk.StringVar(value=f"{expected_point[0]:.2f}")
            expected_y_var = tk.StringVar(value=f"{expected_point[1]:.2f}")
            self.ref_point_expected_vars.append((expected_x_var, expected_y_var))

            expected_entry = ttk.Entry(
                point_frame,
                textvariable=expected_combined,
                width=11,
                font=("TkDefaultFont", 9),
            )
            expected_entry.pack(side="left", padx=(0, 3))

            # Link the combined entry to individual vars
            def update_expected_vars(combined_var, x_var, y_var, idx, *args):
                try:
                    val = combined_var.get()
                    parts = val.replace(" ", "").split(",")
                    if len(parts) == 2:
                        x_var.set(parts[0])
                        y_var.set(parts[1])
                        # Update the reference_points_expected list
                        try:
                            x_val = float(parts[0])
                            y_val = float(parts[1])
                            if idx < len(self.reference_points_expected):
                                self.reference_points_expected[idx] = (x_val, y_val)
                            # Refresh the plot to update arrows
                            self.plot_toolpath()
                        except ValueError:
                            pass
                except:
                    pass

            expected_combined.trace_add(
                "write",
                lambda *args, c=expected_combined, x=expected_x_var, y=expected_y_var, idx=i: update_expected_vars(
                    c, x, y, idx, *args
                ),
            )

            # Actual label and entry
            ttk.Label(
                point_frame, text="Act:", foreground="black", font=("TkDefaultFont", 9)
            ).pack(side="left", padx=(0, 2))

            # Actual X, Y in single entry
            actual_combined = tk.StringVar(
                value=f"{actual_point[0]:.2f}, {actual_point[1]:.2f}"
            )
            # Store both X and Y vars for compatibility
            actual_x_var = tk.StringVar(value=f"{actual_point[0]:.2f}")
            actual_y_var = tk.StringVar(value=f"{actual_point[1]:.2f}")
            self.ref_point_actual_vars.append((actual_x_var, actual_y_var))

            actual_entry = ttk.Entry(
                point_frame,
                textvariable=actual_combined,
                width=11,
                font=("TkDefaultFont", 9),
            )
            actual_entry.pack(side="left", padx=(0, 2))

            # Link the combined entry to individual vars
            def update_actual_vars(combined_var, x_var, y_var, idx, *args):
                try:
                    val = combined_var.get()
                    parts = val.replace(" ", "").split(",")
                    if len(parts) == 2:
                        x_var.set(parts[0])
                        y_var.set(parts[1])
                        # Update the reference_points_actual list
                        try:
                            x_val = float(parts[0])
                            y_val = float(parts[1])
                            if idx < len(self.reference_points_actual):
                                self.reference_points_actual[idx] = (x_val, y_val)
                            # Refresh the plot to update arrows
                            self.plot_toolpath()
                        except ValueError:
                            pass
                except:
                    pass

            actual_combined.trace_add(
                "write",
                lambda *args, c=actual_combined, x=actual_x_var, y=actual_y_var, idx=i: update_actual_vars(
                    c, x, y, idx, *args
                ),
            )

            # "Goto" button to move to expected position
            def goto_expected_pos(exp_x, exp_y):
                """Move laser to the expected reference point position"""
                if not self.is_connected:
                    messagebox.showwarning("Warning", "Please connect to GRBL first!")
                    return

                # Check if laser is currently on
                was_laser_on = self.laser_on

                # If laser is on, turn it off for the rapid move
                if was_laser_on:
                    self.send_gcode_async("M5")  # Turn off laser

                # Send commands to move to the expected position
                self.send_gcode_async("G90")  # Absolute positioning mode
                self.send_gcode_async(f"G0 X{exp_x:.4f} Y{exp_y:.4f}")  # Rapid move

                # If laser was on, turn it back on at low power (same as toggle_laser)
                if was_laser_on:
                    # Turn on laser at configured power level (scaled)
                    scaled_power = int(
                        (self.laser_power / 100.0) * self.laser_power_max
                    )
                    self.send_gcode_async(f"M3 S{scaled_power}")
                    self.send_gcode_async("G1 F100")  # Set feed rate for laser mode
                    self.laser_on = True
                    self.laser_button.config(text="Laser ON")

            goto_button = ttk.Button(
                point_frame,
                text="Goto",
                command=lambda x=expected_point[0], y=expected_point[
                    1
                ]: goto_expected_pos(x, y),
                width=5,
            )
            goto_button.pack(side="left", padx=(0, 2))

            # "Set" button to capture current work position
            def set_from_wpos(combined_var):
                """Set actual coordinates from current work position"""
                x = self.work_pos["x"]
                y = self.work_pos["y"]
                combined_var.set(f"{x:.2f}, {y:.2f}")

            set_button = ttk.Button(
                point_frame,
                text="Set",
                command=lambda c=actual_combined: set_from_wpos(c),
                width=3,
            )
            set_button.pack(side="left", padx=(0, 5))

    def setup_right_panel(self, parent):
        """Set up the right plot panel"""
        # Create control frame for plot options
        control_frame = ttk.Frame(parent)
        control_frame.pack(side="top", fill="x", pady=5)

        # Add checkbox for showing original G-code
        self.show_original_var = tk.BooleanVar(
            value=True
        )  # Default to showing original
        show_original_check = ttk.Checkbutton(
            control_frame,
            text="Show Original G-code",
            variable=self.show_original_var,
            command=self.plot_toolpath,
        )
        show_original_check.pack(side="left", padx=10)

        # Add checkbox for auto-scale behavior
        self.auto_scale_var = tk.BooleanVar(value=True)  # Default to auto-scale enabled
        auto_scale_check = ttk.Checkbutton(
            control_frame,
            text="Auto-scale to Laser",
            variable=self.auto_scale_var,
            command=self.toggle_auto_scale,
        )
        auto_scale_check.pack(side="left", padx=10)

        # Position display on the right side
        pos_display_frame = ttk.Frame(control_frame)
        pos_display_frame.pack(side="right", padx=10)

        # Work Position
        wpos_row = ttk.Frame(pos_display_frame)
        wpos_row.pack(side="top", anchor="e")
        ttk.Label(wpos_row, text="WPos:", font=("TkDefaultFont", 9, "bold")).pack(
            side="left", padx=(0, 5)
        )
        self.work_pos_label = ttk.Label(
            wpos_row, text="X: 0.00  Y: 0.00  Z: 0.00", font=("Courier", 9)
        )
        self.work_pos_label.pack(side="left")

        # Machine Position
        mpos_row = ttk.Frame(pos_display_frame)
        mpos_row.pack(side="top", anchor="e")
        ttk.Label(mpos_row, text="MPos:", font=("TkDefaultFont", 9, "bold")).pack(
            side="left", padx=(0, 5)
        )
        self.machine_pos_label = ttk.Label(
            mpos_row, text="X: 0.00  Y: 0.00  Z: 0.00", font=("Courier", 9)
        )
        self.machine_pos_label.pack(side="left")

        # Create paned window for plot and log
        self.right_paned = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        self.right_paned.pack(fill="both", expand=True)

        # Plot frame (top pane)
        plot_frame = ttk.Frame(self.right_paned)
        self.right_paned.add(plot_frame, weight=3)  # 3/4 of space

        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Set up the plot
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.set_title("G-code Toolpath")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect("equal")

        # Embed plot in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.draw()

        # Add navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        self.toolbar.update()
        self.toolbar.pack(side="bottom", fill="x")

        # Pack canvas after toolbar
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        # Communication log frame (bottom pane)
        log_frame = ttk.LabelFrame(
            self.right_paned, text="Communication Log", padding=5
        )
        self.right_paned.add(log_frame, weight=1)  # 1/4 of space

        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(side="top", fill="x", pady=(0, 5))

        # Enable/disable logging checkbox
        self.log_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            log_controls,
            text="Enable Logging",
            variable=self.log_enabled_var,
            command=self.toggle_logging,
        ).pack(side="left", padx=5)

        # Timestamp checkbox
        self.log_timestamp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            log_controls,
            text="Show Timestamps",
            variable=self.log_timestamp_var,
            command=self.refresh_log_display,
        ).pack(side="left", padx=5)

        # Clear log button
        ttk.Button(
            log_controls, text="Clear Log", command=self.clear_comm_log, width=10
        ).pack(side="left", padx=5)

        # Auto-scroll checkbox
        self.log_autoscroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            log_controls, text="Auto-scroll", variable=self.log_autoscroll_var
        ).pack(side="left", padx=5)

        # Show status queries checkbox
        self.log_status_queries_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            log_controls,
            text="Show Status Queries",
            variable=self.log_status_queries_var,
            command=self.toggle_status_query_logging,
        ).pack(side="left", padx=5)

        # Text widget with scrollbar for log
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill="both", expand=True)

        self.comm_log_text = tk.Text(
            log_text_frame,
            height=10,
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
        self.comm_log_text.tag_config("timestamp", foreground="gray")

        # Bind scroll events to prevent propagation to parent widgets
        def on_mousewheel(event):
            # Handle mouse wheel scrolling within the text widget
            self.comm_log_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"  # Prevent event propagation

        def on_scroll(event):
            # Handle other scroll events
            if event.delta:
                self.comm_log_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"  # Prevent event propagation

        # Bind mouse wheel and scroll events
        self.comm_log_text.bind("<MouseWheel>", on_mousewheel)
        self.comm_log_text.bind("<Button-4>", on_scroll)  # Linux scroll up
        self.comm_log_text.bind("<Button-5>", on_scroll)  # Linux scroll down

        # Initialize plot with laser position marker
        self.initialize_plot()

    def initialize_plot(self):
        """Initialize the plot with laser position marker"""
        # Clear and set up basic plot
        self.ax.clear()
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.set_title("G-code Toolpath")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect("equal")

        # Set initial view limits (default workspace size)
        self.ax.set_xlim(0, 400)
        self.ax.set_ylim(0, 400)

        # Add laser position marker (red circle)
        self.laser_marker = self.ax.plot(
            self.work_pos["x"],
            self.work_pos["y"],
            "ro",
            markersize=8,
            label="Laser Position",
        )[0]

        # Add legend
        self.ax.legend(loc="upper right")

        # Draw the canvas
        self.canvas.draw()

    def load_gcode_file(self):
        """Load a G-code file and parse coordinates"""
        file_path = filedialog.askopenfilename(
            title="Select G-code File",
            filetypes=[
                ("G-code files", "*.nc"),
                ("G-code files", "*.gcode"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                self.original_gcode = f.read()

            # Detect modal units from original G-code (preserve G20/G21)
            self.modal_units = None
            for raw_line in self.original_gcode.split("\n"):
                line = raw_line.strip().upper()
                if not line or line.startswith(";") or line.startswith("("):
                    continue
                if line.startswith("G20"):
                    self.modal_units = "G20"
                    break
                if line.startswith("G21"):
                    self.modal_units = "G21"
                    break

            # Parse reference points from comments
            num_points, expected_points = self.parse_reference_points_from_comments(
                self.original_gcode
            )

            # Check if we found actual reference points (not just padded zeros)
            has_real_points = any(point != (0.0, 0.0) for point in expected_points)

            if expected_points and len(expected_points) >= 2 and has_real_points:
                # Found reference points in comments - use first 3
                self.reference_points_expected = expected_points[:3]
                # Initialize actual points to match expected points
                self.reference_points_actual = expected_points[:3].copy()

                # Update the GUI to show these reference points
                self.update_reference_points_display()

                print(
                    f"Loaded {min(len(expected_points), 3)} reference points from G-code comments"
                )
            else:
                print(
                    "No reference points found in G-code comments - using manual entry"
                )

            # Parse G-code line segments
            self.original_positioning_lines, self.original_engraving_lines = (
                self.parse_gcode_coordinates(self.original_gcode)
            )

            # Reset display and calculation results (but keep expected/actual X,Y values)
            self.reset_display()

            # Plot the original toolpath
            self.plot_toolpath()

            # Store the file path for saving
            self.original_file_path = file_path

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load G-code file:\n{str(e)}")

    def reset_display(self):
        """Reset display and calculation results"""
        # Clear adjusted data
        self.adjusted_positioning_lines = []
        self.adjusted_engraving_lines = []
        self.adjusted_gcode = ""

        # Clear results display
        if hasattr(self, "results_text"):
            self.results_text.delete(1.0, tk.END)

    def parse_reference_points_from_comments(self, gcode):
        """
        Parse reference points from G-code comments.
        Expected format:
        ; reference_point1 = (-79.2465, -21.234)
        ; reference_point2 = ( 79.2465, -21.234)

        Returns: (num_points, expected_points_list) - always returns 3 and first 3 points found
        """
        lines = gcode.split("\n")
        expected_points = []

        for line in lines:
            line_stripped = line.strip()

            # Check for reference_pointN = (x, y)
            if "reference_point" in line_stripped.lower():
                # Match patterns like: reference_point1 = (-79.2465, -21.234)
                match = re.search(
                    r"reference_point\d+\s*=\s*\(\s*([-+]?\d+\.?\d*)\s*,\s*([-+]?\d+\.?\d*)\s*\)",
                    line_stripped,
                    re.IGNORECASE,
                )
                if match:
                    x = float(match.group(1))
                    y = float(match.group(2))
                    expected_points.append((x, y))

                    # Stop after finding 3 points
                    if len(expected_points) >= 3:
                        break

        # Always return 3 points (pad with zeros if needed)
        while len(expected_points) < 3:
            expected_points.append((0.0, 0.0))

        # Always return exactly 3 points
        return 3, expected_points[:3]

    def parse_gcode_coordinates(self, gcode):
        """Parse G-code and extract line segments exactly like dxf2laser.py"""
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

                # Always draw positioning moves (including first one from origin)
                positioning_lines.append([(last_x, last_y), (current_x, current_y)])

                last_x = current_x
                last_y = current_y

            # Parse G1 (engraving) moves
            elif line_upper.startswith("G1 "):
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

                # Always draw engraving moves (including first one if no G0 preceded it)
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
                    start_angle = np.arctan2(last_y - center_y, last_x - center_x)
                    end_angle = np.arctan2(current_y - center_y, current_x - center_x)

                    # Calculate radius
                    radius = np.sqrt(i_offset**2 + j_offset**2)

                    # Determine arc direction (G2 = CW, G3 = CCW)
                    is_ccw = line_upper.startswith("G3")

                    # Calculate arc span
                    if is_ccw:
                        # Counterclockwise
                        if end_angle <= start_angle:
                            end_angle += 2 * np.pi
                        arc_span = end_angle - start_angle
                    else:
                        # Clockwise
                        if end_angle >= start_angle:
                            end_angle -= 2 * np.pi
                        arc_span = start_angle - end_angle

                    # Break arc into segments for visualization (use 5-degree steps)
                    num_segments = max(8, int(abs(arc_span) / np.radians(5)))
                    # For full circles or near-full circles, ensure we have enough segments
                    if abs(arc_span) > 1.9 * np.pi:  # Near full circle
                        num_segments = max(
                            72, num_segments
                        )  # At least 5-degree steps for full circle
                    angle_step = (end_angle - start_angle) / num_segments

                    # Generate arc segments
                    prev_arc_x = last_x
                    prev_arc_y = last_y

                    for i in range(1, num_segments + 1):
                        angle = start_angle + i * angle_step
                        arc_x = center_x + radius * np.cos(angle)
                        arc_y = center_y + radius * np.sin(angle)

                        # Add segment to engraving lines
                        engraving_lines.append(
                            [(prev_arc_x, prev_arc_y), (arc_x, arc_y)]
                        )

                        prev_arc_x = arc_x
                        prev_arc_y = arc_y

                    # Ensure the final segment reaches exactly the end point
                    if (
                        abs(prev_arc_x - current_x) > 0.001
                        or abs(prev_arc_y - current_y) > 0.001
                    ):
                        engraving_lines.append(
                            [(prev_arc_x, prev_arc_y), (current_x, current_y)]
                        )
                else:
                    # No I/J offsets, treat as straight line (fallback)
                    engraving_lines.append([(last_x, last_y), (current_x, current_y)])

                last_x = current_x
                last_y = current_y

        return positioning_lines, engraving_lines

    def plot_toolpath(self):
        """Plot the toolpath on the canvas"""
        self.ax.clear()

        # Check if we should show original G-code (only if checkbox exists and is checked)
        show_original = getattr(self, "show_original_var", None)
        if show_original is None or show_original.get():
            if self.original_positioning_lines or self.original_engraving_lines:
                # Plot original toolpath with color coding
                self.plot_gcode_toolpath(
                    self.original_positioning_lines,
                    self.original_engraving_lines,
                    "Original",
                    self.ax,
                )

        if self.adjusted_positioning_lines or self.adjusted_engraving_lines:
            # Plot adjusted toolpath with color coding
            self.plot_gcode_toolpath(
                self.adjusted_positioning_lines,
                self.adjusted_engraving_lines,
                "Adjusted",
                self.ax,
            )

        # Plot execution path if running G-code
        if self.is_executing and len(self.execution_path) > 1:
            exec_x = [p[0] for p in self.execution_path]
            exec_y = [p[1] for p in self.execution_path]
            self.ax.plot(
                exec_x,
                exec_y,
                "purple",
                linewidth=3,
                alpha=0.7,
                label="Execution Path",
                zorder=90,
            )

        # Plot current position marker (always show it)
        x = self.work_pos["x"]
        y = self.work_pos["y"]
        self.laser_marker = self.ax.plot(
            x,
            y,
            "ro",
            markersize=10,
            markeredgecolor="black",
            markeredgewidth=2,
            label="Current Position",
            zorder=100,
        )[0]

        # Plot reference point arrows (upward facing green arrows)
        self.plot_reference_point_arrows()

        # Set plot properties
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.set_title("G-code Toolpath")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect("equal")

        # Add legend if we have data
        if (
            self.original_positioning_lines
            or self.original_engraving_lines
            or self.adjusted_positioning_lines
            or self.adjusted_engraving_lines
            or self.is_connected
        ):
            self.ax.legend(loc="upper left")

        # Auto-scale to fit all data
        self.ax.relim()
        self.ax.autoscale_view()

        self.canvas.draw()

    def plot_reference_point_arrows(self):
        """Plot upward facing arrows at reference point locations (expected and actual)"""
        try:
            # Get reference points from the GUI variables
            if (
                not hasattr(self, "ref_point_actual_vars")
                or len(self.ref_point_actual_vars) < 3
                or not hasattr(self, "ref_point_expected_vars")
                or len(self.ref_point_expected_vars) < 3
            ):
                return

            arrow_length = 10  # 10mm arrow length

            for i in range(3):  # Plot arrows for all 3 reference points
                try:
                    # Get expected position from GUI
                    exp_x_var, exp_y_var = self.ref_point_expected_vars[i]
                    exp_x = float(exp_x_var.get())
                    exp_y = float(exp_y_var.get())

                    # Get actual position from GUI
                    act_x_var, act_y_var = self.ref_point_actual_vars[i]
                    act_x = float(act_x_var.get())
                    act_y = float(act_y_var.get())

                    # Plot expected reference point (blue arrow)
                    if not (exp_x == 0.0 and exp_y == 0.0):
                        exp_arrow_start_x = exp_x
                        exp_arrow_start_y = exp_y - arrow_length

                        self.ax.annotate(
                            "",  # No text
                            xy=(exp_x, exp_y),  # Arrow tip (expected point)
                            xytext=(exp_arrow_start_x, exp_arrow_start_y),  # Arrow tail
                            arrowprops=dict(
                                arrowstyle="->",
                                color="blue",
                                lw=2,
                                shrinkA=0,
                                shrinkB=0,
                            ),
                            zorder=94,  # Below actual arrows
                        )

                        # Add expected point label
                        self.ax.text(
                            exp_x - 8,  # Offset to the left
                            exp_y + 2,  # Slightly offset up
                            f"E{i+1}",
                            color="blue",
                            fontweight="bold",
                            fontsize=9,
                            zorder=96,
                        )

                    # Plot actual reference point (green arrow)
                    if not (act_x == 0.0 and act_y == 0.0):
                        act_arrow_start_x = act_x
                        act_arrow_start_y = act_y - arrow_length

                        self.ax.annotate(
                            "",  # No text
                            xy=(act_x, act_y),  # Arrow tip (actual point)
                            xytext=(act_arrow_start_x, act_arrow_start_y),  # Arrow tail
                            arrowprops=dict(
                                arrowstyle="->",
                                color="green",
                                lw=2,
                                shrinkA=0,
                                shrinkB=0,
                            ),
                            zorder=95,  # Above expected arrows but below current position
                        )

                        # Add actual point label
                        self.ax.text(
                            act_x + 2,  # Slightly offset to the right
                            act_y + 2,  # Slightly offset up
                            f"A{i+1}",
                            color="green",
                            fontweight="bold",
                            fontsize=9,
                            zorder=96,
                        )

                except (ValueError, IndexError):
                    # Skip if we can't parse the coordinates
                    continue

        except Exception as e:
            # Silently fail if there's any issue - don't break the plot
            pass

    def update_laser_position_only(self):
        """Efficiently update only the laser position marker on plot"""
        if not hasattr(self, "laser_marker"):
            return

        # Update laser marker position
        x = self.work_pos["x"]
        y = self.work_pos["y"]
        self.laser_marker.set_data([x], [y])

        # Efficient redraw (no axis rescaling because we only update existing data)
        self.canvas.draw_idle()

    def plot_gcode_toolpath(self, positioning_lines, engraving_lines, label_prefix, ax):
        """Plot G-code toolpath exactly like dxf2laser.py"""
        # Determine colors based on whether it's original or adjusted
        if label_prefix == "Original":
            positioning_color = "g"
            engraving_color = "r"
        else:  # Adjusted
            positioning_color = "b"
            engraving_color = "orange"

        # Plot positioning moves in green/blue
        for line_segment in positioning_lines:
            start, end = line_segment
            ax.plot(
                [start[0], end[0]],
                [start[1], end[1]],
                color=positioning_color,
                linewidth=2,
                alpha=0.8,
            )

        # Plot engraving moves in red/orange
        for line_segment in engraving_lines:
            start, end = line_segment
            ax.plot(
                [start[0], end[0]],
                [start[1], end[1]],
                color=engraving_color,
                linewidth=2,
                alpha=0.8,
            )

    def adjust_gcode(self):
        """Calculate adjustments and modify G-code using 3-point rigid transformation"""
        try:
            # Get 3 reference points from GUI
            if len(self.ref_point_expected_vars) < 3:
                messagebox.showerror("Error", "Need 3 reference points!")
                return

            expected_points = []
            actual_points = []

            for i in range(3):  # Always use exactly 3 points
                exp_x_var, exp_y_var = self.ref_point_expected_vars[i]
                act_x_var, act_y_var = self.ref_point_actual_vars[i]

                exp_x = float(exp_x_var.get())
                exp_y = float(exp_y_var.get())
                act_x = float(act_x_var.get())
                act_y = float(act_y_var.get())

                expected_points.append((exp_x, exp_y))
                actual_points.append((act_x, act_y))

            # Perform 3-point rigid transformation
            self._adjust_gcode_3point_rigid(expected_points, actual_points)

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input values:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Calculation failed:\n{str(e)}")

    def _adjust_gcode_2point(self, expected_points, actual_points):
        """
        Adjust G-code using 2-point transformation (translation + rotation)
        Uses the method from transformtest.py for accuracy
        """
        P1, P2 = np.array(expected_points[0]), np.array(expected_points[1])
        Q1, Q2 = np.array(actual_points[0]), np.array(actual_points[1])

        if not self.original_positioning_lines and not self.original_engraving_lines:
            messagebox.showwarning("Warning", "Please load a G-code file first!")
            return

        # Compute vectors between points
        v_expected = P2 - P1
        v_actual = Q2 - Q1

        # Validate that reference points are not identical
        expected_dist = np.linalg.norm(v_expected)
        actual_dist = np.linalg.norm(v_actual)

        if expected_dist < 0.1:  # Points are too close (< 0.1mm apart)
            messagebox.showerror(
                "Error",
                f"Expected reference points are too close together!\n"
                f"Distance: {expected_dist:.3f}mm\n\n"
                f"Point 1: ({P1[0]:.3f}, {P1[1]:.3f})\n"
                f"Point 2: ({P2[0]:.3f}, {P2[1]:.3f})\n\n"
                f"Please use reference points at least 10mm apart.",
            )
            return

        if actual_dist < 0.1:  # Points are too close (< 0.1mm apart)
            messagebox.showerror(
                "Error",
                f"Actual reference points are too close together!\n"
                f"Distance: {actual_dist:.3f}mm\n\n"
                f"Point 1: ({Q1[0]:.3f}, {Q1[1]:.3f})\n"
                f"Point 2: ({Q2[0]:.3f}, {Q2[1]:.3f})\n\n"
                f"Please use reference points at least 10mm apart.",
            )
            return

        # Compute rotation angle (from expected vector to actual vector)
        angle_expected = np.arctan2(v_expected[1], v_expected[0])
        angle_actual = np.arctan2(v_actual[1], v_actual[0])
        rotation_angle = angle_actual - angle_expected

        # Compute scale factor (optional, for verification)
        scale = actual_dist / expected_dist

        # Rotation matrix
        cos_r = np.cos(rotation_angle)
        sin_r = np.sin(rotation_angle)

        # Compute translation: Q1 = R × P1 + T
        # Therefore: T = Q1 - R × P1
        rotated_P1 = np.array(
            [cos_r * P1[0] - sin_r * P1[1], sin_r * P1[0] + cos_r * P1[1]]
        )
        translation = Q1 - rotated_P1

        # Validate: Apply transformation to P2 and check if it matches Q2
        rotated_P2 = np.array(
            [cos_r * P2[0] - sin_r * P2[1], sin_r * P2[0] + cos_r * P2[1]]
        )
        transformed_P2 = rotated_P2 + translation
        error_P2 = np.linalg.norm(transformed_P2 - Q2)

        # For compatibility with existing transformation code, use center=(tx, ty)
        actual_center = tuple(translation)

        # Apply transformations to line segments
        self.adjusted_positioning_lines = self.apply_transformations_to_lines(
            self.original_positioning_lines, actual_center, rotation_angle
        )
        self.adjusted_engraving_lines = self.apply_transformations_to_lines(
            self.original_engraving_lines, actual_center, rotation_angle
        )

        # Generate adjusted G-code
        self.adjusted_gcode = self.generate_adjusted_gcode(
            self.original_gcode, actual_center, rotation_angle
        )

        # Display results
        results = f"""CALCULATION RESULTS (2-Point Transformation)
========================

Reference Points:
  Point 1:
    Expected: ({P1[0]:.3f}, {P1[1]:.3f}) mm
    Actual:   ({Q1[0]:.3f}, {Q1[1]:.3f}) mm
  
  Point 2:
    Expected: ({P2[0]:.3f}, {P2[1]:.3f}) mm
    Actual:   ({Q2[0]:.3f}, {Q2[1]:.3f}) mm
    Validation Error: {error_P2:.3f} mm
    Status: {'✓ Valid' if error_P2 <= 0.01 else '✗ Error > 0.01mm'}

Transformation:
  Translation: ({translation[0]:.3f}, {translation[1]:.3f}) mm
  Rotation: {np.degrees(rotation_angle):.3f}°
  Scale Factor: {scale:.6f} (for reference only)

Vector Analysis:
  Expected Distance: {np.linalg.norm(v_expected):.3f} mm
  Actual Distance: {np.linalg.norm(v_actual):.3f} mm
  Distance Change: {np.linalg.norm(v_actual) - np.linalg.norm(v_expected):.3f} mm
"""

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, results)

        # Update plot
        self.plot_toolpath()

    def _adjust_gcode_3point_rigid(self, expected_points, actual_points):
        """
        Adjust G-code using 3-point rigid transformation (SVD-based least-squares)
        Computes optimal rotation and translation using Procrustes analysis
        """
        # Convert to numpy arrays (Nx2)
        P = np.array(expected_points)  # Expected (source) points
        Q = np.array(actual_points)  # Actual (target) points

        if not self.original_positioning_lines and not self.original_engraving_lines:
            messagebox.showwarning("Warning", "Please load a G-code file first!")
            return

        # Validate points form a non-degenerate triangle
        if not self._validate_triangle(P) or not self._validate_triangle(Q):
            messagebox.showerror(
                "Error",
                "Reference points must form a valid triangle!\n"
                "Points cannot be collinear or too close together.",
            )
            return

        # Step 1: Center the point sets (compute centroids)
        centroid_P = np.mean(P, axis=0)
        centroid_Q = np.mean(Q, axis=0)

        # Step 2: Center the points
        P_centered = P - centroid_P
        Q_centered = Q - centroid_Q

        # Step 3: Compute rotation using SVD
        # H = P_centered^T * Q_centered
        H = P_centered.T @ Q_centered

        # SVD decomposition
        U, S, Vt = np.linalg.svd(H)

        # Rotation matrix R = V * U^T
        R = Vt.T @ U.T

        # Handle reflection case (ensure proper rotation, not reflection)
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = Vt.T @ U.T

        # Step 4: Compute translation
        # t = centroid_Q - R * centroid_P
        translation = centroid_Q - R @ centroid_P

        # Step 5: Extract rotation angle from 2D rotation matrix
        rotation_angle = np.arctan2(R[1, 0], R[0, 0])

        # Step 6: Compute residual errors for each point
        errors = []
        error_details = []
        for i, (p, q) in enumerate(zip(P, Q)):
            # Transform expected point
            transformed_p = R @ p + translation
            # Calculate error
            error_vec = transformed_p - q
            error_x = error_vec[0]
            error_y = error_vec[1]
            error_dist = np.linalg.norm(error_vec)
            errors.append(error_dist)
            error_details.append(
                {
                    "index": i,
                    "expected": p,
                    "actual": q,
                    "transformed": transformed_p,
                    "error_x": error_x,
                    "error_y": error_y,
                    "error_dist": error_dist,
                }
            )

        # Compute RMS error
        rms_error = np.sqrt(np.mean(np.array(errors) ** 2))
        max_error = np.max(errors)

        # Apply transformations to line segments
        actual_center = tuple(translation)
        self.adjusted_positioning_lines = self.apply_transformations_to_lines(
            self.original_positioning_lines, actual_center, rotation_angle
        )
        self.adjusted_engraving_lines = self.apply_transformations_to_lines(
            self.original_engraving_lines, actual_center, rotation_angle
        )

        # Generate adjusted G-code
        self.adjusted_gcode = self.generate_adjusted_gcode(
            self.original_gcode, actual_center, rotation_angle
        )

        # Display results with error highlighting
        results = f"""CALCULATION RESULTS (3-Point Rigid Transform - SVD)
========================

Transformation:
  Translation: ({translation[0]:.4f}, {translation[1]:.4f}) mm
  Rotation: {np.degrees(rotation_angle):.4f}°

Reference Point Errors:
"""

        # Add error details for each point (with red highlighting for errors > 0.1mm)
        for detail in error_details:
            i = detail["index"]
            p = detail["expected"]
            q = detail["actual"]
            error_x = detail["error_x"]
            error_y = detail["error_y"]
            error_dist = detail["error_dist"]

            # Mark high errors
            error_marker = " ⚠ HIGH ERROR" if error_dist > 0.1 else ""

            results += f"""
  Point {i+1}:
    Expected:     ({p[0]:.4f}, {p[1]:.4f}) mm
    Actual:       ({q[0]:.4f}, {q[1]:.4f}) mm
    Error X:      {error_x:+.4f} mm
    Error Y:      {error_y:+.4f} mm
    Error Distance: {error_dist:.4f} mm{error_marker}
"""

        results += f"""
Accuracy Metrics:
  RMS Error: {rms_error:.4f} mm
  Max Error: {max_error:.4f} mm
  Status: {'✓ Excellent' if max_error <= 0.05 else '✓ Good' if max_error <= 0.1 else '✗ Poor - Check alignment'}
"""

        # Use tags for red text highlighting
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, results)

        # Highlight high errors in red
        content = self.results_text.get(1.0, tk.END)
        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            if "⚠ HIGH ERROR" in line or (
                "Error Distance:" in line
                and any(f"{e:.4f}" in line for e in errors if e > 0.1)
            ):
                # Find and tag the error distance line
                start_idx = f"{line_num}.0"
                end_idx = f"{line_num}.end"
                self.results_text.tag_add("high_error", start_idx, end_idx)

        # Configure red text tag
        self.results_text.tag_config("high_error", foreground="red")

        # Update plot
        self.plot_toolpath()

    def _validate_triangle(self, points):
        """Validate that 3 points form a valid non-degenerate triangle"""
        if len(points) != 3:
            return False

        P = np.array(points)

        # Check if points are too close together
        for i in range(3):
            for j in range(i + 1, 3):
                dist = np.linalg.norm(P[i] - P[j])
                if dist < 1.0:  # Points must be at least 1mm apart
                    return False

        # Check if points are collinear (triangle area too small)
        # Area = 0.5 * |det([[x1, y1, 1], [x2, y2, 1], [x3, y3, 1]])|
        area_matrix = np.column_stack([P, np.ones(3)])
        area = 0.5 * abs(np.linalg.det(area_matrix))

        if area < 10.0:  # Triangle area must be at least 10mm²
            return False

        return True

    def save_adjusted_gcode(self):
        """Save the adjusted G-code with updated reference points to a file"""
        if not hasattr(self, "adjusted_gcode") or not self.adjusted_gcode:
            messagebox.showwarning(
                "Warning", "No adjusted G-code to save. Please adjust the G-code first."
            )
            return

        try:
            # Generate filename with _adjusted suffix and timestamp
            if hasattr(self, "original_file_path"):
                filename_only = os.path.basename(self.original_file_path)
                base_name, extension = os.path.splitext(filename_only)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                initial_name = f"{base_name}_adjusted_{timestamp}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                initial_name = f"adjusted_gcode_{timestamp}"

            # Ask user for save location
            file_path = filedialog.asksaveasfilename(
                initialfile=initial_name,
                defaultextension=".nc",
                filetypes=[
                    ("G-code files", "*.nc"),
                    ("G-code files", "*.gcode"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*"),
                ],
                title="Save Adjusted G-code",
            )

            if not file_path:
                return  # User cancelled

            # Get actual reference point values
            actual_points = []
            for i in range(2):  # Always 2 points
                act_x_var, act_y_var = self.ref_point_actual_vars[i]
                act_x = float(act_x_var.get())
                act_y = float(act_y_var.get())
                actual_points.append((act_x, act_y))

            # Update reference point comments in the G-code
            updated_gcode = self._update_reference_points_in_gcode(
                self.adjusted_gcode, actual_points
            )

            # Write to file
            with open(file_path, "w") as f:
                f.write(updated_gcode)

            messagebox.showinfo(
                "Success",
                f"Adjusted G-code saved to:\n{file_path}\n\n"
                f"Reference points updated to actual values:\n"
                f"Point 1: ({actual_points[0][0]:.4f}, {actual_points[0][1]:.4f})\n"
                f"Point 2: ({actual_points[1][0]:.4f}, {actual_points[1][1]:.4f})",
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save adjusted G-code:\n{str(e)}")

    def _update_reference_points_in_gcode(self, gcode, actual_points):
        """Update reference point comments in G-code with actual values"""
        lines = gcode.split("\n")
        updated_lines = []

        ref1_updated = False
        ref2_updated = False

        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            # Check if this is a reference point comment
            if line_stripped.startswith(";") and "reference_point" in line_lower:
                # Extract the point number (case-insensitive check)
                if "reference_point1" in line_lower:
                    # Update point 1
                    new_line = f"; reference_point1 = ({actual_points[0][0]:.4f}, {actual_points[0][1]:.4f})"
                    updated_lines.append(new_line)
                    ref1_updated = True
                elif "reference_point2" in line_lower:
                    # Update point 2
                    new_line = f"; reference_point2 = ({actual_points[1][0]:.4f}, {actual_points[1][1]:.4f})"
                    updated_lines.append(new_line)
                    ref2_updated = True
                else:
                    # Keep other reference point comments as-is
                    updated_lines.append(line)
            else:
                # Keep all other lines unchanged
                updated_lines.append(line)

        return "\n".join(updated_lines)

    def apply_transformations_to_lines(self, line_segments, center, rotation_angle):
        """Apply translation and rotation to line segments"""
        adjusted_lines = []

        for line_segment in line_segments:
            start, end = line_segment
            # Transform start point
            start_adj = self.apply_transformations([start], center, rotation_angle)[0]
            # Transform end point
            end_adj = self.apply_transformations([end], center, rotation_angle)[0]
            adjusted_lines.append([start_adj, end_adj])

        return adjusted_lines

    def apply_transformations(self, coords, center, rotation_angle):
        """Apply translation and rotation to coordinates"""
        adjusted = []

        for x, y in coords:
            # Apply rotation first (rotate expected coordinates to match actual orientation)
            cos_r = np.cos(rotation_angle)
            sin_r = np.sin(rotation_angle)

            rx = x * cos_r - y * sin_r
            ry = x * sin_r + y * cos_r

            # Then translate to move rotated expected left point to actual left point (0,0)
            # We need to add the rotated expected left point to move it to origin
            # and then add the actual left point (which is 0,0)
            tx = rx + center[0]
            ty = ry + center[1]

            adjusted.append((tx, ty))

        return adjusted

    def generate_adjusted_gcode(self, original_gcode, center, rotation_angle):
        """Generate adjusted G-code with new coordinates, handling arcs"""
        lines = original_gcode.split("\n")
        adjusted_lines = []

        current_x = 0.0
        current_y = 0.0
        last_x = 0.0
        last_y = 0.0

        for line in lines:
            adjusted_line = line
            line_upper = line.upper().strip()

            # Skip empty lines (don't include them in adjusted G-code)
            if not line_upper:
                continue

            # Keep comments but skip processing them
            if line_upper.startswith(";") or line_upper.startswith("("):
                adjusted_lines.append(adjusted_line)
                continue

            # Apply transformations based on move type
            if line_upper.startswith("G0") or line_upper.startswith("G1"):
                adjusted_line = self.transform_linear_move(line, center, rotation_angle)
                adjusted_lines.append(adjusted_line)
            elif line_upper.startswith("G2") or line_upper.startswith("G3"):
                adjusted_line = self.transform_arc_move(
                    line, center, rotation_angle, last_x, last_y
                )
                adjusted_lines.append(adjusted_line)
            else:
                adjusted_lines.append(adjusted_line)

            # Update position tracking
            x_match = re.search(r"X([+-]?\d+\.?\d*)", line_upper)
            y_match = re.search(r"Y([+-]?\d+\.?\d*)", line_upper)

            if x_match:
                last_x = float(x_match.group(1))
            if y_match:
                last_y = float(y_match.group(1))

        return "\n".join(adjusted_lines)

    def transform_linear_move(self, line, center, rotation_angle):
        """Transform coordinates in a linear G-code move (G0/G1)"""
        # Extract coordinates
        x_match = re.search(r"X([+-]?\d+\.?\d*)", line)
        y_match = re.search(r"Y([+-]?\d+\.?\d*)", line)

        if not x_match and not y_match:
            return line  # No coordinates to transform

        # Get current coordinates
        current_x = float(x_match.group(1)) if x_match else 0.0
        current_y = float(y_match.group(1)) if y_match else 0.0

        # Apply transformations
        adjusted_x, adjusted_y = self.apply_transformations(
            [(current_x, current_y)], center, rotation_angle
        )[0]

        # Replace coordinates in the line
        adjusted_line = line
        if x_match:
            adjusted_line = re.sub(
                r"X[+-]?\d+\.?\d*", f"X{adjusted_x:.3f}", adjusted_line
            )
        if y_match:
            adjusted_line = re.sub(
                r"Y[+-]?\d+\.?\d*", f"Y{adjusted_y:.3f}", adjusted_line
            )

        return adjusted_line

    def transform_arc_move(self, line, center, rotation_angle, last_x, last_y):
        """Transform coordinates in an arc G-code move (G2/G3)"""
        # Extract coordinates
        x_match = re.search(r"X([+-]?\d+\.?\d*)", line)
        y_match = re.search(r"Y([+-]?\d+\.?\d*)", line)
        i_match = re.search(r"I([+-]?\d+\.?\d*)", line)
        j_match = re.search(r"J([+-]?\d+\.?\d*)", line)

        if not (x_match or y_match) and not (i_match or j_match):
            return line  # No coordinates to transform

        # Get current coordinates
        current_x = float(x_match.group(1)) if x_match else last_x
        current_y = float(y_match.group(1)) if y_match else last_y
        i_offset = float(i_match.group(1)) if i_match else 0.0
        j_offset = float(j_match.group(1)) if j_match else 0.0

        # Transform the start point (last position)
        adjusted_start_x, adjusted_start_y = self.apply_transformations(
            [(last_x, last_y)], center, rotation_angle
        )[0]

        # Transform the end point
        adjusted_end_x, adjusted_end_y = self.apply_transformations(
            [(current_x, current_y)], center, rotation_angle
        )[0]

        # Transform the arc center
        arc_center_x = last_x + i_offset
        arc_center_y = last_y + j_offset
        adjusted_center_x, adjusted_center_y = self.apply_transformations(
            [(arc_center_x, arc_center_y)], center, rotation_angle
        )[0]

        # Calculate new I,J offsets relative to adjusted start point
        new_i_offset = adjusted_center_x - adjusted_start_x
        new_j_offset = adjusted_center_y - adjusted_start_y

        # Round X/Y to 3 decimals FIRST, then validate arc with rounded values
        # This ensures the validation matches what GRBL will receive
        adjusted_end_x_rounded = round(adjusted_end_x, 3)
        adjusted_end_y_rounded = round(adjusted_end_y, 3)

        # Validate and correct arc radius AFTER rounding to prevent GRBL error:24
        # GRBL checks that distance(start, center) == distance(end, center)
        radius_start = np.sqrt(new_i_offset**2 + new_j_offset**2)

        # Calculate radius from rounded end point
        i_from_end = adjusted_center_x - adjusted_end_x_rounded
        j_from_end = adjusted_center_y - adjusted_end_y_rounded
        radius_end = np.sqrt(i_from_end**2 + j_from_end**2)

        # Check if radii match within tolerance
        radius_error = abs(radius_start - radius_end)
        if radius_error > 0.001:  # More than 0.001mm error (very tight tolerance)
            # Adjust end point to match the radius from start point
            # This keeps the arc valid while minimizing position error
            if radius_start > 0:
                # Calculate unit vector from center to rounded end point
                dx = adjusted_end_x_rounded - adjusted_center_x
                dy = adjusted_end_y_rounded - adjusted_center_y
                distance = np.sqrt(dx**2 + dy**2)

                if distance > 0:
                    # Normalize and scale to exact radius
                    adjusted_end_x_rounded = (
                        adjusted_center_x + (dx / distance) * radius_start
                    )
                    adjusted_end_y_rounded = (
                        adjusted_center_y + (dy / distance) * radius_start
                    )

                    # Calculate actual adjustment
                    adjustment = np.sqrt(
                        (adjusted_end_x_rounded - adjusted_end_x) ** 2
                        + (adjusted_end_y_rounded - adjusted_end_y) ** 2
                    )

                    # Log correction details
                    print(
                        f"Arc corrected: radius_error={radius_error:.6f}mm, endpoint adjusted by {adjustment:.6f}mm"
                    )

                    if adjustment > 0.05:
                        print(
                            f"WARNING: Arc correction {adjustment:.3f}mm exceeds 0.05mm threshold!"
                        )

        # Use corrected rounded values for output
        adjusted_end_x = adjusted_end_x_rounded
        adjusted_end_y = adjusted_end_y_rounded

        # Replace coordinates in the line with 3 decimal precision
        # Strip trailing zeros from I/J to avoid parser issues
        adjusted_line = line
        if x_match:
            adjusted_line = re.sub(
                r"X[+-]?\d+\.?\d*", f"X{adjusted_end_x:.3f}", adjusted_line
            )
        if y_match:
            adjusted_line = re.sub(
                r"Y[+-]?\d+\.?\d*", f"Y{adjusted_end_y:.3f}", adjusted_line
            )
        if i_match:
            # Format with 4 decimals and strip trailing zeros
            i_formatted = f"{new_i_offset:.4f}".rstrip("0").rstrip(".")
            adjusted_line = re.sub(r"I[+-]?\d+\.?\d*", f"I{i_formatted}", adjusted_line)
        if j_match:
            # Format with 4 decimals and strip trailing zeros
            j_formatted = f"{new_j_offset:.4f}".rstrip("0").rstrip(".")
            adjusted_line = re.sub(r"J[+-]?\d+\.?\d*", f"J{j_formatted}", adjusted_line)

        return adjusted_line

    def refresh_com_ports(self):
        """Scan and populate COM port dropdown"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]

        self.com_port_combo["values"] = port_list

        if port_list:
            if not self.com_port_var.get() or self.com_port_var.get() not in port_list:
                self.com_port_combo.current(0)
        else:
            self.com_port_var.set("")

    def toggle_connection(self):
        """Connect or disconnect from the GRBL controller"""
        # Check button text for more reliable state (in case internal state is inconsistent)
        button_text = self.connect_button.cget("text")

        if button_text == "Disconnect" or self.is_connected:
            self.disconnect_grbl()
        else:
            self.connect_grbl()

    def connect_grbl(self):
        """Connect to GRBL controller"""
        com_port = self.com_port_var.get()

        if not com_port:
            messagebox.showerror("Error", "Please select a COM port!")
            return

        try:
            # Open serial connection (GRBL typically uses 115200 baud)
            self.serial_connection = serial.Serial(
                port=com_port, baudrate=115200, timeout=2, write_timeout=2
            )

            # Wait for GRBL to initialize
            self.root.after(2000, self.complete_connection)

            # Disable COM port selection while connected
            self.com_port_combo.config(state="disabled")
            self.status_label.config(text="Connecting...", foreground="orange")

        except serial.SerialException as e:
            messagebox.showerror(
                "Connection Error", f"Failed to connect to {com_port}:\n{str(e)}"
            )
            self.serial_connection = None

    def complete_connection(self):
        """Complete the connection after GRBL initializes"""
        if self.serial_connection and self.serial_connection.is_open:
            # Flush any startup messages
            self.serial_connection.reset_input_buffer()

            self.is_connected = True
            self.connect_button.config(text="Disconnect")
            self.status_label.config(text="Connected", foreground="green")
            self.grbl_state = "Connecting"
            self.update_state_display()

            # Immediately query status to update GRBL state
            try:
                self.serial_connection.write(b"?")
            except:
                pass

            # Initialize laser state to OFF
            self.laser_on = False
            self.laser_button.config(text="Laser OFF")

            # Start serial reader thread with disconnect callback
            self.serial_reader_thread = SerialReaderThread(
                self.serial_connection,
                self.response_queue,
                disconnect_callback=self.handle_usb_disconnect,
            )
            self.serial_reader_thread.start()

            # Start processing responses from queue
            self.start_response_processing()

            # Query all GRBL settings
            self.query_all_grbl_settings()

            # Set $10=3 to report both MPos and WPos
            self.send_gcode_async("$10=3")

            # Update homing enabled flag from settings (will be set when settings query completes)

            # Start periodic position updates (now just sends ? commands)
            self.start_status_updates()

        else:
            self.disconnect_grbl()
            messagebox.showerror("Error", "Connection timed out")

    def handle_usb_disconnect(self):
        """Handle unexpected USB disconnect - called from serial thread"""
        # Prevent multiple simultaneous disconnect handlers
        if not self.is_connected:
            return

        print("\n⚠️ USB DISCONNECT DETECTED ⚠️")

        # Must use root.after to update GUI from thread safely
        def disconnect_ui():
            # Check again if already disconnected
            if not self.is_connected:
                return

            # Stop any ongoing operations first
            if self.streaming:
                print("Stopping streaming due to disconnect...")
                self.stop_streaming()

            # Stop position updates
            if self.status_update_id:
                try:
                    self.root.after_cancel(self.status_update_id)
                except:
                    pass
                self.status_update_id = None

            # Stop status updates
            if self.status_update_id:
                try:
                    self.root.after_cancel(self.status_update_id)
                except:
                    pass
                self.status_update_id = None

            # Stop processing responses
            self.processing_responses = False

            # Stop serial reader thread
            if self.serial_reader_thread and self.serial_reader_thread.is_alive():
                self.serial_reader_thread.stop()
                self.serial_reader_thread.join(timeout=0.5)
            self.serial_reader_thread = None

            # Clear response queue
            while not self.response_queue.empty():
                try:
                    self.response_queue.get_nowait()
                except queue.Empty:
                    break

            # Update connection state AFTER stopping threads
            self.is_connected = False

            # Update UI
            self.connect_button.config(text="Connect")
            self.status_label.config(text="Disconnected - USB Lost", foreground="red")
            self.com_port_combo.config(state="readonly")
            self.grbl_state = "Disconnected"
            self.update_state_display()

            # Update laser state
            self.laser_on = False
            self.laser_button.config(text="Laser OFF")

            # Disable control buttons
            if hasattr(self, "stop_button"):
                self.stop_button.config(state="disabled")
            if hasattr(self, "next_step_button"):
                self.next_step_button.config(state="disabled")

            # Close progress window if exists
            if hasattr(self, "progress_window"):
                try:
                    if self.progress_window.winfo_exists():
                        self.progress_window.destroy()
                except:
                    pass

            # Clear position display
            self.work_pos_label.config(text="X: 0.00  Y: 0.00  Z: 0.00")
            self.machine_pos_label.config(text="X: 0.00  Y: 0.00  Z: 0.00")

            # Close serial connection properly
            if self.serial_connection:
                try:
                    if self.serial_connection.is_open:
                        self.serial_connection.close()
                    print("Serial connection closed")
                except Exception as e:
                    print(f"Error closing serial: {e}")
            self.serial_connection = None

            # Show alert to user
            messagebox.showerror(
                "USB Disconnected",
                "⚠️ USB CONNECTION LOST ⚠️\n\n"
                "The GRBL controller has been disconnected.\n\n"
                "Possible causes:\n"
                "- USB cable unplugged\n"
                "- Power loss to controller\n"
                "- USB communication error\n\n"
                "⚠️ VERIFY LASER IS OFF\n"
                "⚠️ Machine position has been lost\n\n"
                "Reconnect and rehome before continuing.",
            )

        # Schedule UI update in main thread
        self.root.after(0, disconnect_ui)

    def disconnect_grbl(self):
        """Disconnect from GRBL controller"""
        # If already disconnected, just update UI to be consistent
        if not self.is_connected and not self.serial_connection:
            # Force UI update in case of inconsistent state
            try:
                self.connect_button.config(text="Connect")
                self.status_label.config(text="Disconnected", foreground="gray")
                self.grbl_state = "Disconnected"
                self.update_state_display()
                self.com_port_combo.config(state="readonly")
            except:
                pass
            return

        # Stop position updates first
        if self.status_update_id:
            try:
                self.root.after_cancel(self.status_update_id)
            except:
                pass
            self.status_update_id = None

        # Update state immediately to prevent new commands
        was_connected = self.is_connected
        self.is_connected = False

        # Stop processing responses
        self.processing_responses = False

        # Stop serial reader thread
        if self.serial_reader_thread and self.serial_reader_thread.is_alive():
            self.serial_reader_thread.stop()
            self.serial_reader_thread.join(timeout=1.0)
        self.serial_reader_thread = None

        # Clear response queue
        while not self.response_queue.empty():
            try:
                self.response_queue.get_nowait()
            except queue.Empty:
                break

        # Turn off laser if it's on
        if self.laser_on:
            self.laser_on = False
            self.laser_button.config(text="Laser OFF")

        if self.serial_connection:
            try:
                # Only try to send M5 if we had a good connection
                if was_connected and self.serial_connection.is_open:
                    try:
                        self.serial_connection.write(b"M5\n")
                        time.sleep(0.1)  # Give it time to send
                    except:
                        pass
                self.serial_connection.close()
            except Exception as e:
                print(f"Error closing serial connection: {e}")

        self.serial_connection = None

        # Update UI widgets only if they still exist
        try:
            if self.connect_button.winfo_exists():
                self.connect_button.config(text="Connect")
        except:
            pass

        try:
            if self.status_label.winfo_exists():
                self.status_label.config(text="Disconnected", foreground="red")
        except:
            pass

        # Update GRBL state
        self.grbl_state = "Disconnected"
        try:
            if self.grbl_state_label.winfo_exists():
                self.update_state_display()
        except:
            pass

        try:
            if self.com_port_combo.winfo_exists():
                self.com_port_combo.config(state="readonly")
        except:
            pass

        # Clear position display
        try:
            if self.work_pos_label.winfo_exists():
                self.work_pos_label.config(text="X: 0.00  Y: 0.00  Z: 0.00")
        except:
            pass

        try:
            if self.machine_pos_label.winfo_exists():
                self.machine_pos_label.config(text="X: 0.00  Y: 0.00  Z: 0.00")
        except:
            pass

    def cleanup(self):
        """Clean up resources before closing"""
        # Unbind mousewheel
        if hasattr(self, "left_canvas"):
            self.left_canvas.unbind_all("<MouseWheel>")

        if self.is_connected:
            self.disconnect_grbl()

    def send_gcode(self, command):
        """Send a G-code command to GRBL and wait for response"""
        if not self.is_connected or not self.serial_connection:
            return None

        # Check if serial port is still open
        try:
            if not self.serial_connection.is_open:
                return None
        except:
            return None

        try:
            # Send command
            self.serial_connection.write(f"{command}\n".encode())

            # Wait for response
            response = ""
            start_time = datetime.now()
            while (datetime.now() - start_time).total_seconds() < 2:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode().strip()
                    response += line + "\n"
                    if line in ["ok", "error"]:
                        break

            return response
        except (serial.SerialException, OSError, PermissionError) as e:
            print(f"Serial communication lost: {e}")
            self.root.after(10, self.disconnect_grbl)
            return None
        except Exception as e:
            print(f"Error sending G-code: {e}")
            return None

    # query_position() removed - now using threaded serial with async status queries

    def parse_status_response(self, response):
        """Parse GRBL status response and update position"""
        try:
            # GRBL status format: <Idle|MPos:0.000,0.000,0.000|FS:0,0|WCO:0.000,0.000,0.000>
            if response.startswith("<") and response.endswith(">"):
                parts = response[1:-1].split("|")

                # Extract GRBL state (first part) - update immediately (lightweight)
                if parts:
                    self.grbl_state = parts[0]
                    self.update_state_display()

                # Parse position data
                position_changed = False
                for part in parts:
                    if part.startswith("MPos:"):
                        coords = part[5:].split(",")
                        if len(coords) >= 3:
                            self.machine_pos["x"] = float(coords[0])
                            self.machine_pos["y"] = float(coords[1])
                            self.machine_pos["z"] = float(coords[2])
                            position_changed = True

                    elif part.startswith("WPos:"):
                        coords = part[5:].split(",")
                        if len(coords) >= 3:
                            self.work_pos["x"] = float(coords[0])
                            self.work_pos["y"] = float(coords[1])
                            self.work_pos["z"] = float(coords[2])
                            position_changed = True

                    elif part.startswith("WCO:"):
                        coords = part[4:].split(",")
                        if len(coords) >= 3:
                            self.wco["x"] = float(coords[0])
                            self.wco["y"] = float(coords[1])
                            self.wco["z"] = float(coords[2])
                            position_changed = True

                # Calculate missing positions
                if "MPos:" in response and "WPos:" not in response:
                    # Calculate WPos from MPos - WCO
                    self.work_pos["x"] = self.machine_pos["x"] - self.wco["x"]
                    self.work_pos["y"] = self.machine_pos["y"] - self.wco["y"]
                    self.work_pos["z"] = self.machine_pos["z"] - self.wco["z"]
                    position_changed = True
                elif "WPos:" in response and "MPos:" not in response:
                    # Calculate MPos from WPos + WCO
                    self.machine_pos["x"] = self.work_pos["x"] + self.wco["x"]
                    self.machine_pos["y"] = self.work_pos["y"] + self.wco["y"]
                    self.machine_pos["z"] = self.work_pos["z"] + self.wco["z"]
                    position_changed = True

                # Batch position display updates for better performance
                if position_changed and not self.position_update_pending:
                    self.position_update_pending = True
                    # Schedule batched update (100ms for labels)
                    self.root.after(100, self._flush_position_update)

                # Update execution path if executing (don't update plot - too slow!)
                if self.is_executing:
                    current_pos = (self.work_pos["x"], self.work_pos["y"])
                    # Always add position if changed
                    if (
                        not self.execution_path
                        or current_pos != self.execution_path[-1]
                    ):
                        self.execution_path.append(current_pos)

        except Exception as e:
            print(f"Error parsing status: {e}")

    def update_laser_marker_and_plot(self):
        """Update laser marker on plot and redraw"""
        if hasattr(self, "laser_marker"):
            self.laser_marker.set_data([self.work_pos["x"]], [self.work_pos["y"]])
            self.canvas.draw()
            self.canvas.flush_events()

    def _flush_position_update(self):
        """Flush pending position display update (batched for performance)"""
        self.position_update_pending = False
        self.update_position_display()

    def update_position_display(self):
        """Update position labels and laser marker on plot"""
        # Don't update plot during execution/streaming - huge performance win
        # Only update position labels (fast)
        if self.is_executing or self.streaming:
            # Fast path: only update labels, skip expensive plot updates
            self.work_pos_label.config(
                text=f"X: {self.work_pos['x']:6.2f}  Y: {self.work_pos['y']:6.2f}  Z: {self.work_pos['z']:6.2f}"
            )
            self.machine_pos_label.config(
                text=f"X: {self.machine_pos['x']:6.2f}  Y: {self.machine_pos['y']:6.2f}  Z: {self.machine_pos['z']:6.2f}"
            )
            return

        # Slow path: update labels and plot (only when idle)
        self.work_pos_label.config(
            text=f"X: {self.work_pos['x']:6.2f}  Y: {self.work_pos['y']:6.2f}  Z: {self.work_pos['z']:6.2f}"
        )
        self.machine_pos_label.config(
            text=f"X: {self.machine_pos['x']:6.2f}  Y: {self.machine_pos['y']:6.2f}  Z: {self.machine_pos['z']:6.2f}"
        )

        # Update laser position marker on plot if it exists
        if hasattr(self, "laser_marker"):
            self.laser_marker.set_data([self.work_pos["x"]], [self.work_pos["y"]])

            # Auto-scale plot if laser moves outside current view (only when not executing and auto-scale enabled)
            need_redraw = False
            if self.auto_scale_enabled:
                xlim = self.ax.get_xlim()
                ylim = self.ax.get_ylim()
                x_pos = self.work_pos["x"]
                y_pos = self.work_pos["y"]

                # Check if position is outside current view
                margin = 10  # mm margin around position

                # If position is outside view, EXPAND the view to include it
                # Don't shrink the view to just the position
                if x_pos < xlim[0]:
                    new_xlim = (x_pos - margin, xlim[1])
                    self.ax.set_xlim(new_xlim)
                    need_redraw = True
                elif x_pos > xlim[1]:
                    new_xlim = (xlim[0], x_pos + margin)
                    self.ax.set_xlim(new_xlim)
                    need_redraw = True

                if y_pos < ylim[0]:
                    new_ylim = (y_pos - margin, ylim[1])
                    self.ax.set_ylim(new_ylim)
                    need_redraw = True
                elif y_pos > ylim[1]:
                    new_ylim = (ylim[0], y_pos + margin)
                    self.ax.set_ylim(new_ylim)
                    need_redraw = True

            # Only redraw if needed (throttle to avoid excessive redraws)
            # Throttle: redraw at most every 500ms during execution, every 200ms when idle
            import time

            current_time = time.time()
            min_redraw_interval = 0.5 if self.is_executing else 0.2

            if (
                need_redraw
                or (current_time - self._last_plot_update) > min_redraw_interval
            ):
                self._last_plot_update = current_time
                self.canvas.draw_idle()

    def update_state_display(self):
        """Update GRBL state label with color coding"""
        state_colors = {
            "Idle": "green",
            "Run": "blue",
            "Hold": "orange",
            "Alarm": "red",
            "Home": "purple",
            "Check": "cyan",
            "Door": "orange",
            "Error": "red",
            "Disconnected": "gray",
        }
        color = state_colors.get(self.grbl_state, "black")
        self.grbl_state_label.config(text=f"State: {self.grbl_state}", foreground=color)

    def toggle_auto_scale(self):
        """Toggle auto-scale behavior for laser position tracking"""
        self.auto_scale_enabled = self.auto_scale_var.get()
        if self.auto_scale_enabled:
            print("Auto-scale to laser position: ENABLED")
        else:
            print("Auto-scale to laser position: DISABLED")

    def log_sent_command(self, command):
        """Log a command sent to GRBL"""
        if not self.log_enabled_var.get():
            return

        # Filter out status queries unless explicitly enabled
        if command == "?" and not self.log_status_queries:
            return

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        entry = {"time": timestamp, "direction": "sent", "message": command}
        self.comm_log_entries.append(entry)

        # Trim log if too large
        if len(self.comm_log_entries) > self.comm_log_max_lines:
            self.comm_log_entries.pop(0)

        # Update display
        self.append_to_log(entry)

    def log_received_response(self, response):
        """Log a response received from GRBL"""
        if not self.log_enabled_var.get():
            return

        # Filter out status responses unless explicitly enabled
        if (
            response.startswith("<")
            and response.endswith(">")
            and not self.log_status_queries
        ):
            return

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Determine if this is an error
        is_error = "error" in response.lower() or "alarm" in response.lower()

        entry = {
            "time": timestamp,
            "direction": "received",
            "message": response,
            "is_error": is_error,
        }
        self.comm_log_entries.append(entry)

        # Trim log if too large
        if len(self.comm_log_entries) > self.comm_log_max_lines:
            self.comm_log_entries.pop(0)

        # Update display
        self.append_to_log(entry)

    def append_to_log(self, entry):
        """Buffer log entry for batched update (much faster than immediate update)"""
        # Add to buffer instead of immediate GUI update
        self.log_update_buffer.append(entry)

        # Schedule batched update if not already scheduled
        if self.log_update_timer is None:
            self.log_update_timer = self.root.after(50, self.flush_log_buffer)

    def flush_log_buffer(self):
        """Flush all buffered log entries to GUI in one batch"""
        self.log_update_timer = None

        if not self.log_update_buffer:
            return

        # Batch ALL updates in single state transition (MUCH faster)
        self.comm_log_text.config(state=tk.NORMAL)

        # Trim old lines if widget gets too large (check once per batch)
        line_count = int(self.comm_log_text.index("end-1c").split(".")[0])
        if line_count > self.comm_log_max_lines:
            # Delete oldest 20% of lines to avoid frequent trimming
            lines_to_delete = int(self.comm_log_max_lines * 0.2)
            self.comm_log_text.delete("1.0", f"{lines_to_delete}.0")

        # Insert all buffered entries at once
        for entry in self.log_update_buffer:
            # Build the line to insert
            line_parts = []

            # Add timestamp if enabled
            if self.log_timestamp_var.get():
                line_parts.append((f"[{entry['time']}] ", "timestamp"))

            # Add direction indicator and message
            if entry["direction"] == "sent":
                line_parts.append(("→ ", "sent"))
                line_parts.append((f"{entry['message']}\n", "sent"))
            else:
                if entry.get("is_error", False):
                    line_parts.append(("← ", "error"))
                    line_parts.append((f"{entry['message']}\n", "error"))
                else:
                    line_parts.append(("← ", "received"))
                    line_parts.append((f"{entry['message']}\n", "received"))

            # Insert all parts for this entry
            for text, tag in line_parts:
                self.comm_log_text.insert(tk.END, text, tag)

        # Clear buffer
        self.log_update_buffer.clear()

        self.comm_log_text.config(state=tk.DISABLED)

        # Auto-scroll to bottom if enabled (once per batch)
        if self.log_autoscroll_var.get():
            self.comm_log_text.see(tk.END)

    def clear_comm_log(self):
        """Clear the communication log"""
        self.comm_log_entries.clear()
        self.comm_log_text.config(state=tk.NORMAL)
        self.comm_log_text.delete(1.0, tk.END)
        self.comm_log_text.config(state=tk.DISABLED)

    def toggle_logging(self):
        """Toggle logging on/off"""
        self.comm_log_enabled = self.log_enabled_var.get()

    def toggle_status_query_logging(self):
        """Toggle status query logging on/off"""
        self.log_status_queries = self.log_status_queries_var.get()

    def refresh_log_display(self):
        """Refresh the entire log display (for timestamp toggle)"""
        self.comm_log_text.config(state=tk.NORMAL)
        self.comm_log_text.delete(1.0, tk.END)

        for entry in self.comm_log_entries:
            self.append_to_log(entry)

        self.comm_log_text.config(state=tk.DISABLED)

    def _is_moving(self):
        """Check if GRBL is actually moving based on state"""
        # GRBL states that indicate motion
        moving_states = ["Run", "Jog", "Hold"]
        return self.grbl_state in moving_states

    def _validate_gcode_command(self, command):
        """Validate G-code command syntax before sending to GRBL"""
        if not command or not command.strip():
            return False

        # Remove comments and whitespace
        cmd = command.split(";")[0].strip().upper()
        if not cmd:
            return True  # Empty command after comment removal is OK

        # Check for invalid parameter combinations in arc commands
        # Use word boundary checks to avoid matching G20/G21
        import re

        if re.search(r"\bG2\b", cmd) or re.search(r"\bG3\b", cmd):  # Arc commands
            # Note: F (feedrate) is modal in GRBL - it's NOT required on every arc command
            # Only the first arc needs F, subsequent arcs use the previous F value

            # Arc commands should have I and J parameters (or R parameter)
            has_ij = "I" in cmd or "J" in cmd
            has_r = "R" in cmd

            if not has_ij and not has_r:
                print(
                    f"Warning: G2/G3 arc command missing I/J or R parameters: {command}"
                )
                # Don't reject - let GRBL decide if it's valid

        # Check for invalid feed rates
        if "F" in cmd:
            try:
                # Extract F value and validate it's reasonable
                import re

                f_match = re.search(r"F(\d+(?:\.\d+)?)", cmd)
                if f_match:
                    f_value = float(f_match.group(1))
                    if f_value < 0 or f_value > 10000:  # Reasonable feed rate range
                        print(
                            f"Warning: Feed rate F{f_value} seems unreasonable: {command}"
                        )
            except:
                pass  # If we can't parse F, let GRBL handle it

        # Check for invalid coordinates
        for axis in ["X", "Y", "Z"]:
            if axis in cmd:
                try:
                    import re

                    coord_match = re.search(f"{axis}(-?\\d+(?:\\.\\d+)?)", cmd)
                    if coord_match:
                        coord_value = float(coord_match.group(1))
                        # Check for reasonable coordinate ranges (adjust as needed)
                        if abs(coord_value) > 1000:  # 1000mm max travel
                            print(
                                f"Warning: {axis} coordinate {coord_value} seems large: {command}"
                            )
                except:
                    pass  # If we can't parse coordinate, let GRBL handle it

        return True

    def _process_command_queue(self):
        """Process manual commands from the queue (serial execution)"""
        # Only for manual commands - use waiting_for_ok to ensure serial execution
        if not self.manual_command_queue or self.waiting_for_ok:
            return

        # Send next command from manual queue
        command = self.manual_command_queue.pop(0)

        # Log the sent command
        self.log_sent_command(command)

        # Track command time for smart polling
        import time

        self.last_command_time = time.time()

        # Send the command
        self.serial_connection.write((command + "\n").encode())

        # Track this command (for manual commands, we don't use byte counting)
        # Just set a flag to wait for ok
        self.waiting_for_ok = True

        # Track laser state based on M commands
        command_upper = command.upper().strip()
        if command_upper.startswith("M5") or command_upper == "M5":
            self.laser_on = False
            self.laser_button.config(text="Laser OFF")
        elif command_upper.startswith("M3") or command_upper.startswith("M4"):
            self.laser_on = True
            self.laser_button.config(text="Laser ON")

    def _send_streaming_command(self, command):
        """Send a streaming command directly (bypasses queue for speed)"""
        if not self.is_connected or not self.serial_connection:
            return False

        try:
            # Validate command
            if not self._validate_gcode_command(command):
                print(f"Invalid G-code command rejected: {command}")
                return False

            # Convert arc R-format to I/J-format before sending
            converted_command = self.convert_arc_r_to_ij(
                command, self.current_modal_x, self.current_modal_y
            )

            # Update modal position after conversion
            self._update_modal_position(converted_command)

            # Log the sent command (log the converted command)
            self.log_sent_command(converted_command)

            # Track command time for smart polling
            import time

            self.last_command_time = time.time()

            # Send the converted command directly (immediate, no delays)
            self.serial_connection.write((converted_command + "\n").encode())

            # Track command count (simple and reliable)
            self.buffer_size += 1

            # Track this command for ok matching
            self.command_queue.append(converted_command)

            return True
        except Exception as e:
            print(f"Exception in _send_streaming_command: {e}")
            return False

    def convert_arc_r_to_ij(self, command, current_x, current_y):
        """Convert G2/G3 arc with R parameter to I/J format"""
        import re
        import math

        # Check if this is an arc command with R
        command_upper = command.upper()
        if not (
            re.search(r"\bG2\b", command_upper) or re.search(r"\bG3\b", command_upper)
        ):
            return command

        # Check if R parameter exists
        r_match = re.search(r"\bR\s*(-?\d+\.?\d*)", command_upper, re.IGNORECASE)
        if not r_match:
            return command  # Already in I/J format or invalid

        # Determine if G2 or G3
        is_g2 = bool(re.search(r"\bG2\b", command_upper))

        # Parse X and Y from command (use current position if not specified)
        x_match = re.search(r"\bX\s*(-?\d+\.?\d*)", command_upper)
        y_match = re.search(r"\bY\s*(-?\d+\.?\d*)", command_upper)

        end_x = float(x_match.group(1)) if x_match else current_x
        end_y = float(y_match.group(1)) if y_match else current_y

        # Get radius
        radius = float(r_match.group(1))

        # Calculate arc center using geometry
        # Start point
        x1, y1 = current_x, current_y
        # End point
        x2, y2 = end_x, end_y

        # Calculate chord length
        dx = x2 - x1
        dy = y2 - y1
        chord_length = math.sqrt(dx**2 + dy**2)

        # Check if radius is valid (must be at least half the chord length)
        if abs(radius) < chord_length / 2.0:
            print(
                f"Warning: Invalid arc - radius {radius} too small for chord {chord_length}"
            )
            return command  # Return original command

        # Calculate distance from chord midpoint to arc center
        # Using: h = sqrt(r^2 - (d/2)^2)
        try:
            h = math.sqrt(radius**2 - (chord_length / 2.0) ** 2)
        except ValueError:
            print(f"Warning: Cannot calculate arc center - math domain error")
            return command

        # Find chord midpoint
        mx = (x1 + x2) / 2.0
        my = (y1 + y2) / 2.0

        # Calculate perpendicular direction (normalized)
        if chord_length > 0:
            # Perpendicular to chord: rotate chord 90° clockwise
            # (dx, dy) -> (dy, -dx) normalized
            perp_x = dy / chord_length
            perp_y = -dx / chord_length
        else:
            # Start and end are same point - can't determine arc
            print(f"Warning: Arc start and end points are identical")
            return command

        # There are two possible arc centers, one on each side of the chord
        # We need to choose the correct one based on arc direction and radius sign

        # Calculate both possible centers
        center1_x = mx + h * perp_x
        center1_y = my + h * perp_y
        center2_x = mx - h * perp_x
        center2_y = my - h * perp_y

        # Choose the correct center based on arc direction and radius
        # For R > 0: choose shorter arc (≤ 180°)
        # For R < 0: choose longer arc (> 180°)

        # Calculate which center gives the correct arc span
        def calculate_arc_angle(center_x, center_y):
            # Calculate angles from center to start and end points
            start_angle = math.atan2(y1 - center_y, x1 - center_x)
            end_angle = math.atan2(y2 - center_y, x2 - center_x)

            # Calculate arc span
            if is_g2:  # Clockwise
                if end_angle > start_angle:
                    end_angle -= 2 * math.pi
                span = start_angle - end_angle
            else:  # Counter-clockwise
                if end_angle < start_angle:
                    end_angle += 2 * math.pi
                span = end_angle - start_angle

            return span

        # Calculate arc spans for both centers
        span1 = calculate_arc_angle(center1_x, center1_y)
        span2 = calculate_arc_angle(center2_x, center2_y)

        # Choose center based on radius sign and arc span
        if radius > 0:
            # Choose shorter arc (smaller span)
            if span1 < span2:
                center_x, center_y = center1_x, center1_y
            else:
                center_x, center_y = center2_x, center2_y
        else:
            # Choose longer arc (larger span)
            if span1 > span2:
                center_x, center_y = center1_x, center1_y
            else:
                center_x, center_y = center2_x, center2_y

        # Calculate I and J (offsets from start point to center)
        i_offset = center_x - x1
        j_offset = center_y - y1

        # Build new command with I/J instead of R
        # Preserve original case and format as much as possible
        new_command = re.sub(
            r"\bR\s*-?\d+\.?\d*", "", command, flags=re.IGNORECASE
        ).strip()

        # Find where to insert I and J (after X Y, before F or S or comment)
        # Look for F, S, or semicolon
        insert_pos = len(new_command)
        for pattern in [r"\bF\s*\d+", r"\bS\s*\d+", r";"]:
            match = re.search(pattern, new_command, re.IGNORECASE)
            if match:
                insert_pos = min(insert_pos, match.start())

        # Insert I and J
        ij_str = f" I{i_offset:.4f} J{j_offset:.4f}"
        new_command = new_command[:insert_pos] + ij_str + new_command[insert_pos:]

        print(f"Arc conversion: {command.strip()} -> {new_command.strip()}")
        return new_command

    def _update_modal_position(self, command):
        """Track modal X/Y position from G-code commands"""
        import re

        # Parse movement commands (G0, G1, G2, G3)
        command_upper = command.upper()
        if re.search(r"\b(G0|G1|G2|G3)\b", command_upper):
            # Extract X and Y if present
            x_match = re.search(r"\bX\s*(-?\d+\.?\d*)", command_upper)
            y_match = re.search(r"\bY\s*(-?\d+\.?\d*)", command_upper)

            if x_match:
                self.current_modal_x = float(x_match.group(1))
            if y_match:
                self.current_modal_y = float(y_match.group(1))

    def update_laser_power(self):
        """Update laser power level from input field"""
        try:
            power = int(self.laser_power_var.get())
            if 0 <= power <= 100:
                self.laser_power = power
                # Calculate scaled power value
                scaled_power = int((power / 100.0) * self.laser_power_max)
                # If laser is currently on, update the power level
                if self.laser_on:
                    self.send_gcode_async(f"M3 S{scaled_power}")
            else:
                messagebox.showwarning("Warning", "Power level must be between 0-100%")
                self.laser_power_var.set(str(self.laser_power))
        except ValueError:
            messagebox.showwarning(
                "Warning", "Please enter a valid number for power level"
            )
            self.laser_power_var.set(str(self.laser_power))

    def update_laser_power_max(self):
        """Update maximum laser power value from input field"""
        try:
            max_power = int(self.laser_power_max_var.get())
            if 1 <= max_power <= 65535:  # Reasonable range for laser power
                self.laser_power_max = max_power
                # If laser is currently on, update the power level with new scaling
                if self.laser_on:
                    scaled_power = int(
                        (self.laser_power / 100.0) * self.laser_power_max
                    )
                    self.send_gcode_async(f"M3 S{scaled_power}")
            else:
                messagebox.showwarning("Warning", "Max power must be between 1-65535")
                self.laser_power_max_var.set(str(self.laser_power_max))
        except ValueError:
            messagebox.showwarning(
                "Warning", "Please enter a valid number for max power"
            )
            self.laser_power_max_var.set(str(self.laser_power_max))

    def toggle_laser(self):
        """Toggle laser on/off at configurable power level"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Update power level from input field before toggling
        self.update_laser_power()

        if self.laser_on:
            # Turn laser off
            self.send_gcode_async("M5")
            self.laser_on = False
            self.laser_button.config(text="Laser OFF")
        else:
            # Turn laser on at configured power level (scaled)
            scaled_power = int((self.laser_power / 100.0) * self.laser_power_max)
            self.send_gcode_async(f"M3 S{scaled_power}")
            self.send_gcode_async("G1 F100")
            self.laser_on = True
            self.laser_button.config(text="Laser ON")

    def set_work_origin(self):
        """Set the current position as the work coordinate origin (0,0,0)"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Confirm with user
        response = messagebox.askyesno(
            "Set Work Origin",
            f"Set current position as work origin (0, 0, 0)?\n\n"
            f"Current MPos: X={self.machine_pos['x']:.2f} Y={self.machine_pos['y']:.2f} Z={self.machine_pos['z']:.2f}\n\n"
            f"This will execute: G10 L20 P1 X0 Y0 Z0",
        )

        if response:
            # Send G10 command to set current position as origin for G54 coordinate system
            self.send_gcode_async("G10 L20 P1 X0 Y0 Z0")

            # Query position multiple times to ensure WCO updates
            def query_updated_position(count=0):
                if count < 5 and self.is_connected and self.serial_connection:
                    try:
                        self.serial_connection.write(b"?")
                    except:
                        pass
                    # Query again after a short delay
                    if count < 4:
                        self.root.after(150, lambda: query_updated_position(count + 1))
                    else:
                        # After final query, update the plot
                        self.root.after(100, self.update_laser_marker_and_plot)

            # Start querying after a brief delay to let G10 process
            self.root.after(100, lambda: query_updated_position(0))

            # messagebox.showinfo(
            #    "Success",
            #    "Work origin set to current position\n\nPosition display will update shortly.",
            # )

    def auto_origin(self):
        """Execute automatic origin setting sequence"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Confirm with user
        response = messagebox.askyesno(
            "Auto Origin",
            "Execute automatic origin sequence?\n\n"
            "This will:\n"
            "1. Home the machine ($H)\n"
            "2. Set origin at current position (G10 L20 P1 X0 Y0 Z0)\n"
            "3. Move to X320 Y200 Z-60.1 (G0 X320 Y200 Z-60.1)\n"
            "4. Set origin at current position (G10 L20 P1 X0 Y0 Z0)",
        )

        if response:
            # Send commands in sequence - GRBL will execute them in order
            self.send_gcode_async("$H")
            self.send_gcode_async("G10 L20 P1 X0 Y0 Z0")
            self.send_gcode_async("G0 X320 Y200 Z-60.1")
            self.send_gcode_async("G10 L20 P1 X0 Y0 Z0")

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
        self.send_gcode_async(jog_cmd)

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
        self.send_gcode_async(jog_cmd)

    def execute_manual_gcode(self):
        """Execute a manually entered G-code command"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        command = self.gcode_cmd_var.get().strip()
        if not command:
            return

        print(f"Executing manual G-code: {command}")

        # Send the command async (laser state tracking is handled in send_gcode_async)
        self.send_gcode_async(command)

        # Clear the entry field after execution
        self.gcode_cmd_var.set("")

    def query_all_grbl_settings(self):
        """Query all GRBL settings using $$ command"""
        if not self.is_connected or not self.serial_connection:
            return

        try:
            # Send $$ to get all settings (responses handled by SerialReaderThread)
            self.send_gcode_async("$$")
            # Settings will be parsed in handle_response() when they arrive

        except Exception as e:
            print(f"Error querying GRBL settings: {e}")

    def home_machine(self):
        """Send machine to home position (only if homing is enabled)"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Check if homing is enabled
        if not self.homing_enabled:
            messagebox.showerror(
                "Homing Disabled",
                "Homing cycle is disabled in GRBL settings.\n\n"
                "To enable homing, send: $22=1\n"
                "Then reboot GRBL and reconnect.",
            )
            return

        # Send homing cycle command
        response = messagebox.askyesno(
            "Home Machine",
            "This will run the homing cycle. Make sure the machine is clear!\n\nContinue?",
        )

        if response:
            self.send_gcode_async("$H")

    def clear_errors(self):
        """Clear GRBL errors, alarms, and reset buffers"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        try:
            # Clear serial buffers
            if self.serial_connection:
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()

            # Clear internal command tracking
            self.manual_command_queue.clear()
            self.command_queue.clear()  # Streaming command tracking
            self.buffer_size = 0
            self.waiting_for_ok = False
            self.gcode_buffer.clear()

            # Clear response queue
            while not self.response_queue.empty():
                try:
                    self.response_queue.get_nowait()
                except queue.Empty:
                    break

            # Send unlock command to clear alarms
            self.send_gcode_async("$X")

            # Query status to update display
            time.sleep(0.1)
            if self.serial_connection:
                self.serial_connection.write(b"?")

            messagebox.showinfo(
                "Clear Errors",
                "Buffers cleared and unlock command ($X) sent.\nGRBL should now be ready.",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear errors: {e}")

    def reboot_grbl(self):
        """Reboot GRBL firmware and reinitialize"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        try:
            if self.serial_connection:
                # Send reboot command (Ctrl-X)
                self.serial_connection.write(b"\x18")
                time.sleep(0.5)

                # Clear all buffers and queues
                self.clear_errors()

                # Reinitialize connection
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()

                # Query status to update display
                time.sleep(0.1)
                self.serial_connection.write(b"?")

                messagebox.showinfo(
                    "Reboot GRBL",
                    "GRBL firmware rebooted successfully.\nSystem should be ready.",
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reboot GRBL: {e}")

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
            self.send_gcode_async("G90")  # Absolute positioning mode
            self.send_gcode_async("G0 X0 Y0 Z0")  # Rapid move to origin

    def parse_gcode_position(self, line, current_pos):
        """Parse a G-code line and return the new position"""
        new_pos = current_pos.copy()
        line_upper = line.upper().strip()

        # Parse movement commands (G0, G1, G2, G3)
        if line_upper.startswith(("G0", "G1", "G2", "G3")):
            # Extract X, Y, Z coordinates
            parts = line_upper.replace(",", " ").split()
            for part in parts:
                if part.startswith("X"):
                    try:
                        new_pos["x"] = float(part[1:])
                    except ValueError:
                        pass
                elif part.startswith("Y"):
                    try:
                        new_pos["y"] = float(part[1:])
                    except ValueError:
                        pass
                elif part.startswith("Z"):
                    try:
                        new_pos["z"] = float(part[1:])
                    except ValueError:
                        pass

        # Handle G92 (set position)
        elif line_upper.startswith("G92"):
            parts = line_upper.replace(",", " ").split()
            for part in parts:
                if part.startswith("X"):
                    try:
                        # G92 sets the current position to this value
                        new_pos["x"] = float(part[1:])
                    except ValueError:
                        pass
                elif part.startswith("Y"):
                    try:
                        new_pos["y"] = float(part[1:])
                    except ValueError:
                        pass
                elif part.startswith("Z"):
                    try:
                        new_pos["z"] = float(part[1:])
                    except ValueError:
                        pass

        return new_pos

    def emergency_stop(self):
        """Emergency stop - halt execution, clear buffer, turn off laser, send reset"""
        print("\n=== EMERGENCY STOP ACTIVATED ===")
        try:
            # Clear ALL local command buffers first
            self.gcode_buffer = []
            self.command_queue = []
            self.manual_command_queue = []
            self.buffer_size = 0
            self.waiting_for_ok = False
            print("Emergency stop: Local buffers cleared")

            if self.is_connected and self.serial_connection:
                # Flush any pending serial data
                try:
                    self.serial_connection.reset_output_buffer()
                    self.serial_connection.reset_input_buffer()
                    print("Emergency stop: Serial buffers flushed")
                except Exception as e:
                    print(f"Warning: Could not flush serial buffers: {e}")

                # Send soft reset (Ctrl-X) to clear GRBL buffer and stop immediately
                # This is the most critical command - send multiple times to ensure receipt
                for i in range(3):
                    try:
                        self.serial_connection.write(b"\x18")
                        time.sleep(0.05)  # Brief delay between resets
                    except:
                        pass
                print("Emergency stop: Sent soft reset (Ctrl-X) to GRBL")

                # Wait for GRBL to reset
                time.sleep(0.2)

                # Flush again after reset
                try:
                    self.serial_connection.reset_input_buffer()
                except:
                    pass

                # Turn off laser (M5) - send multiple times for safety
                for i in range(2):
                    try:
                        self.serial_connection.write(b"M5\n")
                        time.sleep(0.05)
                    except:
                        pass
                print("Emergency stop: Laser off command (M5) sent")

                # Set spindle speed to 0 as additional safety
                try:
                    self.serial_connection.write(b"S0\n")
                    print("Emergency stop: Spindle speed set to 0")
                except:
                    pass

            # Stop streaming
            self.stop_streaming()

            # Stop any position updates temporarily
            if self.status_update_id:
                try:
                    self.root.after_cancel(self.status_update_id)
                    self.status_update_id = None
                except:
                    pass

            # Close progress window if exists
            if hasattr(self, "progress_window") and self.progress_window.winfo_exists():
                self.progress_window.destroy()

            # Update laser button state
            if hasattr(self, "laser_button"):
                self.laser_button.config(text="Laser OFF")
                self.laser_on = False

            # Disable stop and next buttons
            if hasattr(self, "stop_button"):
                self.stop_button.config(state="disabled")
            if hasattr(self, "next_step_button"):
                self.next_step_button.config(state="disabled")

            # Restart position updates after a delay
            if self.is_connected:
                self.root.after(500, self.start_status_updates)

            print("=== EMERGENCY STOP COMPLETE ===\n")

            messagebox.showwarning(
                "Emergency Stop",
                "⚠️ EMERGENCY STOP EXECUTED ⚠️\n\n"
                "Safety actions taken:\n"
                "✓ GRBL buffer cleared (Ctrl-X sent)\n"
                "✓ Laser turned OFF (M5 sent)\n"
                "✓ Spindle speed set to 0\n"
                "✓ All local buffers cleared\n"
                "✓ Motion stopped immediately\n\n"
                "⚠️ Machine position may be lost\n"
                "⚠️ Rehoming may be required\n\n"
                "Please verify laser is OFF before continuing!",
            )

        except Exception as e:
            print(f"Error during emergency stop: {e}")
            messagebox.showerror(
                "Emergency Stop Error",
                f"⚠️ CRITICAL ERROR ⚠️\n\n"
                f"Emergency stop encountered an error:\n{str(e)}\n\n"
                f"MANUALLY VERIFY:\n"
                f"- Laser is OFF\n"
                f"- Machine has stopped moving\n"
                f"- Power off equipment if necessary!",
            )

    def start_response_processing(self):
        """Start processing responses from the queue"""
        if self.processing_responses:
            return

        self.processing_responses = True
        self.process_responses()

    def process_responses(self):
        """Process all responses in the queue (runs on GUI thread)"""
        if not self.processing_responses:
            return

        try:
            # Process more responses per call but less frequently (better throughput, less GUI interruption)
            for _ in range(50):
                try:
                    response = self.response_queue.get_nowait()
                    self.handle_response(response)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error processing responses: {e}")

        # Schedule next processing - reduced frequency for better GUI responsiveness
        if self.processing_responses:
            self.root.after(20, self.process_responses)  # Check every 20ms (was 10ms)

    def handle_response(self, response):
        """Handle a single response from GRBL"""
        # Log the received response
        self.log_received_response(response)

        # Check for disconnect signal from serial thread
        if response == "__DISCONNECTED__":
            self.handle_usb_disconnect()
            return

        # Status responses
        if response.startswith("<"):
            # Debug: show status responses
            # if "WPos" in response or "MPos" in response:
            #    print(f"Status: {response}")
            self.parse_status_response(response)

        # OK responses - command completed
        elif response.strip().lower() == "ok":
            self.handle_grbl_ok()

        # Error responses
        elif "error" in response.lower():
            print(f"GRBL Error: {response}")
            # Update GRBL state to show error
            self.grbl_state = "Error"
            self.update_state_display()

            # Show error in a user-friendly way
            error_code = response.replace("error:", "").strip()
            error_messages = {
                "1": "Expected G-code word (malformed line)",
                "2": "Bad number format",
                "3": "Invalid statement",
                "5": "Homing not enabled",
                "20": "Unsupported command",
                "22": "Parameter error",
            }
            error_desc = error_messages.get(error_code, "Unknown error")

            # Show error dialog for user awareness
            messagebox.showwarning(
                "GRBL Error",
                f"Error {error_code}: {error_desc}\n\nResponse: {response}\n\nCheck your G-code file for issues.",
            )

        # Settings responses ($N=value)
        elif response.startswith("$"):
            # Parse setting
            try:
                parts = response[1:].split("=")
                if len(parts) == 2:
                    setting_num = int(parts[0])
                    value = float(parts[1])
                    self.grbl_settings.set(setting_num, value)

                    # Update homing flag if $22
                    if setting_num == 22:
                        self.homing_enabled = value == 1
            except:
                pass

        # Other responses
        else:
            print(f"GRBL: {response}")

    def send_gcode_async(self, command):
        """Send G-code with proper buffer management (for manual commands)"""
        if not self.is_connected or not self.serial_connection:
            return False

        try:
            # Validate G-code command before sending
            if not self._validate_gcode_command(command):
                print(f"Invalid G-code command rejected: {command}")
                return False

            # Add command to manual command queue
            self.manual_command_queue.append(command)

            # Try to send commands from queue
            self._process_command_queue()

            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False

    def start_status_updates(self):
        """Start smart status updates based on GRBL state"""
        if not self.is_connected or self.status_update_id is not None:
            return

        def update_status():
            if self.is_connected and self.serial_connection:
                try:
                    # Always send status query (we need it to know the state)
                    self.serial_connection.write(b"?")
                except Exception as e:
                    print(f"Error sending status query: {e}")
                    # If we can't send, we're probably disconnected
                    if isinstance(e, (OSError, serial.SerialException)):
                        self.handle_usb_disconnect()
                        return

            # Schedule next update based on GRBL state
            if self.is_connected:
                import time

                # In single-step mode, use slower polling to avoid clogging serial
                if self.single_step_mode:
                    # Slow polling during single-step (500ms = 2 Hz)
                    interval = 500
                elif self.is_executing or self.grbl_state == "Run":
                    # Fast polling during G-code execution (50ms = 20 Hz)
                    interval = 50
                elif self.grbl_state in ["Jog", "Hold"]:
                    # Fast polling during jogging or hold (50ms = 20 Hz)
                    interval = 50
                elif (
                    self.grbl_state == "Idle"
                    and (time.time() - self.last_command_time) < 2.0
                ):
                    # Medium polling for 2 seconds after commands finish (200ms = 5 Hz)
                    interval = 200
                elif self.grbl_state == "Idle":
                    # Slow polling when truly idle (2000ms = 0.5 Hz)
                    interval = 2000
                elif self.grbl_state == "Alarm":
                    # Very slow polling in alarm state (5000ms = 0.2 Hz)
                    interval = 5000
                else:
                    # Default for other states (500ms = 2 Hz)
                    interval = 500

                self.status_update_id = self.root.after(interval, update_status)

        # Start with medium interval
        self.status_update_id = self.root.after(200, update_status)

    def stop_status_updates(self):
        """Stop periodic status updates"""
        if self.status_update_id is not None:
            self.root.after_cancel(self.status_update_id)
            self.status_update_id = None

    def handle_grbl_ok(self):
        """Handle GRBL 'ok' response - command completed"""
        # Command completed, reduce buffer count
        if self.command_queue:
            self.command_queue.pop(0)  # Remove completed command
            self.buffer_size = max(0, self.buffer_size - 1)
        else:
            # Safety: command_queue empty but got 'ok'
            # This can happen if manual commands were sent before streaming started
            # Just reduce buffer count
            if self.buffer_size > 0:
                self.buffer_size = max(0, self.buffer_size - 1)

        # Update plot with current laser position in execution modes
        if self.single_step_mode or (self.streaming and not self.single_step_mode):
            self.update_laser_position_only()

        # ALWAYS try streaming first (it checks self.streaming internally)
        # This ensures 'ok' responses during streaming always trigger more sends
        # BUT: Don't auto-send in single-step mode - wait for user to click Next
        if self.streaming and self.gcode_buffer and not self.single_step_mode:
            self._stream_next_available()
        elif not self.streaming:
            # Manual command mode
            self.waiting_for_ok = False
            self._process_command_queue()

    def _stream_next_available(self):
        """Send as many commands as buffer allows (event-driven)"""
        if not self.streaming or not self.gcode_buffer:
            return

        # Send multiple commands if buffer has space (simple command counting)
        while self.gcode_buffer and self.buffer_size < self.max_buffer_size:
            # Get next command
            line_data = self.gcode_buffer.pop(0)
            line = line_data["line"]

            # Send it
            if not self._send_streaming_command(line):
                self.stop_streaming()
                return

            # Update progress
            if hasattr(self, "progress_bar"):
                self.sent_lines += 1
                self.progress_bar["value"] = self.sent_lines
                if hasattr(self, "status_label"):
                    self.status_label.config(
                        text=f"Sent {self.sent_lines}/{self.total_lines} (buf:{self.buffer_size})"
                    )

        # Check if done
        if not self.gcode_buffer:
            self.check_streaming_complete()

    def stream_gcode_line(self):
        """Wrapper to call the streaming function (with or without step support)"""
        # Use the step-aware version for all streaming
        self.stream_gcode_line_with_step()

    def check_streaming_complete(self):
        """Check if streaming is complete (buffer empty)"""
        if not self.streaming:
            return

        # Track completion checks to prevent infinite waiting
        if not hasattr(self, "_completion_checks"):
            self._completion_checks = 0

        self._completion_checks += 1

        # If buffer is empty and command queue is empty, we're done
        # OR if we've waited too long (100 checks = 10 seconds)
        buffer_empty = self.buffer_size <= 0 and len(self.command_queue) == 0
        timeout_reached = self._completion_checks > 100

        if buffer_empty or timeout_reached:
            if timeout_reached:
                print(
                    f"Warning: Completion timeout after 10 seconds. Force completing."
                )

            self._completion_checks = 0

            # Capture final position before stopping
            if self.is_executing:
                # Query position multiple times to ensure we get the final position
                def query_final_position(count=0):
                    if count < 3 and self.is_connected and self.serial_connection:
                        try:
                            self.serial_connection.write(b"?")
                        except:
                            pass
                        # Query again after a short delay
                        self.root.after(100, lambda: query_final_position(count + 1))

                # Wait a moment for machine to settle and get final position
                def finalize_execution():
                    # Start querying final position
                    query_final_position()

                    # Wait for responses and then capture final position
                    def capture_final():
                        if self.is_executing:
                            current_pos = (self.work_pos["x"], self.work_pos["y"])
                            if (
                                not self.execution_path
                                or current_pos != self.execution_path[-1]
                            ):
                                self.execution_path.append(current_pos)
                                print(
                                    f"Captured final position: ({current_pos[0]:.2f}, {current_pos[1]:.2f})"
                                )

                            # Update laser marker to final position
                            if hasattr(self, "laser_marker"):
                                self.laser_marker.set_data(
                                    [self.work_pos["x"]], [self.work_pos["y"]]
                                )

                            # Update plot with final position
                            self.plot_toolpath()
                            self.canvas.draw()
                            self.canvas.flush_events()

                        # Now stop streaming
                        self.stop_streaming()

                        # Close progress window
                        try:
                            if (
                                hasattr(self, "progress_window")
                                and self.progress_window.winfo_exists()
                            ):
                                self.progress_window.destroy()
                                print(
                                    f"G-code execution complete - sent {self.sent_lines} lines"
                                )
                        except Exception as e:
                            print(f"Error destroying progress window: {e}")

                    # Wait for position updates (3 queries * 100ms each + processing time)
                    self.root.after(400, capture_final)

                # Start finalization sequence after a brief delay
                self.root.after(100, finalize_execution)
            else:
                # Not executing, just stop
                self.stop_streaming()

                # Close progress window
                try:
                    if (
                        hasattr(self, "progress_window")
                        and self.progress_window.winfo_exists()
                    ):
                        self.progress_window.destroy()
                        print(
                            f"G-code execution complete - sent {self.sent_lines} lines"
                        )
                except Exception as e:
                    print(f"Error destroying progress window: {e}")
        else:
            # Check again in 100ms
            self.root.after(100, self.check_streaming_complete)

    def stop_streaming(self):
        """Stop streaming G-code"""
        self.streaming = False
        self.gcode_buffer = []
        self.buffer_size = 0
        self.command_queue = []
        self.is_executing = False
        self.single_step_mode = False
        self.step_paused = False

        # Disable stop and next buttons
        if hasattr(self, "stop_button"):
            self.stop_button.config(state="disabled")
        if hasattr(self, "next_step_button"):
            self.next_step_button.config(state="disabled")

    def run_single_step(self):
        """Run G-code in single-step mode (pauses after each line)"""
        self.single_step_mode = True
        self.step_paused = False
        self.run_adjusted_gcode()

    def continue_step(self):
        """Continue to next step in single-step mode - send the previewed command"""
        if self.single_step_mode and self.step_paused:
            self.step_paused = False
            # Disable next buttons while processing
            if hasattr(self, "next_step_button"):
                self.next_step_button.config(state="disabled")
            if hasattr(self, "step_next_button"):
                self.step_next_button.config(state="disabled")

            # Send the previewed command
            if self.gcode_buffer:
                # Get and send the command (single-step doesn't need buffer check)
                line_data = self.gcode_buffer.pop(0)
                line = line_data["line"]

                try:
                    if not self._send_streaming_command(line):
                        print(f"Failed to send line: {line}")
                        self.stop_streaming()
                        return

                    # Update progress
                    if hasattr(self, "progress_bar"):
                        self.sent_lines += 1
                        self.progress_bar["value"] = self.sent_lines
                        self.status_label.config(
                            text=f"Executing line {self.sent_lines} / {self.total_lines}: {line}"
                        )

                    # Preview next command or finish
                    if self.gcode_buffer:
                        # More commands - show next preview immediately
                        # Force GUI update for responsiveness
                        self.root.update_idletasks()
                        self.stream_gcode_line_with_step()
                    else:
                        # No more commands - wait for completion
                        print("Single-step: Last line sent, waiting for completion")
                        self.root.after(500, self.check_streaming_complete)

                except Exception as e:
                    print(f"Error streaming line: {e}")
                    self.stop_streaming()
            else:
                # No more commands
                print("Single-step: No more commands to send")
                self.check_streaming_complete()

    def stream_gcode_line_with_step(self):
        """Stream G-code line with single-step support"""
        if not self.streaming or not self.gcode_buffer:
            return

        # Single-step mode: Preview next command BEFORE sending
        if self.single_step_mode:
            if self.step_paused:
                # Waiting for user to click Next
                return

            # Get next line to preview
            line_data = self.gcode_buffer[0]  # Peek, don't pop yet
            line = line_data["line"]

            # Show preview of next command
            if hasattr(self, "status_label"):
                self.status_label.config(
                    text=f"Ready to send line {self.sent_lines + 1} / {self.total_lines}: {line}"
                )

            # Pause and wait for Next button
            self.step_paused = True
            self.current_line_text = line

            # Enable next buttons
            if hasattr(self, "next_step_button"):
                self.next_step_button.config(state="normal")
            if hasattr(self, "step_next_button"):
                self.step_next_button.config(state="normal")
            return

        # Run mode: use event-driven sending (no timers!)
        self._stream_next_available()

    def run_adjusted_gcode(self):
        """Stream adjusted G-code to GRBL using streaming protocol"""
        if not self.adjusted_gcode:
            messagebox.showwarning("Warning", "Please adjust the G-code first!")
            return

        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to GRBL first!")
            return

        # Confirm with user
        response = messagebox.askyesno(
            "Run Adjusted G-code",
            "This will stream the adjusted G-code to GRBL.\n\n"
            "Make sure:\n"
            "- The machine is properly set up\n"
            "- The work origin is correct\n"
            "- The work area is clear\n"
            "- Eye protection is on\n\n"
            "Continue?",
        )

        if not response:
            return

        try:
            # Prepare G-code lines
            lines = self.adjusted_gcode.split("\n")

            # Prepend modal units only if they exist in the original file
            if self.modal_units in ("G20", "G21"):
                filtered_preview = [
                    l.strip()
                    for l in lines
                    if l.strip()
                    and not l.strip().startswith(";")
                    and not l.strip().startswith("(")
                ]
                if not filtered_preview or not filtered_preview[0].upper().startswith(
                    self.modal_units
                ):
                    lines = [self.modal_units] + lines

            # Filter out empty lines and comments (preserving modal units if injected)
            filtered_lines = []
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.startswith(";") and not line.startswith("("):
                    filtered_lines.append({"line": line, "num": i + 1})

            self.total_lines = len(filtered_lines)
            self.sent_lines = 0

            if self.total_lines == 0:
                messagebox.showwarning("Warning", "No G-code to send!")
                return

            # Create progress window
            self.progress_window = tk.Toplevel(self.root)
            mode_text = (
                "Single-Step Mode" if self.single_step_mode else "Streaming G-code"
            )
            self.progress_window.title(mode_text)
            self.progress_window.geometry("550x220")
            # Don't use transient() to allow interaction with main window
            # self.progress_window.transient(self.root)

            # Progress label
            header_text = (
                "Single-Step Mode - Click 'Next' to advance"
                if self.single_step_mode
                else "Streaming G-code to GRBL..."
            )
            ttk.Label(
                self.progress_window,
                text=header_text,
                font=("TkDefaultFont", 10, "bold"),
            ).pack(pady=10)

            # Progress bar
            self.progress_bar = ttk.Progressbar(
                self.progress_window, length=350, mode="determinate"
            )
            self.progress_bar.pack(pady=10)
            self.progress_bar["maximum"] = self.total_lines

            # Control buttons in progress window (place above status to avoid shifting)
            button_frame = ttk.Frame(self.progress_window)
            button_frame.pack(pady=5)

            # Next button (only for single-step mode)
            if self.single_step_mode:
                self.step_next_button = ttk.Button(
                    button_frame,
                    text="Next Step",
                    command=self.continue_step,
                    width=12,
                    state="disabled",  # Will be enabled after first line sent
                )
                self.step_next_button.pack(side="left", padx=5)

            # Stop button
            def cancel_run():
                self.emergency_stop()

            ttk.Button(button_frame, text="Stop", command=cancel_run, width=12).pack(
                side="left", padx=5
            )

            # Status label - shows current G-code line (placed below buttons)
            self.status_label = ttk.Label(
                self.progress_window,
                text=f"Line 0 / {self.total_lines}",
                font=("Courier", 9),
                wraplength=480,
                justify="left",
            )
            self.status_label.pack(pady=5, padx=10)

            # Initialize execution tracking
            self.is_executing = True
            self.execution_path = [(self.work_pos["x"], self.work_pos["y"])]

            # Initialize modal position tracking for arc conversion
            self.current_modal_x = self.work_pos["x"]
            self.current_modal_y = self.work_pos["y"]

            # Enable STOP button
            if hasattr(self, "stop_button"):
                self.stop_button.config(state="normal")

            # Start streaming with event-driven protocol
            self.gcode_buffer = filtered_lines
            self.streaming = True
            self.buffer_size = 0
            self.command_queue = []

            # Kick off event-driven streaming (fills buffer immediately)
            if self.single_step_mode:
                self.stream_gcode_line()  # Single-step uses preview logic
            else:
                self._stream_next_available()  # Run mode uses fast event-driven

            # Start status updates (250ms) if not already running
            if self.status_update_id is None:
                self.start_status_updates()

        except Exception as e:
            self.is_executing = False
            self.streaming = False
            if hasattr(self, "stop_button"):
                self.stop_button.config(state="disabled")
            messagebox.showerror("Error", f"Failed to run G-code:\n{str(e)}")


def main():
    root = tk.Tk()
    app = GCodeAdjuster(root)

    # Register cleanup on window close
    root.protocol("WM_DELETE_WINDOW", lambda: (app.cleanup(), root.destroy()))

    root.mainloop()


if __name__ == "__main__":
    main()
