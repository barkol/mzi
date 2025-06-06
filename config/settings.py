"""Game configuration with responsive layout support for fullscreen."""
import pygame

# Base design resolution (minimum supported resolution)
DESIGN_WIDTH = 1600
DESIGN_HEIGHT = 900

# Window settings (will be overridden by scaling)
WINDOW_WIDTH = DESIGN_WIDTH
WINDOW_HEIGHT = DESIGN_HEIGHT
FPS = 60

# Scaling variables (will be set at runtime)
SCALE_FACTOR = 1.0
FONT_SCALE = 1.0
IS_FULLSCREEN = False  # Track fullscreen state

# Function to scale values
def scale(value):
    """Scale a value based on current scale factor."""
    if isinstance(value, (list, tuple)):
        return type(value)(int(v * SCALE_FACTOR) for v in value)
    return int(value * SCALE_FACTOR)

def scale_font(size):
    """Scale font size."""
    return max(8, int(size * FONT_SCALE))  # Minimum font size of 8

# Grid settings (base values for windowed mode)
BASE_GRID_SIZE = 45
BASE_CANVAS_WIDTH = 900
BASE_CANVAS_HEIGHT = 675
BASE_CANVAS_OFFSET_X = 280
BASE_CANVAS_OFFSET_Y = 120

# Dynamic grid settings for fullscreen
FULLSCREEN_MIN_SIDEBAR_WIDTH = 320
FULLSCREEN_MIN_RIGHT_PANEL_WIDTH = 300
FULLSCREEN_MIN_CONTROL_HEIGHT = 120
FULLSCREEN_CANVAS_MARGIN = 40

# These will be updated at runtime
GRID_SIZE = BASE_GRID_SIZE
CANVAS_WIDTH = BASE_CANVAS_WIDTH
CANVAS_HEIGHT = BASE_CANVAS_HEIGHT
CANVAS_OFFSET_X = BASE_CANVAS_OFFSET_X
CANVAS_OFFSET_Y = BASE_CANVAS_OFFSET_Y

# Canvas grid dimensions (will be calculated dynamically)
CANVAS_GRID_COLS = 20  # Default
CANVAS_GRID_ROWS = 15  # Default

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
BASE_COMPONENT_RADIUS = 16
BASE_BEAM_WIDTH = 4

# These will be updated at runtime
COMPONENT_RADIUS = BASE_COMPONENT_RADIUS
BEAM_WIDTH = BASE_BEAM_WIDTH

# Physics settings
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

