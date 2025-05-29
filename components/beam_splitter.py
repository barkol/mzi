"""Beam splitter component with careful phase tracking."""
import pygame
import math
import cmath
from components.base import Component
from utils.vector import Vector2
from config.settings import CYAN, BEAM_SPLITTER_LOSS, IDEAL_COMPONENTS, WAVELENGTH

REALISTIC_BEAM_SPLITTER = False

class BeamSplitter(Component):
    """50/50 beam splitter with quantum behavior."""
    
    def __init__(self, x, y):
        super().__init__(x, y, "beamsplitter")
        self.pending_beams = []
        self.last_opd = None
        self.last_phase_diff = None
        self.debug = True  # Enable detailed debugging
    
    def draw(self, screen):
        """Draw beam splitter."""
        # Main square
        rect = pygame.Rect(
            self.position.x - 20, 
            self.position.y - 20, 
            40, 40
        )
        
        # Fill
        s = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], 40), pygame.Rect(0, 0, 40, 40))
        screen.blit(s, rect.topleft)
        
        # Border
        pygame.draw.rect(screen, CYAN, rect, 3)
        
        # Diagonal line (\ orientation)
        pygame.draw.line(screen, CYAN, 
                        (self.position.x - 20, self.position.y - 20),
                        (self.position.x + 20, self.position.y + 20), 2)
        
        # Show port labels for debugging
        if self.debug:
            font = pygame.font.Font(None, 12)
            # Port A (left)
            text_a = font.render("A", True, CYAN)
            screen.blit(text_a, (self.position.x - 35, self.position.y - 5))
            # Port B (bottom)
            text_b = font.render("B", True, CYAN)
            screen.blit(text_b, (self.position.x - 5, self.position.y + 25))
            # Port C (right)
            text_c = font.render("C", True, CYAN)
            screen.blit(text_c, (self.position.x + 25, self.position.y - 5))
            # Port D (top)
            text_d = font.render("D", True, CYAN)
            screen.blit(text_d, (self.position.x - 5, self.position.y - 35))
    
    def process_beam(self, beam):
        """Process incoming beam with quantum behavior."""
        # Check if we have pending beams for interference
        if len(self.pending_beams) >= 2:
            # Two beams for interference
            result = self._interfere_beams(self.pending_beams[0], self.pending_beams[1])
            self.pending_beams.clear()
            return result
        elif len(self.pending_beams) == 1:
            # Only one beam this frame
            self.pending_beams.clear()
            return self._split_single_beam(beam)
        else:
            # No pending beams - just split this single beam
            return self._split_single_beam(beam)
    
    def _split_single_beam(self, beam):
        """Split a single beam 50/50."""
        # For a \ oriented beam splitter with ports:
        # A (left), B (bottom), C (right), D (top)
        
        direction = beam['direction']
        E_in = beam['amplitude'] * cmath.exp(1j * beam['phase'])
        
        if self.debug:
            print(f"\nBeam splitter at {self.position} - single beam:")
            print(f"  Input: dir=({direction.x:.1f},{direction.y:.1f}), phase={beam['phase']*180/math.pi:.1f}°")
        
        # Determine input port and calculate outputs
        if abs(direction.x - 1) < 0.1:  # From left (Port A)
            # Port A → C (transmitted) and D (reflected)
            if REALISTIC_BEAM_SPLITTER:
                E_C = E_in / math.sqrt(2)  # No phase shift
                E_D = 1j * E_in / math.sqrt(2)  # π/2 phase shift
            else:
                # Simplified model - no phase shifts
                E_C = E_in / math.sqrt(2)
                E_D = E_in / math.sqrt(2)
            
            outputs = [
                {'port': 'C', 'E': E_C, 'dir': Vector2(1, 0)},   # Right
                {'port': 'D', 'E': E_D, 'dir': Vector2(0, -1)}   # Up
            ]
            
        elif abs(direction.y - 1) < 0.1:  # From bottom (Port B)
            # Port B → C (reflected) and D (transmitted)
            if REALISTIC_BEAM_SPLITTER:
                E_C = 1j * E_in / math.sqrt(2)  # π/2 phase shift
                E_D = E_in / math.sqrt(2)  # No phase shift
            else:
                # Simplified model - no phase shifts
                E_C = E_in / math.sqrt(2)
                E_D = E_in / math.sqrt(2)
            
            outputs = [
                {'port': 'C', 'E': E_C, 'dir': Vector2(1, 0)},   # Right
                {'port': 'D', 'E': E_D, 'dir': Vector2(0, -1)}   # Up
            ]
            
        elif abs(direction.x + 1) < 0.1:  # From right (Port C)
            # Port C → A (transmitted) and B (reflected)
            E_A = E_in / math.sqrt(2)  # No phase shift
            E_B = 1j * E_in / math.sqrt(2)  # π/2 phase shift
            
            outputs = [
                {'port': 'A', 'E': E_A, 'dir': Vector2(-1, 0)},  # Left
                {'port': 'B', 'E': E_B, 'dir': Vector2(0, 1)}    # Down
            ]
            
        elif abs(direction.y + 1) < 0.1:  # From top (Port D)
            # Port D → A (reflected) and B (transmitted)
            E_A = 1j * E_in / math.sqrt(2)  # π/2 phase shift
            E_B = E_in / math.sqrt(2)  # No phase shift
            
            outputs = [
                {'port': 'A', 'E': E_A, 'dir': Vector2(-1, 0)},  # Left
                {'port': 'B', 'E': E_B, 'dir': Vector2(0, 1)}    # Down
            ]
        else:
            # Shouldn't happen
            print(f"  WARNING: Unexpected beam direction: ({direction.x}, {direction.y})")
            return []
        
        # Apply losses if any
        if not IDEAL_COMPONENTS and BEAM_SPLITTER_LOSS > 0:
            loss_factor = math.sqrt(1.0 - BEAM_SPLITTER_LOSS)
            for output in outputs:
                output['E'] *= loss_factor
        
        # Convert to beam format
        result = []
        for output in outputs:
            if abs(output['E']) > 0.01:
                phase_out = cmath.phase(output['E'])
                result.append({
                    'position': self.position + output['dir'] * 25,
                    'direction': output['dir'],
                    'amplitude': abs(output['E']),
                    'phase': phase_out,
                    'path_length': 0,
                    'total_path_length': beam.get('total_path_length', 0),
                    'source_type': 'shifted' if output['port'] in ['B', 'D'] and beam.get('source_type') == 'laser' else beam['source_type']
                })
                
                if self.debug:
                    print(f"  Output {output['port']}: phase={phase_out*180/math.pi:.1f}° ({'reflected' if output['port'] in ['B', 'D'] else 'transmitted'})")
        
        return result
    
    def _interfere_beams(self, beam1, beam2):
        """Calculate quantum interference between two beams."""
        # Store OPD info
        path1 = beam1.get('total_path_length', 0)
        path2 = beam2.get('total_path_length', 0)
        self.last_opd = path2 - path1
        
        # Get beam parameters
        dir1 = beam1['direction']
        dir2 = beam2['direction']
        E1 = beam1['amplitude'] * cmath.exp(1j * beam1['phase'])
        E2 = beam2['amplitude'] * cmath.exp(1j * beam2['phase'])
        
        self.last_phase_diff = (beam2['phase'] - beam1['phase']) % (2 * math.pi)
        
        if self.debug:
            print(f"\nBeam splitter at {self.position} - two beam interference:")
            print(f"  Beam 1: from ({dir1.x:.0f},{dir1.y:.0f}), phase={beam1['phase']*180/math.pi:.1f}°, path={path1:.0f}px")
            print(f"  Beam 2: from ({dir2.x:.0f},{dir2.y:.0f}), phase={beam2['phase']*180/math.pi:.1f}°, path={path2:.0f}px")
            print(f"  OPD = {self.last_opd:.0f}px = {self.last_opd/WAVELENGTH:.2f}λ")
        
        # Map beams to input ports
        E_A = E_B = 0
        
        # Check Beam 1
        if abs(dir1.x - 1) < 0.1:
            E_A = E1  # Beam 1 enters port A
            port1 = 'A'
        elif abs(dir1.y - 1) < 0.1:
            E_B = E1  # Beam 1 enters port B
            port1 = 'B'
        else:
            print(f"  WARNING: Beam 1 unexpected direction")
            port1 = '?'
        
        # Check Beam 2
        if abs(dir2.x - 1) < 0.1:
            E_A = E2  # Beam 2 enters port A
            port2 = 'A'
        elif abs(dir2.y - 1) < 0.1:
            E_B = E2  # Beam 2 enters port B
            port2 = 'B'
        else:
            print(f"  WARNING: Beam 2 unexpected direction")
            port2 = '?'
        
        if self.debug:
            print(f"  Port mapping: Beam 1→{port1}, Beam 2→{port2}")
        
        # Apply beam splitter matrix
        # [E_C]   [1/√2    i/√2] [E_A]
        # [E_D] = [i/√2    1/√2] [E_B]
        
        E_C = (E_A + 1j * E_B) / math.sqrt(2)
        E_D = (1j * E_A + E_B) / math.sqrt(2)
        
        # Apply losses
        if not IDEAL_COMPONENTS and BEAM_SPLITTER_LOSS > 0:
            loss_factor = math.sqrt(1.0 - BEAM_SPLITTER_LOSS)
            E_C *= loss_factor
            E_D *= loss_factor
        
        # Calculate intensities
        I_in = abs(E_A)**2 + abs(E_B)**2
        I_C = abs(E_C)**2
        I_D = abs(E_D)**2
        I_out = I_C + I_D
        
        if self.debug:
            print(f"  Input power: {I_in:.3f}")
            print(f"  Output: Port C (right)={I_C:.3f}, Port D (up)={I_D:.3f}")
            print(f"  Total output: {I_out:.3f}")
            print(f"  Energy conservation: {I_out/I_in:.6f}")
            
            if abs(I_out/I_in - 1.0) > 0.001 and IDEAL_COMPONENTS:
                print(f"  ERROR: Energy not conserved!")
                print(f"  Debug: E_A={E_A}, E_B={E_B}")
                print(f"  Debug: E_C={E_C}, E_D={E_D}")
        
        # Create output beams
        outputs = []
        path_avg = (path1 + path2) / 2
        
        if abs(E_C) > 0.01:
            outputs.append({
                'position': self.position + Vector2(1, 0) * 25,
                'direction': Vector2(1, 0),
                'amplitude': abs(E_C),
                'phase': cmath.phase(E_C),
                'path_length': 0,
                'total_path_length': path_avg,
                'source_type': beam1.get('source_type', 'laser')
            })
        
        if abs(E_D) > 0.01:
            outputs.append({
                'position': self.position + Vector2(0, -1) * 25,
                'direction': Vector2(0, -1),
                'amplitude': abs(E_D),
                'phase': cmath.phase(E_D),
                'path_length': 0,
                'total_path_length': path_avg,
                'source_type': beam1.get('source_type', 'laser')
            })
        
        return outputs