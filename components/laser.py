"""Laser source component with proper scaling support."""
import logging
import pygame
import math
import numpy as np
from components.base import Component
from utils.vector import Vector2
from config.settings import CYAN, WHITE, scale, scale_font, COMPONENT_RADIUS

logger = logging.getLogger(__name__)

class Laser(Component):
    """Laser source that emits coherent light with proper scaling.

    The laser emits from a configurable port (default: port C / rightward).
    It is transparent along its emission axis so retroinjected light passes
    through to the opposite port.
    """

    # Emission direction → (emission_port, opposite_port)
    _DIR_MAP = {
        'right': (2, 0),  # emit C, retro A
        'left':  (0, 2),  # emit A, retro C
        'down':  (1, 3),  # emit B, retro D
        'up':    (3, 1),  # emit D, retro B
    }

    def __init__(self, x, y, direction='right'):
        super().__init__(x, y, "laser")
        self.enabled = True
        self.radius = COMPONENT_RADIUS
        self.debug = False
        self.emit_direction = direction

        emit_port, retro_port = self._DIR_MAP.get(direction, (2, 0))
        self.EMISSION_PORT = emit_port

        # S-matrix: transparent along emission axis (pass-through
        # between emission port and its opposite).
        self.S = np.zeros((4, 4), dtype=complex)
        self.S[retro_port, emit_port] = 1   # retroinjection pass-through
        self.S[emit_port, retro_port] = 1   # forward pass-through
    
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
        
        # Direction indicator arrow
        if self.enabled:
            d = self.emit_direction
            off1, off2 = self.radius + scale(3), self.radius + scale(12)
            asz = scale(4)
            if d == 'right':
                s_pt = (self.position.x + off1, self.position.y)
                e_pt = (self.position.x + off2, self.position.y)
                head = [(e_pt[0]-asz, e_pt[1]-asz), e_pt, (e_pt[0]-asz, e_pt[1]+asz)]
            elif d == 'left':
                s_pt = (self.position.x - off1, self.position.y)
                e_pt = (self.position.x - off2, self.position.y)
                head = [(e_pt[0]+asz, e_pt[1]-asz), e_pt, (e_pt[0]+asz, e_pt[1]+asz)]
            elif d == 'down':
                s_pt = (self.position.x, self.position.y + off1)
                e_pt = (self.position.x, self.position.y + off2)
                head = [(e_pt[0]-asz, e_pt[1]-asz), e_pt, (e_pt[0]+asz, e_pt[1]-asz)]
            else:  # up
                s_pt = (self.position.x, self.position.y - off1)
                e_pt = (self.position.x, self.position.y - off2)
                head = [(e_pt[0]-asz, e_pt[1]+asz), e_pt, (e_pt[0]+asz, e_pt[1]+asz)]
            pygame.draw.line(screen, CYAN, s_pt, e_pt, scale(2))
            pygame.draw.lines(screen, CYAN, False, head, scale(2))
        
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
                logger.debug("Laser at %s emitting beam: start=%s, dir=(1,0), amp=1.0, phase=0",
                             self.position, beam_start_pos)
            
            return beam
        return None