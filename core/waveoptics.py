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
            print(f"Laser at: {laser.position}")
            for comp in components:
                print(f"  - {comp.component_type} at {comp.position}")
            
        # Reset all components before solving
        for comp in components:
            if hasattr(comp, 'reset_frame'):
                comp.reset_frame()
            # Reset detectors specifically
            if comp.component_type == 'detector':
                comp.intensity = 0
                comp.incoming_beams = []
        
        # Sort components by distance from laser for better connection order
        sorted_components = sorted(components, 
                                 key=lambda c: c.position.distance_to(laser.position))
        
        # Build the optical network
        self._build_network(laser, sorted_components)
        
        # Check if we have any connections
        if len(self.connections) == 0:
            if self.debug:
                print("\nNo connections found - using simple ray tracing")
            # Use simple ray tracing as fallback
            self._simple_ray_trace_with_amplitudes(laser, sorted_components)
            return self._last_traced_beams
        
        # Set up and solve the linear system
        amplitudes = self._solve_beam_equations(laser)
        
        if self.debug:
            print(f"\nBeam amplitudes solved: {len(amplitudes)} beams")
            non_zero = sum(1 for amp in amplitudes.values() if abs(amp) > 0.01)
            print(f"Non-zero amplitudes: {non_zero}")
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
            if len(self.connections) == 0:
                print("WARNING: No connections found!")
                print("Port summary:")
                for comp in all_components:
                    if hasattr(comp, '_ports'):
                        print(f"  {comp.component_type} at {comp.position}: {len(comp._ports)} ports")
            else:
                connection_summary = {}
                for conn in self.connections:
                    key = f"{conn.port1.component.component_type} -> {conn.port2.component.component_type}"
                    connection_summary[key] = connection_summary.get(key, 0) + 1
                print("Connection summary:")
                for conn_type, count in sorted(connection_summary.items()):
                    print(f"  {conn_type}: {count}")
    
    def _create_ports_for_component(self, component):
        """Create optical ports for a component - GRID ALIGNED."""
        ports = []
        
        if self.debug:
            print(f"\nCreating ports for {component.component_type} at {component.position}")
        
        if component.component_type == "laser":
            # Laser has one output port - beam should start from edge of laser
            # The laser is placed on grid, so ensure port aligns with grid
            port_x = component.position.x + component.radius + 5  # Small offset from edge
            port_y = component.position.y  # Same Y as laser center
            
            # Ensure the port position is on a grid line if desired
            # For now, keep it as-is for smooth beam start
            port = OpticalPort(component, 0, 
                             Vector2(port_x, port_y),
                             Vector2(1, 0))  # Emits to the right
            ports.append(port)
            
            if self.debug:
                print(f"  Laser port at {port.position}")
            
        elif component.component_type in ["beamsplitter", "mirror", "tunable_beamsplitter", "partial_mirror"]:
            # These components have 4 ports at grid edges
            # Component is centered on grid, ports should be at half-grid distance
            offset_dist = GRID_SIZE // 2  # Half grid size to reach edge of grid cell
            
            # Use the component's actual position (should already be grid-aligned)
            center_x = component.position.x
            center_y = component.position.y
            
            port_configs = [
                (0, Vector2(-offset_dist, 0), Vector2(-1, 0)),   # Port A (left) - beams exit left
                (1, Vector2(0, offset_dist), Vector2(0, 1)),     # Port B (bottom) - beams exit down
                (2, Vector2(offset_dist, 0), Vector2(1, 0)),     # Port C (right) - beams exit right
                (3, Vector2(0, -offset_dist), Vector2(0, -1))    # Port D (top) - beams exit up
            ]
            
            for idx, offset, direction in port_configs:
                # Use the component's actual position for port calculation
                port_pos = Vector2(center_x + offset.x, center_y + offset.y)
                port = OpticalPort(component, idx, port_pos, direction)
                ports.append(port)
                
                if self.debug:
                    print(f"    Created port {idx} at {port_pos} for {component.component_type}")
                
        elif component.component_type == "detector":
            # Detector has 4 input ports at edges
            offset_dist = GRID_SIZE // 2  # Half grid size for consistency
            
            # Use the component's actual position
            center_x = component.position.x
            center_y = component.position.y
            
            port_configs = [
                (0, Vector2(-offset_dist, 0), Vector2(1, 0)),    # From left
                (1, Vector2(0, offset_dist), Vector2(0, -1)),    # From bottom
                (2, Vector2(offset_dist, 0), Vector2(-1, 0)),    # From right
                (3, Vector2(0, -offset_dist), Vector2(0, 1))     # From top
            ]
            
            for idx, offset, in_direction in port_configs:
                # Use the component's actual position for port calculation
                port_pos = Vector2(center_x + offset.x, center_y + offset.y)
                port = OpticalPort(component, idx, port_pos, in_direction)
                ports.append(port)
                
                if self.debug:
                    print(f"    Created detector port {idx} at {port_pos}")
        
        return ports
    
    def _find_connections_improved(self):
        """Find connections between ports with better handling of complex layouts - GRID BASED."""
        # First, clear any existing connections
        for port in self.ports:
            port.connected_to = None
            port.connection = None
        self.connections.clear()
        
        if self.debug:
            print("\n=== Finding connections ===")
        
        # Collect all potential connections
        potential_connections = []
        
        for port1 in self.ports:
            if port1.connected_to:
                continue
                
            # Don't trace from detector ports (they only receive)
            if port1.component.component_type == "detector":
                continue
            
            # For non-laser components, we need to trace from ALL ports to find connections
            # The S matrix will handle which paths actually carry amplitude
            if port1.component.component_type != "laser" and port1.component.component_type != "detector":
                # Trace from all non-detector ports
                if self.debug:
                    print(f"  Tracing from {port1.component.component_type} port {port1.port_index} at {port1.position}")
            
            # Trace a ray from this port
            hit_port, path, distance, blocked = self._trace_to_first_component(port1)
            
            # Only create connection if not blocked and hit a valid port
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
            elif blocked and self.debug:
                print(f"  Blocked: {port1.component.component_type}:{port1.port_index} blocked after {distance:.0f}")
            elif not hit_port and self.debug:
                print(f"  No hit: {port1.component.component_type}:{port1.port_index} -> edge")
        
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
        
        return priority
    
    def _trace_to_first_component(self, from_port: OpticalPort) -> Tuple[Optional[OpticalPort], List[Vector2], float, bool]:
        """Trace from one port to find the FIRST component it hits - GRID ALIGNED."""
        # Start from the port position
        start_pos = from_port.position
        direction = from_port.direction
        
        if self.debug:
            print(f"\n    Tracing from {from_port.component.component_type} port {from_port.port_index} at {start_pos} direction {direction}")
        
        # Ensure we're using exact grid directions
        if abs(direction.x) > abs(direction.y):
            # Horizontal movement
            direction = Vector2(1 if direction.x > 0 else -1, 0)
        else:
            # Vertical movement
            direction = Vector2(0, 1 if direction.y > 0 else -1)
        
        # Build the path starting from port position
        path = [start_pos]
        current_pos = Vector2(start_pos.x, start_pos.y)
        
        # Use small steps to ensure we don't miss blocked fields
        step_size = 2  # Small step for accurate blocked field detection
        distance = 0
        
        # Track which grid cells we've visited to check for blocked fields
        visited_cells = set()
        
        while distance < self.max_distance:
            # Move forward by step size
            next_pos = current_pos + direction * step_size
            distance += step_size
            
            # Get the grid cell this position is in
            grid_x = round((next_pos.x - CANVAS_OFFSET_X) / GRID_SIZE)
            grid_y = round((next_pos.y - CANVAS_OFFSET_Y) / GRID_SIZE)
            grid_cell = (grid_x, grid_y)
            
            # Check if this grid cell is blocked
            for blocked_pos in self.blocked_positions:
                blocked_grid_x = round((blocked_pos.x - CANVAS_OFFSET_X) / GRID_SIZE)
                blocked_grid_y = round((blocked_pos.y - CANVAS_OFFSET_Y) / GRID_SIZE)
                
                if (grid_x, grid_y) == (blocked_grid_x, blocked_grid_y):
                    # Beam hit a blocked field - end path here
                    # Use the center of the blocked grid cell
                    blocked_center_x = CANVAS_OFFSET_X + blocked_grid_x * GRID_SIZE + GRID_SIZE // 2
                    blocked_center_y = CANVAS_OFFSET_Y + blocked_grid_y * GRID_SIZE + GRID_SIZE // 2
                    blocked_center = Vector2(blocked_center_x, blocked_center_y)
                    path.append(blocked_center)
                    if self.debug:
                        print(f"      Beam blocked at grid ({grid_x}, {grid_y})")
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
            
            # Check if we hit another component using grid metrics
            hit_component = None
            min_grid_distance = float('inf')
            
            for comp in [p.component for p in self.ports if p.component != from_port.component]:
                # Calculate grid distance (Manhattan distance)
                dx = abs(comp.position.x - next_pos.x)
                dy = abs(comp.position.y - next_pos.y)
                grid_distance = dx + dy
                
                # Check if we're in the same grid cell as the component
                comp_grid_x = round((comp.position.x - CANVAS_OFFSET_X) / GRID_SIZE)
                comp_grid_y = round((comp.position.y - CANVAS_OFFSET_Y) / GRID_SIZE)
                beam_grid_x = round((next_pos.x - CANVAS_OFFSET_X) / GRID_SIZE)
                beam_grid_y = round((next_pos.y - CANVAS_OFFSET_Y) / GRID_SIZE)
                
                # Component is hit if beam is in same grid cell
                if comp_grid_x == beam_grid_x and comp_grid_y == beam_grid_y:
                    if grid_distance < min_grid_distance:
                        hit_component = comp
                        min_grid_distance = grid_distance
                        if self.debug:
                            print(f"      Hit {comp.component_type} at grid ({comp_grid_x}, {comp_grid_y})")
            
            if hit_component:
                # End the path at the component's center
                path.append(hit_component.position)
                
                # Find the correct input port based on incoming direction
                best_port = self._find_best_input_port(hit_component, direction)
                if best_port:
                    if self.debug:
                        print(f"      Ray hit: {from_port.component.component_type} -> {hit_component.component_type} port {best_port.port_index}")
                    return best_port, path, distance, False
                else:
                    # Component hit but no suitable port
                    if self.debug:
                        print(f"      Hit {hit_component.component_type} but no suitable port for direction {direction}")
                    return None, path, distance, True
            
            # Add intermediate points periodically for smooth rendering
            if int(distance) % 20 == 0:
                path.append(Vector2(next_pos.x, next_pos.y))
            
            current_pos = next_pos
        
        # No hit found - beam went maximum distance
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
        
        # Fallback - try to find any suitable port
        if len(component._ports) > 0:
            return component._ports[0]
        
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
            if self.debug:
                print("\nNo beam segments to solve")
            return {}
        
        # Build system matrix
        n = len(beam_segments)
        A = np.zeros((n, n), dtype=complex)
        b = np.zeros(n, dtype=complex)
        
        if self.debug:
            print(f"\nBuilding system with {n} beam segments")
        
        # Add equations for each connection
        for i, conn in enumerate(self.connections):
            beam_id = beam_segments[i]
            
            # Phase accumulation along this connection
            phase = cmath.exp(1j * conn.phase_shift)
            
            # Source term (only for laser output)
            if conn.port1.component.component_type == "laser":
                b[i] = 1.0  # Unit amplitude from laser
                if self.debug:
                    print(f"  Beam {i} starts from laser with amplitude 1.0")
            
            # Add scattering contributions
            self._add_scattering_terms(A, i, conn, beam_segments, phase)
        
        # Solve the system
        try:
            if n > 0:
                # For steady state, we solve (I - A)x = b
                I_minus_A = np.eye(n) - A
                
                if self.debug:
                    print(f"\nSolving {n}x{n} system...")
                    # Check condition number
                    try:
                        cond = np.linalg.cond(I_minus_A)
                        print(f"Condition number: {cond:.2e}")
                        if cond > 1e10:
                            print("WARNING: System is ill-conditioned!")
                    except:
                        pass
                
                # Add small regularization for numerical stability
                I_minus_A += np.eye(n) * 1e-10
                
                # Solve the system
                x = np.linalg.solve(I_minus_A, b)
                
                # Store solutions
                for i, beam_id in enumerate(beam_segments):
                    self.beam_amplitudes[beam_id] = x[i]
                
                if self.debug:
                    print(f"\nSolved for {n} beam amplitudes")
                    total_power = sum(abs(amp)**2 for amp in x)
                    print(f"Total power in system: {total_power:.3f}")
                    
                    # Check if solution is reasonable
                    if total_power < 0.1:
                        print("WARNING: Very low total power - check system setup")
                    elif total_power > 10:
                        print("WARNING: Very high total power - possible numerical issues")
                    
        except np.linalg.LinAlgError as e:
            print(f"ERROR: Could not solve beam equations - {e}")
            # Fallback: set laser output beam to unit amplitude
            for i, conn in enumerate(self.connections):
                if conn.port1.component.component_type == "laser":
                    self.beam_amplitudes[beam_segments[i]] = 1.0
                else:
                    self.beam_amplitudes[beam_segments[i]] = 0.0
            
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
                        
                        if self.debug and abs(s_coeff) > 0.1:
                            port_names = ['A', 'B', 'C', 'D']
                            in_name = port_names[input_port_idx] if input_port_idx < 4 else str(input_port_idx)
                            out_name = port_names[output_port_idx] if output_port_idx < 4 else str(output_port_idx)
                            print(f"    {port2_component.component_type} scatters port {in_name} -> {out_name} with coeff {s_coeff:.3f}")
    
    def _generate_beam_paths(self, amplitudes):
        """Generate beam paths for visualization - ensuring proper start positions."""
        paths = []
        
        for conn_idx, conn in enumerate(self.connections):
            beam_id = f"beam_{conn_idx}"
            amplitude = amplitudes.get(beam_id, 0j)
            
            # Include beams with small amplitudes for debugging
            if abs(amplitude) < 0.001 and not self.debug:
                continue
            
            # Use the full path stored in the connection
            # Make sure the path starts from the correct port position
            path = conn.path.copy() if conn.path else []
            
            # If path is empty or doesn't start at port1 position, fix it
            if not path or (path[0].distance_to(conn.port1.position) > 1):
                # Rebuild path from port1 to port2
                path = [conn.port1.position]
                if conn.path and len(conn.path) > 1:
                    # Keep intermediate points
                    path.extend(conn.path[1:-1])
                path.append(conn.port2.position)
            
            paths.append({
                'path': path,
                'amplitude': abs(amplitude),
                'phase': cmath.phase(amplitude),
                'source_type': 'laser' if conn.port1.component.component_type == 'laser' else 'mixed',
                'blocked': False
            })
            
            if self.debug and abs(amplitude) > 0.01:
                print(f"  Path {conn_idx}: {conn.port1.component.component_type} -> {conn.port2.component.component_type}, |A|={abs(amplitude):.3f}")
                print(f"    Start: {path[0]}, End: {path[-1]}")
        
        # Also add any blocked beam paths
        for blocked_path in self._blocked_beam_paths:
            paths.append(blocked_path)
        
        return paths
    
    def _check_gold_fields(self, paths):
        """Check for gold field hits along beam paths."""
        self.gold_field_hits_this_frame.clear()
        
        for path_data in paths:
            path = path_data['path']
            amplitude = path_data['amplitude']
            intensity = amplitude ** 2
            
            # Skip very weak beams
            if intensity < 0.001:
                continue
            
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
        
        # Collect all beams going to each detector
        detector_beams = {}  # detector -> list of beams
        
        # Check all connections
        for conn_idx, conn in enumerate(self.connections):
            if conn.port2.component.component_type == "detector":
                beam_id = f"beam_{conn_idx}"
                amplitude = amplitudes.get(beam_id, 0j)
                
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
    
    def _simple_ray_trace_with_amplitudes(self, laser, components):
        """Simple ray tracing fallback with proper amplitude calculation."""
        if self.debug:
            print("\nUsing simple ray trace with amplitudes")
        
        # Ensure all components have ports created
        for comp in [laser] + components:
            if not hasattr(comp, '_ports') or comp._ports is None:
                comp._ports = self._create_ports_for_component(comp)
        
        # Create laser port
        laser_port = laser._ports[0] if hasattr(laser, '_ports') and laser._ports else self._create_ports_for_component(laser)[0]
        
        # Reset all components
        for comp in components:
            if hasattr(comp, 'reset_frame'):
                comp.reset_frame()
        
        # Trace from laser - starting from port position, not laser center
        traced_paths = []
        active_rays = [{
            'position': laser_port.position,  # Start from port, not center
            'direction': laser_port.direction,
            'amplitude': 1.0 + 0j,  # Complex amplitude
            'path': [laser.position, laser_port.position],  # Include both center and port
            'path_length': 0,
            'generation': 0,
            'processed': set()
        }]
        
        max_bounces = 20
        
        while active_rays and active_rays[0]['generation'] < max_bounces:
            new_rays = []
            
            for ray in active_rays:
                # Trace to next component
                hit_comp, hit_pos, distance, blocked = self._trace_ray_to_component(
                    ray['position'], ray['direction'], ray['processed'], components
                )
                
                # Check if beam was blocked before reaching component
                if blocked and not hit_comp:
                    # Ray was blocked - add blocked path
                    ray['path'].append(hit_pos)
                    
                    if abs(ray['amplitude']) > 0.01:
                        traced_paths.append({
                            'path': ray['path'].copy(),
                            'amplitude': abs(ray['amplitude']),
                            'phase': cmath.phase(ray['amplitude']),
                            'source_type': 'laser',
                            'blocked': True
                        })
                    continue  # Don't process this ray further
                
                if hit_comp:
                    # Complete path to component
                    ray['path'].append(hit_comp.position)
                    ray['path_length'] += distance
                    
                    # Store the path for visualization
                    if abs(ray['amplitude']) > 0.01:
                        traced_paths.append({
                            'path': ray['path'].copy(),
                            'amplitude': abs(ray['amplitude']),
                            'phase': cmath.phase(ray['amplitude']),
                            'source_type': 'laser',
                            'blocked': False
                        })
                    
                    # Handle component interaction
                    if hit_comp.component_type == "detector":
                        # Add beam to detector
                        detector_beam = {
                            'amplitude': abs(ray['amplitude']),
                            'phase': cmath.phase(ray['amplitude']),
                            'accumulated_phase': cmath.phase(ray['amplitude']),
                            'total_path_length': ray['path_length'],
                            'beam_id': f"ray_{len(traced_paths)}",
                            'source_type': 'laser'
                        }
                        hit_comp.add_beam(detector_beam)
                        
                    elif hasattr(hit_comp, 'S'):
                        # Handle scattering
                        # Find input port based on ray direction
                        input_port = self._find_best_input_port(hit_comp, ray['direction'])
                        if input_port:
                            input_idx = input_port.port_index
                            S = hit_comp.S
                            
                            # Calculate phase from propagation
                            phase_shift = self.k * distance
                            propagated_amplitude = ray['amplitude'] * cmath.exp(1j * phase_shift)
                            
                            # Generate output rays
                            port_directions = [Vector2(-1, 0), Vector2(0, 1), Vector2(1, 0), Vector2(0, -1)]
                            
                            for output_idx in range(4):
                                s_coeff = S[output_idx, input_idx]
                                if abs(s_coeff) > 0.01:
                                    output_amplitude = propagated_amplitude * s_coeff
                                    
                                    new_ray = {
                                        'position': hit_comp.position,
                                        'direction': port_directions[output_idx],
                                        'amplitude': output_amplitude,
                                        'path': [hit_comp.position],
                                        'path_length': ray['path_length'] + distance,
                                        'generation': ray['generation'] + 1,
                                        'processed': ray['processed'] | {hit_comp}
                                    }
                                    new_rays.append(new_ray)
                else:
                    # Ray goes to edge or is blocked
                    final_pos = self._trace_to_edge(ray['position'], ray['direction'])
                    ray['path'].append(final_pos)
                    
                    if abs(ray['amplitude']) > 0.01:
                        traced_paths.append({
                            'path': ray['path'].copy(),
                            'amplitude': abs(ray['amplitude']),
                            'phase': cmath.phase(ray['amplitude']),
                            'source_type': 'laser',
                            'blocked': blocked
                        })
            
            active_rays = new_rays
        
        # Finalize all detectors
        for comp in components:
            if comp.component_type == "detector":
                comp.finalize_frame()
        
        # Store traced paths
        self._last_traced_beams = traced_paths
        
        # Check gold fields
        self._check_gold_fields(traced_paths)
    
    def _trace_ray_to_component(self, start_pos, direction, processed, components):
        """Trace a ray until it hits a component, respecting blocked fields."""
        current_pos = Vector2(start_pos.x, start_pos.y)
        path_length = 0
        step_size = 2  # Small steps to ensure we don't miss blocked fields
        
        while path_length < self.max_distance:
            next_pos = current_pos + direction * step_size
            path_length += step_size
            
            # Check if we're in a blocked grid cell
            grid_x = round((next_pos.x - CANVAS_OFFSET_X) / GRID_SIZE)
            grid_y = round((next_pos.y - CANVAS_OFFSET_Y) / GRID_SIZE)
            
            for blocked_pos in self.blocked_positions:
                blocked_grid_x = round((blocked_pos.x - CANVAS_OFFSET_X) / GRID_SIZE)
                blocked_grid_y = round((blocked_pos.y - CANVAS_OFFSET_Y) / GRID_SIZE)
                
                if (grid_x, grid_y) == (blocked_grid_x, blocked_grid_y):
                    # Beam hit a blocked field
                    return None, blocked_pos, path_length, True
            
            # Check bounds
            if (next_pos.x < CANVAS_OFFSET_X - GRID_SIZE or
                next_pos.x > CANVAS_OFFSET_X + CANVAS_WIDTH + GRID_SIZE or
                next_pos.y < CANVAS_OFFSET_Y - GRID_SIZE or
                next_pos.y > CANVAS_OFFSET_Y + CANVAS_HEIGHT + GRID_SIZE):
                return None, next_pos, path_length, False
            
            # Check components
            for comp in components:
                if comp in processed:
                    continue
                
                # Use appropriate collision radius based on component type
                if comp.component_type == "detector":
                    comp_radius = getattr(comp, 'radius', GRID_SIZE // 2)
                else:
                    # For optical components, use radius that accounts for port positions
                    comp_radius = GRID_SIZE // 2 + 5  # Ports are at GRID_SIZE//2 from center
                
                if comp.position.distance_to(next_pos) < comp_radius:
                    return comp, comp.position, path_length, False
            
            current_pos = next_pos
        
        return None, current_pos, path_length, False
    
    def _trace_to_edge(self, start_pos, direction):
        """Trace to edge of canvas."""
        current_pos = Vector2(start_pos.x, start_pos.y)
        step_size = 2
        
        while True:
            next_pos = current_pos + direction * step_size
            
            if (next_pos.x < CANVAS_OFFSET_X or
                next_pos.x > CANVAS_OFFSET_X + CANVAS_WIDTH or
                next_pos.y < CANVAS_OFFSET_Y or
                next_pos.y > CANVAS_OFFSET_Y + CANVAS_HEIGHT):
                return current_pos
            
            current_pos = next_pos
            
            if current_pos.distance_to(start_pos) > self.max_distance:
                return current_pos
    
    # Compatibility methods
    def trace_beams(self, components):
        """Compatibility method - finds laser and redirects to solve_interferometer."""
        # Find laser
        laser = None
        actual_components = []
        
        for comp in components:
            if hasattr(comp, 'component_type') and comp.component_type == 'laser':
                laser = comp
            else:
                actual_components.append(comp)
        
        if not laser:
            if self.debug:
                print("WARNING: No laser found in trace_beams")
            return []
        
        return self.solve_interferometer(laser, actual_components)
    
    def add_beam(self, beam):
        """Compatibility method - not used in wave optics approach."""
        pass