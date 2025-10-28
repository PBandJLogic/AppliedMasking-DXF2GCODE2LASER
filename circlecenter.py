import numpy as np
from scipy.optimize import least_squares

# Actual measured points
points = np.array(
    [
        [-226.0750, 50.0000],  # Pt2
        [0.0000, -174.4750],  # Pt4
        [222.2750, 50.0000],  # Pt6
    ]
)

# Known radius
R = 224.0661


# Cost function: difference between distance to center and radius
def residuals(center):
    x0, y0 = center
    return np.sqrt((points[:, 0] - x0) ** 2 + (points[:, 1] - y0) ** 2) - R


# Initial guess for center
initial_guess = [0, 0]

# Fit the center
result = least_squares(residuals, initial_guess)
center = result.x

# Compute actual radius from center to each point
distances = np.sqrt((points[:, 0] - center[0]) ** 2 + (points[:, 1] - center[1]) ** 2)
errors = distances - R

print("Best-fit center:", center)
print("Radial errors at each point:", errors)
