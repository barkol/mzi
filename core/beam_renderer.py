"""Beam rendering and visualization module."""
import pygame
import math
from config.settings import BEAM_WIDTH, RED, MAGENTA

class BeamRenderer:
    """Handles beam path rendering and visualization."""
    
    def __init__(self, screen):
        self.screen = screen
    
    def draw_beams(self, beam_tracer, laser, components, phase_slider_value):
        """Trace and draw all laser beams."""
        beam_tracer.reset()
        
        # Add laser beam
        laser_beam = laser.emit_beam()
        if laser_beam:
            # Apply phase shift from slider to both phase and accumulated_phase
            phase_from_slider = math.radians(phase_slider_value)
            laser_beam['phase'] += phase_from_slider
            laser_beam['accumulated_phase'] = laser_beam['phase']  # Set accumulated phase
            beam_tracer.add_beam(laser_beam)
            
            # Debug: Draw beam start position
            if hasattr(laser, 'debug') and laser.debug:
                pygame.draw.circle(self.screen, (255, 255, 0),
                                 laser_beam['position'].tuple(), 3)
        
        # Trace beams
        traced_beams = beam_tracer.trace_beams(components)
        
        # Draw beams
        for beam_data in traced_beams:
            self._draw_beam_path(beam_data)
    
    def _draw_beam_path(self, beam_data):
        """Draw a single beam path."""
        path = beam_data['path']
        if len(path) < 2:
            return
        
        # Skip very weak beams
        if beam_data['amplitude'] < 0.01:
            return
        
        # Color based on source type
        if beam_data['source_type'] == 'shifted':
            color = MAGENTA
        else:
            color = RED
        
        # Adjust alpha based on amplitude squared (intensity)
        # Use amplitude squared for intensity representation
        intensity = beam_data['amplitude'] ** 2
        alpha = int(255 * min(1.0, intensity))  # Cap at 255
        alpha = max(10, alpha)  # Ensure minimum visibility
        
        # Adjust beam width based on amplitude
        # Width varies from 1 (weak) to BEAM_WIDTH + 2 (strong)
        beam_width = max(1, int(BEAM_WIDTH * beam_data['amplitude']))
        
        # Draw path
        for i in range(len(path) - 1):
            start = path[i].tuple() if hasattr(path[i], 'tuple') else path[i]
            end = path[i+1].tuple() if hasattr(path[i+1], 'tuple') else path[i+1]
            
            # Draw beam with adjusted color intensity based on amplitude
            beam_color = tuple(int(c * alpha / 255) for c in color)
            
            # Draw glow effect for stronger beams
            if beam_data['amplitude'] > 0.7:
                glow_width = beam_width + 3
                glow_color = tuple(int(c * alpha / 510) for c in color)  # Dimmer glow
                pygame.draw.line(self.screen, glow_color, start, end, glow_width)
            
            # Draw beam core
            pygame.draw.line(self.screen, beam_color, start, end, beam_width)