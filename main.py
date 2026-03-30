"""
Mach-Zehnder Interferometer Game
Main entry point with responsive fullscreen support
"""

__version__ = "1.0.0"

import logging
import pygame
import sys
import platform
from core.game import Game
import config.settings as _settings
from config.settings import (
    DESIGN_WIDTH, DESIGN_HEIGHT, update_scaled_values,
    get_sidebar_width, get_right_panel_width,
    get_control_panel_height, scale,
)

logger = logging.getLogger(__name__)

def get_display_mode():
    """Get the best display mode for the game."""
    # Set DPI awareness on Windows BEFORE pygame.init() so that
    # pygame coordinates match physical pixels at all scale factors.
    if platform.system() == 'Windows':
        try:
            import ctypes
            # Try per-monitor v2 first (best), then v1, then legacy
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
                except Exception:
                    ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
        # Also tell SDL to handle DPI
        os.environ.setdefault('SDL_WINDOWS_DPI_AWARENESS', 'permonitorv2')

    pygame.init()

    # Get display info
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h

    logger.info("Screen: %dx%d | Design: %dx%d | Platform: %s",
                screen_width, screen_height, DESIGN_WIDTH, DESIGN_HEIGHT, platform.system())
    
    # Calculate scale factor
    scale_x = screen_width / DESIGN_WIDTH
    scale_y = screen_height / DESIGN_HEIGHT
    scale_factor = min(scale_x, scale_y)
    
    # Check command line arguments
    fullscreen = False
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--fullscreen", "-f"):
            fullscreen = True
        elif sys.argv[1] in ("--scale", "-s"):
            # Scale to 90% of screen size
            scale_factor = min(scale_x, scale_y) * 0.9
    else:
        # Default: use 90% of available space or original size
        if scale_factor > 1.0:
            scale_factor = min(1.0, scale_factor * 0.9)
        else:
            scale_factor = min(scale_x, scale_y) * 0.9
    
    if fullscreen:
        # Fullscreen mode - use actual screen dimensions
        # Scale factor determines UI element sizes but not layout
        scale_factor = min(scale_x, scale_y)
        
        # Remove the aggressive scale factor limits - let the settings.py handle it
        # The 1.5x boost for external monitors is now handled in update_scaled_values
        
        # Update scaled values with fullscreen layout
        update_scaled_values(scale_factor, screen_width, screen_height, fullscreen=True)
        
        logger.info("Fullscreen mode, base scale: %.2f", scale_factor)
        return (screen_width, screen_height), pygame.FULLSCREEN, scale_factor
    else:
        # Windowed mode - traditional scaling
        update_scaled_values(scale_factor, fullscreen=False)

        window_width = int(DESIGN_WIDTH * scale_factor)
        window_height = int(DESIGN_HEIGHT * scale_factor)
        logger.info("Windowed mode: %dx%d (scale: %.2f)", window_width, window_height, scale_factor)
        return (window_width, window_height), pygame.RESIZABLE, scale_factor

def main():
    """Initialize and run the game."""
    # Get display mode and scale factor
    display_size, display_flags, scale_factor = get_display_mode()
    
    pygame.init()
    pygame.display.set_caption("Photon Path: Mach-Zehnder Interferometer")
    
    # Create display
    screen = pygame.display.set_mode(display_size, display_flags)
    is_fullscreen = (display_flags == pygame.FULLSCREEN)
    
    clock = pygame.time.Clock()
    
    # Create game instance
    game = Game(screen, scale_factor)
    
    # Store default cursor
    default_cursor = pygame.mouse.get_cursor()
    drag_cursor = pygame.SYSTEM_CURSOR_HAND
    
    # Game loop
    running = True
    pending_resize = None  # debounce resize events

    while running:
        dt = clock.tick(_settings.FPS) / 1000.0

        # Handle events — collect last resize, apply after loop
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and is_fullscreen:
                    # Exit fullscreen
                    is_fullscreen = False
                    info = pygame.display.Info()
                    scale_factor = min(1.0, min(info.current_w / DESIGN_WIDTH,
                                              info.current_h / DESIGN_HEIGHT) * 0.9)
                    win_w = int(DESIGN_WIDTH * scale_factor)
                    win_h = int(DESIGN_HEIGHT * scale_factor)
                    update_scaled_values(scale_factor, window_width=win_w,
                                         window_height=win_h, fullscreen=False)
                    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
                    game.update_scale(scale_factor)
                    game.update_screen_references(screen, screen)
                    logger.info("Switched to windowed mode")
                    continue
                elif event.key == pygame.K_F11 and not is_fullscreen:
                    # Only allow F11 to enter fullscreen in windowed mode
                    # Enter fullscreen
                    is_fullscreen = True
                    info = pygame.display.Info()
                    scale_x = info.current_w / DESIGN_WIDTH
                    scale_y = info.current_h / DESIGN_HEIGHT
                    scale_factor = min(scale_x, scale_y)
                    
                    # Remove the scale factor limits - let settings.py handle it
                    
                    update_scaled_values(scale_factor, info.current_w, info.current_h, fullscreen=True)
                    
                    # Store the actual screen for later reference
                    actual_screen = screen
                    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                    
                    game.update_scale(scale_factor)
                    game.update_screen_references(screen, actual_screen)
                    
                    # Manual UI component updates if needed
                    if hasattr(game, 'update_layout'):
                        game.update_layout()
                    
                    logger.info("Switched to fullscreen, scale: %.2f, canvas: %dx%d at (%d,%d)",
                               scale_factor, _settings.CANVAS_WIDTH, _settings.CANVAS_HEIGHT, _settings.CANVAS_OFFSET_X, _settings.CANVAS_OFFSET_Y)
                    continue
            elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
                # Debounce: only record the latest resize, apply after all events
                pending_resize = (event.w, event.h)
            
            game.handle_event(event)
        
        # Apply debounced resize (only the final size from this frame)
        if pending_resize:
            rw, rh = pending_resize
            pending_resize = None
            new_scale_x = rw / DESIGN_WIDTH
            new_scale_y = rh / DESIGN_HEIGHT
            scale_factor = min(new_scale_x, new_scale_y)
            update_scaled_values(scale_factor, window_width=rw,
                                 window_height=rh, fullscreen=False)
            screen = pygame.display.set_mode((rw, rh), pygame.RESIZABLE)
            game.update_scale(scale_factor)
            game.update_screen_references(screen, screen)

        # Update cursor
        if game.sidebar.dragging:
            pygame.mouse.set_cursor(drag_cursor)
        else:
            pygame.mouse.set_cursor(default_cursor)
        
        # Update
        game.update(dt)
        
        # Draw
        game.draw()
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

def _setup_logging():
    """Configure logging based on --verbose flag."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    # Remove the flag so it doesn't interfere with other arg parsing
    sys.argv = [a for a in sys.argv if a not in ("--verbose", "-v")]

    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s [%(name)s] %(message)s",
    )


if __name__ == "__main__":
    _setup_logging()
    logger.info(
        "Photon Path: Mach-Zehnder Interferometer\n"
        "Usage: python main.py [--fullscreen|-f] [--scale|-s] [--verbose|-v]"
    )
    main()