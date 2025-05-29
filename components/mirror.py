"""Mirror components."""
import pygame
from components.base import Component
from utils.vector import Vector2
from config.settings import MAGENTA

class Mirror(Component):
    """45-degree mirror for beam reflection."""
    
    def __init__(self, x, y, mirror_type='/'):
        super().__init__(x, y, "mirror")
        self.mirror_type = mirror_type  # '/' or '\'
    
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
        
        # Draw reflection indicators
        pygame.draw.line(screen, (*MAGENTA, 100), start, end, 2)
        
        # Add direction hint
        if self.mirror_type == '/':
            # Show left->down reflection
            pygame.draw.lines(screen, (*MAGENTA, 80), False, [
                (self.position.x - 20, self.position.y),
                (self.position.x - 10, self.position.y),
                (self.position.x - 10, self.position.y + 10)
            ], 1)
        else:  # '\'
            # Show left->up reflection
            pygame.draw.lines(screen, (*MAGENTA, 80), False, [
                (self.position.x - 20, self.position.y),
                (self.position.x - 10, self.position.y),
                (self.position.x - 10, self.position.y - 10)
            ], 1)
    
    def process_beam(self, beam):
        """Reflect beam according to mirror orientation."""
        direction = beam['direction']
        
        if self.mirror_type == '/':
            # / mirror: (dx,dy) -> (-dy,-dx)
            new_direction = Vector2(-direction.y, -direction.x)
        else:  # '\'
            # \ mirror: (dx,dy) -> (dy,dx)
            new_direction = Vector2(direction.y, direction.x)
        
        return [{
            'position': self.position + new_direction * 25,
            'direction': new_direction,
            'amplitude': beam['amplitude'] * 0.95,  # Small loss
            'phase': beam['phase'],
            'path_length': 0,
            'source_type': beam['source_type']
        }]