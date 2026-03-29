"""Fixed tunable beam splitter with proper beam accumulation and energy conservation."""
import pygame
import numpy as np
import math
import cmath
import logging
from components.base import Component
from utils.vector import Vector2
from config.settings import CYAN, IDEAL_COMPONENTS

logger = logging.getLogger(__name__)

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
    - r' = -r* (phase relation, ensures unitarity)
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
            # Calculate r' so that the scattering matrix is unitary.
            # The correct physical relation is r' = -r* (negative complex
            # conjugate), which guarantees |r'| = |r| and S†S = I.
            # The older r' = -1/r gives |r'| = 1/|r|, breaking unitarity.
            self.r_prime = complex(r_prime) if r_prime is not None else -np.conj(self.r)
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
        
        # Beam tracking with generation awareness
        self.all_beams_by_port = {0: [], 1: [], 2: [], 3: []}  # A, B, C, D
        self.processed_this_frame = False
        self.current_generation = -1  # Track which generation we're processing
        self.output_beams = []
        
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
            logger.warning("Energy not conserved: |r|^2+|t|^2 = %f", energy)
        
        # Check phase relation r' = -r* (ensures unitarity)
        if abs(self.r_prime + np.conj(self.r)) > 1e-6:
            logger.warning("Phase relation violated: r'=%s, expected -conj(r)=%s",
                           self.r_prime, -np.conj(self.r))
    
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
                logger.debug("WARNING: Scattering matrix not unitary! Max error: %s\nS^dagger S =\n%s",
                             identity_error, should_be_identity)
        
        # Also verify symmetry for reciprocity
        symmetry_error = np.max(np.abs(self.S - self.S.T))
        if symmetry_error > 1e-10 and abs(self.r - self.r_prime) > 1e-10:
            if self.debug:
                logger.debug("WARNING: Scattering matrix not symmetric! Max error: %s. "
                             "This is expected when r != r'", symmetry_error)
    
    def reset_frame(self):
        """Reset for new frame processing - clears all accumulated beams."""
        self.all_beams_by_port = {0: [], 1: [], 2: [], 3: []}
        self.processed_this_frame = False
        self.current_generation = -1
        self.output_beams = []
        self._last_v_in = None
        self._last_v_out = None
    
    def add_beam(self, beam):
        """Add a beam to be processed - accumulates beams from the same generation."""
        # Only accept beams if this component hasn't been finalized yet
        if self.processed_this_frame:
            if self.debug:
                logger.debug("  %s at %s: rejecting beam (already processed)", self.component_type, self.position)
            return
        
        # Get beam generation
        beam_generation = beam.get('generation', 0)
        
        # If this is the first beam, set the generation
        if self.current_generation == -1:
            self.current_generation = beam_generation
        elif beam_generation != self.current_generation:
            # This beam is from a different generation - should not happen with proper tracing
            if self.debug:
                logger.debug("  WARNING: %s received beam from generation %d while processing generation %d",
                             self.component_type, beam_generation, self.current_generation)
            return
        
        # Map beam to input port based on direction
        direction = beam['direction']
        port_idx = None
        
        if direction.x > 0.5 and abs(direction.y) < 0.5:  # RIGHT → Port A
            port_idx = 0
        elif direction.y < -0.5 and abs(direction.x) < 0.5:  # UP → Port B
            port_idx = 1
        elif direction.x < -0.5 and abs(direction.y) < 0.5:  # LEFT → Port C
            port_idx = 2
        elif direction.y > 0.5 and abs(direction.x) < 0.5:  # DOWN → Port D
            port_idx = 3
        
        if port_idx is not None:
            self.all_beams_by_port[port_idx].append(beam)
            
            if self.debug:
                phase_deg = beam.get('accumulated_phase', beam['phase']) * 180 / math.pi
                port_name = ['A', 'B', 'C', 'D'][port_idx]
                logger.debug("  %s at %s: beam added to port %s, amp=%.3f, phase=%.1f deg, gen=%d",
                             self.component_type, self.position, port_name,
                             beam['amplitude'], phase_deg, beam_generation)
        else:
            if self.debug:
                logger.debug("  WARNING: Beam direction %s doesn't map to any port", direction)
    
    def process_beam(self, beam):
        """Process single beam (for compatibility)."""
        # Don't reset - just add to accumulation
        self.add_beam(beam)
        # Don't finalize here - wait for explicit finalize_frame call
        return []
    
    def finalize_frame(self):
        """Process all accumulated beams using scattering matrix."""
        if self.processed_this_frame:
            return self.output_beams
        
        self.processed_this_frame = True
        
        # Build input amplitude vector by summing beams at each port
        v_in = np.zeros(4, dtype=complex)
        
        total_beam_count = sum(len(beams) for beams in self.all_beams_by_port.values())
        
        if self.debug and total_beam_count > 0:
            logger.debug("%s at %s - processing generation %d. Total beams: %d. "
                         "Beams by port: A=%d, B=%d, C=%d, D=%d",
                         self.component_type, self.position, self.current_generation,
                         total_beam_count,
                         len(self.all_beams_by_port[0]), len(self.all_beams_by_port[1]),
                         len(self.all_beams_by_port[2]), len(self.all_beams_by_port[3]))
        
        # If no beams, return empty list
        if total_beam_count == 0:
            return []
        
        # Sum complex amplitudes at each port
        port_names = ['A', 'B', 'C', 'D']
        path_lengths_by_port = [[], [], [], []]
        
        for port_idx in range(4):
            port_sum = 0j
            for beam in self.all_beams_by_port[port_idx]:
                total_phase = beam.get('accumulated_phase', beam['phase'])
                amplitude = beam['amplitude'] * cmath.exp(1j * total_phase)
                port_sum += amplitude
                path_lengths_by_port[port_idx].append(beam.get('total_path_length', 0))
                
                if self.debug and abs(amplitude) > 0.001:
                    logger.debug("    Port %s: adding beam with |E|=%.3f, phi=%.1f deg, complex amp=%s",
                                 port_names[port_idx], beam['amplitude'],
                                 total_phase * 180 / math.pi, amplitude)
            
            v_in[port_idx] = port_sum
            
            if self.debug and abs(port_sum) > 0.001:
                logger.debug("    Port %s total input: %s (|E|^2=%.3f)",
                             port_names[port_idx], port_sum, abs(port_sum) ** 2)
        
        self._last_v_in = v_in.copy()
        
        # Apply scattering matrix
        v_out = self.S @ v_in
        
        # Apply losses if configured
        if not IDEAL_COMPONENTS and self.loss > 0:
            loss_factor = math.sqrt(1.0 - self.loss)
            v_out *= loss_factor
        
        self._last_v_out = v_out.copy()
        
        if self.debug and np.any(np.abs(v_in) > 0.001):
            logger.debug("  Input/Output vectors: v_in = [%s, %s, %s, %s], v_out = [%s, %s, %s, %s]",
                         v_in[0], v_in[1], v_in[2], v_in[3],
                         v_out[0], v_out[1], v_out[2], v_out[3])

            # Energy conservation check
            input_power = np.sum(np.abs(v_in)**2)
            output_power = np.sum(np.abs(v_out)**2)
            if input_power > 0:
                ratio = output_power/input_power
                expected_ratio = 1.0 if (IDEAL_COMPONENTS or self.loss == 0) else (1.0 - self.loss)
                logger.debug("  Energy conservation: Input power=%.6f, Output power=%.6f, "
                             "Power ratio=%.6f (expected: %.6f)",
                             input_power, output_power, ratio, expected_ratio)
                if abs(ratio - expected_ratio) > 0.001:
                    logger.debug("    WARNING: Energy not conserved! Deviation: %.2f%%",
                                 (ratio - expected_ratio) * 100)
        
        # Generate output beams
        self.output_beams = []
        
        # Calculate average path lengths for each port
        avg_path_lengths = []
        for port_lengths in path_lengths_by_port:
            if port_lengths:
                avg_path_lengths.append(sum(port_lengths) / len(port_lengths))
            else:
                avg_path_lengths.append(0)
        
        # Port directions
        port_info = [
            {'name': 'A', 'direction': Vector2(-1, 0), 'input_paths': avg_path_lengths[0]},
            {'name': 'B', 'direction': Vector2(0, 1), 'input_paths': avg_path_lengths[1]},
            {'name': 'C', 'direction': Vector2(1, 0), 'input_paths': avg_path_lengths[2]},
            {'name': 'D', 'direction': Vector2(0, -1), 'input_paths': avg_path_lengths[3]}
        ]
        
        output_counter = 0
        for i, (amplitude, port) in enumerate(zip(v_out, port_info)):
            if abs(amplitude) > 0.001:  # Only output significant beams
                output_phase = cmath.phase(amplitude)
                
                # Calculate average input path length
                # Weight by the amplitude of beams from each input port
                weighted_path_sum = 0
                weight_sum = 0
                for j in range(4):
                    if abs(v_in[j]) > 0.001 and avg_path_lengths[j] > 0:
                        weight = abs(self.S[i, j] * v_in[j])
                        weighted_path_sum += weight * avg_path_lengths[j]
                        weight_sum += weight
                
                avg_path_length = weighted_path_sum / weight_sum if weight_sum > 0 else 0
                
                # Unique ID for tracking
                beam_id = f"{self.component_type}_{id(self)}_out_{output_counter}"
                
                beam = {
                    'position': self.position + port['direction'] * 30,
                    'direction': port['direction'],
                    'amplitude': abs(amplitude),
                    'phase': output_phase,
                    'accumulated_phase': output_phase,
                    'path_length': 0,
                    'total_path_length': avg_path_length,
                    'source_type': 'mixed' if total_beam_count > 1 else (
                        self.all_beams_by_port[0][0].get('source_type', 'laser')
                        if self.all_beams_by_port[0] else 'laser'
                    ),
                    'origin_phase': output_phase,
                    'origin_component': self,
                    'generation': self.current_generation,  # Keep track of generation
                    'beam_id': beam_id  # Unique identifier
                }
                self.output_beams.append(beam)
                output_counter += 1
                
                if self.debug:
                    logger.debug("    Output port %s: |E|=%.3f, phi=%.1f deg",
                                 port['name'], abs(amplitude), output_phase * 180 / math.pi)
        
        return self.output_beams
    
    # ------------------------------------------------------------------
    # Fock state interface
    # ------------------------------------------------------------------

    def get_fock_mode_mapping(self):
        """Return port-index mapping between 4-port S-matrix and 2-mode Fock basis.

        The beam-splitter unitary in the Fock module uses the convention::

            ĉ† = t â† + r' b̂†      (output mode c)
            d̂† = r â† + t  b̂†      (output mode d)

        This method returns two sub-block mappings — one for each pair of
        input ports that scatter into the complementary pair of output ports.

        Returns
        -------
        list of dict
            Each dict has keys ``a``, ``b`` (input port indices) and
            ``c``, ``d`` (output port indices) for one sub-block.
        """
        if self.orientation == '\\':
            # S-matrix connects {A(0),D(3)} → {B(1),C(2)}
            #   v_B = r·v_A + t·v_D   →  d = r·a + t·b
            #   v_C = t·v_A + r'·v_D   →  c = t·a + r'·b
            # So Fock a↔A(0), b↔D(3), c↔C(2), d↔B(1)
            return [
                {'a': 0, 'b': 3, 'c': 2, 'd': 1},  # (A,D) → (C,B)
                {'a': 1, 'b': 2, 'c': 3, 'd': 0},  # (B,C) → (D,A)
            ]
        else:  # '/'
            # S-matrix connects {A(0),C(2)} → {B(1),D(3)}
            #   v_B = r·v_A + t·v_C   →  d = r·a + t·b
            #   v_D = t·v_A + r'·v_C   →  c = t·a + r'·b
            return [
                {'a': 0, 'b': 2, 'c': 3, 'd': 1},  # (A,C) → (D,B)
                {'a': 1, 'b': 3, 'c': 2, 'd': 0},  # (B,D) → (C,A)
            ]

    def fock_transform(self, n, m):
        """Sample one Fock-state outcome |n,m⟩ → |p,q⟩ through this BS.

        Parameters
        ----------
        n, m : int
            Input photon numbers (mode a and mode b respectively).

        Returns
        -------
        tuple[int, int]
            Sampled output photon numbers (p in mode c, q in mode d).
        """
        from core.fock import sample_fock_bs
        r_prime = -np.conj(self.r)
        return sample_fock_bs(n, m, self.t, self.r, r_prime)

    def fock_probabilities(self, n, m):
        """Full Fock-state output distribution for |n,m⟩ input.

        Returns
        -------
        dict[(int,int), float]
            Mapping (p, q) → probability.
        """
        from core.fock import fock_bs_probabilities
        r_prime = -np.conj(self.r)
        return fock_bs_probabilities(n, m, self.t, self.r, r_prime)

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
            'last_output': self._last_v_out,
            'total_beams': sum(len(beams) for beams in self.all_beams_by_port.values()),
            'generation': self.current_generation
        }