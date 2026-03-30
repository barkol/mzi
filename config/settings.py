"""Game configuration with responsive layout support for fullscreen."""
import logging
import pygame

logger = logging.getLogger(__name__)

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
    # Increased scaling for external monitors
    return max(12, int(size * FONT_SCALE))  # Increased minimum from 10 to 12

# Grid settings (base values for windowed mode)
BASE_GRID_SIZE = 45
BASE_CANVAS_WIDTH = 900
BASE_CANVAS_HEIGHT = 675
BASE_CANVAS_OFFSET_X = 280
BASE_CANVAS_OFFSET_Y = 120

# Dynamic grid settings for fullscreen
# These are now percentages of screen size for better scaling
FULLSCREEN_SIDEBAR_PERCENT = 0.20  # 20% of screen width (increased from 15%)
FULLSCREEN_RIGHT_PANEL_PERCENT = 0.18  # 18% of screen width (increased from 15%)
FULLSCREEN_TOP_MARGIN_PERCENT = 0.10  # 10% of screen height for title area
FULLSCREEN_CONTROL_HEIGHT_PERCENT = 0.15  # 15% of screen height for controls

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
WAVELENGTH = 20
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

# Quantum packet mode
QUANTUM_PACKET_SPEED = 400        # pixels per second
QUANTUM_PACKET_EMIT_INTERVAL = 0.4  # seconds between emissions
QUANTUM_PACKET_LENGTH = 30        # visual length in pixels
QUANTUM_COLLAPSE_DURATION = 0.3   # seconds for collapse animation
QUANTUM_MAX_FAMILIES = 20         # max concurrent packet families

