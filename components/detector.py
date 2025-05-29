"""Detector component."""
import pygame
import math
from components.base import Component
from config.settings import GREEN, WHITE

class Detector(Component):
    """Detector that shows interference patterns."""
    
    def __init__(self, x, y):
        super().__init__(x, y, "detector")
        self.intensity = 0
        self.last_beam = None
    
    def draw(self, screen):
        """Draw detector with intensity visualization."""
        # Base circle
        s = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*GREEN, 40), (self.radius * 2, self.radius * 2), self.radius)
        screen.blit(s, (self.position.x - self.radius * 2, self.position.y - self.radius * 2))
        
        # Border
        pygame.draw.circle(screen, GREEN, self.position.tuple(), self.radius, 3)
        
        # Inner detection area
        pygame.draw.circle(screen, GREEN, self.position.tuple(), 10)
        
        # Intensity visualization
        if self.intensity > 0:
            # Glow effect based on intensity
            glow_radius = int(35 + self.intensity * 15)
            alpha = int(self.intensity * 128)
            s = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*GREEN, alpha), (glow_radius, glow_radius), glow_radius)
            screen.blit(s, (self.position.x - glow_radius, self.position.y - glow_radius))
            
            # Intensity ring
            pygame.draw.circle(screen, (*GREEN, int(255 * self.intensity)), 
                             self.position.tuple(), glow_radius, 5)
            
            # Display percentage
            font = pygame.font.Font(None, 16)
            text = font.render(f"{int(self.intensity * 100)}%", True, WHITE)
            text_rect = text.get_rect(center=(self.position.x, self.position.y + 50))
            screen.blit(text, text_rect)
    
    def process_beam(self, beam):
        """Detect beam and calculate intensity."""
        self.intensity = beam['amplitude'] ** 2
        self.last_beam = beam
        return []  # Detectors don't output beams