def update_scaled_values(scale_factor, window_width=None, window_height=None, fullscreen=False):
    """Update all scaled values based on new scale factor and window size."""
    global SCALE_FACTOR, FONT_SCALE, IS_FULLSCREEN
    global GRID_SIZE, CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_OFFSET_X, CANVAS_OFFSET_Y
    global COMPONENT_RADIUS, BEAM_WIDTH
    global WINDOW_WIDTH, WINDOW_HEIGHT
    global CANVAS_GRID_COLS, CANVAS_GRID_ROWS
    
    SCALE_FACTOR = scale_factor
    FONT_SCALE = min(2.0, max(0.5, scale_factor))  # Limit font scaling
    IS_FULLSCREEN = fullscreen
    
    if fullscreen and window_width and window_height:
        # Fullscreen mode - use available space dynamically
        WINDOW_WIDTH = window_width
        WINDOW_HEIGHT = window_height
        
        # Calculate optimal grid size based on available space
        # Increase grid size in fullscreen for better spacing
        GRID_SIZE = int(BASE_GRID_SIZE * scale_factor * 1.2)  # 20% larger in fullscreen
        
        # Calculate UI panel sizes
        sidebar_width = max(scale(FULLSCREEN_MIN_SIDEBAR_WIDTH), int(window_width * 0.2))
        right_panel_width = max(scale(FULLSCREEN_MIN_RIGHT_PANEL_WIDTH), int(window_width * 0.18))
        control_height = scale(FULLSCREEN_MIN_CONTROL_HEIGHT)
        
        # Calculate canvas position and size to fill available space
        CANVAS_OFFSET_X = sidebar_width + scale(FULLSCREEN_CANVAS_MARGIN)
        CANVAS_OFFSET_Y = scale(140)  # Leave room for title/header
        
        # Calculate maximum canvas size
        max_canvas_width = window_width - CANVAS_OFFSET_X - right_panel_width - scale(FULLSCREEN_CANVAS_MARGIN)
        max_canvas_height = window_height - CANVAS_OFFSET_Y - control_height - scale(FULLSCREEN_CANVAS_MARGIN * 2)
        
        # Calculate how many grid cells fit
        CANVAS_GRID_COLS = max(15, min(30, max_canvas_width // GRID_SIZE))
        CANVAS_GRID_ROWS = max(12, min(20, max_canvas_height // GRID_SIZE))
        
        # Set canvas size based on grid
        CANVAS_WIDTH = CANVAS_GRID_COLS * GRID_SIZE
        CANVAS_HEIGHT = CANVAS_GRID_ROWS * GRID_SIZE
        
        # Center canvas in available space
        available_width = window_width - sidebar_width - right_panel_width - scale(FULLSCREEN_CANVAS_MARGIN * 2)
        if CANVAS_WIDTH < available_width:
            CANVAS_OFFSET_X += (available_width - CANVAS_WIDTH) // 2
        
        # Adjust component size for larger grid
        COMPONENT_RADIUS = int(BASE_COMPONENT_RADIUS * scale_factor * 1.15)
        BEAM_WIDTH = int(BASE_BEAM_WIDTH * scale_factor * 1.1)
        
        print(f"Fullscreen layout: {window_width}x{window_height}")
        print(f"  Grid size: {GRID_SIZE}px")
        print(f"  Canvas: {CANVAS_GRID_COLS}x{CANVAS_GRID_ROWS} cells ({CANVAS_WIDTH}x{CANVAS_HEIGHT}px)")
        print(f"  Canvas position: ({CANVAS_OFFSET_X}, {CANVAS_OFFSET_Y})")
        
    else:
        # Windowed mode - use traditional scaling
        GRID_SIZE = scale(BASE_GRID_SIZE)
        CANVAS_WIDTH = scale(BASE_CANVAS_WIDTH)
        CANVAS_HEIGHT = scale(BASE_CANVAS_HEIGHT)
        CANVAS_OFFSET_X = scale(BASE_CANVAS_OFFSET_X)
        CANVAS_OFFSET_Y = scale(BASE_CANVAS_OFFSET_Y)
        
        # Component radius maintains proper ratio to grid size
        COMPONENT_RADIUS = scale(BASE_COMPONENT_RADIUS)
        BEAM_WIDTH = scale(BASE_BEAM_WIDTH)
        
        # Update window size
        WINDOW_WIDTH = int(DESIGN_WIDTH * scale_factor)
        WINDOW_HEIGHT = int(DESIGN_HEIGHT * scale_factor)
        
        # Calculate grid dimensions
        CANVAS_GRID_COLS = CANVAS_WIDTH // GRID_SIZE
        CANVAS_GRID_ROWS = CANVAS_HEIGHT // GRID_SIZE

def get_sidebar_width():
    """Get the current sidebar width based on display mode."""
    if IS_FULLSCREEN:
        return max(scale(FULLSCREEN_MIN_SIDEBAR_WIDTH), int(WINDOW_WIDTH * 0.2))
    else:
        return CANVAS_OFFSET_X - scale(50)

def get_right_panel_width():
    """Get the current right panel width based on display mode."""
    if IS_FULLSCREEN:
        return max(scale(FULLSCREEN_MIN_RIGHT_PANEL_WIDTH), int(WINDOW_WIDTH * 0.18))
    else:
        return WINDOW_WIDTH - (CANVAS_OFFSET_X + CANVAS_WIDTH + scale(50))

def get_control_panel_height():
    """Get the current control panel height based on display mode."""
    if IS_FULLSCREEN:
        return scale(FULLSCREEN_MIN_CONTROL_HEIGHT)
    else:
        return scale(100)