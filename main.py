"""
Mach-Zehnder Interferometer Game
Main entry point for the application
"""
import pygame
import sys
from core.game import Game
from config.settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS

def main():
    """Initialize and run the game."""
    pygame.init()
    pygame.display.set_caption("Photon Path: Mach-Zehnder Interferometer")
    
    # Create display
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    
    # Create game instance
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
            game.handle_event(event)
        
        # Update cursor based on drag state
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
    main()
