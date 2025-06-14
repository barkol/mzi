"""Wave optics based physics engine for interferometer simulation.

This replaces the beam tracing approach with a matrix-based solution that
finds steady-state amplitudes for all beams in the system.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import math
import cmath
from utils.vector import Vector2
from config.settings import WAVELENGTH, GRID_SIZE, CANVAS_OFFSET_X, CANVAS_OFFSET_Y, CANVAS_WIDTH, CANVAS_HEIGHT

class OpticalPort:
    """Represents a port on an optical component."""
    def __init__(self, component, port_index: int, position: Vector2, direction: Vector2):
        self.component = component
        self.port_index = port_index
        self.position = position
        self.direction = direction  # Direction beam travels when exiting this port
        self.connected_to = None  # Another OpticalPort
        self.connection = None  # The OpticalConnection

class OpticalConnection:
    """Represents a connection between two ports."""
    def __init__(self, port1: OpticalPort, port2: OpticalPort, path: List[Vector2], length: float):
        self.port1 = port1
        self.port2 = port2
        self.path = path  # Full beam path
        self.length = length
        self.k = 2 * math.pi / WAVELENGTH
        self.phase_shift = self.k * length

class WaveOpticsEngine:
    """Matrix-based wave optics solver for interferometer systems."""
    
    def __init__(self):
        self.k = 2 * math.pi / WAVELENGTH
        self.max_distance = 2000
        self.blocked_positions = []
        self.gold_positions = []
        self.gold_field_hits = {}
        self.collected_gold_fields = set()
        self.gold_field_hits_this_frame = {}
        self.debug = False
        
        # System state
        self.ports = []
        self.connections = []
        self.beam_amplitudes = {}
        self.traced_paths = []
        self._last_traced_beams = []  # For compatibility
        self._network_valid = False
        self._last_component_set = set()
        
    def set_blocked_positions(self, blocked_positions):
        """Set positions that block beam propagation."""
        self.blocked_positions = blocked_positions
    
    def set_gold_positions(self, gold_positions):
        """Set positions that award points when beams pass through."""
        self.gold_positions = gold_positions
    
    def reset(self):
        """Reset the engine for a new calculation."""
        # Clear all connections and ports
        for port in self.ports:
            port.connected_to = None
            port.connection = None
        
        self.ports.clear()
        self.connections.clear()
        self.beam_amplitudes.clear()
        self.traced_paths.clear()
        self.gold_field_hits_this_frame.clear()
        self._last_traced_beams = []
    
    def reset_gold_collection(self):
        """Reset gold field collection state."""
        self.gold_field_hits.clear()
        self.collected_gold_fields.clear()
        self.gold_field_hits_this_frame.clear()
    
    def invalidate_network(self):
        """Mark the network as needing rebuild."""
        self._network_valid = False
    
    def solve_interferometer(self, laser, components):
        """
        Solve for steady-state beam amplitudes in the interferometer.
        
        Returns traced beam paths for visualization.
        """
        # Check if component list has changed
        current_component_set = set(id(c) for c in components)
        if current_component_set != self._last_component_set:
            self._network_valid = False
            self._last_component_set = current_component_set
        
        # Always reset for nested interferometers
        self.reset()
        
        # Clear ALL cached port information
        for comp in [laser] + components:
            if hasattr(comp, '_ports'):
                comp._ports = None
        
        if not laser or not laser.enabled:
            self._last_traced_beams = []
            # Reset all detectors when laser is off
            for comp in components:
                if comp.component_type == 'detector':
                    comp.reset_frame()
                    comp.intensity = 0
            return []
        
        if self.debug:
            print(f"\n=== SOLVING INTERFEROMETER ===")
            print(f"Components: {len(components)}")
            print(f"Network valid: {self._network_valid}")
            for comp in components:
                print(f"  - {comp.component_type} at {comp.position}")
            
        # Reset all components before solving
        for comp in components:
            if hasattr(comp, 'reset_frame'):
                comp.reset_frame()
        
        # Sort components by distance from laser for better connection order
        sorted_components = sorted(components, 
                                 key=lambda c: c.position.distance_to(laser.position))
        
        # Build the optical network
        self._build_network(laser, sorted_components)
        
        # Check for unconnected components and try alternative build if needed
        if self._has_unconnected_components(laser, sorted_components):
            if self.debug:
                print("WARNING: Some components unconnected, trying alternative build order")
            
            # Reset and try with different order
            self.reset()
            for comp in [laser] + components:
                if hasattr(comp, '_ports'):
                    comp._ports = None
            
            # Try building with components grouped by type
            mirrors = [c for c in sorted_components if c.component_type == 'mirror']
            beamsplitters = [c for c in sorted_components if c.component_type in ['beamsplitter', 'tunable_beamsplitter']]
            detectors = [c for c in sorted_components if c.component_type == 'detector']
            others = [c for c in sorted_components if c.component_type not in ['mirror', 'beamsplitter', 'tunable_beamsplitter', 'detector']]
            
            reordered = beamsplitters + mirrors + others + detectors
            self._build_network(laser, reordered)
        
        self._network_valid = True
        
        # Set up and solve the linear system
        amplitudes = self._solve_beam_equations(laser)
        
        if self.debug:
            print(f"\nBeam amplitudes solved: {len(amplitudes)} beams")
            for beam_id, amp in amplitudes.items():
                if abs(amp) > 0.01:
                    print(f"  {beam_id}: |A|={abs(amp):.3f}, φ={cmath.phase(amp)*180/math.pi:.1f}°")
        
        # Generate visualization paths
        paths = self._generate_beam_paths(amplitudes)
        
        # Check gold field hits along paths
        self._check_gold_fields(paths)
        
        # Update detector intensities
        self._update_detectors(sorted_components, amplitudes)
        
        # Store for compatibility
        self._last_traced_beams = paths
        
        return paths
    
    def _has_unconnected_components(self, laser, components):
        """Check if any components are not connected to the network."""
        # Do a simple reachability check from laser
        reachable = {laser}
        to_check = [laser]
        
        while to_check:
            current = to_check.pop()
            if hasattr(current, '_ports'):
                for port in current._ports:
                    if port.connected_to:
                        other = port.connected_to.component
                        if other not in reachable:
                            reachable.add(other)
                            to_check.append(other)
        
        # Check if all non-detector components are reachable
        for comp in components:
            if comp.component_type != 'detector' and comp not in reachable:
                if self.debug:
                    print(f"Component {comp.component_type} at {comp.position} is not reachable!")
                return True
        
        return False
    
    def _build_network(self, laser, components):
        """Build the network of ports and connections."""
        # Create ports for all components
        all_components = [laser] + components
        
        for comp in all_components:
            comp._ports = self._create_ports_for_component(comp)
            self.ports.extend(comp._ports)
        
        # Find connections between ports with improved algorithm
        self._find_connections_improved()
        
        if self.debug:
            print(f"\nBuilt network with {len(self.ports)} ports and {len(self.connections)} connections")
            connection_summary = {}
            for conn in self.connections:
                key = f"{conn.port1.component.component_type} -> {conn.port2.component.component_type}"
                connection_summary[key] = connection_summary.get(key, 0) + 1
            for conn_type, count in sorted(connection_summary.items()):
                print(f"  {conn_type}: {count}")
    
    def _create_ports_for_component(self, component):
        """Create optical ports for a component."""
        ports = []
        
        if component.component_type == "laser":
            # Laser has one output port at its edge
            port = OpticalPort(component, 0, 
                             component.position + Vector2(component.radius + 5, 0),
                             Vector2(1, 0))  # Emits to the right
            ports.append(port)
            
        elif component.component_type in ["beamsplitter", "mirror", "tunable_beamsplitter", "partial_mirror"]:
            # These components have 4 ports
            # Ports are at edges but beams will be drawn from center
            offset_dist = 40  # Distance from center to port
            port_configs = [
                (0, Vector2(-offset_dist, 0), Vector2(-1, 0)),   # Port A (left)
                (1, Vector2(0, offset_dist), Vector2(0, 1)),     # Port B (bottom)
                (2, Vector2(offset_dist, 0), Vector2(1, 0)),     # Port C (right)
                (3, Vector2(0, -offset_dist), Vector2(0, -1))    # Port D (top)
            ]
            
            for idx, offset, direction in port_configs:
                port = OpticalPort(component, idx,
                                 component.position + offset,
                                 direction)
                ports.append(port)
                
        elif component.component_type == "detector":
            # Detector has 4 input ports
            offset_dist = component.radius + 5
            port_configs = [
                (0, Vector2(-offset_dist, 0), Vector2(1, 0)),    # From left
                (1, Vector2(0, offset_dist), Vector2(0, -1)),    # From bottom
                (2, Vector2(offset_dist, 0), Vector2(-1, 0)),    # From right
                (3, Vector2(0, -offset_dist), Vector2(0, 1))     # From top
            ]
            
            for idx, offset, in_direction in port_configs:
                port = OpticalPort(component, idx,
                                 component.position + offset,
                                 in_direction)
                ports.append(port)
        
        return ports
    
    def _find_connections_improved(self):
        """Find connections between ports with better handling of complex layouts."""
        # Collect all potential connections
        potential_connections = []
        
        for port1 in self.ports:
            if port1.connected_to:
                continue
                
            # Don't trace from detector ports (they only receive)
            if port1.component.component_type == "detector":
                continue
            
            # Check if this port can output light
            if hasattr(port1.component, 'S'):
                output_port_idx = port1.port_index
                can_output = any(abs(port1.component.S[output_port_idx, j]) > 1e-10 
                               for j in range(port1.component.S.shape[1]))
                if not can_output:
                    continue
            
            # Trace a ray from this port
            hit_port, path, distance, blocked = self._trace_to_first_component(port1)
            
            if hit_port and not blocked:
                # Check if this connection would carry light
                valid_connection = True
                if hasattr(hit_port.component, 'S'):
                    input_port_idx = hit_port.port_index
                    has_scattering = any(abs(hit_port.component.S[i, input_port_idx]) > 1e-10 
                                       for i in range(hit_port.component.S.shape[0]))
                    if not has_scattering and hit_port.component.component_type != "detector":
                        valid_connection = False
                
                if valid_connection:
                    priority = self._calculate_connection_priority(port1, hit_port)
                    potential_connections.append({
                        'port1': port1,
                        'port2': hit_port,
                        'path': path,
                        'distance': distance,
                        'priority': priority
                    })
        
        # Sort by priority and distance
        potential_connections.sort(key=lambda x: (x['priority'], x['distance']))
        
        # Create connections ensuring each port is used only once
        connected_ports = set()
        
        for conn_data in potential_connections:
            port1 = conn_data['port1']
            port2 = conn_data['port2']
            
            if port1 in connected_ports or port2 in connected_ports:
                continue
            
            # Create bidirectional connection
            connection = OpticalConnection(port1, port2, conn_data['path'], conn_data['distance'])
            self.connections.append(connection)
            port1.connected_to = port2
            port1.connection = connection
            port2.connected_to = port1
            port2.connection = connection
            
            connected_ports.add(port1)
            connected_ports.add(port2)
    
    def _calculate_connection_priority(self, port1, port2):
        """Calculate priority for a connection (lower is better)."""
        priority = 0
        
        # Prioritize laser connections
        if port1.component.component_type == "laser":
            priority -= 1000
        
        # Prioritize detector connections
        if port2.component.component_type == "detector":
            priority -= 100
        
        # Deprioritize same-type connections
        if (port1.component.component_type == port2.component.component_type and 
            port1.component.component_type not in ["laser", "detector"]):
            priority += 500
        
        return priority
    
    def _trace_to_first_component(self, from_port: OpticalPort) -> Tuple[Optional[OpticalPort], List[Vector2], float, bool]:
        """Trace from one port to find the FIRST component it hits."""
        # Start from the component center, not the port position
        start_component = from_port.component
        if start_component.component_type == "laser":
            # For laser, start from its edge
            start_pos = from_port.position
        else:
            # For other components, start from center
            start_pos = start_component.position
        
        direction = from_port.direction
        
        # Build the path starting from component center
        path = [start_pos]
        
        # Move out from the component before tracing
        initial_offset = 30 if start_component.component_type != "laser" else 0
        current_pos = start_pos + direction * initial_offset
        if initial_offset > 0:
            path.append(current_pos)
        
        # Step along the ray
        step_size = 2
        distance = initial_offset
        
        # Track the closest hit
        closest_hit = None
        closest_distance = float('inf')
        closest_component = None
        closest_path_point = None
        
        while distance < self.max_distance:
            # Move forward
            next_pos = current_pos + direction * step_size
            distance += step_size
            
            # Check if blocked
            for blocked_pos in self.blocked_positions:
                if blocked_pos.distance_to(next_pos) < GRID_SIZE / 2:
                    path.append(blocked_pos)  # End at blocked position
                    return None, path, distance, True
            
            # Check bounds
            if (next_pos.x < CANVAS_OFFSET_X - GRID_SIZE or
                next_pos.x > CANVAS_OFFSET_X + CANVAS_WIDTH + GRID_SIZE or
                next_pos.y < CANVAS_OFFSET_Y - GRID_SIZE or
                next_pos.y > CANVAS_OFFSET_Y + CANVAS_HEIGHT + GRID_SIZE):
                # Calculate exact edge intersection
                edge_pos = self._calculate_edge_intersection(current_pos, next_pos)
                if edge_pos:
                    path.append(edge_pos)
                else:
                    path.append(next_pos)
                return None, path, distance, False
            
            # Check if we hit another component
            for port in self.ports:
                if port.component == from_port.component:
                    continue
                    
                comp = port.component
                # Use contains_point method if available, otherwise distance check
                hit = False
                if hasattr(comp, 'contains_point'):
                    hit = comp.contains_point(next_pos.x, next_pos.y)
                else:
                    # Larger hit radius for detectors to ensure we catch beams
                    hit_radius = comp.radius if comp.component_type != "detector" else comp.radius + 20
                    hit = comp.position.distance_to(next_pos) < hit_radius
                
                if hit:
                    # Calculate exact distance to this component
                    comp_distance = start_pos.distance_to(comp.position)
                    
                    # If this is the closest hit so far, remember it
                    if comp_distance < closest_distance:
                        closest_distance = comp_distance
                        closest_component = comp
                        closest_hit = port
                        closest_path_point = Vector2(next_pos.x, next_pos.y)
            
            # If we've found a hit and we're past its position, stop tracing
            if closest_component and current_pos.distance_to(start_pos) >= closest_distance:
                # Complete the path to component center
                path.append(closest_component.position)
                
                # Find which port based on incoming direction
                best_port = self._find_best_input_port(closest_component, direction)
                if best_port:
                    if self.debug:
                        print(f"  Connection: {from_port.component.component_type} port {from_port.port_index} -> {closest_component.component_type} port {best_port.port_index}")
                    return best_port, path, closest_distance, False
                else:
                    return None, path, closest_distance, False
            
            # Add intermediate points for smooth rendering
            if int(distance) % 20 == 0:
                path.append(Vector2(next_pos.x, next_pos.y))
            
            current_pos = next_pos
        
        # Reached max distance
        path.append(current_pos)
        return None, path, distance, False
    
    def _calculate_edge_intersection(self, start, end):
        """Calculate intersection with canvas edge."""
        x_min = CANVAS_OFFSET_X
        x_max = CANVAS_OFFSET_X + CANVAS_WIDTH
        y_min = CANVAS_OFFSET_Y
        y_max = CANVAS_OFFSET_Y + CANVAS_HEIGHT
        
        # Simple edge intersection calculation
        direction = end - start
        if abs(direction.x) > 0.001:
            # Check left/right edges
            if direction.x > 0:
                t = (x_max - start.x) / direction.x
            else:
                t = (x_min - start.x) / direction.x
            
            if 0 <= t <= 1:
                y = start.y + t * direction.y
                if y_min <= y <= y_max:
                    return Vector2(start.x + t * direction.x, y)
        
        if abs(direction.y) > 0.001:
            # Check top/bottom edges
            if direction.y > 0:
                t = (y_max - start.y) / direction.y
            else:
                t = (y_min - start.y) / direction.y
            
            if 0 <= t <= 1:
                x = start.x + t * direction.x
                if x_min <= x <= x_max:
                    return Vector2(x, start.y + t * direction.y)
        
        return None
    
    def _find_best_input_port(self, component, incoming_direction):
        """Find the best input port for an incoming beam direction."""
        if not hasattr(component, '_ports'):
            return None
            
        best_port = None
        best_alignment = -2
        
        for port in component._ports:
            # The port's direction is the direction beams EXIT from it
            # For input, we want opposite alignment
            alignment = -(port.direction.x * incoming_direction.x + 
                         port.direction.y * incoming_direction.y)
            
            if alignment > best_alignment:
                best_alignment = alignment
                best_port = port
        
        return best_port if best_alignment > 0.5 else None
    
    def _solve_beam_equations(self, laser):
        """Set up and solve the linear system for beam amplitudes."""
        # Assign unique IDs to all beam segments
        beam_segments = []
        for i, conn in enumerate(self.connections):
            beam_id = f"beam_{i}"
            beam_segments.append(beam_id)
            self.beam_amplitudes[beam_id] = 0j
        
        if not beam_segments:
            return {}
        
        # Build system matrix
        n = len(beam_segments)
        A = np.zeros((n, n), dtype=complex)
        b = np.zeros(n, dtype=complex)
        
        # Add equations for each connection
        for i, conn in enumerate(self.connections):
            beam_id = beam_segments[i]
            
            # Phase accumulation along this connection
            phase = cmath.exp(1j * conn.phase_shift)
            
            # Source term (only for laser output)
            if conn.port1.component.component_type == "laser":
                b[i] = 1.0  # Unit amplitude from laser
            
            # Add scattering contributions
            self._add_scattering_terms(A, i, conn, beam_segments, phase)
        
        # Solve the system
        try:
            if n > 0:
                # For steady state, we solve (I - A)x = b
                # Add small diagonal term for numerical stability
                I_minus_A = np.eye(n) - A + np.eye(n) * 1e-10
                
                # Solve the system
                x = np.linalg.solve(I_minus_A, b)
                
                # Store solutions
                for i, beam_id in enumerate(beam_segments):
                    self.beam_amplitudes[beam_id] = x[i]
                    
                if self.debug:
                    print(f"\nSolved for {n} beam amplitudes")
                    total_power = sum(abs(amp)**2 for amp in x)
                    print(f"Total power in system: {total_power:.3f}")
                    
        except np.linalg.LinAlgError:
            print("Warning: Could not solve beam equations - system may be singular")
            
        return self.beam_amplitudes
    
    def _add_scattering_terms(self, A, row_idx, connection, beam_segments, phase):
        """Add scattering matrix contributions to the system matrix."""
        port2_component = connection.port2.component
        
        if port2_component.component_type == "detector":
            # Detectors absorb all light - no scattering
            return
            
        # Get scattering matrix for the component
        if hasattr(port2_component, 'S'):
            S = port2_component.S
            input_port_idx = connection.port2.port_index
            
            # Find all outgoing connections from this component
            for other_conn_idx, other_conn in enumerate(self.connections):
                if other_conn.port1.component == port2_component:
                    output_port_idx = other_conn.port1.port_index
                    
                    # Scattering coefficient
                    s_coeff = S[output_port_idx, input_port_idx]
                    
                    if abs(s_coeff) > 1e-10:
                        # This input beam contributes to the output beam
                        # The phase factor accounts for propagation to the component
                        A[other_conn_idx, row_idx] += s_coeff * phase
    
    def _generate_beam_paths(self, amplitudes):
        """Generate beam paths for visualization."""
        paths = []
        
        for conn_idx, conn in enumerate(self.connections):
            beam_id = f"beam_{conn_idx}"
            amplitude = amplitudes.get(beam_id, 0j)
            
            if abs(amplitude) < 0.01:
                continue
            
            # Use the full path stored in the connection
            paths.append({
                'path': conn.path,
                'amplitude': abs(amplitude),
                'phase': cmath.phase(amplitude),
                'source_type': 'laser' if conn.port1.component.component_type == 'laser' else 'mixed',
                'blocked': False
            })
        
        return paths
    
    def _check_gold_fields(self, paths):
        """Check for gold field hits along beam paths."""
        self.gold_field_hits_this_frame.clear()
        
        for path_data in paths:
            path = path_data['path']
            amplitude = path_data['amplitude']
            intensity = amplitude ** 2
            
            # Check all segments of the path
            for i in range(len(path) - 1):
                start = path[i]
                end = path[i + 1]
                
                # Sample points along this segment
                segment_length = start.distance_to(end)
                num_samples = max(2, int(segment_length / 5))
                
                for j in range(num_samples):
                    t = j / max(1, num_samples - 1)
                    point = Vector2(
                        start.x + t * (end.x - start.x),
                        start.y + t * (end.y - start.y)
                    )
                    
                    # Check each gold position
                    for gold_pos in self.gold_positions:
                        if gold_pos.distance_to(point) < GRID_SIZE / 2:
                            grid_x = round((gold_pos.x - CANVAS_OFFSET_X) / GRID_SIZE)
                            grid_y = round((gold_pos.y - CANVAS_OFFSET_Y) / GRID_SIZE)
                            gold_key = (grid_x, grid_y)
                            
                            # Track for this frame (for sound effects)
                            if gold_key not in self.gold_field_hits_this_frame:
                                self.gold_field_hits_this_frame[gold_key] = 0
                            self.gold_field_hits_this_frame[gold_key] += intensity
                            
                            # Only count for scoring if not already collected
                            if gold_key not in self.collected_gold_fields:
                                self.collected_gold_fields.add(gold_key)
                                if gold_key not in self.gold_field_hits:
                                    self.gold_field_hits[gold_key] = 0
                                self.gold_field_hits[gold_key] += intensity
                                
                                if self.debug:
                                    print(f"  Beam hit gold field at grid ({grid_x}, {grid_y}) with intensity {intensity:.3f}")
    
    def _update_detectors(self, components, amplitudes):
        """Update detector intensities based on beam amplitudes."""
        if self.debug:
            print(f"\n_update_detectors called with {len(components)} components")
            detector_count = sum(1 for c in components if c.component_type == "detector")
            print(f"Found {detector_count} detectors")
        
        # First, reset ALL detectors
        for comp in components:
            if comp.component_type == "detector":
                comp.reset_frame()
                if self.debug:
                    print(f"Reset detector at {comp.position}")
        
        # Collect all beams going to each detector
        detector_beams = {}  # detector -> list of beams
        connections_to_detectors = 0
        
        # Check all connections
        for conn_idx, conn in enumerate(self.connections):
            if conn.port2.component.component_type == "detector":
                connections_to_detectors += 1
                beam_id = f"beam_{conn_idx}"
                amplitude = amplitudes.get(beam_id, 0j)
                
                if self.debug:
                    print(f"Connection {conn_idx} to detector: amplitude = {abs(amplitude):.3f}")
                
                if abs(amplitude) > 0.001:
                    detector = conn.port2.component
                    
                    if detector not in detector_beams:
                        detector_beams[detector] = []
                    
                    # Create beam data for the detector
                    beam_data = {
                        'amplitude': abs(amplitude),
                        'phase': cmath.phase(amplitude),
                        'accumulated_phase': cmath.phase(amplitude),
                        'total_path_length': conn.length,
                        'path_length': conn.length,
                        'beam_id': beam_id,
                        'generation': 0,
                        'source_type': 'laser'
                    }
                    
                    detector_beams[detector].append(beam_data)
        
        if self.debug:
            print(f"Found {connections_to_detectors} connections to detectors")
            print(f"Detectors receiving beams: {len(detector_beams)}")
        
        # Update each detector with its beams
        for detector, beams in detector_beams.items():
            if self.debug:
                print(f"\nUpdating detector at {detector.position} with {len(beams)} beams")
            
            # Add all beams
            for beam in beams:
                detector.add_beam(beam)
                
                if self.debug:
                    print(f"  Added beam: amp={beam['amplitude']:.3f}, phase={beam['phase']*180/math.pi:.1f}°")
            
            # Finalize to calculate interference
            detector.finalize_frame()
            
            if self.debug:
                print(f"  Final intensity: {detector.intensity:.3f}")
                print(f"  Incoming beams: {len(detector.incoming_beams)}")
        
        # Also finalize detectors that didn't receive any beams
        for comp in components:
            if comp.component_type == "detector" and comp not in detector_beams:
                comp.finalize_frame()
                if self.debug:
                    print(f"Finalized detector at {comp.position} with no beams: intensity={comp.intensity}")
    
    def trace_beams(self, components):
        """Compatibility method - finds laser and redirects to solve_interferometer."""
        # Find laser - it might be in the components list or passed separately
        laser = None
        actual_components = []
        
        for comp in components:
            if hasattr(comp, 'component_type') and comp.component_type == 'laser':
                laser = comp
            else:
                actual_components.append(comp)
        
        # If no laser found in components, return empty
        if not laser:
            if self.debug:
                print("WARNING: No laser found in trace_beams")
            return []
        
        return self.solve_interferometer(laser, actual_components)
    
    def add_beam(self, beam):
        """Compatibility method - not used in wave optics approach."""
        # The wave optics engine doesn't add individual beams
        # It solves for all beams simultaneously
        pass
    
    def remove_component(self, component):
        """Remove a component from the network."""
        # Mark network as invalid
        self._network_valid = False
        
        # Remove ports associated with this component
        if hasattr(component, '_ports'):
            for port in component._ports:
                # Remove connections involving this port
                self.connections = [conn for conn in self.connections 
                                  if conn.port1 != port and conn.port2 != port]
                # Clear port references
                if port.connected_to:
                    port.connected_to.connected_to = None
                    port.connected_to = None
            
            # Remove ports from main list
            self.ports = [p for p in self.ports if p.component != component]
            
            # Clear component's port list
            component._ports = None
    
    def force_rebuild(self):
        """Force a complete network rebuild on next solve."""
        self.reset()
        self._network_valid = False
        # Clear all component port caches
        for port in self.ports:
            if hasattr(port.component, '_ports'):
                port.component._ports = None
    
    def diagnose_network(self, laser, components):
        """Diagnose network connectivity issues."""
        print("\n=== NETWORK DIAGNOSTIC ===")
        
        # Build network if needed
        if not self._network_valid:
            self.reset()
            self._build_network(laser, components)
        
        # 1. Check component reachability
        print("\n1. Component Reachability:")
        reachable = self._find_reachable_components(laser)
        
        for comp in [laser] + components:
            status = "✓ Reachable" if comp in reachable else "✗ UNREACHABLE"
            print(f"   {comp.component_type} at {comp.position}: {status}")
        
        # 2. Check port connections
        print("\n2. Port Connections:")
        for comp in [laser] + components:
            if hasattr(comp, '_ports'):
                print(f"\n   {comp.component_type} at {comp.position}:")
                for i, port in enumerate(comp._ports):
                    if port.connected_to:
                        other = port.connected_to.component
                        print(f"     Port {i} -> {other.component_type} port {port.connected_to.port_index}")
                    else:
                        print(f"     Port {i} -> [Not connected]")
        
        # 3. Find isolated components
        print("\n3. Isolated Components:")
        isolated = []
        for comp in components:
            if comp not in reachable and comp.component_type != "detector":
                isolated.append(comp)
        
        if isolated:
            print("   Found isolated components:")
            for comp in isolated:
                print(f"     - {comp.component_type} at {comp.position}")
        else:
            print("   No isolated components found")
        
        return reachable, isolated
    
    def _find_reachable_components(self, laser):
        """Find all components reachable from the laser."""
        reachable = {laser}
        to_visit = [laser]
        
        while to_visit:
            current = to_visit.pop(0)
            
            # Find all components connected to current
            if hasattr(current, '_ports'):
                for port in current._ports:
                    if port.connected_to:
                        other_comp = port.connected_to.component
                        if other_comp not in reachable:
                            reachable.add(other_comp)
                            if other_comp.component_type != "detector":
                                to_visit.append(other_comp)
        
        return reachable