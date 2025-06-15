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
        self._blocked_beam_paths = []  # Track beams that hit edges/blocks
        
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
        self._blocked_beam_paths = []
    
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
        unconnected = self._has_unconnected_components(laser, sorted_components)
        if unconnected:
            if self.debug:
                print("\nWARNING: Some components unconnected, trying direct grid-based connections")
            
            # Try a more aggressive connection strategy for unconnected components
            self._connect_unconnected_components(laser, sorted_components)
        
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
        # Clear any existing network data
        self.ports.clear()
        self.connections.clear()
        
        # Create ports for all components
        all_components = [laser] + components
        
        for comp in all_components:
            comp._ports = self._create_ports_for_component(comp)
            self.ports.extend(comp._ports)
        
        # Find connections between ports
        self._find_connections_improved()
        
        if self.debug:
            print(f"\nBuilt network with {len(self.ports)} ports and {len(self.connections)} connections")
            connection_summary = {}
            for conn in self.connections:
                key = f"{conn.port1.component.component_type} -> {conn.port2.component.component_type}"
                connection_summary[key] = connection_summary.get(key, 0) + 1
            for conn_type, count in sorted(connection_summary.items()):
                print(f"  {conn_type}: {count}")
            
            # Check for mirror chains
            mirror_chain_broken = False
            for comp in components:
                if comp.component_type == "mirror":
                    # Check if this mirror has incoming connections
                    has_input = any(conn.port2.component == comp for conn in self.connections)
                    if not has_input:
                        # Check if it should be reachable
                        # This is a simple check - in reality we'd need path analysis
                        print(f"  WARNING: Mirror at {comp.position} has no input connection!")
                        mirror_chain_broken = True
            
            if mirror_chain_broken:
                print("  Mirror chain appears to be broken - check alternating mirror setup")
    
    def _create_ports_for_component(self, component):
        """Create optical ports for a component - GRID ALIGNED."""
        ports = []
        
        if component.component_type == "laser":
            # Laser has one output port at its right edge
            port = OpticalPort(component, 0, 
                             component.position + Vector2(component.radius + GRID_SIZE//4, 0),
                             Vector2(1, 0))  # Emits to the right
            ports.append(port)
            
        elif component.component_type in ["beamsplitter", "mirror", "tunable_beamsplitter", "partial_mirror"]:
            # These components have 4 ports aligned with grid
            # Use GRID_SIZE for consistent port placement
            offset_dist = GRID_SIZE
            port_configs = [
                (0, Vector2(-offset_dist, 0), Vector2(-1, 0)),   # Port A (left) - beams exit left
                (1, Vector2(0, offset_dist), Vector2(0, 1)),     # Port B (bottom) - beams exit down
                (2, Vector2(offset_dist, 0), Vector2(1, 0)),     # Port C (right) - beams exit right
                (3, Vector2(0, -offset_dist), Vector2(0, -1))    # Port D (top) - beams exit up
            ]
            
            for idx, offset, direction in port_configs:
                port = OpticalPort(component, idx,
                                 component.position + offset,
                                 direction)
                ports.append(port)
                
        elif component.component_type == "detector":
            # Detector has 4 input ports aligned with grid
            offset_dist = component.radius + GRID_SIZE//4
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
        """Find connections between ports with better handling of complex layouts - GRID BASED."""
        # First, clear any existing connections
        for port in self.ports:
            port.connected_to = None
            port.connection = None
        self.connections.clear()
        
        # Collect all potential connections
        potential_connections = []
        
        for port1 in self.ports:
            if port1.connected_to:
                continue
                
            # Don't trace from detector ports (they only receive)
            if port1.component.component_type == "detector":
                continue
            
            # For non-laser components, check if this port can output based on the S matrix
            if port1.component.component_type != "laser" and hasattr(port1.component, 'S'):
                output_port_idx = port1.port_index
                can_output = any(abs(port1.component.S[output_port_idx, j]) > 1e-10 
                               for j in range(port1.component.S.shape[1]))
                if not can_output:
                    continue
            
            # Trace a ray from this port
            hit_port, path, distance, blocked = self._trace_to_first_component(port1)
            
            if hit_port and not blocked and hit_port.component != port1.component:
                # Valid connection found
                priority = self._calculate_connection_priority(port1, hit_port)
                potential_connections.append({
                    'port1': port1,
                    'port2': hit_port,
                    'path': path,
                    'distance': distance,
                    'priority': priority
                })
                
                if self.debug:
                    print(f"  Potential: {port1.component.component_type}:{port1.port_index} -> {hit_port.component.component_type}:{hit_port.port_index} (dist={distance:.0f})")
        
        # Sort by priority and distance
        potential_connections.sort(key=lambda x: (x['priority'], x['distance']))
        
        # Create connections ensuring each port is used only once
        connected_ports = set()
        
        for conn_data in potential_connections:
            port1 = conn_data['port1']
            port2 = conn_data['port2']
            
            # Skip if either port is already connected
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
            
            if self.debug:
                print(f"  Created: {port1.component.component_type}:{port1.port_index} <-> {port2.component.component_type}:{port2.port_index}")
        
        # Second pass: try to connect any unconnected laser outputs
        for port in self.ports:
            if (port.component.component_type == "laser" and 
                port not in connected_ports):
                # Try to find ANY reachable component
                if self.debug:
                    print(f"  Laser port {port.port_index} unconnected, searching for target...")
                
                hit_port, path, distance, blocked = self._trace_to_first_component(port)
                if hit_port and not blocked and hit_port not in connected_ports:
                    connection = OpticalConnection(port, hit_port, path, distance)
                    self.connections.append(connection)
                    port.connected_to = hit_port
                    port.connection = connection
                    hit_port.connected_to = port
                    hit_port.connection = connection
                    
                    connected_ports.add(port)
                    connected_ports.add(hit_port)
                    
                    if self.debug:
                        print(f"  Laser connected to {hit_port.component.component_type}")
        
        if self.debug:
            print(f"\nTotal connections created: {len(self.connections)}")
            # Show unconnected components
            unconnected_components = set()
            for port in self.ports:
                if port not in connected_ports and port.component.component_type != "detector":
                    unconnected_components.add(port.component)
            
            if unconnected_components:
                print("  Unconnected components:")
                for comp in unconnected_components:
                    print(f"    - {comp.component_type} at {comp.position}")
    
    def _calculate_connection_priority(self, port1, port2):
        """Calculate priority for a connection (lower is better) - GRID AWARE."""
        priority = 0
        
        # Prioritize laser connections
        if port1.component.component_type == "laser":
            priority -= 10000
        
        # Prioritize connections to detectors
        if port2.component.component_type == "detector":
            priority -= 1000
        
        # Prioritize direct grid-aligned connections
        dx = abs(port1.component.position.x - port2.component.position.x)
        dy = abs(port1.component.position.y - port2.component.position.y)
        
        # Check if components are grid-aligned (same row or column)
        if dx < GRID_SIZE / 2:  # Same column
            priority -= 100
        elif dy < GRID_SIZE / 2:  # Same row
            priority -= 100
        
        # Deprioritize same-type connections (except laser->laser or detector->detector)
        if (port1.component.component_type == port2.component.component_type and 
            port1.component.component_type not in ["laser", "detector"]):
            priority += 500
        
        # Prioritize shorter connections
        distance = port1.component.position.distance_to(port2.component.position)
        priority += int(distance / GRID_SIZE)  # Add penalty based on grid distance
        
        # Special handling for mirrors - they should connect in chains
        if (port1.component.component_type == "mirror" and 
            port2.component.component_type == "mirror"):
            # Mirrors in a line should have lower priority
            if dx < GRID_SIZE / 2 or dy < GRID_SIZE / 2:
                priority -= 200
        
        return priority
    
    def _trace_to_first_component(self, from_port: OpticalPort) -> Tuple[Optional[OpticalPort], List[Vector2], float, bool]:
        """Trace from one port to find the FIRST component it hits - GRID ALIGNED."""
        # Start from the component center
        start_component = from_port.component
        if start_component.component_type == "laser":
            # For laser, start from its edge
            start_pos = from_port.position
        else:
            # For other components, start from center
            start_pos = start_component.position
        
        direction = from_port.direction
        
        # Ensure we're using exact grid directions
        if abs(direction.x) > abs(direction.y):
            # Horizontal movement
            direction = Vector2(1 if direction.x > 0 else -1, 0)
        else:
            # Vertical movement
            direction = Vector2(0, 1 if direction.y > 0 else -1)
        
        # Build the path starting from component center
        path = [start_pos]
        
        # Move out from the component before tracing - use grid-aligned offset
        initial_offset = GRID_SIZE if start_component.component_type != "laser" else 0
        current_pos = start_pos + direction * initial_offset
        if initial_offset > 0:
            path.append(current_pos)
        
        # Step along the ray - use grid-aligned steps
        step_size = GRID_SIZE // 2  # Half grid size for better precision
        distance = initial_offset
        
        # Track all hits along the path
        component_hits = []
        
        while distance < self.max_distance:
            # Move forward by step size
            next_pos = current_pos + direction * step_size
            distance += step_size
            
            # Check if blocked
            for blocked_pos in self.blocked_positions:
                # Check if we're in the same grid cell as the blocked position
                if (abs(next_pos.x - blocked_pos.x) < GRID_SIZE / 2 and
                    abs(next_pos.y - blocked_pos.y) < GRID_SIZE / 2):
                    path.append(blocked_pos)
                    return None, path, distance, True
            
            # Check bounds
            if (next_pos.x < CANVAS_OFFSET_X - GRID_SIZE or
                next_pos.x > CANVAS_OFFSET_X + CANVAS_WIDTH + GRID_SIZE or
                next_pos.y < CANVAS_OFFSET_Y - GRID_SIZE or
                next_pos.y > CANVAS_OFFSET_Y + CANVAS_HEIGHT + GRID_SIZE):
                edge_pos = self._calculate_edge_intersection(current_pos, next_pos)
                if edge_pos:
                    path.append(edge_pos)
                else:
                    path.append(next_pos)
                return None, path, distance, False
            
            # Check if we hit another component
            for comp in [p.component for p in self.ports if p.component != from_port.component]:
                # Check if beam passes through component's grid cell
                grid_x_match = abs(next_pos.x - comp.position.x) < GRID_SIZE / 2
                grid_y_match = abs(next_pos.y - comp.position.y) < GRID_SIZE / 2
                
                if grid_x_match and grid_y_match:
                    # We're in the component's grid cell
                    comp_distance = start_pos.distance_to(comp.position)
                    already_recorded = any(h['component'] == comp for h in component_hits)
                    
                    if not already_recorded:
                        component_hits.append({
                            'component': comp,
                            'distance': comp_distance,
                            'position': comp.position
                        })
            
            # Add intermediate points at grid boundaries
            if int(distance) % GRID_SIZE == 0:
                path.append(Vector2(next_pos.x, next_pos.y))
            
            current_pos = next_pos
        
        # Process hits - find the closest one
        if component_hits:
            # Sort by distance
            component_hits.sort(key=lambda h: h['distance'])
            closest_hit = component_hits[0]
            
            # Complete path to component
            path.append(closest_hit['position'])
            
            # Find the correct input port based on incoming direction
            best_port = self._find_best_input_port(closest_hit['component'], direction)
            if best_port:
                if self.debug:
                    print(f"  Connection: {from_port.component.component_type} port {from_port.port_index} -> {closest_hit['component'].component_type} port {best_port.port_index}")
                return best_port, path, closest_hit['distance'], False
            else:
                if self.debug:
                    print(f"  WARNING: No suitable input port found on {closest_hit['component'].component_type}")
                return None, path, closest_hit['distance'], False
        
        # No hit found
        path.append(current_pos)
        return None, path, distance, False
    
    def _calculate_edge_intersection(self, start, end):
        """Calculate intersection with canvas edge - GRID ALIGNED."""
        x_min = CANVAS_OFFSET_X
        x_max = CANVAS_OFFSET_X + CANVAS_WIDTH
        y_min = CANVAS_OFFSET_Y
        y_max = CANVAS_OFFSET_Y + CANVAS_HEIGHT
        
        # Get direction
        direction = end - start
        if abs(direction.x) < 0.001 and abs(direction.y) < 0.001:
            return None
        
        # Normalize to grid direction
        if abs(direction.x) > abs(direction.y):
            # Horizontal movement
            if direction.x > 0:
                # Moving right
                edge_x = x_max
                edge_y = start.y
            else:
                # Moving left
                edge_x = x_min
                edge_y = start.y
        else:
            # Vertical movement
            if direction.y > 0:
                # Moving down
                edge_x = start.x
                edge_y = y_max
            else:
                # Moving up
                edge_x = start.x
                edge_y = y_min
        
        # Return the edge intersection point
        return Vector2(edge_x, edge_y)
    
    def _find_best_input_port(self, component, incoming_direction):
        """Find the best input port for an incoming beam direction - GRID ALIGNED."""
        if not hasattr(component, '_ports'):
            return None
        
        # Normalize incoming direction to grid-aligned direction
        if abs(incoming_direction.x) > abs(incoming_direction.y):
            # Horizontal
            grid_direction = Vector2(1 if incoming_direction.x > 0 else -1, 0)
        else:
            # Vertical
            grid_direction = Vector2(0, 1 if incoming_direction.y > 0 else -1)
        
        # Map grid directions to port indices
        # Port 0 = left (expects beam from left, going right)
        # Port 1 = bottom (expects beam from bottom, going up)
        # Port 2 = right (expects beam from right, going left)
        # Port 3 = top (expects beam from top, going down)
        
        if grid_direction.x > 0:  # Coming from left
            return component._ports[0] if len(component._ports) > 0 else None
        elif grid_direction.x < 0:  # Coming from right
            return component._ports[2] if len(component._ports) > 2 else None
        elif grid_direction.y > 0:  # Coming from bottom
            return component._ports[1] if len(component._ports) > 1 else None
        elif grid_direction.y < 0:  # Coming from top
            return component._ports[3] if len(component._ports) > 3 else None
        
        return None
    
    def _solve_beam_equations(self, laser):
        """Set up and solve the linear system for beam amplitudes."""
        # Clear any blocked beam paths from previous solve
        self._blocked_beam_paths = []
        
        # Assign unique IDs to all beam segments
        beam_segments = []
        for i, conn in enumerate(self.connections):
            beam_id = f"beam_{i}"
            beam_segments.append(beam_id)
            self.beam_amplitudes[beam_id] = 0j
        
        if not beam_segments:
            # No connections - check if laser beam hits edge or blocked
            if laser and laser.enabled:
                # Create a dummy port for the laser
                laser_port = self._create_ports_for_component(laser)[0] if laser else None
                if laser_port:
                    hit_port, path, distance, blocked = self._trace_to_first_component(laser_port)
                    if not hit_port and path and len(path) > 1:
                        # Beam goes to edge or blocked position
                        self._blocked_beam_paths.append({
                            'path': path,
                            'amplitude': 1.0,
                            'phase': 0,
                            'source_type': 'laser',
                            'blocked': blocked
                        })
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
                
                # Check if system is singular
                det = np.linalg.det(I_minus_A)
                if abs(det) < 1e-10:
                    if self.debug:
                        print("WARNING: System matrix is nearly singular!")
                
                # Solve the system
                x = np.linalg.solve(I_minus_A, b)
                
                # Store solutions
                for i, beam_id in enumerate(beam_segments):
                    self.beam_amplitudes[beam_id] = x[i]
                    
                if self.debug:
                    print(f"\nSolved for {n} beam amplitudes")
                    total_power = sum(abs(amp)**2 for amp in x)
                    print(f"Total power in system: {total_power:.3f}")
                    
        except np.linalg.LinAlgError as e:
            print(f"Warning: Could not solve beam equations - {e}")
            # Try a simpler approach for debugging
            if self.debug:
                print("Matrix A:")
                print(A)
                print("Vector b:")
                print(b)
            
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
        """Generate beam paths for visualization - including edge/blocked beams."""
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
        
        # Also check for any beams that hit edges or blocked positions
        # This is important for showing the full beam path even if it doesn't connect
        if hasattr(self, '_blocked_beam_paths'):
            for blocked_path in self._blocked_beam_paths:
                paths.append({
                    'path': blocked_path['path'],
                    'amplitude': blocked_path.get('amplitude', 1.0),
                    'phase': blocked_path.get('phase', 0),
                    'source_type': blocked_path.get('source_type', 'laser'),
                    'blocked': True
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
    
    def _connect_unconnected_components(self, laser, components):
        """Try to connect any remaining unconnected components using direct grid paths."""
        # Find all unconnected non-detector components
        connected_components = set()
        for conn in self.connections:
            connected_components.add(conn.port1.component)
            connected_components.add(conn.port2.component)
        
        unconnected = []
        for comp in components:
            if comp not in connected_components and comp.component_type != "detector":
                unconnected.append(comp)
        
        if not unconnected:
            return
        
        if self.debug:
            print(f"\nAttempting to connect {len(unconnected)} unconnected components:")
            for comp in unconnected:
                print(f"  - {comp.component_type} at {comp.position}")
        
        # For each unconnected component, try to find a connection
        # by checking all four directions
        connected_ports = set()
        for conn in self.connections:
            connected_ports.add(conn.port1)
            connected_ports.add(conn.port2)
        
        for comp in unconnected:
            if not hasattr(comp, '_ports'):
                continue
            
            # Try each port of the unconnected component
            for port in comp._ports:
                if port in connected_ports:
                    continue
                
                # Trace from this port
                hit_port, path, distance, blocked = self._trace_to_first_component(port)
                
                if hit_port and not blocked and hit_port not in connected_ports:
                    # Create connection
                    connection = OpticalConnection(port, hit_port, path, distance)
                    self.connections.append(connection)
                    port.connected_to = hit_port
                    port.connection = connection
                    hit_port.connected_to = port
                    hit_port.connection = connection
                    
                    connected_ports.add(port)
                    connected_ports.add(hit_port)
                    
                    if self.debug:
                        print(f"  Connected: {comp.component_type} -> {hit_port.component.component_type}")
                    
                    break  # Move to next component
    
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
                # Try to trace from each port
                if hasattr(comp, '_ports'):
                    for i, port in enumerate(comp._ports):
                        hit_port, path, distance, blocked = self._trace_to_first_component(port)
                        if hit_port:
                            print(f"       Port {i} CAN reach {hit_port.component.component_type}")
                        elif blocked:
                            print(f"       Port {i} blocked at distance {distance}")
                        else:
                            print(f"       Port {i} reaches edge at distance {distance}")
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