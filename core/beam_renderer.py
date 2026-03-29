"""Beam rendering module updated for wave optics engine."""
import pygame
import math
import time
import config.settings as _settings
from config.settings import CYAN, WHITE, scale, scale_font


class BeamRenderer:
    """Handles beam path rendering with dynamic pulsing and color effects."""

    def __init__(self, screen):
        self.screen = screen
        self.debug = False
        self.start_time = time.time()
        self._frame_time = 0.0  # Cached per-frame time offset
        self.ghost_mode = False  # Dim beams when quantum packet mode is active

    def begin_frame(self):
        """Call once per frame to cache the current time."""
        self._frame_time = time.time() - self.start_time

    def set_debug(self, debug_state):
        """Set debug mode for beam renderer."""
        self.debug = debug_state
    
    def _get_dynamic_color(self, amplitude, time_offset=0):
        """Get a dynamically shifting color based on amplitude and time."""
        current_time = self._frame_time + time_offset
        
        # Base color shifts between cyan variants
        if amplitude > 0.7:
            # Strong beams: Cyan to Light Blue
            phase = math.sin(current_time * 2.0) * 0.5 + 0.5
            r = min(255, max(0, int(0 + phase * 100)))
            g = min(255, max(0, int(200 + phase * 55)))
            b = 255
        elif amplitude > 0.4:
            # Medium beams: Cyan to Aqua
            phase = math.sin(current_time * 2.5) * 0.5 + 0.5
            r = min(255, max(0, int(0 + phase * 50)))
            g = 255
            b = min(255, max(0, int(200 + phase * 55)))
        else:
            # Weak beams: Cyan to Turquoise
            phase = math.sin(current_time * 3.0) * 0.5 + 0.5
            r = min(255, max(0, int(0 + phase * 64)))
            g = min(255, max(0, int(200 + phase * 55)))
            b = min(255, max(0, int(180 + phase * 75)))
        
        return (r, g, b)
    
    def _get_pulse_factor(self, amplitude, time_offset=0):
        """Get a pulsing factor for beam width and glow."""
        current_time = self._frame_time + time_offset
        
        if amplitude > 0.8:
            pulse_speed = 1.5
            pulse_amplitude = 0.15
        elif amplitude > 0.5:
            pulse_speed = 2.0
            pulse_amplitude = 0.12
        else:
            pulse_speed = 3.0
            pulse_amplitude = 0.20
        
        pulse = 1.0 + math.sin(current_time * pulse_speed) * pulse_amplitude
        return pulse
    
    def draw_beams_waveoptics(self, wave_engine, laser, components):
        """Draw beams from wave optics engine results."""
        if not self.screen or not laser or not laser.enabled:
            return
            
        # Get solved beam paths from wave optics engine
        traced_beams = wave_engine.solve_interferometer(laser, components)
        
        # Store for other uses
        self._last_traced_beams = traced_beams
        
        # Draw beams with slight time offset for each beam
        for i, beam_data in enumerate(traced_beams):
            time_offset = i * 0.3
            self._draw_beam_path(beam_data, time_offset)
    
    def draw_beams(self, beam_tracer, laser, components, phase_value=0, blocked_positions=None):
        """Legacy interface - redirect to wave optics if available."""
        # This maintains compatibility with existing code
        if hasattr(beam_tracer, 'solve_interferometer'):
            # It's actually a wave optics engine
            self.draw_beams_waveoptics(beam_tracer, laser, components)
        else:
            # Fall back to old tracer
            self._draw_beams_legacy(beam_tracer, laser, components, phase_value, blocked_positions)
    
    def _draw_beams_legacy(self, beam_tracer, laser, components, phase_value=0, blocked_positions=None):
        """Legacy beam drawing for old beam tracer."""
        if not self.screen:
            return
        
        self.debug = beam_tracer.debug
        
        if hasattr(beam_tracer, '_last_traced_beams'):
            traced_beams = beam_tracer._last_traced_beams
        else:
            if blocked_positions:
                beam_tracer.set_blocked_positions(blocked_positions)
            else:
                beam_tracer.set_blocked_positions([])
            
            if len(beam_tracer.active_beams) == 0 and laser and laser.enabled:
                laser_beam = laser.emit_beam()
                if laser_beam:
                    laser_beam['phase'] = 0
                    laser_beam['accumulated_phase'] = 0
                    laser_beam['origin_phase'] = 0
                    laser_beam['origin_component'] = laser
                    beam_tracer.add_beam(laser_beam)
            
            traced_beams = beam_tracer.trace_beams(components)
        
        for i, beam_data in enumerate(traced_beams):
            time_offset = i * 0.3
            self._draw_beam_path(beam_data, time_offset)
    
    def _draw_beam_path(self, beam_data, time_offset=0):
        """Draw a single beam path with pulsing and color effects."""
        path = beam_data['path']
        if len(path) < 2:
            return

        if beam_data['amplitude'] < 0.01:
            return

        # In ghost mode (quantum packet mode), draw beams very dimly
        if self.ghost_mode:
            self._draw_ghost_beam_path(beam_data, time_offset)
            return
        
        was_blocked = beam_data.get('blocked', False)
        
        color = self._get_dynamic_color(beam_data['amplitude'], time_offset)
        
        if was_blocked:
            current_time = self._frame_time
            flash = (math.sin(current_time * 10) + 1) * 0.5
            color = (min(255, max(0, int(100 * flash))), 255, 255)
        
        intensity = beam_data['amplitude'] ** 2
        alpha = int(200 + 55 * intensity)
        alpha = max(200, min(255, alpha))
        
        pulse_factor = self._get_pulse_factor(beam_data['amplitude'], time_offset)
        
        min_width = max(1, _settings.BEAM_WIDTH // 2)
        base_beam_width = max(min_width, int(_settings.BEAM_WIDTH * beam_data['amplitude']))
        beam_width = int(base_beam_width * pulse_factor)
        beam_width = max(1, beam_width)
        
        for i in range(len(path) - 1):
            start = path[i].tuple() if hasattr(path[i], 'tuple') else path[i]
            end = path[i+1].tuple() if hasattr(path[i+1], 'tuple') else path[i+1]
            
            beam_color = color
            
            if beam_data['amplitude'] > 0.7 and not was_blocked:
                glow_pulse = 1.0 + math.sin((self._frame_time + time_offset) * 2.0) * 0.3
                glow_width = int((beam_width + beam_width * 2.0) * glow_pulse)
                
                for j in range(3):
                    layer_width = glow_width - j * (glow_width // 4)
                    dim_factor = 0.3 / (j + 1)
                    
                    glow_color = (min(255, max(0, int(color[0] * dim_factor))),
                                 min(255, max(0, int(color[1] * dim_factor))),
                                 min(255, max(0, int(color[2] * dim_factor))))
                    
                    if layer_width > 0:
                        pygame.draw.line(self.screen, glow_color, start, end, layer_width)
            
            if hasattr(pygame.draw, 'aaline') and beam_width <= 2:
                pygame.draw.aaline(self.screen, beam_color, start, end)
            else:
                pygame.draw.line(self.screen, beam_color, start, end, beam_width)
            
            if beam_data['amplitude'] > 0.9 and not was_blocked:
                center_width = max(1, beam_width // 3)
                
                current_time = self._frame_time + time_offset
                center_phase = (math.sin(current_time * 4.0) + 1) * 0.5
                
                center_r = min(255, max(0, int(200 + center_phase * 55)))
                center_g = 255
                center_b = 255
                center_color = (center_r, center_g, center_b)
                
                pygame.draw.line(self.screen, center_color, start, end, center_width)
        
        if was_blocked and len(path) >= 2:
            self._draw_blocked_impact(path[-1], beam_data['amplitude'], time_offset)
        
        if self.debug and len(path) >= 2 and not was_blocked:
            self._draw_phase_info(beam_data, path)
    
    def _draw_blocked_impact(self, position, amplitude, time_offset=0):
        """Draw pulsing impact effect where beam hits blocked position."""
        pos = position.tuple() if hasattr(position, 'tuple') else position
        
        min_width = max(1, _settings.BEAM_WIDTH // 2)
        beam_width = max(min_width, int(_settings.BEAM_WIDTH * amplitude))
        
        current_time = self._frame_time + time_offset
        impact_pulse = 1.0 + math.sin(current_time * 8.0) * 0.5
        
        impact_radius = int((beam_width * 3 + amplitude * beam_width * 2) * impact_pulse)
        
        num_ripples = 3
        for r in range(num_ripples):
            ripple_phase = (current_time * 2.0 + r * 0.5) % 2.0
            ripple_radius = int(impact_radius * (0.5 + ripple_phase * 0.5))
            
            if ripple_radius > 0:
                intensity = (1.0 - ripple_phase * 0.5) / (r + 1)
                r_val = min(255, max(0, int(100 * intensity + ripple_phase * 155 * intensity)))
                g_val = min(255, max(0, int(255 * intensity)))
                b_val = min(255, max(0, int(255 * intensity)))
                ripple_color = (r_val, g_val, b_val)
                pygame.draw.circle(self.screen, ripple_color, pos, ripple_radius, 2)
        
        inner_radius = max(3, beam_width)
        flash_r = min(255, max(0, int(200 + impact_pulse * 55)))
        flash_color = (flash_r, 255, 255)
        pygame.draw.circle(self.screen, flash_color, pos, inner_radius)
        
        import random
        random.seed(int(pos[0] + pos[1]))
        particle_spread = impact_radius
        
        for i in range(12):
            angle = (i * 30 + current_time * 100) % 360
            distance = particle_spread * (0.5 + random.random() * 0.5)
            
            particle_x = int(pos[0] + distance * math.cos(math.radians(angle)))
            particle_y = int(pos[1] + distance * math.sin(math.radians(angle)))
            
            particle_size = max(1, beam_width // 3)
            particle_brightness = random.random()
            p_r = min(255, max(0, int(100 + particle_brightness * 155)))
            p_g = min(255, max(0, int(200 + particle_brightness * 55)))
            particle_color = (p_r, p_g, 255)
            
            pygame.draw.circle(self.screen, particle_color,
                             (particle_x, particle_y), particle_size)
    
    def _draw_phase_info(self, beam_data, path):
        """Draw phase information at beam origin and end with scaling."""
        font = pygame.font.Font(None, scale_font(12))
        
        origin = path[0].tuple() if hasattr(path[0], 'tuple') else path[0]
        end = path[-1].tuple() if hasattr(path[-1], 'tuple') else path[-1]
        
        if 'origin_phase' in beam_data:
            origin_phase_deg = beam_data['origin_phase'] * 180 / math.pi
            origin_text = f"φ₀={origin_phase_deg:.0f}°"
            
            text_surface = font.render(origin_text, True, WHITE)
            text_rect = text_surface.get_rect()
            text_rect.center = (origin[0] + scale(20), origin[1] - scale(10))
            
            bg_rect = text_rect.inflate(scale(4), scale(2))
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.screen.blit(s, bg_rect.topleft)
            
            self.screen.blit(text_surface, text_rect)
        
        end_phase_deg = beam_data['phase'] * 180 / math.pi
        end_text = f"φ={end_phase_deg:.0f}°"
        
        text_surface = font.render(end_text, True, CYAN)
        text_rect = text_surface.get_rect()
        text_rect.center = (end[0] + scale(20), end[1] + scale(10))
        
        bg_rect = text_rect.inflate(scale(4), scale(2))
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, bg_rect.topleft)
        
        self.screen.blit(text_surface, text_rect)
        
        if beam_data['amplitude'] > 0.1:
            amp_text = f"|E|={beam_data['amplitude']:.2f}"
            amp_surface = font.render(amp_text, True, WHITE)
            amp_rect = amp_surface.get_rect()
            amp_rect.center = (end[0] + scale(20), end[1] + scale(22))
            
            bg_rect = amp_rect.inflate(scale(4), scale(2))
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.screen.blit(s, bg_rect.topleft)
            
            self.screen.blit(amp_surface, amp_rect)

    def _draw_ghost_beam_path(self, beam_data, time_offset=0):
        """Draw a beam path very dimly as a guide in quantum packet mode."""
        path = beam_data['path']
        amp = beam_data['amplitude']

        # Dim pulsing
        pulse = 0.12 + 0.05 * math.sin((self._frame_time + time_offset) * 1.5)
        alpha = max(15, min(50, int(255 * pulse * amp)))
        width = max(1, _settings.BEAM_WIDTH // 2)

        for i in range(len(path) - 1):
            start = path[i].tuple() if hasattr(path[i], 'tuple') else path[i]
            end = path[i+1].tuple() if hasattr(path[i+1], 'tuple') else path[i+1]

            # Create surface with alpha
            x1, y1 = start
            x2, y2 = end
            min_x = min(x1, x2) - width
            min_y = min(y1, y2) - width
            w = max(1, max(x1, x2) - min_x + width + 1)
            h = max(1, max(y1, y2) - min_y + width + 1)
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            local_p1 = (x1 - min_x, y1 - min_y)
            local_p2 = (x2 - min_x, y2 - min_y)
            color = (0, 160, 180, alpha)
            pygame.draw.line(surf, color, local_p1, local_p2, width)
            self.screen.blit(surf, (min_x, min_y))