def update_scaled_values(scale_factor, window_width=None, window_height=None, fullscreen=False):
    """Update all scaled values based on new scale factor and window size."""
    global SCALE_FACTOR, FONT_SCALE, IS_FULLSCREEN
    global GRID_SIZE, CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_OFFSET_X, CANVAS_OFFSET_Y
    global COMPONENT_RADIUS, BEAM_WIDTH
    global WINDOW_WIDTH, WINDOW_HEIGHT
    global CANVAS_GRID_COLS, CANVAS_GRID_ROWS
    
    SCALE_FACTOR = scale_factor
    IS_FULLSCREEN = fullscreen
    
    if fullscreen and window_width and window_height:
        # Detect external monitor (typically higher resolution than laptop screens)
        is_external_monitor = window_width >= 2560 or window_height >= 1440
        
        # Apply monitor-specific scaling boost
        if is_external_monitor:
            # MORE AGGRESSIVE: Boost scale factor by 2x-2.5x for external monitors
            if window_width >= 3840:  # 4K or larger
                ui_scale = scale_factor * 2.5
            elif window_width >= 2560:  # 1440p
                ui_scale = scale_factor * 2.0
            else:
                ui_scale = scale_factor * 1.8
            
            FONT_SCALE = min(3.5, max(1.2, ui_scale * 1.2))  # Extra boost for fonts
            SCALE_FACTOR = ui_scale  # UPDATE GLOBAL SCALE FACTOR!
        else:
            ui_scale = scale_factor * 1.2  # Even laptop screens get a small boost
            FONT_SCALE = min(2.0, max(0.8, ui_scale))
            SCALE_FACTOR = ui_scale
        
        # Update window dimensions
        WINDOW_WIDTH = window_width
        WINDOW_HEIGHT = window_height

        # Calculate grid size, capped for large screens
        max_grid_scale = 2.0 if is_external_monitor else ui_scale
        GRID_SIZE = min(int(BASE_GRID_SIZE * ui_scale),
                        int(BASE_GRID_SIZE * max_grid_scale))

        # Cap SCALE_FACTOR to stay proportional to GRID_SIZE so that
        # scale() values (panel sizes, margins) don't outgrow the grid
        effective_scale = GRID_SIZE / BASE_GRID_SIZE
        SCALE_FACTOR = effective_scale
        FONT_SCALE = min(3.5, max(0.8, effective_scale * 1.2))

        # Now compute UI panel sizes with the capped scale
        sidebar_width = max(int(window_width * FULLSCREEN_SIDEBAR_PERCENT),
                            scale(200))
        right_panel_width = max(int(window_width * FULLSCREEN_RIGHT_PANEL_PERCENT),
                                scale(180))
        top_margin = int(window_height * FULLSCREEN_TOP_MARGIN_PERCENT)
        control_height = max(int(window_height * FULLSCREEN_CONTROL_HEIGHT_PERCENT),
                             scale(80))

        canvas_margin = scale(20)
        bottom_margin = scale(15)

        available_width = window_width - sidebar_width - right_panel_width - (canvas_margin * 2)
        available_height = window_height - top_margin - control_height - canvas_margin - bottom_margin
        
        # FIXED: Calculate how many grid cells can fit in available space
        CANVAS_GRID_COLS = max(10, available_width // GRID_SIZE)
        CANVAS_GRID_ROWS = max(8, available_height // GRID_SIZE)
        
        # Cap grid dimensions for reasonable gameplay
        CANVAS_GRID_COLS = min(CANVAS_GRID_COLS, 40 if is_external_monitor else 30)
        CANVAS_GRID_ROWS = min(CANVAS_GRID_ROWS, 25 if is_external_monitor else 20)
        
        # Calculate actual canvas size
        CANVAS_WIDTH = CANVAS_GRID_COLS * GRID_SIZE
        CANVAS_HEIGHT = CANVAS_GRID_ROWS * GRID_SIZE
        
        # Center canvas in available space, clamp to non-negative
        CANVAS_OFFSET_X = max(sidebar_width + canvas_margin,
                              sidebar_width + (available_width - CANVAS_WIDTH) // 2)
        CANVAS_OFFSET_Y = max(canvas_margin,
                              top_margin + (available_height - CANVAS_HEIGHT) // 2)

        # Component sizes - proportional to grid
        COMPONENT_RADIUS = max(12, min(int(GRID_SIZE * 0.3),
                                        int(BASE_COMPONENT_RADIUS * effective_scale)))
        
        # Ensure component fits in grid cell with spacing
        max_radius = int(GRID_SIZE * 0.3)  # 60% diameter leaves 40% spacing
        COMPONENT_RADIUS = min(COMPONENT_RADIUS, max_radius)
        COMPONENT_RADIUS = max(COMPONENT_RADIUS, 12)  # Minimum size
        
        # Beam width scales with grid
        BEAM_WIDTH = max(3, int(BASE_BEAM_WIDTH * effective_scale))
        
        logger.debug(
            "Fullscreen layout: %dx%d | External: %s | UI scale: %.2f (base: %.2f) | "
            "Grid: %dpx | Canvas: %dx%d cells = %dx%dpx at (%d,%d) | "
            "Component radius: %dpx (%.0f%%)",
            window_width, window_height, is_external_monitor, ui_scale, scale_factor,
            GRID_SIZE, CANVAS_GRID_COLS, CANVAS_GRID_ROWS, CANVAS_WIDTH, CANVAS_HEIGHT,
            CANVAS_OFFSET_X, CANVAS_OFFSET_Y, COMPONENT_RADIUS,
            (COMPONENT_RADIUS * 2 / GRID_SIZE) * 100
        )
        
    else:
        # Windowed mode
        FONT_SCALE = min(2.0, max(0.5, scale_factor))
        GRID_SIZE = scale(BASE_GRID_SIZE)
        COMPONENT_RADIUS = scale(BASE_COMPONENT_RADIUS)
        BEAM_WIDTH = scale(BASE_BEAM_WIDTH)

        # Use actual window size if provided, otherwise compute from scale
        WINDOW_WIDTH = window_width if window_width else int(DESIGN_WIDTH * scale_factor)
        WINDOW_HEIGHT = window_height if window_height else int(DESIGN_HEIGHT * scale_factor)

        # Compute layout from actual window size
        sidebar_w = min(scale(230), int(WINDOW_WIDTH * 0.18))
        right_panel_w = min(scale(200), int(WINDOW_WIDTH * 0.16))
        top_margin = scale(BASE_CANVAS_OFFSET_Y)
        control_h = scale(80)

        CANVAS_OFFSET_X = sidebar_w + scale(15)
        CANVAS_OFFSET_Y = top_margin
        available_w = WINDOW_WIDTH - CANVAS_OFFSET_X - right_panel_w - scale(15)
        available_h = WINDOW_HEIGHT - CANVAS_OFFSET_Y - control_h - scale(15)

        # Fit grid cells in available space
        CANVAS_GRID_COLS = max(10, available_w // GRID_SIZE)
        CANVAS_GRID_ROWS = max(8, available_h // GRID_SIZE)
        CANVAS_WIDTH = CANVAS_GRID_COLS * GRID_SIZE
        CANVAS_HEIGHT = CANVAS_GRID_ROWS * GRID_SIZE
        
        logger.debug(
            "Windowed mode: %dx%d | Scale: %.2f | Canvas: %dx%d cells",
            WINDOW_WIDTH, WINDOW_HEIGHT, scale_factor, CANVAS_GRID_COLS, CANVAS_GRID_ROWS
        )

def get_sidebar_width():
    """Get the current sidebar width based on display mode."""
    if IS_FULLSCREEN:
        sidebar_width = int(WINDOW_WIDTH * FULLSCREEN_SIDEBAR_PERCENT)
        min_width = scale(280)
        return max(sidebar_width, min_width)
    else:
        # Sidebar fills space left of canvas
        return max(scale(100), CANVAS_OFFSET_X - scale(10))

def get_right_panel_width():
    """Get the current right panel width based on display mode."""
    if IS_FULLSCREEN:
        panel_width = int(WINDOW_WIDTH * FULLSCREEN_RIGHT_PANEL_PERCENT)
        min_width = scale(250)
        return max(panel_width, min_width)
    else:
        return max(scale(80), WINDOW_WIDTH - CANVAS_OFFSET_X - CANVAS_WIDTH - scale(10))

def get_control_panel_height():
    """Get the current control panel height based on display mode."""
    if IS_FULLSCREEN:
        control_height = int(WINDOW_HEIGHT * FULLSCREEN_CONTROL_HEIGHT_PERCENT)
        min_height = scale(100)
        return max(control_height, min_height)
    else:
        return scale(100)

def get_control_panel_y():
    """Get the Y position for the control panel."""
    if IS_FULLSCREEN:
        # Position control panel at bottom with margin
        return WINDOW_HEIGHT - get_control_panel_height() - scale(20)
    else:
        # Traditional positioning
        return CANVAS_OFFSET_Y + CANVAS_HEIGHT + scale(20)