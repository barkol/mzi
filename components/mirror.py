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
        
        # Ensure direction is normalized
        mag = math.sqrt(direction.x**2 + direction.y**2)
        if abs(mag - 1.0) > 0.001:
            print(f"WARNING: Mirror received non-normalized direction vector: ({direction.x}, {direction.y}), magnitude={mag}")
            direction = Vector2(direction.x / mag, direction.y / mag)
        
        # Calculate new direction based on mirror type
        if self.mirror_type == '/':
            # / mirror: (dx,dy) -> (-dy,-dx)
            new_direction = Vector2(-direction.y, -direction.x)
        else:  # '\'
            # \ mirror: (dx,dy) -> (dy,dx)
            new_direction = Vector2(direction.y, direction.x)
        
        # Verify output is normalized
        out_mag = math.sqrt(new_direction.x**2 + new_direction.y**2)
        if abs(out_mag - 1.0) > 0.001:
            print(f"WARNING: Mirror producing non-normalized output: ({new_direction.x}, {new_direction.y}), magnitude={out_mag}")
        
        # Calculate amplitude after reflection
        if IDEAL_COMPONENTS:
            amplitude_factor = 1.0  # No loss
        else:
            amplitude_factor = 1.0 - MIRROR_LOSS  # Apply configured loss
        
        # Mirrors add π (180°) phase shift on reflection
        phase_shift = math.pi  # 180 degrees
        
        if self.debug:
            print(f"\nMirror {self.mirror_type} at ({self.position.x}, {self.position.y}):")
            print(f"  Input: dir=({direction.x:.3f},{direction.y:.3f}), phase={beam['phase']*180/math.pi:.1f}°")
            print(f"  Output: dir=({new_direction.x:.3f},{new_direction.y:.3f}), phase={(beam['phase']+phase_shift)*180/math.pi:.1f}°")
            print(f"  Phase shift: {phase_shift*180/math.pi:.0f}° (reflection)")
            if not IDEAL_COMPONENTS and MIRROR_LOSS > 0:
                print(f"  Loss: {MIRROR_LOSS*100:.1f}% (amplitude factor: {amplitude_factor:.3f})")
        
        return [{
            'position': self.position + new_direction * 30,  # Increased from 25 to avoid immediate collision
            'direction': new_direction,
            'amplitude': beam['amplitude'] * amplitude_factor,
            'phase': beam['phase'] + phase_shift,  # Base phase + mirror phase shift
            'path_length': 0,
            'total_path_length': beam.get('total_path_length', 0),  # Preserve total path
            'source_type': beam['source_type']
        }]
