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
            color = (*RED, alpha)
            s = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (self.radius * 2, self.radius * 2), self.radius + i * 3)
            screen.blit(s, (self.position.x - self.radius * 2, self.position.y - self.radius * 2))
        
        # Main laser circle
        pygame.draw.circle(screen, RED, self.position.tuple(), self.radius)
        
        # Label
        font = pygame.font.Font(None, 14)
        text = font.render("LASER", True, WHITE)
        text_rect = text.get_rect(center=(self.position.x, self.position.y + 30))
        screen.blit(text, text_rect)
    
    def emit_beam(self):
        """Emit a beam in the positive x direction."""
        if self.enabled:
            return {
                'position': Vector2(self.position.x + self.radius, self.position.y),
                'direction': Vector2(1, 0),
                'amplitude': 1.0,
                'phase': 0,
                'path_length': 0,
                'source_type': 'laser'
            }
        return None