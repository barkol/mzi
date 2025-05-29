"""Beam splitter component."""
import pygame
import math
from components.base import Component
from utils.vector import Vector2
from config.settings import CYAN

class BeamSplitter(Component):
    """50/50 beam splitter with quantum behavior."""
    
    def __init__(self, x, y):
        super().__init__(x, y, "beamsplitter")
        self.pending_beams = []
    
    def draw(self, screen):
        """Draw beam splitter."""
        # Main square
        rect = pygame.Rect(
            self.position.x - 20, 
            self.position.y - 20, 
            40, 40
        )
        
        # Fill
        s = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], 40), pygame.Rect(0, 0, 40, 40))
        screen.blit(s, rect.topleft)
        
        # Border
        pygame.draw.rect(screen, CYAN, rect, 3)
        
        # Diagonal line (\ orientation)
        pygame.draw.line(screen, CYAN, 
                        (self.position.x - 20, self.position.y - 20),
                        (self.position.x + 20, self.position.y + 20), 2)
        
        # Direction indicators
        if hasattr(self, 'show_indicators') and self.show_indicators:
            # Draw small arrows showing beam paths (without alpha)
            points = [
                (self.position.x - 25, self.position.y),
                (self.position.x - 5, self.position.y),
                (self.position.x - 5, self.position.y - 20)
            ]
            pygame.draw.lines(screen, CYAN, False, points, 1)
    
    def process_beam(self, beam):
        """Process incoming beam with quantum behavior."""
        # Store beam for potential interference
        self.pending_beams.append(beam)
        
        # Single beam - normal 50/50 split
        if len(self.pending_beams) == 1:
            return self._split_single_beam(beam)
        
        # Two beams - quantum interference
        elif len(self.pending_beams) == 2:
            result = self._interfere_beams(self.pending_beams[0], self.pending_beams[1])
            self.pending_beams.clear()
            return result
        
        return []
    
    def _split_single_beam(self, beam):
        """Split a single beam 50/50."""
        amplitude = beam['amplitude'] / math.sqrt(2)
        
        # Transmitted beam (continues straight)
        transmitted = {
            'position': self.position + beam['direction'] * 25,
            'direction': beam['direction'],
            'amplitude': amplitude,
            'phase': beam['phase'],
            'path_length': 0,
            'source_type': beam['source_type']
        }
        
        # Reflected beam (like \ mirror: swap dx and dy)
        reflected_dir = Vector2(beam['direction'].y, beam['direction'].x)
        reflected = {
            'position': self.position + reflected_dir * 25,
            'direction': reflected_dir,
            'amplitude': amplitude,
            'phase': beam['phase'] + math.pi/2,  # 90 degree phase shift
            'path_length': 0,
            'source_type': 'shifted' if beam.get('source_type') == 'laser' else beam['source_type']
        }
        
        return [transmitted, reflected]
    
    def _interfere_beams(self, beam1, beam2):
        """Calculate quantum interference between two beams."""
        # Complex amplitudes
        a1_real = beam1['amplitude'] * math.cos(beam1['phase'])
        a1_imag = beam1['amplitude'] * math.sin(beam1['phase'])
        a2_real = beam2['amplitude'] * math.cos(beam2['phase'])
        a2_imag = beam2['amplitude'] * math.sin(beam2['phase'])
        
        # Quantum beam splitter transformation
        # Output 1: (α + iβ)/√2
        out1_real = (a1_real - a2_imag) / math.sqrt(2)
        out1_imag = (a1_imag + a2_real) / math.sqrt(2)
        out1_amplitude = math.sqrt(out1_real**2 + out1_imag**2)
        out1_phase = math.atan2(out1_imag, out1_real)
        
        # Output 2: (iα + β)/√2
        out2_real = (a2_real - a1_imag) / math.sqrt(2)
        out2_imag = (a1_real + a2_imag) / math.sqrt(2)
        out2_amplitude = math.sqrt(out2_real**2 + out2_imag**2)
        out2_phase = math.atan2(out2_imag, out2_real)
        
        return [
            {
                'position': self.position + beam1['direction'] * 25,
                'direction': beam1['direction'],
                'amplitude': out1_amplitude,
                'phase': out1_phase,
                'path_length': 0,
                'source_type': beam1.get('source_type', 'laser')
            },
            {
                'position': self.position + beam2['direction'] * 25,
                'direction': beam2['direction'],
                'amplitude': out2_amplitude,
                'phase': out2_phase,
                'path_length': 0,
                'source_type': beam2.get('source_type', 'laser')
            }
        ]
