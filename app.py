#!/usr/bin/env python3
"""
Flask Web Application for DXF Viewer and Editor
Allows loading DXF files, adjusting origin, and marking elements for engraving or removal.
"""

import os
import json
import base64
import io
from flask import Flask, render_template, request, jsonify, send_file
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import ezdxf
import math
from typing import List, Tuple, Dict, Any
import tempfile
from datetime import datetime

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Global variables to store session data
session_data = {
    "original_points": [],
    "current_points": [],
    "origin_offset": (0.0, 0.0),
    "removed_elements": set(),
    "engraved_elements": set(),
    "selected_elements": set(),
    "element_counter": 0,
    "element_data": {},
    "gcode_settings": {
        "preamble": "G21 ; Set units to millimeters\nG90 ; Absolute positioning\nG0 X0, Y0, Z-5 ; Go to zero position\n",
        "postscript": "G0 Z-5 ; Raise Z\nM5 ; Turn off laser\nG0 X0 Y0 ; Return to origin\n",
        "laser_power": 1000,
        "cutting_z": -30,
        "feedrate": 1500,
        "max_workspace_x": 800.0 - 10.0,
        "max_workspace_y": 400.0 - 10.0,
    },
}


def get_next_element_id():
    """Get next unique element ID"""
    session_data["element_counter"] += 1
    return session_data["element_counter"]


def transform_point(x, y, insert_pos, scale, rotation):
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


def extract_lwpolyline_geometry(entity, insert_pos=None, scale=None, rotation=None):
    """Extract LWPOLYLINE points"""
    points = []
    polyline_points = list(entity.get_points())
    is_closed = entity.closed

    for x, y, *_ in polyline_points:
        if insert_pos and scale and rotation is not None:
            tx, ty = transform_point(x, y, insert_pos, scale, rotation)
        else:
            tx, ty = x, y
        points.append((tx, ty))

    if is_closed and len(points) > 2:
        points.append(points[0])

    return points


