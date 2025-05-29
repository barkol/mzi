"""Game configuration and constants."""
import pygame

# Window settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
FPS = 60

# Grid settings
GRID_SIZE = 40
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
CANVAS_OFFSET_X = 300
CANVAS_OFFSET_Y = 100

# Colors
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
PURPLE = (138, 43, 226)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_PURPLE = (26, 10, 46)

# UI Colors
GRID_COLOR = (*PURPLE, 40)
GRID_MAJOR_COLOR = (*PURPLE, 80)
HOVER_VALID_COLOR = (*CYAN, 80)
HOVER_INVALID_COLOR = (*RED, 80)

# Component settings
COMPONENT_RADIUS = 25
BEAM_WIDTH = 3

# Physics settings
WAVELENGTH = 40
SPEED_OF_LIGHT = 300  # pixels per second (arbitrary units)

# Scoring
PLACEMENT_SCORE = 10
COMPLETION_SCORE = 100