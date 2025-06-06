"""Debug display module for showing OPD and physics information with scaling."""
import pygame
import math
from config.settings import CYAN, WHITE, GREEN, CANVAS_OFFSET_X, CANVAS_OFFSET_Y, CANVAS_HEIGHT, CANVAS_WIDTH, WAVELENGTH, GRID_SIZE, IDEAL_COMPONENTS, scale, scale_font

class DebugDisplay:
    """Handles display of debug information and optical path differences with scaling."""
    
    def __init__(self, screen):
        self.screen = screen
        self.assets_loader = None  # Will be set by the game
        self._actual_screen_size = None  # Store actual screen size for fullscreen
    
    def set_assets_loader(self, assets_loader):
        """Set the assets loader instance."""
        self.assets_loader = assets_loader
    
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
        """Draw OPD info from beam splitter interference with scaling."""
        # Get OPD from the beam splitter where interference happened
        opd = beam_splitter.last_opd
        phase_diff = beam_splitter.last_phase_diff
        
        # Calculate phase contribution from OPD
        phase_from_opd = (abs(opd) * 2 * math.pi / WAVELENGTH) % (2 * math.pi)
        
        # Find detectors to show output intensities
        detectors = [c for c in components if c.component_type == 'detector' and c.intensity > 0.01]
        
        # Draw info box
        font = pygame.font.Font(None, scale_font(18))
        info_y = CANVAS_OFFSET_Y + CANVAS_HEIGHT - scale(120)
        
        # Background
        bg_rect = pygame.Rect(CANVAS_OFFSET_X + scale(10), info_y, scale(360), scale(110))
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        pygame.draw.rect(s, CYAN, s.get_rect(), scale(1))
        self.screen.blit(s, bg_rect.topleft)
        
        # Text
        title_text = font.render("Interferometer Status (at beam splitter):", True, CYAN)
        opd_text = font.render(f"Optical Path Difference: {abs(opd):.1f} px = {abs(opd)/WAVELENGTH:.2f}λ", True, WHITE)
        phase_from_opd = abs(opd) * 2 * math.pi / WAVELENGTH
        phase_opd_text = font.render(f"Phase from path difference: {phase_from_opd*180/math.pi:.1f}°", True, WHITE)
        phase_text = font.render(f"Total phase difference (including components): {phase_diff*180/math.pi:.1f}°", True, GREEN)
        
        self.screen.blit(title_text, (bg_rect.x + scale(10), bg_rect.y + scale(5)))
        self.screen.blit(opd_text, (bg_rect.x + scale(10), bg_rect.y + scale(25)))
        self.screen.blit(phase_opd_text, (bg_rect.x + scale(10), bg_rect.y + scale(45)))
        self.screen.blit(phase_text, (bg_rect.x + scale(10), bg_rect.y + scale(65)))
        
        # Show detector intensities if available
        if len(detectors) >= 2:
            total_intensity = sum(d.intensity for d in detectors)
            detector_text = font.render(f"Detector Intensities: {detectors[0].intensity*100:.0f}% + {detectors[1].intensity*100:.0f}% = {total_intensity*100:.0f}%", True, CYAN)
            self.screen.blit(detector_text, (bg_rect.x + scale(10), bg_rect.y + scale(85)))
    
    def _draw_detector_opd(self, components):
        """Draw OPD based on detector readings with scaling."""
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
            font = pygame.font.Font(None, scale_font(18))
            info_y = CANVAS_OFFSET_Y + CANVAS_HEIGHT - scale(60)
            
            # Background
            bg_rect = pygame.Rect(CANVAS_OFFSET_X + scale(10), info_y, scale(280), scale(50))
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 200))
            pygame.draw.rect(s, CYAN, s.get_rect(), scale(1))
            self.screen.blit(s, bg_rect.topleft)
            
            # Text
            opd_text = font.render(f"Optical Path Difference: {opd:.1f} px", True, CYAN)
            phase_text = font.render(f"Phase from OPD: {phase_from_opd*180/math.pi:.1f}° ({opd/WAVELENGTH:.2f}λ)", True, WHITE)
            
            self.screen.blit(opd_text, (bg_rect.x + scale(10), bg_rect.y + scale(5)))
            self.screen.blit(phase_text, (bg_rect.x + scale(10), bg_rect.y + scale(25)))
        else:
            # Show hint if no interference yet
            font = pygame.font.Font(None, scale_font(16))
            hint_text = f"Tip: Create asymmetric paths for non-zero OPD (λ={WAVELENGTH}px ≠ grid={GRID_SIZE}px)"
            hint = font.render(hint_text, True, WHITE)
            hint_rect = hint.get_rect(center=(CANVAS_OFFSET_X + CANVAS_WIDTH // 2,
                                             CANVAS_OFFSET_Y + CANVAS_HEIGHT - scale(20)))
            
            # Background for hint
            bg_rect = hint_rect.inflate(scale(20), scale(10))
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))
            self.screen.blit(s, bg_rect.topleft)
            
            self.screen.blit(hint, hint_rect)
    
    def draw_banner(self):
        """Draw the banner image as full window background."""
        if self.assets_loader and self.screen:
            try:
                # Get screen size - prefer stored actual screen size
                if hasattr(self, '_actual_screen_size') and self._actual_screen_size:
                    screen_size = self._actual_screen_size
                elif hasattr(self.screen, 'get_size'):
                    screen_size = self.screen.get_size()
                else:
                    # Fallback to window settings if screen is invalid
                    from config.settings import WINDOW_WIDTH, WINDOW_HEIGHT
                    screen_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
                
                banner = self.assets_loader.get_banner(screen_size)
                # Draw at (0, 0) to fill entire window
                self.screen.blit(banner, (0, 0))
            except pygame.error as e:
                # Handle the case where screen is temporarily invalid
                print(f"Banner draw skipped during display transition: {e}")
                pass
    
    def draw_info_text(self):
        """Draw small info text in bottom right with scaling."""
        # Show if using ideal components
        info_y = CANVAS_OFFSET_Y + CANVAS_HEIGHT - scale(45)
        info_x = CANVAS_OFFSET_X + CANVAS_WIDTH - scale(20)
        
        if IDEAL_COMPONENTS:
            ideal_font = pygame.font.Font(None, scale_font(14))
            ideal_text = ideal_font.render("IDEAL COMPONENTS", True, GREEN)
            ideal_rect = ideal_text.get_rect(right=info_x, y=info_y)
            self.screen.blit(ideal_text, ideal_rect)
            info_y += scale(20)
        
        # Show physics model info
        physics_font = pygame.font.Font(None, scale_font(12))
        physics_text = physics_font.render("BS +90° | Mirror +180°", True, CYAN)
        physics_rect = physics_text.get_rect(right=info_x, y=info_y)
        self.screen.blit(physics_text, physics_rect)