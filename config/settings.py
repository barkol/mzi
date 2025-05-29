"""Game configuration and constants."""
import pygame

# Window settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
FPS = 60

# Grid settings
GRID_SIZE = 40  # Grid spacing in pixels
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
CANVAS_OFFSET_X = 300
CANVAS_OFFSET_Y = 100

# Colors (RGB)
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
PURPLE = (138, 43, 226)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_PURPLE = (26, 10, 46)

# UI Colors (RGBA)
GRID_COLOR = (138, 43, 226, 40)
GRID_MAJOR_COLOR = (138, 43, 226, 80)
HOVER_VALID_COLOR = (0, 255, 255, 80)
HOVER_INVALID_COLOR = (255, 0, 0, 80)

# Component settings
COMPONENT_RADIUS = 25
BEAM_WIDTH = 3

# Physics settings
WAVELENGTH = 30  # Wavelength in pixels (λ = 30px) - not a multiple of grid size
SPEED_OF_LIGHT = 300  # pixels per second (arbitrary units)

# Component losses (0.0 = no loss, 1.0 = complete loss)
MIRROR_LOSS = 0.05  # 5% loss at each mirror (95% transmission)
BEAM_SPLITTER_LOSS = 0.0  # No loss at beam splitters
DETECTOR_DECAY_RATE = 0.95  # How fast detector readings decay (visual effect only)

# Set to True for ideal components (no losses)
# When True, all components have 100% efficiency
IDEAL_COMPONENTS = False  # Change to True for perfect components

# Beam splitter model
# Set to True for realistic beam splitter with π/2 phase shift on reflection
# Set to False for simplified model with no phase shifts
REALISTIC_BEAM_SPLITTER = False  # Change to True for realistic phase behavior

# If you want custom losses, set IDEAL_COMPONENTS = False and adjust the values above
# Examples:
# MIRROR_LOSS = 0.0  # Perfect mirrors
# MIRROR_LOSS = 0.02  # 2% loss (98% reflectivity) - high quality mirrors
# MIRROR_LOSS = 0.10  # 10% loss (90% reflectivity) - standard mirrors

# Scoring
PLACEMENT_SCORE = 10
COMPLETION_SCORE = 100
