"""Detector component."""
import pygame
import math
import cmath
from components.base import Component
from config.settings import CYAN, WHITE

class Detector(Component):
    """Detector that shows total beam intensity."""
    
    def __init__(self, x, y):
        super().__init__(x, y, "detector")
        self.intensity = 0
        self.last_beam = None
        self.total_path_length = 0
        self.incoming_beams = []  # Store all incoming beams
        self.processed_this_frame = False
        self.debug = False  # Debug off by default
    
    def reset_frame(self):
        """Reset for new frame processing."""
        self.incoming_beams = []
        self.processed_this_frame = False
        self.intensity = 0  # Reset intensity each frame
        self.total_path_length = 0
    
    def add_beam(self, beam):
        """Add a beam to the detector."""
        if not self.processed_this_frame:
            # Store the beam information
            self.incoming_beams.append({
                'amplitude': beam['amplitude'],
                'phase': beam.get('accumulated_phase', beam['phase']),
                'path_length': beam.get('total_path_length', 0)
            })
            
            if self.debug:
                print(f"  Detector at {self.position} received beam:")
                print(f"    Amplitude: {beam['amplitude']:.3f}")
                print(f"    Phase: {beam.get('accumulated_phase', beam['phase'])*180/math.pi:.1f}°")
        else:
            # Detector already processed - reject beam to prevent double counting
            if self.debug:
                print(f"  Detector at {self.position}: rejecting beam (already processed)")
    
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
        
        # If no beams reached this detector, intensity remains 0
        if not self.incoming_beams:
            self.intensity = 0
            self.total_path_length = 0
            return
        
        # Calculate intensity using coherent superposition
        # For coherent beams: E_total = Σ(A_i * e^(iφ_i))
        # Intensity = |E_total|²
        
        complex_sum = 0j
        
        for beam in self.incoming_beams:
            # Add complex amplitudes
            phase = beam['phase']
            complex_amplitude = beam['amplitude'] * cmath.exp(1j * phase)
            complex_sum += complex_amplitude
            
            if self.debug:
                print(f"    Beam amplitude: {beam['amplitude']:.3f}, phase: {phase*180/math.pi:.1f}°")
        
        # Calculate intensity as magnitude squared
        self.intensity = abs(complex_sum) ** 2
        
        # Calculate average path length for display
        if self.incoming_beams:
            self.total_path_length = sum(beam['path_length'] for beam in self.incoming_beams) / len(self.incoming_beams)
        
        if self.debug:
            print(f"\n  Detector at {self.position} - intensity calculation:")
            print(f"    Number of beams: {len(self.incoming_beams)}")
            print(f"    Total intensity: {self.intensity:.3f} = {self.intensity*100:.0f}%")
            print(f"    (Coherent sum of amplitudes)")
    
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
                'power': beam['amplitude']**2
            })
        
        return {
            'position': str(self.position),
            'num_beams': len(self.incoming_beams),
            'coherent_intensity': self.intensity,
            'input_power_sum': incoherent_sum,
            'beams': beam_details
        }
    
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
        if self.intensity > 0:
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
            
            # Display percentage
            # For simple intensity addition, 100% = 1 full beam
            # Multiple beams can exceed 100%
            display_percent = round(self.intensity * 100)  # FIXED: Use round() instead of int()
            font = pygame.font.Font(None, 20)
            
            # Color changes based on intensity
            if self.intensity > 1.5:  # More than 150%
                text_color = (255, 255, 255)  # White for high intensity
            elif self.intensity > 1.0:  # More than 100%
                text_color = (0, 255, 255)  # Bright cyan
            elif self.intensity < 0.1:  # Less than 10%
                text_color = (0, 128, 128)  # Dark cyan
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
        else:
            # Show 0% when no intensity
            font = pygame.font.Font(None, 20)
            text = font.render("0%", True, (100, 100, 100))
            text_rect = text.get_rect(center=(self.position.x, self.position.y + 50))
            
            # Background for text
            bg_rect = text_rect.inflate(10, 5)
            s3 = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s3.fill((0, 0, 0, 180))
            screen.blit(s3, bg_rect.topleft)
            
            screen.blit(text, text_rect)