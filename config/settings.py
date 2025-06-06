"""Game configuration and constants with scaling support."""
import pygame

# Base design resolution (what the game was designed for)
DESIGN_WIDTH = 1600
DESIGN_HEIGHT = 810

# Window settings (will be overridden by scaling)
WINDOW_WIDTH = DESIGN_WIDTH
WINDOW_HEIGHT = DESIGN_HEIGHT
FPS = 60

# Scaling variables (will be set at runtime)
SCALE_FACTOR = 1.0
FONT_SCALE = 1.0

# Function to scale values
def scale(value):
    """Scale a value based on current scale factor."""
    if isinstance(value, (list, tuple)):
        return type(value)(int(v * SCALE_FACTOR) for v in value)
    return int(value * SCALE_FACTOR)

def scale_font(size):
    """Scale font size."""
    return max(8, int(size * FONT_SCALE))  # Minimum font size of 8

# Grid settings (base values)
BASE_GRID_SIZE = 40
BASE_CANVAS_WIDTH = 800
BASE_CANVAS_HEIGHT = 600
BASE_CANVAS_OFFSET_X = 320
BASE_CANVAS_OFFSET_Y = 100

# These will be updated at runtime
GRID_SIZE = BASE_GRID_SIZE
CANVAS_WIDTH = BASE_CANVAS_WIDTH
CANVAS_HEIGHT = BASE_CANVAS_HEIGHT
CANVAS_OFFSET_X = BASE_CANVAS_OFFSET_X
CANVAS_OFFSET_Y = BASE_CANVAS_OFFSET_Y

# Colors (RGB)
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
PURPLE = (138, 43, 226)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_PURPLE = (26, 10, 46)
GOLD = (255, 215, 0)

# UI Colors (RGBA)
GRID_COLOR = (138, 43, 226, 40)
GRID_MAJOR_COLOR = (138, 43, 226, 80)
HOVER_VALID_COLOR = (0, 255, 255, 80)
HOVER_INVALID_COLOR = (255, 0, 0, 80)

# Component settings (base values)
BASE_COMPONENT_RADIUS = 25
BASE_BEAM_WIDTH = 5

# These will be updated at runtime
COMPONENT_RADIUS = BASE_COMPONENT_RADIUS
BEAM_WIDTH = BASE_BEAM_WIDTH

# Physics settings (don't scale these - they affect gameplay)
WAVELENGTH = 30
SPEED_OF_LIGHT = 300

# Component losses
MIRROR_LOSS = 0.05
BEAM_SPLITTER_LOSS = 0.0
DETECTOR_DECAY_RATE = 0.95

# Component behavior settings
IDEAL_COMPONENTS = True
REALISTIC_BEAM_SPLITTER = False

# Scoring
PLACEMENT_SCORE = 10
COMPLETION_SCORE = 100

def update_scaled_values(scale_factor):
    """Update all scaled values based on new scale factor."""
    global SCALE_FACTOR, FONT_SCALE
    global GRID_SIZE, CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_OFFSET_X, CANVAS_OFFSET_Y
    global COMPONENT_RADIUS, BEAM_WIDTH
    global WINDOW_WIDTH, WINDOW_HEIGHT
    
    SCALE_FACTOR = scale_factor
    FONT_SCALE = min(2.0, max(0.5, scale_factor))  # Limit font scaling
    
    # Update all scaled values
    GRID_SIZE = scale(BASE_GRID_SIZE)
    CANVAS_WIDTH = scale(BASE_CANVAS_WIDTH)
    CANVAS_HEIGHT = scale(BASE_CANVAS_HEIGHT)
    CANVAS_OFFSET_X = scale(BASE_CANVAS_OFFSET_X)
    CANVAS_OFFSET_Y = scale(BASE_CANVAS_OFFSET_Y)
    
    COMPONENT_RADIUS = scale(BASE_COMPONENT_RADIUS)
    BEAM_WIDTH = scale(BASE_BEAM_WIDTH)
    
    # Update window size
    WINDOW_WIDTH = int(DESIGN_WIDTH * scale_factor)
    WINDOW_HEIGHT = int(DESIGN_HEIGHT * scale_factor)