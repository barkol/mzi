"""Beam rendering and visualization module with pulsing and color effects."""
import pygame
import math
import time
from config.settings import BEAM_WIDTH, CYAN, WHITE, scale, scale_font

class BeamRenderer:
    """Handles beam path rendering with dynamic pulsing and color effects."""
    
    def __init__(self, screen):
        self.screen = screen
        self.debug = False
        self.start_time = time.time()
    
    def set_debug(self, debug_state):
        """Set debug mode for beam renderer."""
        self.debug = debug_state
    
    def _get_dynamic_color(self, amplitude, time_offset=0):
        """Get a dynamically shifting color based on amplitude and time."""
        current_time = time.time() - self.start_time + time_offset
        
        # Base color shifts between cyan variants
        # Strong beams shift between cyan and light blue
        # Weak beams shift between cyan and turquoise
        
        if amplitude > 0.7:
            # Strong beams: Cyan to Light Blue
            phase = math.sin(current_time * 2.0) * 0.5 + 0.5  # 0 to 1
            r = min(255, max(0, int(0 + phase * 100)))  # 0 to 100
            g = min(255, max(0, int(200 + phase * 55)))  # 200 to 255
            b = 255
        elif amplitude > 0.4:
            # Medium beams: Cyan to Aqua
            phase = math.sin(current_time * 2.5) * 0.5 + 0.5
            r = min(255, max(0, int(0 + phase * 50)))  # 0 to 50
            g = 255
            b = min(255, max(0, int(200 + phase * 55)))  # 200 to 255
        else:
            # Weak beams: Cyan to Turquoise
            phase = math.sin(current_time * 3.0) * 0.5 + 0.5
            r = min(255, max(0, int(0 + phase * 64)))  # 0 to 64
            g = min(255, max(0, int(200 + phase * 55)))  # 200 to 255
            b = min(255, max(0, int(180 + phase * 75)))  # 180 to 255
        
        return (r, g, b)
    
    def _get_pulse_factor(self, amplitude, time_offset=0):
        """Get a pulsing factor for beam width and glow."""
        current_time = time.time() - self.start_time + time_offset
        
        # Different pulse speeds for different amplitudes
        if amplitude > 0.8:
            # Strong beams pulse slowly
            pulse_speed = 1.5
            pulse_amplitude = 0.15  # 15% variation
        elif amplitude > 0.5:
            # Medium beams pulse moderately
            pulse_speed = 2.0
            pulse_amplitude = 0.12  # 12% variation
        else:
            # Weak beams pulse faster
            pulse_speed = 3.0
            pulse_amplitude = 0.20  # 20% variation
        
        # Calculate pulse (varies from 1-pulse_amplitude to 1+pulse_amplitude)
        pulse = 1.0 + math.sin(current_time * pulse_speed) * pulse_amplitude
        return pulse
    
    def draw_beams(self, beam_tracer, laser, components, phase_value=0, blocked_positions=None):
            """Draw all laser beams (beams should already be traced in update phase)."""
            # Ensure we have a valid screen reference
            if not self.screen:
                print("WARNING: BeamRenderer has no screen reference!")
                return
            
            # Update debug state from beam tracer
            self.debug = beam_tracer.debug
            
            # Get the traced beams from the beam tracer
            # The beam tracer should have already traced the beams in the update phase
            if hasattr(beam_tracer, '_last_traced_beams'):
                traced_beams = beam_tracer._last_traced_beams
            else:
                # If no traced beams stored, we need to trace them now
                # This shouldn't happen in normal operation but is a fallback
                print("WARNING: No pre-traced beams found, tracing now")
                
                # Pass blocked positions to beam tracer
                if blocked_positions:
                    beam_tracer.set_blocked_positions(blocked_positions)
                else:
                    beam_tracer.set_blocked_positions([])
                
                # Add laser beam if not already added
                if len(beam_tracer.active_beams) == 0 and laser and laser.enabled:
                    laser_beam = laser.emit_beam()
                    if laser_beam:
                        laser_beam['phase'] = 0
                        laser_beam['accumulated_phase'] = 0
                        laser_beam['origin_phase'] = 0
                        laser_beam['origin_component'] = laser
                        beam_tracer.add_beam(laser_beam)
                
                # Trace beams
                traced_beams = beam_tracer.trace_beams(components)
            
            # Draw beams with slight time offset for each beam to create variation
            for i, beam_data in enumerate(traced_beams):
                time_offset = i * 0.3  # Slight phase difference between beams
                self._draw_beam_path(beam_data, time_offset)

    def _draw_beam_path(self, beam_data, time_offset=0):
        """Draw a single beam path with pulsing and color effects."""
        path = beam_data['path']
        if len(path) < 2:
            return
        
        # Skip very weak beams
        if beam_data['amplitude'] < 0.01:
            return
        
        # Check if beam was blocked
        was_blocked = beam_data.get('blocked', False)
        
        # Get dynamic color based on amplitude and time
        color = self._get_dynamic_color(beam_data['amplitude'], time_offset)
        
        # For blocked beams, use a reddish-cyan flash
        if was_blocked:
            current_time = time.time() - self.start_time
            flash = (math.sin(current_time * 10) + 1) * 0.5  # Fast flash
            color = (min(255, max(0, int(100 * flash))), 255, 255)  # Red-cyan flash
        
        # Keep beams bright - use high alpha for visibility
        intensity = beam_data['amplitude'] ** 2
        alpha = int(200 + 55 * intensity)  # Range: 200-255, always bright
        alpha = max(200, min(255, alpha))
        
        # Get pulse factor for this beam
        pulse_factor = self._get_pulse_factor(beam_data['amplitude'], time_offset)
        
        # Consistent beam width calculation with pulsing
        min_width = max(1, BEAM_WIDTH // 2)
        base_beam_width = max(min_width, int(BEAM_WIDTH * beam_data['amplitude']))
        beam_width = int(base_beam_width * pulse_factor)
        beam_width = max(1, beam_width)  # Ensure minimum width
        
        # Draw path
        for i in range(len(path) - 1):
            start = path[i].tuple() if hasattr(path[i], 'tuple') else path[i]
            end = path[i+1].tuple() if hasattr(path[i+1], 'tuple') else path[i+1]
            
            # Draw beam with dynamic color
            beam_color = color
            
            # Draw glow effect for stronger beams (not for blocked beams)
            if beam_data['amplitude'] > 0.7 and not was_blocked:
                # Pulsing glow layers
                glow_pulse = 1.0 + math.sin((time.time() - self.start_time + time_offset) * 2.0) * 0.3
                
                # Draw multiple glow layers directly for smoother effect
                glow_width = int((beam_width + beam_width * 2.0) * glow_pulse)
                
                for j in range(3):
                    layer_width = glow_width - j * (glow_width // 4)
                    # Simulate alpha by dimming the color
                    dim_factor = 0.3 / (j + 1)  # Gets dimmer with each layer
                    
                    # Clamp glow color values
                    glow_color = (min(255, max(0, int(color[0] * dim_factor))), 
                                 min(255, max(0, int(color[1] * dim_factor))), 
                                 min(255, max(0, int(color[2] * dim_factor))))
                    
                    # Draw glow directly on screen
                    if layer_width > 0:
                        pygame.draw.line(self.screen, glow_color, start, end, layer_width)
            
            # Draw beam core with anti-aliasing for smoother appearance
            if hasattr(pygame.draw, 'aaline') and beam_width <= 2:
                # Use anti-aliased line for thin beams
                pygame.draw.aaline(self.screen, beam_color, start, end)
            else:
                # Regular line for thicker beams
                pygame.draw.line(self.screen, beam_color, start, end, beam_width)
            
            # Add bright center line for very strong beams with color shift
            if beam_data['amplitude'] > 0.9 and not was_blocked:
                center_width = max(1, beam_width // 3)
                
                # Shifting center color
                current_time = time.time() - self.start_time + time_offset
                center_phase = (math.sin(current_time * 4.0) + 1) * 0.5
                
                # Shift between white and light cyan - clamp values
                center_r = min(255, max(0, int(200 + center_phase * 55)))  # 200-255
                center_g = 255
                center_b = 255
                center_color = (center_r, center_g, center_b)
                
                pygame.draw.line(self.screen, center_color, start, end, center_width)
        
        # Draw impact effect for blocked beams
        if was_blocked and len(path) >= 2:
            self._draw_blocked_impact(path[-1], beam_data['amplitude'], time_offset)
        
        # Draw phase information in debug mode
        if self.debug and len(path) >= 2 and not was_blocked:
            self._draw_phase_info(beam_data, path)
    
    def _draw_blocked_impact(self, position, amplitude, time_offset=0):
        """Draw pulsing impact effect where beam hits blocked position."""
        pos = position.tuple() if hasattr(position, 'tuple') else position
        
        # Calculate beam width for this amplitude
        min_width = max(1, BEAM_WIDTH // 2)
        beam_width = max(min_width, int(BEAM_WIDTH * amplitude))
        
        # Pulsing impact effect
        current_time = time.time() - self.start_time + time_offset
        impact_pulse = 1.0 + math.sin(current_time * 8.0) * 0.5  # Fast pulse
        
        # Draw impact flash effect - scale with beam width and pulse
        impact_radius = int((beam_width * 3 + amplitude * beam_width * 2) * impact_pulse)
        
        # Draw ripple effect directly on screen
        num_ripples = 3
        for r in range(num_ripples):
            # Each ripple expands outward with time
            ripple_phase = (current_time * 2.0 + r * 0.5) % 2.0
            ripple_radius = int(impact_radius * (0.5 + ripple_phase * 0.5))
            
            if ripple_radius > 0:
                # Ripple color shifts from cyan to white based on phase
                # Make outer ripples dimmer by adjusting color intensity
                intensity = (1.0 - ripple_phase * 0.5) / (r + 1)
                # Clamp all color values to 0-255 range
                r_val = min(255, max(0, int(100 * intensity + ripple_phase * 155 * intensity)))
                g_val = min(255, max(0, int(255 * intensity)))
                b_val = min(255, max(0, int(255 * intensity)))
                ripple_color = (r_val, g_val, b_val)
                # Draw circle directly on screen with width for ring effect
                pygame.draw.circle(self.screen, ripple_color, pos, ripple_radius, 2)
        
        # Inner bright spot with color pulse - clamp values
        inner_radius = max(3, beam_width)
        flash_r = min(255, max(0, int(200 + impact_pulse * 55)))
        flash_color = (flash_r, 255, 255)
        pygame.draw.circle(self.screen, flash_color, pos, inner_radius)
        
        # Draw rotating particles/sparks
        import random
        random.seed(int(pos[0] + pos[1]))  # Consistent randomness based on position
        particle_spread = impact_radius
        
        for i in range(12):  # More particles
            # Rotate particles around impact point
            angle = (i * 30 + current_time * 100) % 360
            distance = particle_spread * (0.5 + random.random() * 0.5)
            
            particle_x = int(pos[0] + distance * math.cos(math.radians(angle)))
            particle_y = int(pos[1] + distance * math.sin(math.radians(angle)))
            
            particle_size = max(1, beam_width // 3)
            particle_brightness = random.random()
            # Clamp particle colors
            p_r = min(255, max(0, int(100 + particle_brightness * 155)))
            p_g = min(255, max(0, int(200 + particle_brightness * 55)))
            particle_color = (p_r, p_g, 255)
            
            pygame.draw.circle(self.screen, particle_color, 
                             (particle_x, particle_y), particle_size)
    
    def _draw_phase_info(self, beam_data, path):
        """Draw phase information at beam origin and end with scaling."""
        font = pygame.font.Font(None, scale_font(12))
        
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
            text_rect.center = (origin[0] + scale(20), origin[1] - scale(10))
            
            # Draw background for readability
            bg_rect = text_rect.inflate(scale(4), scale(2))
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
        text_rect.center = (end[0] + scale(20), end[1] + scale(10))
        
        # Draw background for readability
        bg_rect = text_rect.inflate(scale(4), scale(2))
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
            amp_rect.center = (end[0] + scale(20), end[1] + scale(22))
            
            # Draw background
            bg_rect = amp_rect.inflate(scale(4), scale(2))
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.screen.blit(s, bg_rect.topleft)
            
            # Draw text
            self.screen.blit(amp_surface, amp_rect)