"""Mirror components."""
import pygame
import math
from components.base import Component
from utils.vector import Vector2
from config.settings import MAGENTA, MIRROR_LOSS, IDEAL_COMPONENTS

class Mirror(Component):
    """45-degree mirror for beam reflection."""
    
    def __init__(self, x, y, mirror_type='/'):
        super().__init__(x, y, "mirror")
        self.mirror_type = mirror_type  # '/' or '\'
        self.debug = True  # Enable debugging
    
    def draw(self, screen):
        """Draw mirror."""
        # Mirror surface
        if self.mirror_type == '/':
            start = (self.position.x - 20, self.position.y + 20)
            end = (self.position.x + 20, self.position.y - 20)
        else:  # '\'
            start = (self.position.x - 20, self.position.y - 20)
            end = (self.position.x + 20, self.position.y + 20)
        
        # Draw thick mirror line
        pygame.draw.line(screen, MAGENTA, start, end, 6)
        
        # Draw reflection indicators (dimmed)
        s = pygame.Surface((60, 60), pygame.SRCALPHA)
        s_center = (30, 30)
        if self.mirror_type == '/':
            pygame.draw.line(s, (MAGENTA[0], MAGENTA[1], MAGENTA[2], 100), 
                           (s_center[0] - 20, s_center[1] + 20),
                           (s_center[0] + 20, s_center[1] - 20), 2)
        else:
            pygame.draw.line(s, (MAGENTA[0], MAGENTA[1], MAGENTA[2], 100), 
                           (s_center[0] - 20, s_center[1] - 20),
                           (s_center[0] + 20, s_center[1] + 20), 2)
        screen.blit(s, (self.position.x - 30, self.position.y - 30))
        
        # Add direction hint
        if self.mirror_type == '/':
            # Show left->down reflection
            points = [
                (self.position.x - 20, self.position.y),
                (self.position.x - 10, self.position.y),
                (self.position.x - 10, self.position.y + 10)
            ]
            pygame.draw.lines(screen, MAGENTA, False, points, 1)
        else:  # '\'
            # Show left->up reflection
            points = [
                (self.position.x - 20, self.position.y),
                (self.position.x - 10, self.position.y),
                (self.position.x - 10, self.position.y - 10)
            ]
            pygame.draw.lines(screen, MAGENTA, False, points, 1)
    
    def process_beam(self, beam):
        """Reflect beam according to mirror orientation."""
        direction = beam['direction']
        
        # Calculate new direction based on mirror type
        if self.mirror_type == '/':
            # / mirror: (dx,dy) -> (-dy,-dx)
            new_direction = Vector2(-direction.y, -direction.x)
        else:  # '\'
            # \ mirror: (dx,dy) -> (dy,dx)
            new_direction = Vector2(direction.y, direction.x)
        
        # Calculate amplitude after reflection
        if IDEAL_COMPONENTS:
            amplitude_factor = 1.0  # No loss
        else:
            amplitude_factor = 1.0 - MIRROR_LOSS  # Apply configured loss
        
        # In this simplified model, mirrors don't add phase shift
        # (In reality, metallic mirrors add π, dielectric mirrors vary)
        phase_shift = 0
        
        if self.debug:
            print(f"Mirror {self.mirror_type} at {self.position}:")
            print(f"  Input: dir=({direction.x:.0f},{direction.y:.0f}), phase={beam['phase']*180/math.pi:.1f}°")
            print(f"  Output: dir=({new_direction.x:.0f},{new_direction.y:.0f}), phase={(beam['phase']+phase_shift)*180/math.pi:.1f}°")
        
        return [{
            'position': self.position + new_direction * 25,
            'direction': new_direction,
            'amplitude': beam['amplitude'] * amplitude_factor,
            'phase': beam['phase'] + phase_shift,
            'path_length': 0,
            'total_path_length': beam.get('total_path_length', 0),
            'source_type': beam['source_type']
        }]