def extract_geometry(file_path):
    """Extract geometry from DXF file"""
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

            for block_entity in block:
                if block_entity.dxftype() == "LINE":
                    start_pt = block_entity.dxf.start
                    end_pt = block_entity.dxf.end
                    start_x, start_y = transform_point(
                        start_pt.x, start_pt.y, insert_pos, scale, rotation
                    )
                    end_x, end_y = transform_point(
                        end_pt.x, end_pt.y, insert_pos, scale, rotation
                    )

                    element_id = get_next_element_id()
                    all_points.append((start_x, start_y, 0, "LINE", element_id))
                    all_points.append((end_x, end_y, 0, "LINE", element_id))

                    session_data["element_data"][element_id] = (
                        (start_x, end_x),
                        (start_y, end_y),
                        0,
                        "LINE",
                        ((start_pt.x, start_pt.y), (end_pt.x, end_pt.y), "LINE"),
                    )

                elif block_entity.dxftype() == "CIRCLE":
                    original_cx = block_entity.dxf.center.x
                    original_cy = block_entity.dxf.center.y
                    cx, cy = transform_point(
                        original_cx,
                        original_cy,
                        insert_pos,
                        scale,
                        rotation,
                    )
                    original_radius = block_entity.dxf.radius
                    scaled_radius = original_radius * scale[0]

                    element_id = get_next_element_id()
                    all_points.append((cx, cy, scaled_radius, "CIRCLE", element_id))
                    session_data["element_data"][element_id] = (
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
                    polyline_points = extract_lwpolyline_geometry(
                        block_entity, insert_pos, scale, rotation
                    )
                    element_id = get_next_element_id()
                    for tx, ty in polyline_points:
                        all_points.append((tx, ty, 0, "LWPOLYLINE", element_id))

                    session_data["element_data"][element_id] = (
                        [pt[0] for pt in polyline_points],
                        [pt[1] for pt in polyline_points],
                        0,
                        "LWPOLYLINE",
                        polyline_points,
                    )

        elif entity_type == "LINE":
            start_pt = entity.dxf.start
            end_pt = entity.dxf.end
            element_id = get_next_element_id()

            all_points.append((start_pt.x, start_pt.y, 0, "LINE", element_id))
            all_points.append((end_pt.x, end_pt.y, 0, "LINE", element_id))

            session_data["element_data"][element_id] = (
                (start_pt.x, end_pt.x),
                (start_pt.y, end_pt.y),
                0,
                "LINE",
                ((start_pt.x, start_pt.y), (end_pt.x, end_pt.y), "LINE"),
            )

        elif entity_type == "CIRCLE":
            center = entity.dxf.center
            radius = entity.dxf.radius
            element_id = get_next_element_id()
            all_points.append((center.x, center.y, radius, "CIRCLE", element_id))
            session_data["element_data"][element_id] = (
                center.x,
                center.y,
                radius,
                "CIRCLE",
                (center.x, center.y, radius, "CIRCLE"),
            )

    return all_points


def create_plot_image(selected_elements=None):
    """Create matplotlib plot and return as base64 image"""
    if selected_elements is None:
        selected_elements = set()

    fig, ax = plt.subplots(figsize=(12, 8), dpi=100)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.grid(True, alpha=0.3)
    ax.set_title("DXF Geometry - Click on elements to select")

    # Get unique elements
    unique_elements = {}
    for x, y, radius, geom_type, element_id in session_data["current_points"]:
        if element_id not in unique_elements:
            unique_elements[element_id] = {
                "geom_type": geom_type,
                "radius": radius,
                "points": [],
            }
        unique_elements[element_id]["points"].append((x, y))

    # Plot each unique element
    for element_id, element_info in unique_elements.items():
        if element_id in session_data["removed_elements"]:
            continue

        geom_type = element_info["geom_type"]
        radius = element_info["radius"]
        points = element_info["points"]

        is_engraved = element_id in session_data["engraved_elements"]
        is_selected = element_id in selected_elements

        # Choose colors and styles
        if is_selected:
            line_color = "lime"
            marker_color = "lime"
            line_width = 4
            alpha = 1.0
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
                ax.plot(
                    x_coords,
                    y_coords,
                    color=line_color,
                    linewidth=line_width,
                    alpha=alpha,
                )
                marker_size = 15 if is_selected else 5
                ax.scatter(
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
                circle = plt.Circle(
                    (center_x, center_y),
                    radius,
                    color=line_color,
                    fill=False,
                    linewidth=line_width,
                    alpha=alpha,
                )
                ax.add_patch(circle)

        elif geom_type == "LWPOLYLINE":
            if len(points) >= 2:
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]
                ax.plot(
                    x_coords,
                    y_coords,
                    color=line_color,
                    linewidth=line_width,
                    alpha=alpha,
                )
                marker_size = 15 if is_selected else 5
                ax.scatter(
                    x_coords,
                    y_coords,
                    c=marker_color,
                    s=marker_size,
                    marker="s",
                    alpha=alpha,
                )

    # Calculate axis limits to show all visible elements
    if unique_elements:
        all_x = []
        all_y = []

        for element_id, element_info in unique_elements.items():
            if element_id in session_data["removed_elements"]:
                continue

            points = element_info["points"]
            radius = element_info["radius"]
            geom_type = element_info["geom_type"]

            for point in points:
                all_x.append(point[0])
                all_y.append(point[1])

            # For circles, extend bounds to include the full circle
            if geom_type == "CIRCLE" and len(points) >= 1:
                center_x, center_y = points[0]
                all_x.extend([center_x - radius, center_x + radius])
                all_y.extend([center_y - radius, center_y + radius])

        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)

            # Add some padding (10% of range)
            x_range = max_x - min_x
            y_range = max_y - min_y
            padding_x = max(x_range * 0.1, 10)  # At least 10mm padding
            padding_y = max(y_range * 0.1, 10)  # At least 10mm padding

            ax.set_xlim(min_x - padding_x, max_x + padding_x)
            ax.set_ylim(min_y - padding_y, max_y + padding_y)

    ax.set_aspect("equal")

    # Convert plot to base64 image
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png", bbox_inches="tight", dpi=100)
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close(fig)

    return img_base64


