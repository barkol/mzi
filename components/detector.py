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
        self.total_path_length = 0
    
    def draw(self, screen):
        """Draw detector with intensity visualization."""
        # Base circle
        s = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (GREEN[0], GREEN[1], GREEN[2], 40), (self.radius * 2, self.radius * 2), self.radius)
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
            pygame.draw.circle(s, (GREEN[0], GREEN[1], GREEN[2], alpha), (glow_radius, glow_radius), glow_radius)
            screen.blit(s, (self.position.x - glow_radius, self.position.y - glow_radius))
            
            # Intensity ring
            ring_color = (GREEN[0], GREEN[1], GREEN[2], int(255 * self.intensity))
            s2 = pygame.Surface((glow_radius * 2 + 10, glow_radius * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(s2, ring_color, (glow_radius + 5, glow_radius + 5), glow_radius, 5)
            screen.blit(s2, (self.position.x - glow_radius - 5, self.position.y - glow_radius - 5))
            
            # Display percentage
            font = pygame.font.Font(None, 20)
            text = font.render(f"{int(self.intensity * 100)}%", True, WHITE)
            text_rect = text.get_rect(center=(self.position.x, self.position.y + 50))
            
            # Background for text
            bg_rect = text_rect.inflate(10, 5)
            s3 = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s3.fill((0, 0, 0, 180))
            screen.blit(s3, bg_rect.topleft)
            
            screen.blit(text, text_rect)
    
    def process_beam(self, beam):
        """Detect beam and calculate intensity."""
        self.intensity = beam['amplitude'] ** 2
        self.last_beam = beam
        self.total_path_length = beam.get('total_path_length', 0)
        return []  # Detectors don't output beams