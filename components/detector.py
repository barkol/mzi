"""Detector component."""
import pygame
import math
import cmath
from components.base import Component
from config.settings import CYAN, WHITE

class Detector(Component):
    """Detector that shows interference patterns."""
    
    def __init__(self, x, y):
        super().__init__(x, y, "detector")
        self.intensity = 0
        self.last_beam = None
        self.total_path_length = 0
        self.incoming_amplitudes = []  # Store complex amplitudes
        self.processed_this_frame = False
        self.debug = False  # Debug off by default
    
    def reset_frame(self):
        """Reset for new frame processing."""
        self.incoming_amplitudes = []
        self.processed_this_frame = False
        self.intensity = 0  # Reset intensity each frame
        self.total_path_length = 0
    
    def add_beam(self, beam):
        """Add a beam's complex amplitude for accumulation."""
        if not self.processed_this_frame:
            # Calculate complex amplitude including accumulated phase
            total_phase = beam.get('accumulated_phase', beam['phase'])
            complex_amplitude = beam['amplitude'] * cmath.exp(1j * total_phase)
            
            self.incoming_amplitudes.append({
                'amplitude': complex_amplitude,
                'path_length': beam.get('total_path_length', 0)
            })
            
            if self.debug:
                print(f"  Detector at {self.position} received beam:")
                print(f"    |E| = {beam['amplitude']:.3f}, accumulated phase = {total_phase*180/math.pi:.1f}°")
                print(f"    Complex amplitude: {complex_amplitude:.3f}")
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
        if not self.incoming_amplitudes:
            self.intensity = 0
            self.total_path_length = 0
            return
        
        # Sum all complex amplitudes
        total_amplitude = sum(beam['amplitude'] for beam in self.incoming_amplitudes)
        
        # Calculate intensity as |E|²
        self.intensity = abs(total_amplitude) ** 2
        
        # Calculate average path length for display
        if self.incoming_amplitudes:
            self.total_path_length = sum(beam['path_length'] for beam in self.incoming_amplitudes) / len(self.incoming_amplitudes)
        
        if self.debug and len(self.incoming_amplitudes) > 1:
            print(f"\n  Detector at {self.position} - interference calculation:")
            print(f"    Number of beams: {len(self.incoming_amplitudes)}")
            for i, beam in enumerate(self.incoming_amplitudes):
                print(f"    Beam {i+1}: E = {beam['amplitude']:.3f}")
            print(f"    Total complex amplitude: E_total = {total_amplitude:.3f}")
            print(f"    Intensity: |E_total|² = {self.intensity:.3f} = {self.intensity*100:.0f}%")
    
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
            # Glow effect based on intensity (scale for up to 400% intensity)
            glow_radius = int(35 + min(self.intensity, 4.0) * 10)
            alpha = int(min(255, self.intensity * 64))
            s = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (glow_radius, glow_radius), glow_radius)
            screen.blit(s, (self.position.x - glow_radius, self.position.y - glow_radius))
            
            # Intensity ring
            ring_alpha = int(min(255, 128 + self.intensity * 32))
            ring_color = (CYAN[0], CYAN[1], CYAN[2], ring_alpha)
            s2 = pygame.Surface((glow_radius * 2 + 10, glow_radius * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(s2, ring_color, (glow_radius + 5, glow_radius + 5), glow_radius, 5)
            screen.blit(s2, (self.position.x - glow_radius - 5, self.position.y - glow_radius - 5))
            
            # Display percentage (can go up to 400% for two beams constructively interfering)
            # For display, we normalize to single beam = 100%
            # Two beams constructively interfering = 400%
            display_percent = int(self.intensity * 100)
            font = pygame.font.Font(None, 20)
            
            # Color changes based on intensity - shades of turquoise
            if self.intensity > 3.5:  # Near maximum constructive interference
                text_color = (255, 255, 255)  # White for maximum
            elif self.intensity > 2.0:  # Strong constructive
                text_color = (0, 255, 255)  # Bright cyan
            elif self.intensity < 0.1:  # Near destructive
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
