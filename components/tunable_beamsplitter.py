"""Tunable beam splitter - base class for all optical components."""
import pygame
import numpy as np
import math
import cmath
from components.base import Component
from utils.vector import Vector2
from config.settings import CYAN, IDEAL_COMPONENTS

class TunableBeamSplitter(Component):
    """
    General beam splitter with tunable transmission and reflection coefficients.
    
    All optical components (beam splitters, mirrors, etc.) are special cases
    of this general beam splitter.
    
    Parameters:
    - t: transmission coefficient (complex)
    - r: reflection coefficient from one side (complex)
    - r_prime: reflection coefficient from other side (complex)
    
    Constraints:
    - t = t' (reciprocity)
    - r * r' = -1 (phase relation)
    - |r|² + |t|² = 1 (energy conservation)
    """
    
    def __init__(self, x, y, t=None, r=None, r_prime=None, orientation='\\', loss=0.0):
        """
        Initialize tunable beam splitter.
        
        Args:
            x, y: Position
            t: Transmission coefficient (if None, calculated from r)
            r: Reflection coefficient from one side
            r_prime: Reflection coefficient from other side (if None, calculated as -1/r)
            orientation: '\\' or '/' - determines port connections
            loss: Loss factor (0 to 1)
        """
        super().__init__(x, y, "tunable_beamsplitter")
        
        # Set coefficients
        if r is None and t is None:
            # Default to 50/50 beam splitter
            self.t = 1.0 / np.sqrt(2)
            self.r = 1j / np.sqrt(2)
            self.r_prime = -1j / np.sqrt(2)
        elif r is not None:
            self.r = complex(r)
            # Calculate r' from constraint r * r' = -1
            self.r_prime = complex(r_prime) if r_prime is not None else -1.0 / self.r
            # Calculate t from energy conservation |r|² + |t|² = 1
            self.t = complex(t) if t is not None else np.sqrt(1.0 - abs(self.r)**2)
        else:
            # Only t provided
            self.t = complex(t)
            # For pure transmission, no reflection
            self.r = 0
            self.r_prime = 0
        
        # Verify constraints
        self._verify_constraints()
        
        self.orientation = orientation
        self.loss = loss
        self.incoming_beams = []
        self.processed_this_frame = False
        self.debug = False
        
        # Build scattering matrix based on orientation
        self._build_scattering_matrix()
        
        # Store debug info
        self._last_v_in = None
        self._last_v_out = None
    
    def _verify_constraints(self):
        """Verify physical constraints on coefficients."""
        # Check energy conservation (within numerical tolerance)
        energy = abs(self.r)**2 + abs(self.t)**2
        if abs(energy - 1.0) > 1e-6:
            print(f"WARNING: Energy not conserved: |r|²+|t|² = {energy:.6f}")
        
        # Check phase relation r*r' = -1
        product = self.r * self.r_prime
        if abs(product + 1.0) > 1e-6:
            print(f"WARNING: Phase relation violated: r*r' = {product:.6f} (should be -1)")
    
    def _build_scattering_matrix(self):
        """Build scattering matrix based on coefficients and orientation."""
        # Port order: [A (left), B (bottom), C (right), D (top)]
        
        if self.orientation == '\\':
            # Backslash orientation: A↔C transmission, B↔D transmission
            # The scattering matrix must be symmetric for reciprocity
            self.S = np.array([
                [0,           self.r,       self.t,      0          ],  # A
                [self.r,      0,           0,           self.t      ],  # B
                [self.t,      0,           0,           self.r_prime],  # C
                [0,           self.t,      self.r_prime, 0          ]   # D
            ], dtype=complex)
        else:  # '/'
            # Forward slash orientation: A↔D transmission, B↔C transmission
            self.S = np.array([
                [0,           self.r,      0,           self.t      ],  # A
                [self.r,      0,           self.t,      0          ],  # B
                [0,           self.t,      0,           self.r_prime],  # C
                [self.t,      0,           self.r_prime, 0          ]   # D
            ], dtype=complex)
        
        # Verify the matrix is unitary (S†S = I) for energy conservation
        S_dagger = np.conj(self.S.T)
        should_be_identity = S_dagger @ self.S
        identity_error = np.max(np.abs(should_be_identity - np.eye(4)))
        
        if identity_error > 1e-10:
            if self.debug:
                print(f"WARNING: Scattering matrix not unitary! Max error: {identity_error}")
                print("S†S =")
                print(should_be_identity)
        
        # Also verify symmetry for reciprocity
        symmetry_error = np.max(np.abs(self.S - self.S.T))
        if symmetry_error > 1e-10 and abs(self.r - self.r_prime) > 1e-10:
            if self.debug:
                print(f"WARNING: Scattering matrix not symmetric! Max error: {symmetry_error}")
                print("This is expected when r ≠ r'")
    
    def reset_frame(self):
        """Reset for new frame processing."""
        self.incoming_beams = []
        self.processed_this_frame = False
    
    def add_beam(self, beam):
        """Add a beam to be processed."""
        if not self.processed_this_frame:
            self.incoming_beams.append(beam)
            if self.debug:
                phase_deg = beam.get('accumulated_phase', beam['phase']) * 180 / math.pi
                print(f"  {self.component_type} at {self.position}: beam from dir ({beam['direction'].x:.1f}, {beam['direction'].y:.1f}), phase={phase_deg:.1f}°")
    
    def process_beam(self, beam):
        """Process single beam (for compatibility)."""
        self.reset_frame()
        self.add_beam(beam)
        return self.finalize_frame()
    
    def finalize_frame(self):
        """Process all beams using scattering matrix formalism."""
        if self.processed_this_frame or not self.incoming_beams:
            return []
        
        self.processed_this_frame = True
        
        if self.debug:
            print(f"\n{self.component_type} at {self.position} - processing {len(self.incoming_beams)} beam(s)")
            print(f"  Coefficients: t={self.t:.3f}, r={self.r:.3f}, r'={self.r_prime:.3f}")
            print(f"  Orientation: {self.orientation}")
        
        # Build input amplitude vector
        v_in = np.zeros(4, dtype=complex)
        path_lengths = []
        
        for beam in self.incoming_beams:
            direction = beam['direction']
            total_phase = beam.get('accumulated_phase', beam['phase'])
            amplitude = beam['amplitude'] * cmath.exp(1j * total_phase)
            path_lengths.append(beam.get('total_path_length', 0))
            
            # Map to input port
            port_idx = None
            port_name = None
            
            if direction.x > 0.5 and abs(direction.y) < 0.5:  # RIGHT → Port A
                v_in[0] += amplitude
                port_name = 'A'
            elif direction.y < -0.5 and abs(direction.x) < 0.5:  # UP → Port B
                v_in[1] += amplitude
                port_name = 'B'
            elif direction.x < -0.5 and abs(direction.y) < 0.5:  # LEFT → Port C
                v_in[2] += amplitude
                port_name = 'C'
            elif direction.y > 0.5 and abs(direction.x) < 0.5:  # DOWN → Port D
                v_in[3] += amplitude
                port_name = 'D'
            
            if self.debug and port_name:
                print(f"    Beam → port {port_name}: |E|={beam['amplitude']:.3f}, φ={total_phase*180/math.pi:.1f}°")
        
        self._last_v_in = v_in.copy()
        
        # Apply scattering matrix
        v_out = self.S @ v_in
        
        # Apply losses if configured
        if not IDEAL_COMPONENTS and self.loss > 0:
            loss_factor = math.sqrt(1.0 - self.loss)
            v_out *= loss_factor
        
        self._last_v_out = v_out.copy()
        
        if self.debug:
            print(f"\n  Input/Output vectors:")
            print(f"    v_in  = [{v_in[0]:.3f}, {v_in[1]:.3f}, {v_in[2]:.3f}, {v_in[3]:.3f}]")
            print(f"    v_out = [{v_out[0]:.3f}, {v_out[1]:.3f}, {v_out[2]:.3f}, {v_out[3]:.3f}]")
            
            # Detailed port analysis
            port_names = ['A(left)', 'B(bottom)', 'C(right)', 'D(top)']
            print(f"\n  Detailed transformation:")
            for i in range(4):
                if abs(v_in[i]) > 0.001:
                    print(f"    Input at {port_names[i]}: {v_in[i]:.3f}")
                    for j in range(4):
                        if abs(self.S[j, i]) > 0.001:
                            contribution = self.S[j, i] * v_in[i]
                            print(f"      → {port_names[j]}: S[{j},{i}]={self.S[j, i]:.3f} × {v_in[i]:.3f} = {contribution:.3f}")
            
            # Energy conservation check
            input_power = np.sum(np.abs(v_in)**2)
            output_power = np.sum(np.abs(v_out)**2)
            if input_power > 0:
                ratio = output_power/input_power
                print(f"\n  Energy conservation:")
                print(f"    Input power: Σ|v_in|² = {input_power:.6f}")
                print(f"    Output power: Σ|v_out|² = {output_power:.6f}")
                print(f"    Power ratio: {ratio:.6f}")
                if abs(ratio - 1.0) > 0.001:
                    print(f"    WARNING: Energy not conserved! Deviation: {(ratio-1)*100:.2f}%")
        
        # Generate output beams
        output_beams = []
        avg_path_length = sum(path_lengths) / len(path_lengths) if path_lengths else 0
        
        # Port directions
        port_info = [
            {'name': 'A', 'direction': Vector2(-1, 0)},
            {'name': 'B', 'direction': Vector2(0, 1)},
            {'name': 'C', 'direction': Vector2(1, 0)},
            {'name': 'D', 'direction': Vector2(0, -1)}
        ]
        
        for i, (amplitude, port) in enumerate(zip(v_out, port_info)):
            if abs(amplitude) > 0.001:
                output_phase = cmath.phase(amplitude)
                
                beam = {
                    'position': self.position + port['direction'] * 30,
                    'direction': port['direction'],
                    'amplitude': abs(amplitude),
                    'phase': output_phase,
                    'accumulated_phase': output_phase,
                    'path_length': 0,
                    'total_path_length': avg_path_length,
                    'source_type': self.incoming_beams[0].get('source_type', 'laser') if self.incoming_beams else 'laser',
                    'origin_phase': output_phase,
                    'origin_component': self
                }
                output_beams.append(beam)
                
                if self.debug:
                    print(f"    Output port {port['name']}: |E|={abs(amplitude):.3f}, φ={output_phase*180/math.pi:.1f}°")
        
        return output_beams
    
    def get_info(self):
        """Get component information."""
        return {
            'type': self.component_type,
            't': self.t,
            'r': self.r,
            'r_prime': self.r_prime,
            'orientation': self.orientation,
            'matrix': self.S,
            'last_input': self._last_v_in,
            'last_output': self._last_v_out
        }
