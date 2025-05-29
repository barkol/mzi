"""Laser source component."""
import pygame
import math
from components.base import Component
from utils.vector import Vector2
from config.settings import RED, WHITE

class Laser(Component):
    """Laser source that emits coherent light."""
    
    def __init__(self, x, y):
        super().__init__(x, y, "laser")
        self.enabled = True
        self.radius = 15
    
    def draw(self, screen):
        """Draw laser source."""
        # Glow effect
        for i in range(5, 0, -1):
            alpha = 50 // i
            s = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (RED[0], RED[1], RED[2], alpha), (self.radius * 2, self.radius * 2), self.radius + i * 3)
            screen.blit(s, (int(self.position.x - self.radius * 2), int(self.position.y - self.radius * 2)))
        
        # Main laser circle
        pygame.draw.circle(screen, RED, self.position.tuple(), self.radius)
        
        # Inner bright spot
        pygame.draw.circle(screen, WHITE, self.position.tuple(), 5)
        
        # Direction indicator (shows beam will go right)
        if self.enabled:
            # Arrow pointing right
            arrow_start = (self.position.x + self.radius + 5, self.position.y)
            arrow_end = (self.position.x + self.radius + 15, self.position.y)
            pygame.draw.line(screen, RED, arrow_start, arrow_end, 2)
            # Arrowhead
            pygame.draw.lines(screen, RED, False, [
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
            return {
                'position': Vector2(self.position.x + self.radius, self.position.y),
                'direction': Vector2(1, 0),
                'amplitude': 1.0,
                'phase': 0,
                'path_length': 0,
                'total_path_length': 0,  # Track cumulative distance
                'source_type': 'laser'
            }
        return None