"""
Mach-Zehnder Interferometer Game
Main entry point for the application
"""
import pygame
import sys
import platform
from core.game import Game
from config.settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS

def get_display_mode():
    """Get the best display mode for the game."""
    pygame.init()
    
    # Get display info
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h
    
    print(f"Screen resolution: {screen_width}x{screen_height}")
    print(f"Default game resolution: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    print(f"Platform: {platform.system()}")
    
    # Check if we should use fullscreen or windowed mode
    if screen_width < WINDOW_WIDTH or screen_height < WINDOW_HEIGHT:
        # Screen is smaller than default game size - use fullscreen
        print("Using fullscreen mode (screen smaller than game)")
        return (screen_width, screen_height), pygame.FULLSCREEN
    else:
        # Check for command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--fullscreen" or sys.argv[1] == "-f":
                print("Using fullscreen mode (requested)")
                return (screen_width, screen_height), pygame.FULLSCREEN
            elif sys.argv[1] == "--scale" or sys.argv[1] == "-s":
                # Scale to 90% of screen size to leave room for taskbar
                scaled_width = int(screen_width * 0.9)
                scaled_height = int(screen_height * 0.9)
                
                # Maintain aspect ratio
                game_aspect = WINDOW_WIDTH / WINDOW_HEIGHT
                screen_aspect = scaled_width / scaled_height
                
                if screen_aspect > game_aspect:
                    # Screen is wider - limit by height
                    final_height = scaled_height
                    final_width = int(final_height * game_aspect)
                else:
                    # Screen is taller - limit by width
                    final_width = scaled_width
                    final_height = int(final_width / game_aspect)
                
                print(f"Using scaled windowed mode: {final_width}x{final_height}")
                return (final_width, final_height), pygame.RESIZABLE
        
        # Default windowed mode
        print("Using default windowed mode")
        return (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE

def toggle_fullscreen_safe(screen, game, is_fullscreen):
    """Safely toggle fullscreen mode, especially on macOS."""
    try:
        if platform.system() == 'Darwin':  # macOS
            # On macOS, we need to be more careful with fullscreen transitions
            if is_fullscreen:
                # Exit fullscreen to windowed
                pygame.display.quit()
                pygame.display.init()
                screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                game.screen = screen
                # Force refresh of assets
                if hasattr(game, 'assets_loader'):
                    game.assets_loader.images.clear()  # Clear image cache
                return screen, False, 1.0, 0, 0, None
            else:
                # Enter fullscreen
                info = pygame.display.Info()
                pygame.display.quit()
                pygame.display.init()
                screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                
                # Calculate scaling
                scale_x = info.current_w / WINDOW_WIDTH
                scale_y = info.current_h / WINDOW_HEIGHT
                scale = min(scale_x, scale_y)
                
                # Create game surface
                game_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                
                # Calculate offsets
                scaled_width = int(WINDOW_WIDTH * scale)
                scaled_height = int(WINDOW_HEIGHT * scale)
                x_offset = (info.current_w - scaled_width) // 2
                y_offset = (info.current_h - scaled_height) // 2
                
                game.screen = game_surface
                # Force refresh of assets
                if hasattr(game, 'assets_loader'):
                    game.assets_loader.images.clear()  # Clear image cache
                
                return screen, True, scale, x_offset, y_offset, game_surface
        else:
            # Non-macOS systems can use the regular method
            if is_fullscreen:
                # Exit fullscreen
                screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                game.screen = screen
                return screen, False, 1.0, 0, 0, None
            else:
                # Enter fullscreen
                info = pygame.display.Info()
                screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                
                scale_x = info.current_w / WINDOW_WIDTH
                scale_y = info.current_h / WINDOW_HEIGHT
                scale = min(scale_x, scale_y)
                
                game_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                scaled_width = int(WINDOW_WIDTH * scale)
                scaled_height = int(WINDOW_HEIGHT * scale)
                x_offset = (info.current_w - scaled_width) // 2
                y_offset = (info.current_h - scaled_height) // 2
                
                game.screen = game_surface
                return screen, True, scale, x_offset, y_offset, game_surface
                
    except Exception as e:
        print(f"Error toggling fullscreen: {e}")
        # Fallback to windowed mode
        pygame.display.quit()
        pygame.display.init()
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        game.screen = screen
        return screen, False, 1.0, 0, 0, None

def main():
    """Initialize and run the game."""
    # Get display mode
    display_size, display_flags = get_display_mode()
    
    pygame.init()
    pygame.display.set_caption("Photon Path: Mach-Zehnder Interferometer")
    
    # Track fullscreen state
    is_fullscreen = (display_flags == pygame.FULLSCREEN)
    
    # Create display with appropriate flags
    if is_fullscreen:
        # For fullscreen, create at full resolution
        screen = pygame.display.set_mode(display_size, display_flags)
        
        # Calculate scaling factor
        scale_x = display_size[0] / WINDOW_WIDTH
        scale_y = display_size[1] / WINDOW_HEIGHT
        scale = min(scale_x, scale_y)
        
        # Create a surface at the game's native resolution
        game_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # Calculate centered position
        scaled_width = int(WINDOW_WIDTH * scale)
        scaled_height = int(WINDOW_HEIGHT * scale)
        x_offset = (display_size[0] - scaled_width) // 2
        y_offset = (display_size[1] - scaled_height) // 2
        
    else:
        # For windowed mode, allow resizing
        screen = pygame.display.set_mode(display_size, display_flags)
        game_surface = None
        scale = 1.0
        x_offset = 0
        y_offset = 0
    
    clock = pygame.time.Clock()
    
    # Create game instance with the appropriate surface
    if game_surface:
        game = Game(game_surface)
    else:
        game = Game(screen)
    
    # Store default cursor
    default_cursor = pygame.mouse.get_cursor()
    drag_cursor = pygame.SYSTEM_CURSOR_HAND
    
    # Game loop
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds
        
        # Handle events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Allow ESC to exit fullscreen
                if event.key == pygame.K_ESCAPE and is_fullscreen:
                    # Use safe fullscreen toggle
                    screen, is_fullscreen, scale, x_offset, y_offset, game_surface = \
                        toggle_fullscreen_safe(screen, game, is_fullscreen)
                    print("Switched to windowed mode")
                    continue
                # Allow F11 to toggle fullscreen
                elif event.key == pygame.K_F11:
                    # Use safe fullscreen toggle
                    screen, is_fullscreen, scale, x_offset, y_offset, game_surface = \
                        toggle_fullscreen_safe(screen, game, is_fullscreen)
                    mode = "fullscreen" if is_fullscreen else "windowed"
                    print(f"Switched to {mode} mode")
                    continue
            elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
                # Handle window resize
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                # For now, just use the screen directly
                game.screen = screen
                
            # Adjust mouse position for fullscreen scaling
            if game_surface and event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                # Convert screen coordinates to game coordinates
                if hasattr(event, 'pos'):
                    mouse_x = (event.pos[0] - x_offset) / scale
                    mouse_y = (event.pos[1] - y_offset) / scale
                    # Clamp to game bounds
                    mouse_x = max(0, min(WINDOW_WIDTH, mouse_x))
                    mouse_y = max(0, min(WINDOW_HEIGHT, mouse_y))
                    # Create new event with adjusted position
                    if event.type == pygame.MOUSEMOTION:
                        new_event = pygame.event.Event(event.type, {
                            'pos': (int(mouse_x), int(mouse_y)),
                            'rel': event.rel,
                            'buttons': event.buttons
                        })
                    else:  # MOUSEBUTTONDOWN or MOUSEBUTTONUP
                        new_event = pygame.event.Event(event.type, {
                            'pos': (int(mouse_x), int(mouse_y)),
                            'button': event.button
                        })
                    game.handle_event(new_event)
                else:
                    game.handle_event(event)
            else:
                game.handle_event(event)
        
        # Update cursor based on drag state
        if game.sidebar.dragging:
            pygame.mouse.set_cursor(drag_cursor)
        else:
            pygame.mouse.set_cursor(default_cursor)
        
        # Update
        game.update(dt)
        
        # Draw
        if game_surface:
            # Draw to game surface
            game.draw()
            
            # Clear screen with black
            screen.fill((0, 0, 0))
            
            # Scale and blit game surface to screen
            scaled_surface = pygame.transform.smoothscale(game_surface, (scaled_width, scaled_height))
            screen.blit(scaled_surface, (x_offset, y_offset))
        else:
            # Draw directly to screen
            game.draw()
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # Print usage info
    print("\nPhoton Path: Mach-Zehnder Interferometer")
    print("========================================")
    print("Usage:")
    print("  python main.py              - Run in default windowed mode")
    print("  python main.py --fullscreen - Run in fullscreen mode")
    print("  python main.py --scale      - Run in scaled windowed mode (90% of screen)")
    print("\nControls:")
    print("  F11 - Toggle fullscreen")
    print("  ESC - Exit fullscreen")
    print()
    
    # macOS warning
    if platform.system() == 'Darwin':
        print("Note: On macOS, fullscreen transitions may take a moment.")
        print()
    
    main()
