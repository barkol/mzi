"""Partial mirror component - example of custom tunable beam splitter with scaling support."""
import pygame
import numpy as np
import math
from components.tunable_beamsplitter import TunableBeamSplitter
from config.settings import CYAN, scale, scale_font

# Use turquoise color for partial mirrors
PARTIAL_MIRROR_COLOR = CYAN

class PartialMirror(TunableBeamSplitter):
    """Partial mirror with adjustable reflectivity and scaling support."""
    
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
        """Draw partial mirror with transparency indicating reflectivity and scaling support."""
        # Mirror surface with transparency based on reflectivity - scaled size
        size = scale(40)
        half_size = size // 2
        
        if self.mirror_type == '/':
            start = (self.position.x - half_size, self.position.y + half_size)
            end = (self.position.x + half_size, self.position.y - half_size)
        else:  # '\'
            start = (self.position.x - half_size, self.position.y - half_size)
            end = (self.position.x + half_size, self.position.y + half_size)
        
        # Draw mirror line with thickness based on reflectivity - scaled
        base_thickness = scale(3)
        reflectivity_thickness = scale(int(self.reflectivity * 5))
        thickness = base_thickness + reflectivity_thickness
        pygame.draw.line(screen, PARTIAL_MIRROR_COLOR, start, end, thickness)
        
        # Draw partial transparency effect - scaled
        alpha = int(100 + self.reflectivity * 155)  # Alpha from 100 to 255
        surface_size = scale(60)
        s = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        s_center = (surface_size // 2, surface_size // 2)
        
        # Draw main line with scaled dimensions
        if self.mirror_type == '/':
            pygame.draw.line(s, (*PARTIAL_MIRROR_COLOR, alpha),
                           (s_center[0] - half_size, s_center[1] + half_size),
                           (s_center[0] + half_size, s_center[1] - half_size), scale(4))
        else:
            pygame.draw.line(s, (*PARTIAL_MIRROR_COLOR, alpha),
                           (s_center[0] - half_size, s_center[1] - half_size),
                           (s_center[0] + half_size, s_center[1] + half_size), scale(4))
        screen.blit(s, (self.position.x - surface_size // 2, self.position.y - surface_size // 2))
        
        # Show reflectivity percentage - scaled font and position
        font = pygame.font.Font(None, scale_font(14))
        text = font.render(f"{int(self.reflectivity * 100)}%", True, PARTIAL_MIRROR_COLOR)
        text_rect = text.get_rect(center=(self.position.x, self.position.y - scale(30)))
        screen.blit(text, text_rect)
        
        # Show debug info with scaling
        if self.debug:
            debug_font = pygame.font.Font(None, scale_font(10))
            coeff_text = f"R={self.reflectivity:.2f}, T={1-self.reflectivity:.2f}"
            coeff_surface = debug_font.render(coeff_text, True, PARTIAL_MIRROR_COLOR)
            screen.blit(coeff_surface, (self.position.x - scale(30), self.position.y + scale(25)))
            
            # Show |r| and |t| values
            values_text = f"|r|={abs(self.r):.2f}, |t|={abs(self.t):.2f}"
            values_surface = debug_font.render(values_text, True, PARTIAL_MIRROR_COLOR)
            screen.blit(values_surface, (self.position.x - scale(30), self.position.y + scale(35)))