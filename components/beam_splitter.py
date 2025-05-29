"""Beam splitter component with accurate phase-coherent accumulation."""
import pygame
import math
import cmath
from components.base import Component
from utils.vector import Vector2
from config.settings import CYAN, BEAM_SPLITTER_LOSS, IDEAL_COMPONENTS, WAVELENGTH

class BeamSplitter(Component):
    """50/50 beam splitter with proper quantum amplitude accumulation."""
    
    def __init__(self, x, y, realistic=True):  # Default to True, but keep parameter for compatibility
        super().__init__(x, y, "beamsplitter")
        self.incoming_beams = []  # Store all beams arriving this frame
        self.last_opd = None
        self.last_phase_diff = None
        self.debug = True
        self.processed_this_frame = False
        self.realistic = True  # Always use realistic phase shifts (π/2 on reflection)
        
        # Define the beam splitter transformation matrix
        # For a 50/50 beam splitter with \ orientation:
        # Input ports: A (left), B (bottom), C (right), D (top)
        # Output ports: same labeling
        # The transformation is symmetric
    
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
            
            # Show which ports have beams (visual feedback)
            if hasattr(self, '_last_frame_inputs'):
                for port, has_beam in self._last_frame_inputs.items():
                    if has_beam:
                        color = (255, 255, 0)  # Yellow for active ports
                        if port == 'A':
                            pygame.draw.circle(screen, color, (self.position.x - 25, self.position.y), 3)
                        elif port == 'B':
                            pygame.draw.circle(screen, color, (self.position.x, self.position.y + 25), 3)
                        elif port == 'C':
                            pygame.draw.circle(screen, color, (self.position.x + 25, self.position.y), 3)
                        elif port == 'D':
                            pygame.draw.circle(screen, color, (self.position.x, self.position.y - 25), 3)
            
            # Show expected behavior with small arrows
            arrow_color = (100, 255, 255, 128)
            # From A: right + down
            pygame.draw.line(screen, arrow_color, (self.position.x - 15, self.position.y),
                           (self.position.x - 10, self.position.y), 1)
            pygame.draw.line(screen, arrow_color, (self.position.x, self.position.y),
                           (self.position.x, self.position.y + 5), 1)
    
    def reset_frame(self):
        """Reset for new frame processing."""
        self.incoming_beams = []
        self.processed_this_frame = False
    
    def add_beam(self, beam):
        """Add a beam to the list of incoming beams."""
        if not self.processed_this_frame:
            self.incoming_beams.append(beam)
            if self.debug:
                print(f"  Beam splitter at {self.position} received beam from direction ({beam['direction'].x:.1f}, {beam['direction'].y:.1f})")
    
    def process_beam(self, beam):
        """Process beam - for beam splitters, we need to use finalize_frame instead."""
        # This method should not be called directly for beam splitters
        # The physics engine should handle beam splitters specially
        return []
    
    def finalize_frame(self):
        """Process all collected beams and generate outputs with proper amplitude accumulation."""
        if self.processed_this_frame or not self.incoming_beams:
            return []
        
        self.processed_this_frame = True
        
        if self.debug:
            print(f"\nBeam splitter at {self.position} - finalizing frame with {len(self.incoming_beams)} beam(s)")
        
        # STEP 1: Accumulate input amplitudes at each port
        E_in = {'A': complex(0, 0), 'B': complex(0, 0), 'C': complex(0, 0), 'D': complex(0, 0)}
        
        # Store which ports received beams for visualization
        self._last_frame_inputs = {'A': False, 'B': False, 'C': False, 'D': False}
        
        # Store path length info for OPD calculation
        path_lengths = []
        
        for beam in self.incoming_beams:
            direction = beam['direction']
            # Use the full phase including path length accumulation
            total_phase = beam.get('accumulated_phase', beam['phase'])
            amplitude = beam['amplitude'] * cmath.exp(1j * total_phase)
            path_lengths.append(beam.get('total_path_length', 0))
            
            # Debug: Show exact direction values and phase info
            if self.debug:
                path_phase = (beam.get('total_path_length', 0) * 2 * math.pi / WAVELENGTH) % (2 * math.pi)
                print(f"  Incoming beam: dir=({direction.x:.3f}, {direction.y:.3f}), |E|={beam['amplitude']:.3f}")
                print(f"    Path length: {beam.get('total_path_length', 0):.1f}px = {beam.get('total_path_length', 0)/WAVELENGTH:.2f}λ")
                print(f"    Initial phase: {beam.get('phase', 0)*180/math.pi:.1f}°")
                print(f"    Path phase contribution: {path_phase*180/math.pi:.1f}°")
                print(f"    Total phase: {total_phase*180/math.pi:.1f}°")
            
            # Determine which port this beam enters
            # In screen coordinates: +Y is DOWN, -Y is UP
            port = None
            if direction.x > 0.5 and abs(direction.y) < 0.5:  # Traveling RIGHT (from left)
                E_in['A'] += amplitude
                port = 'A'
                self._last_frame_inputs['A'] = True
            elif direction.y < -0.5 and abs(direction.x) < 0.5:  # Traveling UP (from bottom)
                E_in['B'] += amplitude
                port = 'B'
                self._last_frame_inputs['B'] = True
            elif direction.x < -0.5 and abs(direction.y) < 0.5:  # Traveling LEFT (from right)
                E_in['C'] += amplitude
                port = 'C'
                self._last_frame_inputs['C'] = True
            elif direction.y > 0.5 and abs(direction.x) < 0.5:  # Traveling DOWN (from top)
                E_in['D'] += amplitude
                port = 'D'
                self._last_frame_inputs['D'] = True
            else:
                print(f"WARNING: Unexpected beam direction: ({direction.x}, {direction.y})")
                # Try to determine closest port based on screen coordinates
                if abs(direction.x) > abs(direction.y):
                    if direction.x > 0:
                        E_in['A'] += amplitude
                        port = 'A (guessed - traveling RIGHT)'
                        self._last_frame_inputs['A'] = True
                    else:
                        E_in['C'] += amplitude
                        port = 'C (guessed - traveling LEFT)'
                        self._last_frame_inputs['C'] = True
                else:
                    if direction.y > 0:
                        E_in['D'] += amplitude
                        port = 'D (guessed - traveling DOWN)'
                        self._last_frame_inputs['D'] = True
                    else:
                        E_in['B'] += amplitude
                        port = 'B (guessed - traveling UP)'
                        self._last_frame_inputs['B'] = True
            
            if self.debug and port:
                print(f"    → Assigned to port {port}, accumulated |E|={abs(E_in[port[0]]):.3f}")
        
        # Calculate OPD and phase info if we have exactly 2 beams (for display purposes)
        if len(path_lengths) == 2 and len(self.incoming_beams) == 2:
            self.last_opd = path_lengths[1] - path_lengths[0]
            # Calculate actual phase difference including all contributions
            phase1 = self.incoming_beams[0].get('accumulated_phase', self.incoming_beams[0]['phase'])
            phase2 = self.incoming_beams[1].get('accumulated_phase', self.incoming_beams[1]['phase'])
            self.last_phase_diff = (phase2 - phase1) % (2 * math.pi)
            
            if self.debug:
                print(f"\n  Two-beam interference analysis:")
                print(f"    Path 1: {path_lengths[0]:.1f}px, Path 2: {path_lengths[1]:.1f}px")
                print(f"    OPD = {self.last_opd:.1f}px = {self.last_opd/WAVELENGTH:.2f}λ")
                print(f"    Phase 1: {phase1*180/math.pi:.1f}°, Phase 2: {phase2*180/math.pi:.1f}°")
                print(f"    Total phase difference: {self.last_phase_diff*180/math.pi:.1f}°")
        
        # SAFETY CHECK: Store a copy of input amplitudes before transformation for verification
        if self.debug:
            E_in_copy = {k: v for k, v in E_in.items()}
        
        # STEP 2: Apply beam splitter transformation
        # For a 50/50 beam splitter oriented like \ :
        # - Transmitted beams maintain direction (no phase shift)
        # - Reflected beams change direction (π/2 phase shift)
        
        # IMPORTANT: Calculate output amplitudes in a SEPARATE dictionary
        # to avoid any confusion between input and output modes
        E_out = {'A': complex(0, 0), 'B': complex(0, 0), 'C': complex(0, 0), 'D': complex(0, 0)}
        
        # Apply the beam splitter transformation matrix
        # Each INPUT port contributes to exactly TWO OUTPUT ports
        
        # From input port A (left, traveling right):
        if E_in['A'] != 0:
            # Transmitted to port C (continues right, no phase shift)
            E_out['C'] += E_in['A'] / math.sqrt(2)
            # Reflected to port B (turns down, π/2 phase shift)
            E_out['B'] += 1j * E_in['A'] / math.sqrt(2)
        
        # From input port B (bottom, traveling up):
        if E_in['B'] != 0:
            # Transmitted to port D (continues up, no phase shift)
            E_out['D'] += E_in['B'] / math.sqrt(2)
            # Reflected to port A (turns left, π/2 phase shift)
            E_out['A'] += 1j * E_in['B'] / math.sqrt(2)
        
        # From input port C (right, traveling left):
        if E_in['C'] != 0:
            # Transmitted to port A (continues left, no phase shift)
            E_out['A'] += E_in['C'] / math.sqrt(2)
            # Reflected to port D (turns up, π/2 phase shift)
            E_out['D'] += 1j * E_in['C'] / math.sqrt(2)
        
        # From input port D (top, traveling down):
        if E_in['D'] != 0:
            # Transmitted to port B (continues down, no phase shift)
            E_out['B'] += E_in['D'] / math.sqrt(2)
            # Reflected to port C (turns right, π/2 phase shift)
            E_out['C'] += 1j * E_in['D'] / math.sqrt(2)
        
        if self.debug:
            print(f"\n  Beam splitter transformation applied (with π/2 phase shifts on reflection):")
            print(f"  INPUT amplitudes:")
            for port in ['A', 'B', 'C', 'D']:
                if abs(E_in[port]) > 0.001:
                    print(f"    E_in[{port}] = {E_in[port]:.3f}")
            
            print(f"\n  Transformation matrix contributions:")
            if E_in['A'] != 0:
                print(f"    A→C: E_in[A]/√2 = {E_in['A']/math.sqrt(2):.3f} (transmitted)")
                print(f"    A→B: i·E_in[A]/√2 = {1j*E_in['A']/math.sqrt(2):.3f} (reflected)")
            if E_in['B'] != 0:
                print(f"    B→D: E_in[B]/√2 = {E_in['B']/math.sqrt(2):.3f} (transmitted)")
                print(f"    B→A: i·E_in[B]/√2 = {1j*E_in['B']/math.sqrt(2):.3f} (reflected)")
            if E_in['C'] != 0:
                print(f"    C→A: E_in[C]/√2 = {E_in['C']/math.sqrt(2):.3f} (transmitted)")
                print(f"    C→D: i·E_in[C]/√2 = {1j*E_in['C']/math.sqrt(2):.3f} (reflected)")
            if E_in['D'] != 0:
                print(f"    D→B: E_in[D]/√2 = {E_in['D']/math.sqrt(2):.3f} (transmitted)")
                print(f"    D→C: i·E_in[D]/√2 = {1j*E_in['D']/math.sqrt(2):.3f} (reflected)")
        
        # Apply losses if configured
        if not IDEAL_COMPONENTS and BEAM_SPLITTER_LOSS > 0:
            loss_factor = math.sqrt(1.0 - BEAM_SPLITTER_LOSS)
            for port in E_out:
                E_out[port] *= loss_factor
        
        # SAFETY CHECK: Verify input amplitudes weren't modified during transformation
        if self.debug:
            for port in ['A', 'B', 'C', 'D']:
                if E_in[port] != E_in_copy[port]:
                    print(f"ERROR: Input amplitude E_in[{port}] was modified!")
                    print(f"  Before: {E_in_copy[port]}")
                    print(f"  After: {E_in[port]}")
        
        # Debug: Check energy conservation
        if self.debug:
            # Show the complex amplitudes at each output port
            print(f"\n  OUTPUT port complex amplitudes:")
            for port, E in E_out.items():
                if abs(E) > 0.001:
                    dir_name = {'A': 'LEFT', 'B': 'DOWN', 'C': 'RIGHT', 'D': 'UP'}[port]
                    real = E.real
                    imag = E.imag
                    print(f"    Port {port} ({dir_name}): E = {real:.3f} + {imag:.3f}i, |E|={abs(E):.3f}, |E|²={abs(E)**2:.3f}")
            
            input_power = sum(abs(E)**2 for E in E_in.values())
            output_power = sum(abs(E)**2 for E in E_out.values())
            print(f"\n  Energy conservation check:")
            print(f"    Total input power: {input_power:.6f}")
            print(f"    Total output power: {output_power:.6f}")
            print(f"    Power ratio (out/in): {output_power/input_power if input_power > 0 else 0:.6f}")
            if abs(output_power/input_power - 1.0) > 0.001 and IDEAL_COMPONENTS:
                print(f"    WARNING: Energy not conserved!")
            
            if self.last_opd is not None:
                print(f"\n  Interference info:")
                print(f"    OPD = {self.last_opd:.1f}px = {self.last_opd/WAVELENGTH:.2f}λ")
                print(f"    Phase difference = {self.last_phase_diff*180/math.pi:.1f}°")
        
        # STEP 3: Generate output beams based on E_out
        output_beams = []
        avg_path_length = sum(path_lengths) / len(path_lengths) if path_lengths else 0
        
        # Port directions - corrected for screen coordinates where +Y is DOWN
        port_directions = {
            'A': Vector2(-1, 0),  # Left
            'B': Vector2(0, 1),   # Down (positive Y in screen coords)
            'C': Vector2(1, 0),   # Right
            'D': Vector2(0, -1)   # Up (negative Y in screen coords)
        }
        
        # Debug: show what beams we're generating
        if self.debug:
            print(f"\n  Generating output beams from E_out:")
        
        for port, E in E_out.items():
            if abs(E) > 0.001:  # Only emit beams with significant amplitude
                # Calculate the phase of the output complex amplitude
                output_phase = cmath.phase(E)
                
                beam = {
                    'position': self.position + port_directions[port] * 30,  # Increased from 25 to avoid immediate collision
                    'direction': port_directions[port],
                    'amplitude': abs(E),
                    'phase': output_phase,  # This is the phase after interference
                    'path_length': 0,
                    'total_path_length': avg_path_length,  # Preserve the average path length
                    'source_type': self.incoming_beams[0].get('source_type', 'laser') if self.incoming_beams else 'laser'
                }
                output_beams.append(beam)
                if self.debug:
                    dir_name = {'A': 'LEFT', 'B': 'DOWN', 'C': 'RIGHT', 'D': 'UP'}[port]
                    print(f"    Port {port} ({dir_name}): |E|={abs(E):.3f}, phase={output_phase*180/math.pi:.1f}°, path={avg_path_length:.1f}px")
        
        if self.debug:
            print(f"  Total output beams generated: {len(output_beams)}")
            
            # Check if we're missing any significant amplitude
            for port, E in E_out.items():
                if 0.0001 < abs(E) <= 0.001:
                    dir_name = {'A': 'LEFT', 'B': 'DOWN', 'C': 'RIGHT', 'D': 'UP'}[port]
                    print(f"    Note: Port {port} ({dir_name}) has small amplitude {abs(E):.6f} - not generated")
        
        return output_beams
