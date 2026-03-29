"""Detector component with improved interference calculation."""
import logging
import pygame
import math
import cmath
from components.base import Component
from config.settings import CYAN, WHITE

logger = logging.getLogger(__name__)

class Detector(Component):
    """Detector that shows total beam intensity with proper interference."""
    
    def __init__(self, x, y):
        super().__init__(x, y, "detector")
        self.intensity = 0
        self.last_beam = None
        self.total_path_length = 0
        self.incoming_beams = []  # Store all incoming beams
        self.processed_this_frame = False
        self.debug = False
        self.current_generation = -1  # Track which generation we're processing
    
    def reset_frame(self):
        """Reset for new frame processing."""
        self.incoming_beams = []
        self.processed_this_frame = False
        # Don't reset intensity immediately - let it persist until new beams arrive
        self.total_path_length = 0
        self.current_generation = -1
    
    def add_beam(self, beam):
        """Add a beam to the detector."""
        if self.processed_this_frame:
            # Detector already processed - reject beam
            if self.debug:
                logger.debug("  Detector at %s: rejecting beam (already processed)", self.position)
            return
        
        # Get beam generation
        beam_generation = beam.get('generation', 0)
        
        # If this is the first beam, set the generation
        if self.current_generation == -1:
            self.current_generation = beam_generation
        elif beam_generation != self.current_generation:
            # This beam is from a different generation - should not happen with proper tracing
            if self.debug:
                logger.warning("  Detector received beam from generation %d while processing generation %d", beam_generation, self.current_generation)
            return
        
        # Store the beam information
        self.incoming_beams.append({
            'amplitude': beam['amplitude'],
            'phase': beam.get('accumulated_phase', beam.get('phase', 0)),
            'path_length': beam.get('total_path_length', beam.get('path_length', 0)),
            'beam_id': beam.get('beam_id', 'unknown')
        })
        
        if self.debug:
            logger.debug("  Detector at %s received beam %s:", self.position, beam.get('beam_id', 'unknown'))
            logger.debug("    Amplitude: %.3f", beam['amplitude'])
            logger.debug("    Phase: %.1f°", beam.get('accumulated_phase', beam.get('phase', 0))*180/math.pi)
            logger.debug("    Generation: %d", beam_generation)
    
    def process_beam(self, beam):
        """Process beam - for detectors, we accumulate in add_beam instead."""
        # Add the beam for accumulation
        self.add_beam(beam)
        return []  # Detectors don't output beams
    
    def finalize_frame(self):
        """Calculate final intensity from all accumulated beams."""
        if self.processed_this_frame:
            return
        
        self.processed_this_frame = True
        
        # If no beams reached this detector, set intensity to 0
        if not self.incoming_beams:
            self.intensity = 0
            self.total_path_length = 0
            if self.debug:
                logger.debug("Detector at %s: No beams received", self.position)
            return
        
        # Calculate intensity using coherent superposition
        # For coherent beams: E_total = Σ(A_i * e^(iφ_i))
        # Intensity = |E_total|²
        
        complex_sum = 0j
        
        if self.debug:
            logger.debug("Detector at %s - intensity calculation (gen %d):", self.position, self.current_generation)
            logger.debug("  Number of beams: %d", len(self.incoming_beams))
        
        for i, beam in enumerate(self.incoming_beams):
            # Add complex amplitudes
            phase = beam['phase']
            complex_amplitude = beam['amplitude'] * cmath.exp(1j * phase)
            complex_sum += complex_amplitude
            
            if self.debug:
                logger.debug("  Beam %d (%s): A=%.3f, φ=%.1f°", i+1, beam['beam_id'], beam['amplitude'], phase*180/math.pi)
                logger.debug("    Complex amplitude: %s", f"{complex_amplitude:.3f}")
        
        # Calculate intensity as magnitude squared
        self.intensity = abs(complex_sum) ** 2
        
        # Calculate average path length for display
        if self.incoming_beams:
            self.total_path_length = sum(beam['path_length'] for beam in self.incoming_beams) / len(self.incoming_beams)
        
        if self.debug:
            logger.debug("  Total complex amplitude: %s", f"{complex_sum:.3f}")
            logger.debug("  Total intensity: %.3f = %.0f%%", self.intensity, self.intensity*100)

            # Show interference effects
            incoherent_sum = sum(beam['amplitude']**2 for beam in self.incoming_beams)
            logger.debug("  Incoherent sum: %.3f", incoherent_sum)
            if incoherent_sum > 0:
                logger.debug("  Interference factor: %.3f", self.intensity/incoherent_sum)
    
    def get_energy_info(self):
        """Get detailed energy information for conservation analysis."""
        # Calculate incoherent sum (what we'd get without interference)
        incoherent_sum = sum(beam['amplitude']**2 for beam in self.incoming_beams)
        
        # Detailed beam info
        beam_details = []
        for i, beam in enumerate(self.incoming_beams):
            beam_details.append({
                'amplitude': beam['amplitude'],
                'phase_rad': beam['phase'],
                'phase_deg': beam['phase'] * 180 / math.pi,
                'power': beam['amplitude']**2,
                'beam_id': beam.get('beam_id', f'beam_{i}')
            })
        
        return {
            'position': str(self.position),
            'num_beams': len(self.incoming_beams),
            'coherent_intensity': self.intensity,
            'input_power_sum': incoherent_sum,
            'beams': beam_details,
            'generation': self.current_generation
        }
    
    def get_intensity_percentage(self):
        """Get intensity as a percentage for display."""
        return int(round(self.intensity * 100))
    
    def draw(self, screen):
        """Draw detector with intensity visualization."""
        # Base circle
        s = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], 40), (self.radius * 2, self.radius * 2), self.radius)
        screen.blit(s, (self.position.x - self.radius * 2, self.position.y - self.radius * 2))
        
        # Border
        pygame.draw.circle(screen, CYAN, self.position.tuple(), self.radius, 3)
        
        # Inner detection area
        pygame.draw.circle(screen, CYAN, self.position.tuple(), 10)
        
        # Intensity visualization
        if self.intensity > 0.01:  # Show if > 1%
            # Glow effect based on intensity
            # Scale the glow for intensities up to 2.0 (200%)
            glow_radius = int(35 + min(self.intensity, 2.0) * 15)
            alpha = int(min(255, self.intensity * 64))
            s = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (glow_radius, glow_radius), glow_radius)
            screen.blit(s, (self.position.x - glow_radius, self.position.y - glow_radius))
            
            # Intensity ring
            ring_alpha = int(min(255, 128 + self.intensity * 64))
            ring_color = (CYAN[0], CYAN[1], CYAN[2], ring_alpha)
            s2 = pygame.Surface((glow_radius * 2 + 10, glow_radius * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(s2, ring_color, (glow_radius + 5, glow_radius + 5), glow_radius, 5)
            screen.blit(s2, (self.position.x - glow_radius - 5, self.position.y - glow_radius - 5))
        
        # Always display percentage
        display_percent = self.get_intensity_percentage()
        font = pygame.font.Font(None, 20)
        
        # Color changes based on intensity
        if self.intensity > 1.5:  # More than 150%
            text_color = (255, 255, 255)  # White for high intensity
        elif self.intensity > 1.0:  # More than 100%
            text_color = (0, 255, 255)  # Bright cyan
        elif self.intensity < 0.1:  # Less than 10%
            text_color = (100, 100, 100)  # Gray for low/no intensity
        else:
            text_color = (0, 200, 200)  # Normal cyan
        
        text = font.render(f"{display_percent}%", True, text_color)
        text_rect = text.get_rect(center=(self.position.x, self.position.y + 50))
        
        # Background for text
        bg_rect = text_rect.inflate(10, 5)
        s3 = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s3.fill((0, 0, 0, 180))
        screen.blit(s3, bg_rect.topleft)
        
        screen.blit(text, text_rect)
        
        # Show beam count in debug mode
        if self.debug and len(self.incoming_beams) > 1:
            beam_count_font = pygame.font.Font(None, 14)
            beam_text = beam_count_font.render(f"{len(self.incoming_beams)} beams", True, CYAN)
            beam_rect = beam_text.get_rect(center=(self.position.x, self.position.y + 70))
            screen.blit(beam_text, beam_rect)