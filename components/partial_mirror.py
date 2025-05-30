"""Partial mirror component - example of custom tunable beam splitter."""
import pygame
import numpy as np
import math
from components.tunable_beamsplitter import TunableBeamSplitter

# Use a purple-ish color for partial mirrors
PARTIAL_MIRROR_COLOR = (200, 100, 255)

class PartialMirror(TunableBeamSplitter):
    """Partial mirror with adjustable reflectivity."""
    
    def __init__(self, x, y, reflectivity=0.3, mirror_type='/', loss=0.0):
        """
        Initialize partial mirror.
        
        Args:
            x, y: Position
            reflectivity: Power reflectivity (0 to 1)
            mirror_type: '/' or '\' - determines reflection geometry
            loss: Additional loss factor
        """
        # Calculate coefficients from reflectivity
        # |r|² = reflectivity, |t|² = 1 - reflectivity
        r_magnitude = np.sqrt(reflectivity)
        t_magnitude = np.sqrt(1.0 - reflectivity)
        
        # Give reflection a phase shift (can be customized)
        # Using -r_magnitude gives π phase shift like a regular mirror
        r = -r_magnitude
        t = t_magnitude
        
        super().__init__(x, y, t=t, r=r, orientation=mirror_type, loss=loss)
        self.component_type = "partial_mirror"
        self.reflectivity = reflectivity
        self.mirror_type = mirror_type
    
    def draw(self, screen):
        """Draw partial mirror with transparency indicating reflectivity."""
        # Mirror surface with transparency based on reflectivity
        if self.mirror_type == '/':
            start = (self.position.x - 20, self.position.y + 20)
            end = (self.position.x + 20, self.position.y - 20)
        else:  # '\'
            start = (self.position.x - 20, self.position.y - 20)
            end = (self.position.x + 20, self.position.y + 20)
        
        # Draw mirror line with thickness based on reflectivity
        thickness = int(3 + self.reflectivity * 5)
        pygame.draw.line(screen, PARTIAL_MIRROR_COLOR, start, end, thickness)
        
        # Draw partial transparency effect
        alpha = int(100 + self.reflectivity * 155)  # Alpha from 100 to 255
        s = pygame.Surface((60, 60), pygame.SRCALPHA)
        s_center = (30, 30)
        
        # Draw main line
        if self.mirror_type == '/':
            pygame.draw.line(s, (*PARTIAL_MIRROR_COLOR, alpha),
                           (s_center[0] - 20, s_center[1] + 20),
                           (s_center[0] + 20, s_center[1] - 20), 4)
        else:
            pygame.draw.line(s, (*PARTIAL_MIRROR_COLOR, alpha),
                           (s_center[0] - 20, s_center[1] - 20),
                           (s_center[0] + 20, s_center[1] + 20), 4)
        screen.blit(s, (self.position.x - 30, self.position.y - 30))
        
        # Show reflectivity percentage
        font = pygame.font.Font(None, 14)
        text = font.render(f"{int(self.reflectivity * 100)}%", True, PARTIAL_MIRROR_COLOR)
        text_rect = text.get_rect(center=(self.position.x, self.position.y - 30))
        screen.blit(text, text_rect)
        
        # Show debug info
        if self.debug:
            debug_font = pygame.font.Font(None, 10)
            coeff_text = f"R={self.reflectivity:.2f}, T={1-self.reflectivity:.2f}"
            coeff_surface = debug_font.render(coeff_text, True, PARTIAL_MIRROR_COLOR)
            screen.blit(coeff_surface, (self.position.x - 30, self.position.y + 25))
            
            # Show |r| and |t| values
            values_text = f"|r|={abs(self.r):.2f}, |t|={abs(self.t):.2f}"
            values_surface = debug_font.render(values_text, True, PARTIAL_MIRROR_COLOR)
            screen.blit(values_surface, (self.position.x - 30, self.position.y + 35))