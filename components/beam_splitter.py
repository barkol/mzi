"""Beam splitter component with scaling support."""
import pygame
import numpy as np
import math
import cmath
from components.tunable_beamsplitter import TunableBeamSplitter
from config.settings import CYAN, BEAM_SPLITTER_LOSS, scale, scale_font

class BeamSplitter(TunableBeamSplitter):
    """50/50 beam splitter with scaling support."""
    
    def __init__(self, x, y):
        """Initialize 50/50 beam splitter."""
        # For a 50/50 beam splitter:
        # t = 1/√2 (transmission)
        # r = i/√2 (reflection with π/2 phase shift)
        # r' = -i/√2 (to satisfy r*r' = -1)
        t = 1.0 / np.sqrt(2)
        r = 1j / np.sqrt(2)
        
        # Initialize parent (will build matrix)
        super().__init__(x, y, t=t, r=r, orientation='\\', loss=BEAM_SPLITTER_LOSS)
        self.component_type = "beamsplitter"
        
        # Override with explicit symmetric 50/50 beam splitter matrix
        if self.orientation == '\\':
            # Backslash orientation
            self.S = np.array([
                [0,      1j,     1,      0 ],  # A
                [1j,     0,      0,      1 ],  # B
                [1,      0,      0,      1j],  # C
                [0,      1,      1j,     0 ]   # D
            ], dtype=complex) / np.sqrt(2)
        else:  # '/'
            # Forward slash orientation
            self.S = np.array([
                [0,      1j,     0,      1 ],  # A
                [1j,     0,      1,      0 ],  # B
                [0,      1,      0,      1j],  # C
                [1,      0,      1j,     0 ]   # D
            ], dtype=complex) / np.sqrt(2)
        
        # Verify unitarity
        S_dagger = np.conj(self.S.T)
        identity_check = S_dagger @ self.S
        max_error = np.max(np.abs(identity_check - np.eye(4)))
        if max_error > 1e-10:
            print(f"WARNING: BeamSplitter matrix not unitary! Error: {max_error}")
        
        # For display - store OPD info
        self.last_opd = None
        self.last_phase_diff = None
    
    def draw(self, screen):
        """Draw beam splitter with custom appearance and scaling."""
        # Main square - scaled size
        size = scale(40)
        half_size = size // 2
        rect = pygame.Rect(
            self.position.x - half_size,
            self.position.y - half_size,
            size, size
        )
        
        # Fill
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], 40), pygame.Rect(0, 0, size, size))
        screen.blit(s, rect.topleft)
        
        # Border
        pygame.draw.rect(screen, CYAN, rect, scale(3))
        
        # Diagonal line (\ orientation)
        pygame.draw.line(screen, CYAN,
                        (self.position.x - half_size, self.position.y - half_size),
                        (self.position.x + half_size, self.position.y + half_size), scale(2))
        
        # Show port labels in debug mode
        if self.debug:
            font = pygame.font.Font(None, scale_font(12))
            # Port A (left)
            text_a = font.render("A", True, CYAN)
            screen.blit(text_a, (self.position.x - scale(35), self.position.y - scale(5)))
            # Port B (bottom)
            text_b = font.render("B", True, CYAN)
            screen.blit(text_b, (self.position.x - scale(5), self.position.y + scale(25)))
            # Port C (right)
            text_c = font.render("C", True, CYAN)
            screen.blit(text_c, (self.position.x + scale(25), self.position.y - scale(5)))
            # Port D (top)
            text_d = font.render("D", True, CYAN)
            screen.blit(text_d, (self.position.x - scale(5), self.position.y - scale(35)))
            
            # Show coefficients
            coeff_font = pygame.font.Font(None, scale_font(10))
            coeff_text = f"t={abs(self.t):.2f}, r={abs(self.r):.2f}∠{cmath.phase(self.r)*180/math.pi:.0f}°"
            coeff_surface = coeff_font.render(coeff_text, True, CYAN)
            screen.blit(coeff_surface, (self.position.x - scale(40), self.position.y + scale(50)))
            
            # Show input/output vectors if available
            if self._last_v_in is not None and self._last_v_out is not None:
                # Find non-zero ports
                active_ports = []
                for i, (v_in, v_out) in enumerate(zip(self._last_v_in, self._last_v_out)):
                    if abs(v_in) > 0.001 or abs(v_out) > 0.001:
                        active_ports.append(i)
                
                if active_ports:
                    port_names = ['A', 'B', 'C', 'D']
                    y_offset = scale(65)
                    for port_idx in active_ports[:2]:  # Show max 2 to avoid clutter
                        port_text = f"{port_names[port_idx]}: {self._last_v_in[port_idx]:.2f} → {self._last_v_out[port_idx]:.2f}"
                        port_surface = coeff_font.render(port_text, True, CYAN)
                        screen.blit(port_surface, (self.position.x - scale(40), self.position.y + y_offset))
                        y_offset += scale(10)
    
    def finalize_frame(self):
        """Process beams and calculate OPD for display."""
        # Store beam info for OPD calculation if we have beams from exactly 2 ports
        ports_with_beams = []
        for port_idx, beams in self.all_beams_by_port.items():
            if beams:
                ports_with_beams.append(port_idx)
        
        if len(ports_with_beams) == 2:
            # Calculate average path length and phase for each port
            path_lengths = []
            phases = []
            
            for port_idx in ports_with_beams:
                port_beams = self.all_beams_by_port[port_idx]
                if port_beams:
                    # Average path length for this port
                    avg_path = sum(b.get('total_path_length', 0) for b in port_beams) / len(port_beams)
                    path_lengths.append(avg_path)
                    
                    # Calculate resultant phase from interference at this port
                    complex_sum = 0j
                    for beam in port_beams:
                        total_phase = beam.get('accumulated_phase', beam['phase'])
                        complex_sum += beam['amplitude'] * cmath.exp(1j * total_phase)
                    resultant_phase = cmath.phase(complex_sum) if abs(complex_sum) > 0 else 0
                    phases.append(resultant_phase)
            
            if len(path_lengths) == 2:
                self.last_opd = path_lengths[1] - path_lengths[0]
                self.last_phase_diff = (phases[1] - phases[0]) % (2 * math.pi)
        
        # Call parent method
        return super().finalize_frame()