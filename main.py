"""
Mach-Zehnder Interferometer Game
Main entry point with responsive fullscreen support
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
        elif sys.argv[1] == "--scale" or sys.argv[1] == "-s":
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
        
        # Adaptive scale factor limits based on screen size
        if screen_width > 3840:  # 4K ultra-wide or larger
            scale_factor = min(scale_factor, 2.5)
        elif screen_width > 2560:  # 4K or 1440p ultra-wide
            scale_factor = min(scale_factor, 2.0)
        else:  # 1080p and smaller
            scale_factor = min(scale_factor, 1.5)
        
        # Update scaled values with fullscreen layout
        update_scaled_values(scale_factor, screen_width, screen_height, fullscreen=True)
        
        print(f"Using fullscreen mode with responsive layout")
        print(f"  UI scale factor: {scale_factor:.2f}")
        print(f"  Canvas will expand to use available space")
        return (screen_width, screen_height), pygame.FULLSCREEN, scale_factor
    else:
        # Windowed mode - traditional scaling
        update_scaled_values(scale_factor, fullscreen=False)
        
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
    
    # Create game instance
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
                    update_scaled_values(scale_factor, fullscreen=False)
                    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                    game.update_scale(scale_factor)
                    game.update_screen_references(screen, screen)
                    print("Switched to windowed mode")
                    continue
                elif event.key == pygame.K_F11 and not is_fullscreen:
                    # Only allow F11 to enter fullscreen in windowed mode
                    # Enter fullscreen
                    is_fullscreen = True
                    info = pygame.display.Info()
                    scale_x = info.current_w / DESIGN_WIDTH
                    scale_y = info.current_h / DESIGN_HEIGHT
                    scale_factor = min(scale_x, scale_y)
                    
                    # Adaptive scale factor limits based on screen size
                    if info.current_w > 3840:  # 4K ultra-wide or larger
                        scale_factor = min(scale_factor, 2.5)
                    elif info.current_w > 2560:  # 4K or 1440p ultra-wide
                        scale_factor = min(scale_factor, 2.0)
                    else:  # 1080p and smaller
                        scale_factor = min(scale_factor, 1.5)
                    
                    update_scaled_values(scale_factor, info.current_w, info.current_h, fullscreen=True)
                    
                    # Store the actual screen for later reference
                    actual_screen = screen
                    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                    
                    game.update_scale(scale_factor)
                    game.update_screen_references(screen, actual_screen)
                    mode = "fullscreen"
                    print(f"Switched to {mode} mode with scale: {scale_factor:.2f}")
                    continue
            elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
                # Handle window resize
                new_scale_x = event.w / DESIGN_WIDTH
                new_scale_y = event.h / DESIGN_HEIGHT
                scale_factor = min(new_scale_x, new_scale_y)
                update_scaled_values(scale_factor, fullscreen=False)
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                game.update_scale(scale_factor)
                game.update_screen_references(screen, screen)
                print(f"Window resized, new scale: {scale_factor:.2f}")
            
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
    print("  python main.py --fullscreen - Run in fullscreen mode (responsive layout)")
    print("  python main.py --scale      - Run in 90% scaled windowed mode")
    print("\nControls:")
    print("  F11 - Enter fullscreen (from windowed mode only)")
    print("  ESC - Exit fullscreen")
    print("\nGameplay:")
    print("  - Use 'Load Fields' button to cycle through different map layouts")
    print("  - Red blocks create obstacles, gold fields give bonus points")
    print("  - Build interferometers to complete challenges and maximize score")
    print("\nFullscreen mode uses responsive layout to fill available space")
    print("UI panels are justified to edges, game area is centered")
    print()
    
    main()