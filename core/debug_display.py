"""Debug display module for showing OPD and physics information."""
import pygame
import math
from config.settings import CYAN, WHITE, GREEN, CANVAS_OFFSET_X, CANVAS_OFFSET_Y, CANVAS_HEIGHT, CANVAS_WIDTH, WAVELENGTH

class DebugDisplay:
    """Handles display of debug information and optical path differences."""
    
    def __init__(self, screen):
        self.screen = screen
    
    def draw_opd_info(self, components, show_opd):
        """Draw optical path difference info if interferometer has interference."""
        if not show_opd:
            return
            
        # First check for beam splitter with recent interference
        interfering_bs = None
        for comp in components:
            if (comp.component_type == 'beamsplitter' and
                hasattr(comp, 'last_opd') and
                comp.last_opd is not None):
                interfering_bs = comp
                break
        
        if interfering_bs:
            self._draw_beamsplitter_opd(interfering_bs, components)
        else:
            self._draw_detector_opd(components)
    
    def _draw_beamsplitter_opd(self, beam_splitter, components):
        """Draw OPD info from beam splitter interference."""
        # Get OPD from the beam splitter where interference happened
        opd = beam_splitter.last_opd
        phase_diff = beam_splitter.last_phase_diff
        
        # Calculate phase contribution from OPD
        phase_from_opd = (abs(opd) * 2 * math.pi / WAVELENGTH) % (2 * math.pi)
        
        # Find detectors to show output intensities
        detectors = [c for c in components if c.component_type == 'detector' and c.intensity > 0.01]
        
        # Draw info box
        font = pygame.font.Font(None, 18)
        info_y = CANVAS_OFFSET_Y + CANVAS_HEIGHT - 120
        
        # Background
        bg_rect = pygame.Rect(CANVAS_OFFSET_X + 10, info_y, 360, 110)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        pygame.draw.rect(s, CYAN, s.get_rect(), 1)
        self.screen.blit(s, bg_rect.topleft)
        
        # Text
        title_text = font.render("Interferometer Status (at beam splitter):", True, CYAN)
        opd_text = font.render(f"Optical Path Difference: {abs(opd):.1f} px = {abs(opd)/WAVELENGTH:.2f}λ", True, WHITE)
        phase_from_opd = abs(opd) * 2 * math.pi / WAVELENGTH
        phase_opd_text = font.render(f"Phase from path difference: {phase_from_opd*180/math.pi:.1f}°", True, WHITE)
        phase_text = font.render(f"Total phase difference (including components): {phase_diff*180/math.pi:.1f}°", True, GREEN)
        
        self.screen.blit(title_text, (bg_rect.x + 10, bg_rect.y + 5))
        self.screen.blit(opd_text, (bg_rect.x + 10, bg_rect.y + 25))
        self.screen.blit(phase_opd_text, (bg_rect.x + 10, bg_rect.y + 45))
        self.screen.blit(phase_text, (bg_rect.x + 10, bg_rect.y + 65))
        
        # Show detector intensities if available
        if len(detectors) >= 2:
            total_intensity = sum(d.intensity for d in detectors)
            detector_text = font.render(f"Detector Intensities: {detectors[0].intensity*100:.0f}% + {detectors[1].intensity*100:.0f}% = {total_intensity*100:.0f}%", True, CYAN)
            self.screen.blit(detector_text, (bg_rect.x + 10, bg_rect.y + 85))
    
    def _draw_detector_opd(self, components):
        """Draw OPD based on detector readings."""
        # Fallback: Show detector-based OPD if available
        active_detectors = [c for c in components
                          if c.component_type == 'detector' and c.intensity > 0.01]
        
        if len(active_detectors) >= 2:
            # Calculate optical path difference from detectors
            path1 = active_detectors[0].total_path_length
            path2 = active_detectors[1].total_path_length
            opd = abs(path1 - path2)
            
            # Calculate phase difference from OPD
            phase_from_opd = (opd * 2 * math.pi / WAVELENGTH) % (2 * math.pi)
            
            # Draw info box
            font = pygame.font.Font(None, 18)
            info_y = CANVAS_OFFSET_Y + CANVAS_HEIGHT - 60
            
            # Background
            bg_rect = pygame.Rect(CANVAS_OFFSET_X + 10, info_y, 280, 50)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 200))
            pygame.draw.rect(s, CYAN, s.get_rect(), 1)
            self.screen.blit(s, bg_rect.topleft)
            
            # Text
            opd_text = font.render(f"Optical Path Difference: {opd:.1f} px", True, CYAN)
            phase_text = font.render(f"Phase from OPD: {phase_from_opd*180/math.pi:.1f}° ({opd/WAVELENGTH:.2f}λ)", True, WHITE)
            
            self.screen.blit(opd_text, (bg_rect.x + 10, bg_rect.y + 5))
            self.screen.blit(phase_text, (bg_rect.x + 10, bg_rect.y + 25))
        else:
            # Show hint if no interference yet
            font = pygame.font.Font(None, 16)
            hint_text = f"Tip: Create asymmetric paths for non-zero OPD (λ={WAVELENGTH}px ≠ grid={GRID_SIZE}px)"
            hint = font.render(hint_text, True, WHITE)
            hint_rect = hint.get_rect(center=(CANVAS_OFFSET_X + CANVAS_WIDTH // 2,
                                             CANVAS_OFFSET_Y + CANVAS_HEIGHT - 20))
            
            # Background for hint
            bg_rect = hint_rect.inflate(20, 10)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))
            self.screen.blit(s, bg_rect.topleft)
            
            self.screen.blit(hint, hint_rect)
    
    def draw_title_info(self):
        """Draw title and physics information."""
        font = pygame.font.Font(None, 48)
        title = font.render("PHOTON PATH", True, CYAN)
        subtitle_font = pygame.font.Font(None, 24)
        subtitle = subtitle_font.render("Build a Mach-Zehnder Interferometer", True, WHITE)
        
        title_rect = title.get_rect(centerx=CANVAS_OFFSET_X + CANVAS_WIDTH // 2, y=20)
        subtitle_rect = subtitle.get_rect(centerx=CANVAS_OFFSET_X + CANVAS_WIDTH // 2, y=70)
        
        self.screen.blit(title, title_rect)
        self.screen.blit(subtitle, subtitle_rect)
        
        # Show if using ideal components
        from config.settings import IDEAL_COMPONENTS, GRID_SIZE
        info_y = 20
        if IDEAL_COMPONENTS:
            ideal_font = pygame.font.Font(None, 18)
            ideal_text = ideal_font.render("IDEAL COMPONENTS (No Losses)", True, GREEN)
            ideal_rect = ideal_text.get_rect(right=CANVAS_OFFSET_X + CANVAS_WIDTH - 20, y=info_y)
            self.screen.blit(ideal_text, ideal_rect)
            info_y += 25
        
        # Show physics model info
        physics_font = pygame.font.Font(None, 16)
        physics_text = physics_font.render("Physics: BS +90° reflection, Mirror +180° reflection", True, CYAN)
        physics_rect = physics_text.get_rect(right=CANVAS_OFFSET_X + CANVAS_WIDTH - 20, y=info_y)
        self.screen.blit(physics_text, physics_rect)
        
        # Show wavelength info
        info_font = pygame.font.Font(None, 16)
        wave_text = info_font.render(f"λ = {WAVELENGTH}px, Grid = {GRID_SIZE}px", True, WHITE)
        wave_rect = wave_text.get_rect(right=CANVAS_OFFSET_X + CANVAS_WIDTH - 20, y=45)
        self.screen.blit(wave_text, wave_rect)
        
        # Show control hints
        toggle_text = info_font.render("C:MZ A:asym Shift+D:demo M:multi I:test V:vis H:help O:OPD T:BS G:debug", True, WHITE)
        toggle_rect = toggle_text.get_rect(left=CANVAS_OFFSET_X + 20, y=45)
        self.screen.blit(toggle_text, toggle_rect)