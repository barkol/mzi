"""Beam rendering and visualization module."""
import pygame
import math
from config.settings import BEAM_WIDTH, GREEN, MAGENTA, WHITE, CYAN, RED

class BeamRenderer:
    """Handles beam path rendering and visualization."""
    
    def __init__(self, screen):
        self.screen = screen
        self.debug = False  # Track debug state
    
    def set_debug(self, debug_state):
        """Set debug mode for beam renderer."""
        self.debug = debug_state
    
    def draw_beams(self, beam_tracer, laser, components, phase_value=0, blocked_positions=None):
        """Trace and draw all laser beams."""
        beam_tracer.reset()
        
        # Pass blocked positions to beam tracer
        if blocked_positions:
            beam_tracer.set_blocked_positions(blocked_positions)
        else:
            beam_tracer.set_blocked_positions([])
        
        # Update debug state from beam tracer
        self.debug = beam_tracer.debug
        
        # Add laser beam
        laser_beam = laser.emit_beam()
        if laser_beam:
            # Apply phase shift (now always 0, but kept for compatibility)
            phase_from_slider = math.radians(phase_value)
            laser_beam['phase'] += phase_from_slider
            laser_beam['accumulated_phase'] = laser_beam['phase']  # Set accumulated phase
            laser_beam['origin_phase'] = 0  # Original phase at laser
            laser_beam['origin_component'] = laser
            beam_tracer.add_beam(laser_beam)
            
            # Debug: Draw beam start position
            if self.debug:
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
        
        # Check if beam was blocked
        was_blocked = beam_data.get('blocked', False)
        
        # Color based on source type and blocked status
        if was_blocked:
            color = RED  # Red for blocked beams
        elif beam_data['source_type'] == 'shifted':
            color = MAGENTA
        else:
            color = GREEN  # Changed from RED to GREEN
        
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
            
            # Draw glow effect for stronger beams (not for blocked beams)
            if beam_data['amplitude'] > 0.7 and not was_blocked:
                glow_width = beam_width + 3
                glow_color = tuple(int(c * alpha / 510) for c in color)  # Dimmer glow
                pygame.draw.line(self.screen, glow_color, start, end, glow_width)
            
            # Draw beam core
            pygame.draw.line(self.screen, beam_color, start, end, beam_width)
        
        # Draw impact effect for blocked beams
        if was_blocked and len(path) >= 2:
            self._draw_blocked_impact(path[-1], beam_data['amplitude'])
        
        # Draw phase information in debug mode
        if self.debug and len(path) >= 2 and not was_blocked:
            self._draw_phase_info(beam_data, path)
    
    def _draw_blocked_impact(self, position, amplitude):
        """Draw impact effect where beam hits blocked position."""
        pos = position.tuple() if hasattr(position, 'tuple') else position
        
        # Draw impact flash effect
        impact_radius = int(10 + amplitude * 20)
        alpha = int(amplitude * 128)
        
        # Outer glow
        for r in range(3):
            radius = impact_radius - r * 3
            if radius > 0:
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (RED[0], RED[1], RED[2], alpha // (r + 1)),
                                 (radius, radius), radius)
                self.screen.blit(surf, (pos[0] - radius, pos[1] - radius))
        
        # Inner bright spot
        pygame.draw.circle(self.screen, (255, 200, 200), pos, 3)
        
        # Draw small particles/sparks
        import random
        random.seed(int(pos[0] + pos[1]))  # Consistent randomness based on position
        for _ in range(5):
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            particle_pos = (pos[0] + offset_x, pos[1] + offset_y)
            pygame.draw.circle(self.screen, (255, 100, 100), particle_pos, 1)
    
    def _draw_phase_info(self, beam_data, path):
        """Draw phase information at beam origin and end."""
        font = pygame.font.Font(None, 12)
        
        # Get origin and end positions
        origin = path[0].tuple() if hasattr(path[0], 'tuple') else path[0]
        end = path[-1].tuple() if hasattr(path[-1], 'tuple') else path[-1]
        
        # Origin phase (if available)
        if 'origin_phase' in beam_data:
            origin_phase_deg = beam_data['origin_phase'] * 180 / math.pi
            origin_text = f"φ₀={origin_phase_deg:.0f}°"
            
            # Create text surface
            text_surface = font.render(origin_text, True, WHITE)
            text_rect = text_surface.get_rect()
            
            # Position text near origin (offset to avoid overlap)
            text_rect.center = (origin[0] + 20, origin[1] - 10)
            
            # Draw background for readability
            bg_rect = text_rect.inflate(4, 2)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.screen.blit(s, bg_rect.topleft)
            
            # Draw text
            self.screen.blit(text_surface, text_rect)
        
        # End phase
        end_phase_deg = beam_data['phase'] * 180 / math.pi
        end_text = f"φ={end_phase_deg:.0f}°"
        
        # Create text surface
        text_surface = font.render(end_text, True, CYAN)
        text_rect = text_surface.get_rect()
        
        # Position text near end (offset to avoid overlap)
        text_rect.center = (end[0] + 20, end[1] + 10)
        
        # Draw background for readability
        bg_rect = text_rect.inflate(4, 2)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, bg_rect.topleft)
        
        # Draw text
        self.screen.blit(text_surface, text_rect)
        
        # Draw amplitude info if significant
        if beam_data['amplitude'] > 0.1:
            amp_text = f"|E|={beam_data['amplitude']:.2f}"
            amp_surface = font.render(amp_text, True, WHITE)
            amp_rect = amp_surface.get_rect()
            
            # Position below phase
            amp_rect.center = (end[0] + 20, end[1] + 22)
            
            # Draw background
            bg_rect = amp_rect.inflate(4, 2)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.screen.blit(s, bg_rect.topleft)
            
            # Draw text
            self.screen.blit(amp_surface, amp_rect)
