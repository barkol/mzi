"""
Mach-Zehnder Interferometer Game
Main entry point for the application with fixed scaling support
"""
import pygame
import sys
import platform
from core.game import Game
from config.settings import *

def get_display_mode():
    """Get the best display mode for the game."""
    pygame.init()
    
    # Get display info
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h
    
    print(f"Screen resolution: {screen_width}x{screen_height}")
    print(f"Design resolution: {DESIGN_WIDTH}x{DESIGN_HEIGHT}")
    print(f"Platform: {platform.system()}")
    
    # Calculate scale factor
    scale_x = screen_width / DESIGN_WIDTH
    scale_y = screen_height / DESIGN_HEIGHT
    scale_factor = min(scale_x, scale_y)
    
    # Check command line arguments
    fullscreen = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--fullscreen" or sys.argv[1] == "-f":
            fullscreen = True
            scale_factor = min(scale_x, scale_y)
        elif sys.argv[1] == "--scale" or sys.argv[1] == "-s":
            # Scale to 90% of screen size
            scale_factor = min(scale_x, scale_y) * 0.9
    else:
        # Default: use 90% of available space or original size
        if scale_factor > 1.0:
            scale_factor = min(1.0, scale_factor * 0.9)
        else:
            scale_factor = min(scale_x, scale_y) * 0.9
    
    # Update all scaled values BEFORE creating any UI
    update_scaled_values(scale_factor)
    
    if fullscreen:
        print(f"Using fullscreen mode with scale factor: {scale_factor:.2f}")
        return (screen_width, screen_height), pygame.FULLSCREEN, scale_factor
    else:
        window_width = int(DESIGN_WIDTH * scale_factor)
        window_height = int(DESIGN_HEIGHT * scale_factor)
        print(f"Using windowed mode: {window_width}x{window_height} (scale: {scale_factor:.2f})")
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
    
    # Create game instance with scale factor
    game = Game(screen, scale_factor)
    
    # Store default cursor
    default_cursor = pygame.mouse.get_cursor()
    drag_cursor = pygame.SYSTEM_CURSOR_HAND
    
    # Game loop
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # Handle events
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
                    # Update scaled values FIRST
                    update_scaled_values(scale_factor)
                    # Then set display mode
                    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                    # Then update game
                    game.update_scale(scale_factor)
                    game.update_screen_references(screen, screen)
                    print(f"Switched to windowed mode, scale: {scale_factor:.2f}")
                    continue
                elif event.key == pygame.K_F11:
                    # Toggle fullscreen
                    if is_fullscreen:
                        # Exit fullscreen
                        is_fullscreen = False
                        info = pygame.display.Info()
                        scale_factor = min(1.0, min(info.current_w / DESIGN_WIDTH,
                                                  info.current_h / DESIGN_HEIGHT) * 0.9)
                        # Update scaled values FIRST
                        update_scaled_values(scale_factor)
                        # Then set display mode
                        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                    else:
                        # Enter fullscreen
                        is_fullscreen = True
                        info = pygame.display.Info()
                        scale_x = info.current_w / DESIGN_WIDTH
                        scale_y = info.current_h / DESIGN_HEIGHT
                        scale_factor = min(scale_x, scale_y)
                        # Update scaled values FIRST
                        update_scaled_values(scale_factor)
                        # Then set display mode
                        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                    
                    # Update game after display mode change
                    game.update_scale(scale_factor)
                    game.update_screen_references(screen, screen)
                    mode = "fullscreen" if is_fullscreen else "windowed"
                    print(f"Switched to {mode} mode with scale: {scale_factor:.2f}")
                    print(f"Window size: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
                    print(f"Canvas offset: ({CANVAS_OFFSET_X}, {CANVAS_OFFSET_Y})")
                    continue
            elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
                # Handle window resize
                new_scale_x = event.w / DESIGN_WIDTH
                new_scale_y = event.h / DESIGN_HEIGHT
                scale_factor = min(new_scale_x, new_scale_y)
                
                # Update scaled values FIRST
                update_scaled_values(scale_factor)
                
                # Then resize the display
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                
                # Finally update the game
                game.update_scale(scale_factor)
                game.update_screen_references(screen, screen)
                
                print(f"Window resized to {event.w}x{event.h}, new scale: {scale_factor:.2f}")
                print(f"Canvas offset: ({CANVAS_OFFSET_X}, {CANVAS_OFFSET_Y})")
                print(f"Canvas size: {CANVAS_WIDTH}x{CANVAS_HEIGHT}")
            
            game.handle_event(event)
        
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

if __name__ == "__main__":
    print("\nPhoton Path: Mach-Zehnder Interferometer")
    print("========================================")
    print("Usage:")
    print("  python main.py              - Run in auto-scaled windowed mode")
    print("  python main.py --fullscreen - Run in fullscreen mode")
    print("  python main.py --scale      - Run in 90% scaled windowed mode")
    print("\nControls:")
    print("  F11 - Toggle fullscreen")
    print("  ESC - Exit fullscreen")
    print()
    
    main()