@app.route("/")
def index():
    """Main page"""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle DXF file upload"""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".dxf"):
        return jsonify({"error": "Please upload a DXF file"}), 400

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
            file.save(tmp_file.name)

            # Extract geometry
            session_data["original_points"] = extract_geometry(tmp_file.name)
            session_data["current_points"] = session_data["original_points"].copy()
            session_data["removed_elements"] = set()
            session_data["engraved_elements"] = set()
            session_data["origin_offset"] = (0.0, 0.0)

            # Clean up temp file
            os.unlink(tmp_file.name)

            # Generate plot image
            plot_image = create_plot_image()

            # Calculate statistics
            total_elements = len(session_data["original_points"])
            removed_count = len(session_data["removed_elements"])
            engraved_count = len(session_data["engraved_elements"])
            remaining_count = total_elements - removed_count

            return jsonify(
                {
                    "success": True,
                    "plot_image": plot_image,
                    "statistics": {
                        "total_elements": total_elements,
                        "removed": removed_count,
                        "engraved": engraved_count,
                        "remaining": remaining_count,
                        "origin_offset": session_data["origin_offset"],
                    },
                }
            )

    except Exception as e:
        return jsonify({"error": f"Failed to process DXF file: {str(e)}"}), 500


@app.route("/apply_offset", methods=["POST"])
def apply_offset():
    """Apply origin offset"""
    try:
        data = request.get_json()
        x_offset = float(data["x_offset"])
        y_offset = float(data["y_offset"])

        session_data["origin_offset"] = (x_offset, y_offset)

        # Update current points with offset
        session_data["current_points"] = []
        for x, y, radius, geom_type, element_id in session_data["original_points"]:
            new_x = x + x_offset
            new_y = y + y_offset
            session_data["current_points"].append(
                (new_x, new_y, radius, geom_type, element_id)
            )

        # Generate updated plot
        plot_image = create_plot_image()

        # Calculate statistics
        total_elements = len(session_data["original_points"])
        removed_count = len(session_data["removed_elements"])
        engraved_count = len(session_data["engraved_elements"])
        remaining_count = total_elements - removed_count

        return jsonify(
            {
                "success": True,
                "plot_image": plot_image,
                "statistics": {
                    "total_elements": total_elements,
                    "removed": removed_count,
                    "engraved": engraved_count,
                    "remaining": remaining_count,
                    "origin_offset": session_data["origin_offset"],
                },
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to apply offset: {str(e)}"}), 500


@app.route("/mark_engraving", methods=["POST"])
def mark_engraving():
    """Mark elements for engraving"""
    try:
        data = request.get_json()
        element_ids = data.get("element_ids", [])

        # If no specific elements provided, use selected elements
        if not element_ids:
            # Check if this is a "select all" request (empty array from frontend)
            if data.get("element_ids") == []:
                # Mark all non-removed elements for engraving
                all_element_ids = set()
                for x, y, radius, geom_type, element_id in session_data[
                    "current_points"
                ]:
                    if element_id not in session_data["removed_elements"]:
                        all_element_ids.add(element_id)
                element_ids = list(all_element_ids)
            else:
                # Use currently selected elements
                element_ids = list(session_data["selected_elements"])

        # Mark elements for engraving
        for element_id in element_ids:
            if element_id not in session_data["removed_elements"]:
                session_data["engraved_elements"].add(element_id)

        # Clear selection after marking
        session_data["selected_elements"].clear()

        # Generate updated plot
        plot_image = create_plot_image(session_data["selected_elements"])

        # Calculate statistics
        total_elements = len(session_data["original_points"])
        removed_count = len(session_data["removed_elements"])
        engraved_count = len(session_data["engraved_elements"])
        remaining_count = total_elements - removed_count

        return jsonify(
            {
                "success": True,
                "plot_image": plot_image,
                "statistics": {
                    "total_elements": total_elements,
                    "removed": removed_count,
                    "engraved": engraved_count,
                    "remaining": remaining_count,
                    "origin_offset": session_data["origin_offset"],
                },
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to mark for engraving: {str(e)}"}), 500


@app.route("/remove_elements", methods=["POST"])
def remove_elements():
    """Remove elements"""
    try:
        data = request.get_json()
        element_ids = data.get("element_ids", [])

        # If no specific elements provided, use selected elements
        if not element_ids:
            element_ids = list(session_data["selected_elements"])

        # Remove elements
        for element_id in element_ids:
            session_data["removed_elements"].add(element_id)
            session_data["engraved_elements"].discard(element_id)

        # Clear selection after removing
        session_data["selected_elements"].clear()

        # Generate updated plot
        plot_image = create_plot_image(session_data["selected_elements"])

        # Calculate statistics
        total_elements = len(session_data["original_points"])
        removed_count = len(session_data["removed_elements"])
        engraved_count = len(session_data["engraved_elements"])
        remaining_count = total_elements - removed_count

        return jsonify(
            {
                "success": True,
                "plot_image": plot_image,
                "statistics": {
                    "total_elements": total_elements,
                    "removed": removed_count,
                    "engraved": engraved_count,
                    "remaining": remaining_count,
                    "origin_offset": session_data["origin_offset"],
                },
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to remove elements: {str(e)}"}), 500


@app.route("/reset", methods=["POST"])
def reset():
    """Reset all selections and modifications"""
    session_data["removed_elements"] = set()
    session_data["engraved_elements"] = set()
    session_data["selected_elements"] = set()
    session_data["origin_offset"] = (0.0, 0.0)

    if session_data["original_points"]:
        session_data["current_points"] = session_data["original_points"].copy()
        plot_image = create_plot_image(session_data["selected_elements"])
    else:
        plot_image = None

    # Calculate statistics
    total_elements = len(session_data["original_points"])
    removed_count = len(session_data["removed_elements"])
    engraved_count = len(session_data["engraved_elements"])
    remaining_count = total_elements - removed_count

    return jsonify(
        {
            "success": True,
            "plot_image": plot_image,
            "statistics": {
                "total_elements": total_elements,
                "removed": removed_count,
                "engraved": engraved_count,
                "remaining": remaining_count,
                "origin_offset": session_data["origin_offset"],
            },
        }
    )


@app.route("/preview_gcode", methods=["GET"])
def preview_gcode():
    """Preview G-code for the current design"""
    if not session_data["current_points"]:
        return jsonify({"error": "No DXF file loaded"}), 400

    # Filter points for engraving only
    engraving_elements = {}
    for x, y, radius, geom_type, element_id in session_data["current_points"]:
        if (
            element_id in session_data["engraved_elements"]
            and element_id not in session_data["removed_elements"]
        ):
            if element_id not in engraving_elements:
                engraving_elements[element_id] = {
                    "geom_type": geom_type,
                    "radius": radius,
                    "points": [],
                }
            engraving_elements[element_id]["points"].append((x, y))

    if not engraving_elements:
        return jsonify({"error": "No elements marked for engraving"}), 400

    # Generate G-code
    gcode = generate_gcode(engraving_elements)

    return jsonify(
        {"success": True, "gcode": gcode, "element_count": len(engraving_elements)}
    )


@app.route("/export_gcode", methods=["GET"])
def export_gcode():
    """Export G-code for the current design"""
    if not session_data["current_points"]:
        return jsonify({"error": "No DXF file loaded"}), 400

    # Filter points for engraving only
    engraving_elements = {}
    for x, y, radius, geom_type, element_id in session_data["current_points"]:
        if (
            element_id in session_data["engraved_elements"]
            and element_id not in session_data["removed_elements"]
        ):
            if element_id not in engraving_elements:
                engraving_elements[element_id] = {
                    "geom_type": geom_type,
                    "radius": radius,
                    "points": [],
                }
            engraving_elements[element_id]["points"].append((x, y))

    if not engraving_elements:
        return jsonify({"error": "No elements marked for engraving"}), 400

    # Generate G-code
    gcode = generate_gcode(engraving_elements)

    # Create temporary file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dxf_gcode_{timestamp}.nc"

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".nc") as tmp_file:
        tmp_file.write(gcode)
        tmp_file_path = tmp_file.name

    return send_file(
        tmp_file_path, as_attachment=True, download_name=filename, mimetype="text/plain"
    )


@app.route("/update_gcode_settings", methods=["POST"])
def update_gcode_settings():
    """Update G-code generation settings"""
    try:
        data = request.get_json()

        # Update the session data with new settings
        if "preamble" in data:
            session_data["gcode_settings"]["preamble"] = data["preamble"]
        if "postscript" in data:
            session_data["gcode_settings"]["postscript"] = data["postscript"]
        if "laser_power" in data:
            session_data["gcode_settings"]["laser_power"] = data["laser_power"]
        if "cutting_z" in data:
            session_data["gcode_settings"]["cutting_z"] = data["cutting_z"]
        if "feedrate" in data:
            session_data["gcode_settings"]["feedrate"] = data["feedrate"]
        if "max_workspace_x" in data:
            session_data["gcode_settings"]["max_workspace_x"] = data["max_workspace_x"]
        if "max_workspace_y" in data:
            session_data["gcode_settings"]["max_workspace_y"] = data["max_workspace_y"]

        return jsonify({"success": True, "message": "Settings updated successfully"})

    except Exception as e:
        return jsonify({"error": f"Failed to update settings: {str(e)}"}), 500


@app.route("/preview_gcode_plot", methods=["GET"])
def preview_gcode_plot():
    """Generate G-code toolpath plot"""
    if not session_data["current_points"]:
        return jsonify({"error": "No DXF file loaded"}), 400

    # Filter points for engraving only
    engraving_elements = {}
    for x, y, radius, geom_type, element_id in session_data["current_points"]:
        if (
            element_id in session_data["engraved_elements"]
            and element_id not in session_data["removed_elements"]
        ):
            if element_id not in engraving_elements:
                engraving_elements[element_id] = {
                    "geom_type": geom_type,
                    "radius": radius,
                    "points": [],
                }
            engraving_elements[element_id]["points"].append((x, y))

    if not engraving_elements:
        return jsonify({"error": "No elements marked for engraving"}), 400

    # Generate G-code
    gcode = generate_gcode(engraving_elements)

    # Create toolpath plot
    plot_image = create_gcode_toolpath_plot(gcode)

    return jsonify(
        {
            "success": True,
            "plot_image": plot_image,
            "element_count": len(engraving_elements),
        }
    )


def create_gcode_toolpath_plot(gcode):
    """Create matplotlib plot of G-code toolpath and return as base64 image"""
    fig, ax = plt.subplots(figsize=(10, 8), dpi=100)

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
                    try:
                        x_pos = float(part[1:])
                    except ValueError:
                        continue
                elif part.startswith("Y"):
                    try:
                        y_pos = float(part[1:])
                    except ValueError:
                        continue

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
                    try:
                        x_pos = float(part[1:])
                    except ValueError:
                        continue
                elif part.startswith("Y"):
                    try:
                        y_pos = float(part[1:])
                    except ValueError:
                        continue

            if x_pos is not None:
                current_x = x_pos
            if y_pos is not None:
                current_y = y_pos

            # Draw engraving move
            engraving_lines.append([(last_x, last_y), (current_x, current_y)])
            last_x = current_x
            last_y = current_y

    # Plot positioning moves in green with arrows
    positioning_labeled = False
    for line_segment in positioning_lines:
        start, end = line_segment
        if start != end:  # Only plot if there's actual movement
            ax.plot(
                [start[0], end[0]],
                [start[1], end[1]],
                "g-",
                linewidth=2,
                alpha=0.8,
                label="Positioning (G0)" if not positioning_labeled else "",
            )
            positioning_labeled = True

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

                # Arrow length (proportional to line length)
                arrow_length = max(0.3, length * 0.15)

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
    engraving_labeled = False
    for line_segment in engraving_lines:
        start, end = line_segment
        if start != end:  # Only plot if there's actual movement
            ax.plot(
                [start[0], end[0]],
                [start[1], end[1]],
                "r-",
                linewidth=2,
                alpha=0.8,
                label="Engraving (G1)" if not engraving_labeled else "",
            )
            engraving_labeled = True

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

                # Arrow length (proportional to line length)
                arrow_length = max(0.3, length * 0.15)

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

    # Add start point marker
    ax.plot(0, 0, "go", markersize=8, label="Start")

    # Set up the plot
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_title("G-code Toolpath Preview")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")
    ax.legend()

    # Convert plot to base64 image
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png", bbox_inches="tight", dpi=100)
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close(fig)

    return img_base64


@app.route("/find_element_at_click", methods=["POST"])
def find_element_at_click():
    """Find the closest element to a click position"""
    try:
        data = request.get_json()
        print(f"Click request data: {data}")

        if not data:
            print("ERROR: No JSON data received")
            return jsonify({"error": "No data received"}), 400

        if "x" not in data or "y" not in data:
            print(f"ERROR: Missing x or y coordinates in data: {data}")
            return jsonify({"error": "Missing x or y coordinates"}), 400

        click_x = data["x"]
        click_y = data["y"]
        print(f"Processing click at: ({click_x}, {click_y})")

        if not session_data["current_points"]:
            print(
                f"ERROR: No current points. Session data: {len(session_data['original_points'])} original points"
            )
            return jsonify({"error": "No DXF file loaded"}), 400

        # Convert normalized coordinates to actual plot coordinates
        # We need to get the plot bounds to convert properly
        unique_elements = {}
        for x, y, radius, geom_type, element_id in session_data["current_points"]:
            if element_id not in unique_elements:
                unique_elements[element_id] = {
                    "geom_type": geom_type,
                    "radius": radius,
                    "points": [],
                }
            unique_elements[element_id]["points"].append((x, y))

        if not unique_elements:
            return jsonify({"error": "No elements to select"}), 400

        # Calculate plot bounds (same as in create_plot_image)
        all_x = []
        all_y = []

        for element_id, element_info in unique_elements.items():
            if element_id in session_data["removed_elements"]:
                continue

            points = element_info["points"]
            radius = element_info["radius"]
            geom_type = element_info["geom_type"]

            for point in points:
                all_x.append(point[0])
                all_y.append(point[1])

            # For circles, extend bounds to include the full circle
            if geom_type == "CIRCLE" and len(points) >= 1:
                center_x, center_y = points[0]
                all_x.extend([center_x - radius, center_x + radius])
                all_y.extend([center_y - radius, center_y + radius])

        if not all_x or not all_y:
            return jsonify({"error": "No valid points found"}), 400

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        # Add same padding as in create_plot_image
        x_range = max_x - min_x
        y_range = max_y - min_y
        padding_x = max(x_range * 0.1, 10)  # At least 10mm padding
        padding_y = max(y_range * 0.1, 10)  # At least 10mm padding

        min_x -= padding_x
        max_x += padding_x
        min_y -= padding_y
        max_y += padding_y

        # The problem is that the web image might be scaled differently than the matplotlib figure
        # We need to account for the actual plot area that matplotlib creates

        # Matplotlib creates a figure with aspect ratio enforcement
        # When we use bbox_inches="tight", it crops to the actual data
        # But we need to account for equal aspect ratio

        data_width = max_x - min_x
        data_height = max_y - min_y

        if data_width == 0:
            data_width = 1
        if data_height == 0:
            data_height = 1

        # Simple direct mapping - this should work if the image displays the full data range
        actual_x = min_x + click_x * data_width
        actual_y = max_y - click_y * data_height  # Flip Y and use max_y as origin

        # Debug logging
        print(f"Click coordinates: normalized=({click_x:.3f}, {click_y:.3f})")
        print(
            f"Data bounds: x=({min_x:.3f}, {max_x:.3f}), y=({min_y:.3f}, {max_y:.3f})"
        )
        print(f"Actual coordinates: ({actual_x:.3f}, {actual_y:.3f})")

        # Find closest element
        closest_element_id = None
        closest_distance = float("inf")
        checked_elements = []

        for element_id, element_info in unique_elements.items():
            if element_id in session_data["removed_elements"]:
                continue

            geom_type = element_info["geom_type"]
            radius = element_info["radius"]
            points = element_info["points"]

            if geom_type == "CIRCLE" and len(points) >= 1:
                center_x, center_y = points[0]
                distance_to_center = math.sqrt(
                    (actual_x - center_x) ** 2 + (actual_y - center_y) ** 2
                )
                # Calculate distance to circumference (not center)
                distance_to_circumference = abs(distance_to_center - radius)
                # Use tolerance for circumference selection
                tolerance = 50.0  # 50mm tolerance for circle circumference - increased for easier selection
                checked_elements.append(
                    f"Circle {element_id}: center=({center_x:.1f},{center_y:.1f}), radius={radius:.1f}, distance_to_circumference={distance_to_circumference:.1f}, tolerance={tolerance:.1f}"
                )
                if (
                    distance_to_circumference <= tolerance
                    and distance_to_circumference < closest_distance
                ):
                    closest_distance = distance_to_circumference
                    closest_element_id = element_id

            elif geom_type in ["LINE", "LWPOLYLINE"] and len(points) >= 2:
                # Check distance to line segments
                for i in range(len(points) - 1):
                    p1 = points[i]
                    p2 = points[i + 1]
                    distance = point_to_line_distance((actual_x, actual_y), p1, p2)
                    tolerance = 50.0  # 50mm tolerance for lines - much larger for easier selection
                    checked_elements.append(
                        f"Line {element_id}: p1=({p1[0]:.1f},{p1[1]:.1f}), p2=({p2[0]:.1f},{p2[1]:.1f}), distance={distance:.1f}, tolerance={tolerance:.1f}"
                    )
                    if distance <= tolerance and distance < closest_distance:
                        closest_distance = distance
                        closest_element_id = element_id

        print(f"Checked {len(checked_elements)} elements:")
        for elem in checked_elements:  # Show all elements for debugging
            print(f"  {elem}")
        print(f"Total elements by type:")
        circles = len(
            [e for e in unique_elements.values() if e["geom_type"] == "CIRCLE"]
        )
        lines = len([e for e in unique_elements.values() if e["geom_type"] == "LINE"])
        polylines = len(
            [e for e in unique_elements.values() if e["geom_type"] == "LWPOLYLINE"]
        )
        print(f"  Circles: {circles}, Lines: {lines}, Polylines: {polylines}")

        # Show all elements within tolerance
        selectable_elements = []
        for element_id, element_info in unique_elements.items():
            if element_id in session_data["removed_elements"]:
                continue
                
            geom_type = element_info["geom_type"]
            radius = element_info["radius"]
            points = element_info["points"]
            
            if geom_type == "CIRCLE" and len(points) >= 1:
                center_x, center_y = points[0]
                distance_to_center = math.sqrt((actual_x - center_x) ** 2 + (actual_y - center_y) ** 2)
                distance_to_circumference = abs(distance_to_center - radius)
                if distance_to_circumference <= 50.0:
                    selectable_elements.append(f"SELECTABLE Circle {element_id}: distance={distance_to_circumference:.1f}")
                    
            elif geom_type in ["LINE", "LWPOLYLINE"] and len(points) >= 2:
                for i in range(len(points) - 1):
                    p1 = points[i]
                    p2 = points[i + 1]
                    distance = point_to_line_distance((actual_x, actual_y), p1, p2)
                    if distance <= 50.0:
                        selectable_elements.append(f"SELECTABLE Line {element_id}: distance={distance:.1f}")
                        break  # Only check first segment for each line
        
        print(f"Elements within tolerance: {len(selectable_elements)}")
        for elem in selectable_elements:
            print(f"  {elem}")

        print(
            f"Closest element: {closest_element_id}, distance: {closest_distance:.3f}"
        )

        if closest_element_id:
            # Toggle element selection
            if closest_element_id in session_data["selected_elements"]:
                session_data["selected_elements"].remove(closest_element_id)
                print(f"Removed element {closest_element_id} from selection")
            else:
                session_data["selected_elements"].add(closest_element_id)
                print(f"Added element {closest_element_id} to selection")

            return jsonify(
                {
                    "success": True,
                    "element_id": closest_element_id,
                    "distance": closest_distance,
                    "selected": closest_element_id in session_data["selected_elements"],
                }
            )
        else:
            print("No element found within tolerance")
            return jsonify(
                {"success": False, "message": "No element found at click position"}
            )

    except Exception as e:
        return jsonify({"error": f"Failed to find element: {str(e)}"}), 500


@app.route("/get_plot", methods=["GET"])
def get_plot():
    """Get current plot with selected elements highlighted"""
    try:
        plot_image = create_plot_image(session_data["selected_elements"])

        return jsonify({"success": True, "plot_image": plot_image})

    except Exception as e:
        return jsonify({"error": f"Failed to get plot: {str(e)}"}), 500


def point_to_line_distance(point, line_start, line_end):
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


def clamp_to_workspace(x, y):
    """Clamp coordinates to workspace limits"""
    max_x = session_data["gcode_settings"]["max_workspace_x"]
    max_y = session_data["gcode_settings"]["max_workspace_y"]

    clamped_x = max(0, min(x, max_x))
    clamped_y = max(0, min(y, max_y))

    # Log if coordinates were clamped
    if x != clamped_x or y != clamped_y:
        print(
            f"WARNING: Coordinates clamped from ({x:.3f}, {y:.3f}) to ({clamped_x:.3f}, {clamped_y:.3f})"
        )

    return clamped_x, clamped_y


def generate_gcode(elements_by_id):
    """Generate G-code from elements"""
    gcode = []

    # Add preamble
    preamble_lines = session_data["gcode_settings"]["preamble"].strip().split("\n")
    gcode.extend(preamble_lines)
    gcode.append("")

    # Generate G-code for each element
    for element_id, element_info in elements_by_id.items():
        geom_type = element_info["geom_type"]
        radius = element_info["radius"]

        if geom_type == "LINE":
            gcode.append("; === LINE GEOMETRY ===")
            line_points = element_info["points"]
            if len(line_points) >= 2:
                start_x, start_y = line_points[0]
                end_x, end_y = line_points[1]

                # Clamp coordinates to workspace limits
                start_x, start_y = clamp_to_workspace(start_x, start_y)
                end_x, end_y = clamp_to_workspace(end_x, end_y)

                # Position to start point
                gcode.append(f"G0 X{start_x:.3f} Y{start_y:.3f}")

                # Turn on laser and lower Z
                gcode.append(
                    f"M3 S{session_data['gcode_settings']['laser_power']} ; Turn on laser"
                )
                gcode.append(
                    f"G1 Z{session_data['gcode_settings']['cutting_z']:.3f} F{session_data['gcode_settings']['feedrate']} ; Lower Z"
                )

                # Engrave to end point
                gcode.append(f"G1 X{end_x:.3f} Y{end_y:.3f} ; Engrave line")

                # Turn off laser and raise Z
                gcode.append("M5 ; Turn off laser")
                gcode.append("G0 Z5 ; Raise Z")
                gcode.append("")

        elif geom_type == "CIRCLE":
            gcode.append("; === CIRCLE GEOMETRY ===")
            circle_points = element_info["points"]
            if len(circle_points) >= 1:
                cx, cy = circle_points[0]
                radius = element_info["radius"]

                # Position to circle start point (top of circle)
                start_x = cx
                start_y = cy + radius
                start_x, start_y = clamp_to_workspace(start_x, start_y)
                gcode.append(f"G0 X{start_x:.3f} Y{start_y:.3f}")

                # Turn on laser and lower Z
                gcode.append(
                    f"M3 S{session_data['gcode_settings']['laser_power']} ; Turn on laser"
                )
                gcode.append(
                    f"G1 Z{session_data['gcode_settings']['cutting_z']:.3f} F{session_data['gcode_settings']['feedrate']} ; Lower Z"
                )

                # Generate circular path
                angles = list(range(90, 450, 5))
                angles.append(450)

                for i in angles:
                    angle = math.radians(i)
                    x = cx + radius * math.cos(angle)
                    y = cy + radius * math.sin(angle)
                    # Clamp each point to workspace limits
                    x, y = clamp_to_workspace(x, y)
                    gcode.append(f"G1 X{x:.3f} Y{y:.3f} ; Engrave circle")

                # Turn off laser and raise Z
                gcode.append("M5 ; Turn off laser")
                gcode.append("G0 Z5 ; Raise Z")
                gcode.append("")

        elif geom_type == "LWPOLYLINE":
            gcode.append("; === POLYLINE GEOMETRY ===")
            polyline_points = element_info["points"]
            if len(polyline_points) >= 2:
                # Position to first point
                first_x, first_y = polyline_points[0]
                first_x, first_y = clamp_to_workspace(first_x, first_y)
                gcode.append(f"G0 X{first_x:.3f} Y{first_y:.3f}")

                # Turn on laser and lower Z
                gcode.append(
                    f"M3 S{session_data['gcode_settings']['laser_power']} ; Turn on laser"
                )
                gcode.append(
                    f"G1 Z{session_data['gcode_settings']['cutting_z']:.3f} F{session_data['gcode_settings']['feedrate']} ; Lower Z"
                )

                # Engrave polyline segments
                for i in range(1, len(polyline_points)):
                    x, y = polyline_points[i]
                    # Clamp each point to workspace limits
                    x, y = clamp_to_workspace(x, y)
                    gcode.append(f"G1 X{x:.3f} Y{y:.3f} ; Engrave polyline")

                # Turn off laser and raise Z
                gcode.append("M5 ; Turn off laser")
                gcode.append("G0 Z5 ; Raise Z")
                gcode.append("")

    # Add postscript
    postscript_lines = session_data["gcode_settings"]["postscript"].strip().split("\n")
    gcode.append("")
    gcode.extend(postscript_lines)

    return "\n".join(gcode)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
