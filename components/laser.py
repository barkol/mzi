"""Laser source component."""
import pygame
import math
from components.base import Component
from utils.vector import Vector2
from config.settings import CYAN, WHITE

class Laser(Component):
    """Laser source that emits coherent light."""
    
    def __init__(self, x, y):
        super().__init__(x, y, "laser")
        self.enabled = True
        self.radius = 15
        self.debug = False  # Disable debug by default
    
    def draw(self, screen):
        """Draw laser source."""
        # Glow effect
        for i in range(5, 0, -1):
            alpha = 50 // i
            s = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (self.radius * 2, self.radius * 2), self.radius + i * 3)
            screen.blit(s, (int(self.position.x - self.radius * 2), int(self.position.y - self.radius * 2)))
        
        # Main laser circle
        pygame.draw.circle(screen, CYAN, self.position.tuple(), self.radius)
        
        # Inner bright spot
        pygame.draw.circle(screen, WHITE, self.position.tuple(), 5)
        
        # Direction indicator (shows beam will go right)
        if self.enabled:
            # Arrow pointing right
            arrow_start = (self.position.x + self.radius + 5, self.position.y)
            arrow_end = (self.position.x + self.radius + 15, self.position.y)
            pygame.draw.line(screen, CYAN, arrow_start, arrow_end, 2)
            # Arrowhead
            pygame.draw.lines(screen, CYAN, False, [
                (arrow_end[0] - 5, arrow_end[1] - 5),
                arrow_end,
                (arrow_end[0] - 5, arrow_end[1] + 5)
            ], 2)
        
        # Label
        font = pygame.font.Font(None, 14)
        text = font.render("LASER", True, WHITE)
        text_rect = text.get_rect(center=(int(self.position.x), int(self.position.y + 30)))
        screen.blit(text, text_rect)
    
    def contains_point(self, x, y):
        """Check if point is within laser component."""
        return self.position.distance_to(Vector2(x, y)) <= self.radius + 5
    
    def emit_beam(self):
        """Emit a beam in the positive x direction."""
        if self.enabled:
            beam_start_pos = Vector2(self.position.x + self.radius + 5, self.position.y)
            beam = {
                'position': beam_start_pos,
                'direction': Vector2(1, 0),
                'amplitude': 1.0,
                'phase': 0,  # Initial phase at laser
                'accumulated_phase': 0,  # Start with zero accumulated phase
                'path_length': 0,
                'total_path_length': 0,  # No distance traveled yet
                'source_type': 'laser'
            }
            
            if self.debug:
                print(f"\nLaser at {self.position} emitting beam:")
                print(f"  Start position: {beam_start_pos}")
                print(f"  Direction: (1, 0)")
                print(f"  Amplitude: 1.0")
                print(f"  Initial phase: 0°")
            
            return beam
        return None
