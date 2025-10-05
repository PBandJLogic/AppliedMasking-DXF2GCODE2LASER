#!/usr/bin/env python3
"""
G-code Adjuster - GUI application for adjusting G-code toolpaths
based on actual vs expected target positions.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import os
from datetime import datetime
import re


class GCodeAdjuster:
    def __init__(self, root):
        self.root = root
        self.root.title("G-code Adjuster")
        self.root.geometry("1200x800")

        # Data storage
        self.original_gcode = ""
        self.adjusted_gcode = ""
        self.original_coords = []
        self.original_move_types = []
        self.adjusted_coords = []
        self.adjusted_move_types = []

        # GUI setup
        self.setup_gui()

        # Initialize radius calculation
        self.update_expected_radius()

    def setup_gui(self):
        """Set up the GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel for controls
        left_panel = ttk.Frame(main_frame, width=350)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Right panel for plot
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)

        # Set up trace callbacks after GUI is complete
        self.setup_trace_callbacks()

    def setup_left_panel(self, parent):
        """Set up the left control panel"""
        # File operations
        file_frame = ttk.LabelFrame(parent, text="File Operations", padding=10)
        file_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(
            file_frame, text="Load G-code File", command=self.load_gcode_file
        ).pack(fill="x")

        # Expected radius (calculated from left expected point)
        radius_frame = ttk.LabelFrame(
            parent, text="Expected Radius (Auto-calculated)", padding=10
        )
        radius_frame.pack(fill="x", pady=(0, 10))

        self.expected_radius_var = tk.StringVar(value="224.066")
        radius_entry = ttk.Entry(
            radius_frame,
            textvariable=self.expected_radius_var,
            width=20,
            state="readonly",
        )
        radius_entry.pack()

        # Right point validation label
        self.right_validation_label = ttk.Label(radius_frame, text="", foreground="red")
        self.right_validation_label.pack()

        # Left Target section
        left_frame = ttk.LabelFrame(parent, text="Left Target", padding=10)
        left_frame.pack(fill="x", pady=(0, 10))

        # Left Target Expected
        ttk.Label(left_frame, text="Expected X, Y:", foreground="gray").pack(anchor="w")
        left_expected_frame = ttk.Frame(left_frame)
        left_expected_frame.pack(fill="x", pady=(0, 5))

        self.left_expected_x_var = tk.StringVar(value="-222.959")
        self.left_expected_y_var = tk.StringVar(value="-22.250")
        ttk.Entry(
            left_expected_frame,
            textvariable=self.left_expected_x_var,
            width=10,
        ).pack(side="left", padx=(0, 5))
        ttk.Entry(
            left_expected_frame,
            textvariable=self.left_expected_y_var,
            width=10,
        ).pack(side="left")

        # Bind the update function to variable changes (will be set up after GUI is complete)

        # Left Target Actual
        ttk.Label(left_frame, text="Actual X, Y:", foreground="black").pack(anchor="w")
        left_actual_frame = ttk.Frame(left_frame)
        left_actual_frame.pack(fill="x")

        self.left_actual_x_var = tk.StringVar(value="-222.959")
        self.left_actual_y_var = tk.StringVar(value="-22.250")
        ttk.Entry(
            left_actual_frame, textvariable=self.left_actual_x_var, width=10
        ).pack(side="left", padx=(0, 5))
        ttk.Entry(
            left_actual_frame, textvariable=self.left_actual_y_var, width=10
        ).pack(side="left")

        # Right Target section
        right_frame = ttk.LabelFrame(parent, text="Right Target", padding=10)
        right_frame.pack(fill="x", pady=(0, 10))

        # Right Target Expected
        ttk.Label(right_frame, text="Expected X, Y:", foreground="gray").pack(
            anchor="w"
        )
        right_expected_frame = ttk.Frame(right_frame)
        right_expected_frame.pack(fill="x", pady=(0, 5))

        self.right_expected_x_var = tk.StringVar(value="222.959")
        self.right_expected_y_var = tk.StringVar(value="-22.250")
        ttk.Entry(
            right_expected_frame, textvariable=self.right_expected_x_var, width=10
        ).pack(side="left", padx=(0, 5))
        ttk.Entry(
            right_expected_frame, textvariable=self.right_expected_y_var, width=10
        ).pack(side="left")

        # Bind the validation function to variable changes (will be set up after GUI is complete)

        # Right Target Actual
        ttk.Label(right_frame, text="Actual X, Y:", foreground="black").pack(anchor="w")
        right_actual_frame = ttk.Frame(right_frame)
        right_actual_frame.pack(fill="x")

        self.right_actual_x_var = tk.StringVar(value="222.959")
        self.right_actual_y_var = tk.StringVar(value="-22.250")
        ttk.Entry(
            right_actual_frame, textvariable=self.right_actual_x_var, width=10
        ).pack(side="left", padx=(0, 5))
        ttk.Entry(
            right_actual_frame, textvariable=self.right_actual_y_var, width=10
        ).pack(side="left")

        # Adjust button
        ttk.Button(parent, text="Adjust G-code", command=self.adjust_gcode).pack(
            fill="x", pady=(0, 10)
        )

        # Results display
        results_frame = ttk.LabelFrame(parent, text="Calculation Results", padding=10)
        results_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.results_text = tk.Text(results_frame, height=12, width=40, wrap=tk.WORD)
        results_text_scroll = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.results_text.yview
        )
        self.results_text.configure(yscrollcommand=results_text_scroll.set)
        self.results_text.pack(side="left", fill="both", expand=True)
        results_text_scroll.pack(side="right", fill="y")

        # Save button
        ttk.Button(
            parent, text="Save Adjusted G-code", command=self.save_adjusted_gcode
        ).pack(fill="x")

    def setup_right_panel(self, parent):
        """Set up the right plot panel"""
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
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()

        # Add navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent)
        self.toolbar.update()
        self.toolbar.pack(side="bottom", fill="x")

        # Pack canvas after toolbar
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

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

            # Parse G-code coordinates
            self.original_coords, self.original_move_types = (
                self.parse_gcode_coordinates(self.original_gcode)
            )

            # Plot the original toolpath
            self.plot_toolpath()

            # Store the file path for saving
            self.original_file_path = file_path

            messagebox.showinfo(
                "Success",
                f"G-code file loaded successfully!\n{len(self.original_coords)} coordinate points found.",
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load G-code file:\n{str(e)}")

    def parse_gcode_coordinates(self, gcode):
        """Parse G-code and extract X,Y coordinates with move types"""
        coords = []
        move_types = []
        lines = gcode.split("\n")

        current_x = 0.0
        current_y = 0.0

        for line in lines:
            line = line.strip()
            if not line or line.startswith(";") or line.startswith("("):
                continue

            # Parse X and Y coordinates
            x_match = re.search(r"X([+-]?\d+\.?\d*)", line)
            y_match = re.search(r"Y([+-]?\d+\.?\d*)", line)

            if x_match:
                current_x = float(x_match.group(1))
            if y_match:
                current_y = float(y_match.group(1))

            # Determine move type and add coordinate if this line has movement
            if x_match or y_match:
                if "G0" in line:
                    coords.append((current_x, current_y))
                    move_types.append("G0")
                elif "G1" in line or "G2" in line or "G3" in line:
                    coords.append((current_x, current_y))
                    move_types.append("G1")

        return coords, move_types

    def plot_toolpath(self):
        """Plot the toolpath on the canvas"""
        self.ax.clear()

        if self.original_coords:
            # Plot original toolpath with color coding
            self.plot_gcode_toolpath(
                self.original_coords, self.original_move_types, "Original", self.ax
            )

        if self.adjusted_coords:
            # Plot adjusted toolpath with color coding
            self.plot_gcode_toolpath(
                self.adjusted_coords, self.adjusted_move_types, "Adjusted", self.ax
            )

        # Set plot properties
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.set_title("G-code Toolpath")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_aspect("equal")

        # Add legend if we have data
        if self.original_coords or self.adjusted_coords:
            self.ax.legend()

        # Auto-scale to fit all data
        self.ax.relim()
        self.ax.autoscale_view()

        self.canvas.draw()

    def setup_trace_callbacks(self):
        """Set up trace callbacks for real-time updates"""
        try:
            # Bind the update function to variable changes
            self.left_expected_x_var.trace("w", self._update_radius_callback)
            self.left_expected_y_var.trace("w", self._update_radius_callback)

            # Bind the validation function to variable changes
            self.right_expected_x_var.trace("w", self._validate_right_callback)
            self.right_expected_y_var.trace("w", self._validate_right_callback)
        except Exception as e:
            print(f"Warning: Could not set up trace callbacks: {e}")

    def update_expected_radius(self, *args):
        """Calculate expected radius from left expected point"""
        try:
            left_x = float(self.left_expected_x_var.get())
            left_y = float(self.left_expected_y_var.get())

            # Calculate radius from distance to origin
            radius = np.sqrt(left_x**2 + left_y**2)
            self.expected_radius_var.set(f"{radius:.3f}")

            # Validate right expected point
            self.validate_right_expected()

        except ValueError:
            # Invalid input, skip calculation
            pass

    def validate_right_expected(self, *args):
        """Validate that right expected point matches the calculated radius"""
        try:
            left_x = float(self.left_expected_x_var.get())
            left_y = float(self.left_expected_y_var.get())
            right_x = float(self.right_expected_x_var.get())
            right_y = float(self.right_expected_y_var.get())

            # Calculate expected radius from left point
            expected_radius = np.sqrt(left_x**2 + left_y**2)

            # Calculate actual radius from right point
            actual_radius = np.sqrt(right_x**2 + right_y**2)

            # Check if within tolerance
            error = abs(actual_radius - expected_radius)
            if error <= 0.01:
                self.right_validation_label.config(text="✓ Valid", foreground="green")
            else:
                self.right_validation_label.config(
                    text=f"✗ Error: {error:.3f}mm", foreground="red"
                )

        except ValueError:
            # Invalid input, clear validation
            self.right_validation_label.config(text="", foreground="red")

    def _update_radius_callback(self, *args):
        """Wrapper callback for trace method"""
        self.update_expected_radius()

    def _validate_right_callback(self, *args):
        """Wrapper callback for trace method"""
        self.validate_right_expected()

    def plot_gcode_toolpath(self, coords, move_types, label_prefix, ax):
        """Plot G-code toolpath with color coding for move types"""
        if not coords:
            return

        # Separate G0 and G1+ moves
        g0_coords = []
        g1_coords = []

        for i, (coord, move_type) in enumerate(zip(coords, move_types)):
            if move_type == "G0":
                g0_coords.append(coord)
            else:  # G1, G2, G3
                g1_coords.append(coord)

        # Determine colors based on whether it's original or adjusted
        if label_prefix == "Original":
            g0_color = "green"
            g1_color = "red"
        else:  # Adjusted
            g0_color = "blue"
            g1_color = "orange"

        # Plot G0 moves (positioning)
        if g0_coords:
            g0_x, g0_y = zip(*g0_coords)
            ax.plot(
                g0_x,
                g0_y,
                f"{g0_color[0]}-",
                linewidth=2,
                label=f"{label_prefix} - Positioning (G0)",
                alpha=0.7,
            )
            ax.scatter(g0_x, g0_y, c=g0_color, s=8, alpha=0.5)

        # Plot G1+ moves (engraving)
        if g1_coords:
            g1_x, g1_y = zip(*g1_coords)
            ax.plot(
                g1_x,
                g1_y,
                f"{g1_color[0]}-",
                linewidth=2,
                label=f"{label_prefix} - Engraving (G1+)",
                alpha=0.7,
            )
            ax.scatter(g1_x, g1_y, c=g1_color, s=8, alpha=0.5)

    def adjust_gcode(self):
        """Calculate adjustments and modify G-code"""
        try:
            # Get input values
            expected_radius = float(self.expected_radius_var.get())

            left_expected = (
                float(self.left_expected_x_var.get()),
                float(self.left_expected_y_var.get()),
            )
            left_actual = (
                float(self.left_actual_x_var.get()),
                float(self.left_actual_y_var.get()),
            )
            right_expected = (
                float(self.right_expected_x_var.get()),
                float(self.right_expected_y_var.get()),
            )
            right_actual = (
                float(self.right_actual_x_var.get()),
                float(self.right_actual_y_var.get()),
            )

            if not self.original_coords:
                messagebox.showwarning("Warning", "Please load a G-code file first!")
                return

            # Calculate actual circle center and rotation
            actual_center, rotation_angle = self.calculate_corrections(
                left_actual, right_actual, expected_radius
            )

            # Calculate distances and errors
            left_distance = np.sqrt(
                (left_actual[0] - actual_center[0]) ** 2
                + (left_actual[1] - actual_center[1]) ** 2
            )
            right_distance = np.sqrt(
                (right_actual[0] - actual_center[0]) ** 2
                + (right_actual[1] - actual_center[1]) ** 2
            )

            left_error = abs(left_distance - expected_radius)
            right_error = abs(right_distance - expected_radius)

            # Apply transformations to coordinates and preserve move types
            self.adjusted_coords = self.apply_transformations(
                self.original_coords, actual_center, rotation_angle
            )
            self.adjusted_move_types = self.original_move_types.copy()

            # Generate adjusted G-code
            self.adjusted_gcode = self.generate_adjusted_gcode(
                self.original_gcode, actual_center, rotation_angle
            )

            # Validate expected points
            left_expected_x = float(self.left_expected_x_var.get())
            left_expected_y = float(self.left_expected_y_var.get())
            right_expected_x = float(self.right_expected_x_var.get())
            right_expected_y = float(self.right_expected_y_var.get())

            # Calculate expected radius from left point
            calculated_radius = np.sqrt(left_expected_x**2 + left_expected_y**2)

            # Calculate actual radius from right point
            right_radius = np.sqrt(right_expected_x**2 + right_expected_y**2)
            right_radius_error = abs(right_radius - calculated_radius)

            # Display results
            results = f"""CALCULATION RESULTS
========================

Expected Circle (from left point):
  Radius: {calculated_radius:.3f} mm
  Center: (0.000, 0.000) mm

Right Point Validation:
  Expected radius: {calculated_radius:.3f} mm
  Actual radius: {right_radius:.3f} mm
  Error: {right_radius_error:.3f} mm
  Status: {'✓ Valid' if right_radius_error <= 0.01 else '✗ Error > 0.01mm'}

Actual Circle Center:
  X: {actual_center[0]:.3f} mm
  Y: {actual_center[1]:.3f} mm

Rotation Angle: {np.degrees(rotation_angle):.3f} degrees

Distance to Left Target: {left_distance:.3f} mm
Expected Radius: {expected_radius:.3f} mm
Left Error: {left_error:.3f} mm

Distance to Right Target: {right_distance:.3f} mm
Expected Radius: {expected_radius:.3f} mm
Right Error: {right_error:.3f} mm

Transformation Applied:
- Translation: ({actual_center[0]:.3f}, {actual_center[1]:.3f})
- Rotation: {np.degrees(rotation_angle):.3f}°
"""

            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, results)

            # Update plot
            self.plot_toolpath()

            messagebox.showinfo("Success", "G-code adjustment completed!")

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input values:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Calculation failed:\n{str(e)}")

    def calculate_corrections(self, left_actual, right_actual, expected_radius):
        """Calculate the center and rotation needed for correction"""
        # Calculate the actual circle center from the two actual points
        mid_x = (left_actual[0] + right_actual[0]) / 2
        mid_y = (left_actual[1] + right_actual[1]) / 2

        # Distance between the two actual points
        chord_length = np.sqrt(
            (right_actual[0] - left_actual[0]) ** 2
            + (right_actual[1] - left_actual[1]) ** 2
        )

        # Calculate the perpendicular distance from chord to center
        if chord_length > 2 * expected_radius:
            # Points are too far apart for the expected radius
            actual_radius = chord_length / 2
        else:
            actual_radius = expected_radius

        perpendicular_dist = np.sqrt(actual_radius**2 - (chord_length / 2) ** 2)

        # Calculate perpendicular direction
        dx = right_actual[0] - left_actual[0]
        dy = right_actual[1] - left_actual[1]

        # Perpendicular vector (rotated 90 degrees)
        perp_x = -dy / chord_length
        perp_y = dx / chord_length

        # Calculate actual center (there are two possible centers, we'll use one)
        actual_center_x = mid_x + perp_x * perpendicular_dist
        actual_center_y = mid_y + perp_y * perpendicular_dist

        # Calculate rotation angle to align the chord direction
        # Expected: left at (-X, Y), right at (+X, Y) - horizontal line
        # Actual: left at (x1, y1), right at (x2, y2)
        # We want to rotate the actual chord to match the expected horizontal direction

        # Expected direction (horizontal, left to right)
        expected_dx = 1.0  # horizontal direction
        expected_dy = 0.0

        # Actual direction (normalized)
        actual_dx = dx / chord_length
        actual_dy = dy / chord_length

        # Calculate rotation angle to align actual direction with expected direction
        # This rotates the actual chord to be horizontal
        rotation_angle = np.arctan2(
            expected_dx * actual_dy - expected_dy * actual_dx,
            expected_dx * actual_dx + expected_dy * actual_dy,
        )

        return (actual_center_x, actual_center_y), rotation_angle

    def apply_transformations(self, coords, center, rotation_angle):
        """Apply translation and rotation to coordinates"""
        adjusted = []

        for x, y in coords:
            # Translate to move center to origin
            tx = x - center[0]
            ty = y - center[1]

            # Apply rotation
            cos_r = np.cos(rotation_angle)
            sin_r = np.sin(rotation_angle)

            rx = tx * cos_r - ty * sin_r
            ry = tx * sin_r + ty * cos_r

            adjusted.append((rx, ry))

        return adjusted

    def generate_adjusted_gcode(self, original_gcode, center, rotation_angle):
        """Generate adjusted G-code with new coordinates"""
        lines = original_gcode.split("\n")
        adjusted_lines = []

        for line in lines:
            adjusted_line = line

            # Check if line contains X or Y coordinates
            x_match = re.search(r"X([+-]?\d+\.?\d*)", line)
            y_match = re.search(r"Y([+-]?\d+\.?\d*)", line)

            if x_match or y_match:
                # Extract current coordinates
                current_x = float(x_match.group(1)) if x_match else 0.0
                current_y = float(y_match.group(1)) if y_match else 0.0

                # Apply transformation
                tx = current_x - center[0]
                ty = current_y - center[1]

                cos_r = np.cos(rotation_angle)
                sin_r = np.sin(rotation_angle)

                new_x = tx * cos_r - ty * sin_r
                new_y = tx * sin_r + ty * cos_r

                # Replace coordinates in line
                if x_match:
                    adjusted_line = re.sub(
                        r"X[+-]?\d+\.?\d*", f"X{new_x:.6f}", adjusted_line
                    )
                if y_match:
                    adjusted_line = re.sub(
                        r"Y[+-]?\d+\.?\d*", f"Y{new_y:.6f}", adjusted_line
                    )

            adjusted_lines.append(adjusted_line)

        return "\n".join(adjusted_lines)

    def save_adjusted_gcode(self):
        """Save the adjusted G-code to a new file"""
        if not self.adjusted_gcode:
            messagebox.showwarning("Warning", "Please adjust the G-code first!")
            return

        try:
            # Generate filename with _adjusted suffix and timestamp
            if hasattr(self, "original_file_path"):
                base_path = os.path.splitext(self.original_file_path)[0]
                extension = os.path.splitext(self.original_file_path)[1]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"{base_path}_adjusted_{timestamp}{extension}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"adjusted_gcode_{timestamp}.nc"

            # Ask user for save location
            save_path = filedialog.asksaveasfilename(
                defaultextension=(
                    extension if hasattr(self, "original_file_path") else ".nc"
                ),
                initialfile=os.path.basename(new_filename),
                filetypes=[
                    ("G-code files", "*.nc"),
                    ("G-code files", "*.gcode"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*"),
                ],
                title="Save Adjusted G-code File",
            )

            if save_path:
                with open(save_path, "w") as f:
                    f.write(self.adjusted_gcode)

                messagebox.showinfo(
                    "Success", f"Adjusted G-code saved to:\n{save_path}"
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save adjusted G-code:\n{str(e)}")


def main():
    root = tk.Tk()
    app = GCodeAdjuster(root)
    root.mainloop()


if __name__ == "__main__":
    main()
