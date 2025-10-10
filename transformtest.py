import numpy as np
import math

# Ideal points on the circle
ideal_points = np.array(
    [
        [79.246, 21.234],
        [58.012, 58.012],
        [21.234, 79.246],
        [-21.234, 79.246],
        [-58.012, 58.012],
        [-79.246, 21.234],
        [-79.246, -21.234],
        [-58.012, -58.012],
        [-21.234, -79.246],
        [21.234, -79.246],
        [58.012, -58.012],
        [79.246, -21.234],
    ]
)

# Measured actual positions for point 7 and 12
actual_points = np.array(
    [
        [-83.35, -21.84],  # Corresponds to ideal point 7
        [75.85, -24.64],  # Corresponds to ideal point 12
    ]
)

# Extract corresponding ideal points
P1 = ideal_points[6]  # Point 7
P2 = ideal_points[11]  # Point 12
Q1 = actual_points[0]
Q2 = actual_points[1]

# Compute vector between points
v_ideal = P2 - P1
v_actual = Q2 - Q1

# Compute scale
scale = np.linalg.norm(v_actual) / np.linalg.norm(v_ideal)

# Compute rotation angle
angle_rad = math.atan2(v_actual[1], v_actual[0]) - math.atan2(v_ideal[1], v_ideal[0])
angle_deg = math.degrees(angle_rad)

# Rotation matrix
R = np.array(
    [
        [math.cos(angle_rad), -math.sin(angle_rad)],
        [math.sin(angle_rad), math.cos(angle_rad)],
    ]
)

# Compute translation
translated_P1 = scale * R @ P1
translation = Q1 - translated_P1

# Apply transformation to all ideal points
adjusted_points = scale * (R @ ideal_points.T).T + translation

# Print results
print(f"Rotation (degrees): {angle_deg:.4f}")
print(f"Translation vector: ({translation[0]:.4f}, {translation[1]:.4f})")
print("\nAdjusted Coordinates:")
for pt in adjusted_points:
    print(f"({pt[0]:.4f}, {pt[1]:.4f})")
