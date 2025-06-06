"""Laser source component with proper scaling support."""
import pygame
import math
from components.base import Component
from utils.vector import Vector2
from config.settings import CYAN, WHITE, scale, scale_font, COMPONENT_RADIUS

class Laser(Component):
    """Laser source that emits coherent light with proper scaling."""
    
    def __init__(self, x, y):
        super().__init__(x, y, "laser")
        self.enabled = True
        # Use the scaled component radius from settings
        self.radius = COMPONENT_RADIUS
        self.debug = False
    
    def draw(self, screen):
        """Draw laser source with proper scaling."""
        # Glow effect - scale all glow layers
        for i in range(5, 0, -1):
            alpha = 50 // i
            glow_radius = self.radius + scale(i * 2)  # Reduced glow size
            s = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), 
                             (glow_radius, glow_radius), glow_radius)
            screen.blit(s, (int(self.position.x - glow_radius), 
                           int(self.position.y - glow_radius)))
        
        # Main laser circle - uses the component radius
        pygame.draw.circle(screen, CYAN, self.position.tuple(), self.radius)
        
        # Inner bright spot - scaled relative to radius
        inner_radius = max(scale(3), self.radius // 3)
        pygame.draw.circle(screen, WHITE, self.position.tuple(), inner_radius)
        
        # Direction indicator (shows beam will go right)
        if self.enabled:
            # Arrow pointing right - positioned relative to radius
            arrow_start = (self.position.x + self.radius + scale(3), self.position.y)
            arrow_end = (self.position.x + self.radius + scale(12), self.position.y)
            pygame.draw.line(screen, CYAN, arrow_start, arrow_end, scale(2))
            # Arrowhead
            arrow_size = scale(4)
            pygame.draw.lines(screen, CYAN, False, [
                (arrow_end[0] - arrow_size, arrow_end[1] - arrow_size),
                arrow_end,
                (arrow_end[0] - arrow_size, arrow_end[1] + arrow_size)
            ], scale(2))
        
        # Label - positioned below component
        font = pygame.font.Font(None, scale_font(14))
        text = font.render("LASER", True, WHITE)
        text_rect = text.get_rect(center=(int(self.position.x), 
                                         int(self.position.y + self.radius + scale(15))))
        screen.blit(text, text_rect)
    
    def contains_point(self, x, y):
        """Check if point is within laser component."""
        return self.position.distance_to(Vector2(x, y)) <= self.radius + scale(3)
    
    def emit_beam(self):
        """Emit a beam in the positive x direction."""
        if self.enabled:
            # Start beam from edge of laser
            beam_start_pos = Vector2(self.position.x + self.radius + scale(3), self.position.y)
            beam = {
                'position': beam_start_pos,
                'direction': Vector2(1, 0),
                'amplitude': 1.0,
                'phase': 0,
                'accumulated_phase': 0,
                'path_length': 0,
                'total_path_length': 0,
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