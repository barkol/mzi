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
        
        # FIXED: Calculate UI panel sizes as percentages of screen size
        sidebar_width = int(window_width * FULLSCREEN_SIDEBAR_PERCENT)
        right_panel_width = int(window_width * FULLSCREEN_RIGHT_PANEL_PERCENT)
        top_margin = int(window_height * FULLSCREEN_TOP_MARGIN_PERCENT)
        control_height = int(window_height * FULLSCREEN_CONTROL_HEIGHT_PERCENT)
        
        # Apply minimum sizes scaled by UI scale
        min_sidebar = scale(280)
        min_right_panel = scale(250)
        min_control_height = scale(100)
        
        sidebar_width = max(sidebar_width, min_sidebar)
        right_panel_width = max(right_panel_width, min_right_panel)
        control_height = max(control_height, min_control_height)
        
        # Calculate margins
        canvas_margin = scale(30)  # Space between panels and canvas
        bottom_margin = scale(20)  # Space at bottom
        
        # FIXED: Calculate available space for canvas
        available_width = window_width - sidebar_width - right_panel_width - (canvas_margin * 2)
        available_height = window_height - top_margin - control_height - canvas_margin - bottom_margin
        
        # Calculate grid size based on UI scale
        GRID_SIZE = int(BASE_GRID_SIZE * ui_scale)
        
        # Ensure grid isn't too large for very big screens
        if is_external_monitor:
            GRID_SIZE = min(GRID_SIZE, int(BASE_GRID_SIZE * 2.0))
        
        # FIXED: Calculate how many grid cells can fit in available space
        CANVAS_GRID_COLS = max(15, available_width // GRID_SIZE)
        CANVAS_GRID_ROWS = max(12, available_height // GRID_SIZE)
        
        # Cap grid dimensions for reasonable gameplay
        CANVAS_GRID_COLS = min(CANVAS_GRID_COLS, 40 if is_external_monitor else 30)
        CANVAS_GRID_ROWS = min(CANVAS_GRID_ROWS, 25 if is_external_monitor else 20)
        
        # Calculate actual canvas size
        CANVAS_WIDTH = CANVAS_GRID_COLS * GRID_SIZE
        CANVAS_HEIGHT = CANVAS_GRID_ROWS * GRID_SIZE
        
        # FIXED: Center canvas in available space
        CANVAS_OFFSET_X = sidebar_width + (available_width - CANVAS_WIDTH) // 2
        CANVAS_OFFSET_Y = top_margin + (available_height - CANVAS_HEIGHT) // 2
        
        # Component sizes - maintain proper ratio to grid
        component_scale = ui_scale * 0.7  # Components are 70% of UI scale
        COMPONENT_RADIUS = int(BASE_COMPONENT_RADIUS * component_scale)
        
        # Ensure component fits in grid cell with spacing
        max_radius = int(GRID_SIZE * 0.3)  # 60% diameter leaves 40% spacing
        COMPONENT_RADIUS = min(COMPONENT_RADIUS, max_radius)
        COMPONENT_RADIUS = max(COMPONENT_RADIUS, 12)  # Minimum size
        
        # Beam width scales with UI
        BEAM_WIDTH = int(BASE_BEAM_WIDTH * ui_scale)
        BEAM_WIDTH = max(BEAM_WIDTH, 3)  # Minimum width
        
        print(f"\nFullscreen layout: {window_width}x{window_height}")
        print(f"  External monitor: {is_external_monitor}")
        print(f"  UI scale: {ui_scale:.2f} (base: {scale_factor:.2f})")
        print(f"  Grid size: {GRID_SIZE}px")
        print(f"  Available space: {available_width}x{available_height}px")
        print(f"  Canvas: {CANVAS_GRID_COLS}x{CANVAS_GRID_ROWS} cells = {CANVAS_WIDTH}x{CANVAS_HEIGHT}px")
        print(f"  Canvas position: ({CANVAS_OFFSET_X}, {CANVAS_OFFSET_Y})")
        print(f"  Component radius: {COMPONENT_RADIUS}px (grid ratio: {(COMPONENT_RADIUS*2/GRID_SIZE)*100:.0f}%)")
        print(f"  UI Layout:")
        print(f"    Sidebar: {sidebar_width}px ({sidebar_width/window_width*100:.0f}%)")
        print(f"    Right panel: {right_panel_width}px ({right_panel_width/window_width*100:.0f}%)")
        print(f"    Top margin: {top_margin}px")
        print(f"    Control height: {control_height}px")
        
    else:
        # Windowed mode - use traditional scaling
        FONT_SCALE = min(2.0, max(0.5, scale_factor))
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
        
        print(f"\nWindowed mode: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        print(f"  Scale: {scale_factor:.2f}")
        print(f"  Canvas: {CANVAS_GRID_COLS}x{CANVAS_GRID_ROWS} cells")

def get_sidebar_width():
    """Get the current sidebar width based on display mode."""
    if IS_FULLSCREEN:
        sidebar_width = int(WINDOW_WIDTH * FULLSCREEN_SIDEBAR_PERCENT)
        min_width = scale(280)
        return max(sidebar_width, min_width)
    else:
        return CANVAS_OFFSET_X - scale(50)

def get_right_panel_width():
    """Get the current right panel width based on display mode."""
    if IS_FULLSCREEN:
        panel_width = int(WINDOW_WIDTH * FULLSCREEN_RIGHT_PANEL_PERCENT)
        min_width = scale(250)
        return max(panel_width, min_width)
    else:
        return WINDOW_WIDTH - (CANVAS_OFFSET_X + CANVAS_WIDTH + scale(50))

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