"""Physics engine for beam propagation."""
import math
import cmath
from utils.vector import Vector2
from config.settings import WAVELENGTH, IDEAL_COMPONENTS, GRID_SIZE, CANVAS_OFFSET_X, CANVAS_OFFSET_Y, CANVAS_WIDTH, CANVAS_HEIGHT

class BeamTracer:
    """Traces beam paths through optical components."""
    
    def __init__(self):
        self.active_beams = []
        self.k = 2 * math.pi / WAVELENGTH  # Wave number
        self.debug = False  # Debug flag for detailed output
        self.blocked_positions = []  # Positions that block beams
        self.gold_positions = []  # Positions that award points
        self.gold_field_hits = {}  # Track gold field hits: {position: total_intensity}
    
    def set_blocked_positions(self, blocked_positions):
        """Set positions that block beam propagation."""
        self.blocked_positions = blocked_positions
    
    def set_gold_positions(self, gold_positions):
        """Set positions that award points when beams pass through."""
        self.gold_positions = gold_positions
    
    def reset(self):
        """Reset beam tracer for new frame."""
        self.active_beams = []
        self.gold_field_hits = {}  # Reset gold field tracking
    
    def add_beam(self, beam):
        """Add a beam to trace."""
        self.active_beams.append(beam)
    
    def trace_beams(self, components, max_depth=10):
        """
        Trace all beams through components.
        
        Key change: Components accumulate beams across all iterations,
        then process everything at the end.
        """
        # Reset components for new frame
        for comp in components:
            if hasattr(comp, 'reset_frame'):
                comp.reset_frame()
        
        # Storage for visualization
        all_traced_paths = []
        
        if self.debug:
            print(f"\n=== NEW FRAME - Beam tracing with proper accumulation ===")
        
        # Start with initial beams
        active_beams = self.active_beams.copy()
        iteration = 0
        
        # Phase 1: Trace all beams and accumulate them at components
        # Keep iterating until no new beams are generated
        while active_beams and iteration < max_depth:
            if self.debug:
                print(f"\n--- Iteration {iteration} ---")
                print(f"Active beams: {len(active_beams)}")
            
            new_beams = []
            
            # Trace all active beams
            for beam in active_beams:
                # Skip very weak beams
                if abs(beam['amplitude']) < 0.01:
                    continue
                
                # Trace beam to next component or blocked position
                path, hit_component, path_length, blocked = self._trace_single_beam(beam, components)
                
                if path and len(path) >= 2:
                    # Calculate phase change from propagation
                    phase_change = self.k * path_length
                    new_accumulated_phase = beam.get('accumulated_phase', beam['phase']) + phase_change
                    
                    # Store path for visualization
                    all_traced_paths.append({
                        'path': path,
                        'amplitude': abs(beam['amplitude']),
                        'phase': new_accumulated_phase,
                        'source_type': beam.get('source_type', 'laser'),
                        'blocked': blocked  # Mark if beam was blocked
                    })
                    
                    if blocked:
                        # Beam hit a blocked position - stop propagation
                        if self.debug:
                            print(f"  Beam blocked at position {path[-1]}")
                        continue
                    
                    if hit_component:
                        # Update beam with new phase
                        beam_at_component = beam.copy()
                        beam_at_component['accumulated_phase'] = new_accumulated_phase
                        beam_at_component['total_path_length'] = beam.get('total_path_length', 0) + path_length
                        
                        if self.debug:
                            print(f"  Beam hit {hit_component.component_type} at {hit_component.position}")
                        
                        # Add beam to component (accumulate, don't process yet)
                        if hit_component.component_type in ["mirror", "beamsplitter", "detector"]:
                            hit_component.add_beam(beam_at_component)
                            
                            # For mirrors, process immediately since they don't have interference
                            if hit_component.component_type == "mirror" and not hit_component.processed_this_frame:
                                output_beams = hit_component.finalize_frame()
                                
                                for out_beam in output_beams:
                                    # Visualization
                                    output_path = [hit_component.position, out_beam['position']]
                                    all_traced_paths.append({
                                        'path': output_path,
                                        'amplitude': abs(out_beam['amplitude']),
                                        'phase': out_beam['phase'],
                                        'source_type': out_beam.get('source_type', 'laser'),
                                        'blocked': False
                                    })
                                    
                                    new_beams.append(out_beam)
                                    
                                    if self.debug:
                                        dir_str = self._direction_to_string(out_beam['direction'])
                                        print(f"    Mirror output {dir_str}: amp={abs(out_beam['amplitude']):.3f}")
            
            # Continue with new beams from mirrors only
            active_beams = new_beams
            iteration += 1
        
        # Phase 2: Process all beam splitters AFTER all beams have been accumulated
        if self.debug:
            print(f"\n=== PROCESSING BEAM SPLITTERS - All beams accumulated ===")
        
        # Keep processing beam splitters until no new beams are generated
        bs_iteration = 0
        bs_processed_any = True
        
        while bs_processed_any and bs_iteration < max_depth:
            bs_processed_any = False
            new_beams = []
            
            for comp in components:
                if comp.component_type == "beamsplitter" and not comp.processed_this_frame:
                    # Check if this beam splitter has any beams to process
                    total_beams = sum(len(beams) for beams in comp.all_beams_by_port.values())
                    
                    if total_beams > 0:
                        bs_processed_any = True
                        
                        if self.debug:
                            print(f"\n  Processing beam splitter at {comp.position}")
                            print(f"    Total accumulated beams: {total_beams}")
                        
                        # Process with ALL accumulated beams
                        output_beams = comp.finalize_frame()
                        
                        total_output_intensity = 0
                        for out_beam in output_beams:
                            intensity = out_beam['amplitude']**2
                            total_output_intensity += intensity
                            
                            # Visualization
                            output_path = [comp.position, out_beam['position']]
                            all_traced_paths.append({
                                'path': output_path,
                                'amplitude': abs(out_beam['amplitude']),
                                'phase': out_beam['phase'],
                                'source_type': out_beam.get('source_type', 'laser'),
                                'blocked': False
                            })
                            
                            new_beams.append(out_beam)
                            
                            if self.debug:
                                dir_str = self._direction_to_string(out_beam['direction'])
                                print(f"    Output {dir_str}: amp={abs(out_beam['amplitude']):.3f}, intensity={intensity*100:.1f}%")
            
            # Trace the new beams from beam splitters
            if new_beams:
                active_beams = new_beams
                
                # Trace these new beams to see if they hit other components
                while active_beams:
                    next_beams = []
                    
                    for beam in active_beams:
                        if abs(beam['amplitude']) < 0.01:
                            continue
                        
                        path, hit_component, path_length, blocked = self._trace_single_beam(beam, components)
                        
                        if path and len(path) >= 2:
                            phase_change = self.k * path_length
                            new_accumulated_phase = beam.get('accumulated_phase', beam['phase']) + phase_change
                            
                            all_traced_paths.append({
                                'path': path,
                                'amplitude': abs(beam['amplitude']),
                                'phase': new_accumulated_phase,
                                'source_type': beam.get('source_type', 'laser'),
                                'blocked': blocked
                            })
                            
                            if blocked:
                                if self.debug:
                                    print(f"  Beam blocked at position {path[-1]}")
                                continue
                            
                            if hit_component:
                                beam_at_component = beam.copy()
                                beam_at_component['accumulated_phase'] = new_accumulated_phase
                                beam_at_component['total_path_length'] = beam.get('total_path_length', 0) + path_length
                                
                                if hit_component.component_type in ["mirror", "beamsplitter", "detector"]:
                                    hit_component.add_beam(beam_at_component)
                                    
                                    # Process mirrors immediately
                                    if hit_component.component_type == "mirror" and not hit_component.processed_this_frame:
                                        mirror_outputs = hit_component.finalize_frame()
                                        
                                        for out_beam in mirror_outputs:
                                            output_path = [hit_component.position, out_beam['position']]
                                            all_traced_paths.append({
                                                'path': output_path,
                                                'amplitude': abs(out_beam['amplitude']),
                                                'phase': out_beam['phase'],
                                                'source_type': out_beam.get('source_type', 'laser'),
                                                'blocked': False
                                            })
                                            
                                            next_beams.append(out_beam)
                    
                    active_beams = next_beams
            
            bs_iteration += 1
        
        # Phase 3: Process all detectors
        for comp in components:
            if comp.component_type == "detector" and hasattr(comp, 'finalize_frame'):
                comp.finalize_frame()
                
                if self.debug and (comp.intensity > 0 or len(comp.incoming_beams) > 0):
                    print(f"\nDetector at {comp.position}:")
                    print(f"  Intensity: {comp.intensity*100:.1f}%")
                    print(f"  Beams: {len(comp.incoming_beams)}")
        
        return all_traced_paths
    
    def _direction_to_string(self, direction):
        """Convert direction vector to string."""
        if direction.x > 0.5:
            return "RIGHT"
        elif direction.x < -0.5:
            return "LEFT"
        elif direction.y > 0.5:
            return "DOWN"
        elif direction.y < -0.5:
            return "UP"
        else:
            return "UNKNOWN"
    
    def _trace_single_beam(self, beam, components):
        """
        Trace a single beam until it hits a component, blocked position, or leaves bounds.
        Returns: (path, hit_component, path_length, blocked)
        """
        path = [beam['position']]
        current_pos = Vector2(beam['position'].x, beam['position'].y)
        direction = beam['direction']
        
        step_size = 2
        max_distance = 1000
        distance = 0
        total_path_length = 0
        
        # Track gold field hits for this beam
        gold_hits_this_beam = set()  # Avoid double-counting same field
        
        while distance < max_distance:
            # Move beam forward
            next_pos = current_pos + direction * step_size
            distance += step_size
            
            # Check if beam passes through a gold field
            for gold_pos in self.gold_positions:
                if gold_pos.distance_to(next_pos) < GRID_SIZE / 2:
                    # Convert position to grid coordinates for consistent tracking
                    grid_x = round((gold_pos.x - CANVAS_OFFSET_X) / GRID_SIZE)
                    grid_y = round((gold_pos.y - CANVAS_OFFSET_Y) / GRID_SIZE)
                    gold_key = (grid_x, grid_y)
                    
                    # Only count each gold field once per beam
                    if gold_key not in gold_hits_this_beam:
                        gold_hits_this_beam.add(gold_key)
                        # Add beam intensity to this gold field
                        intensity = beam['amplitude'] ** 2  # Intensity is amplitude squared
                        if gold_key not in self.gold_field_hits:
                            self.gold_field_hits[gold_key] = 0
                        self.gold_field_hits[gold_key] += intensity
                        
                        if self.debug:
                            print(f"  Beam hit gold field at grid ({grid_x}, {grid_y}) with intensity {intensity:.3f}")
            
            # Check if beam hits a blocked position
            for blocked_pos in self.blocked_positions:
                if blocked_pos.distance_to(next_pos) < GRID_SIZE / 2:
                    # Beam hit a blocked position - calculate exact intersection
                    intersection = self._calculate_blocked_intersection(current_pos, next_pos, blocked_pos)
                    if intersection:
                        path.append(intersection)
                        total_path_length += current_pos.distance_to(intersection)
                    else:
                        path.append(blocked_pos)
                        total_path_length += current_pos.distance_to(blocked_pos)
                    return path, None, total_path_length, True
            
            # Check grid bounds
            if (next_pos.x < CANVAS_OFFSET_X or
                next_pos.x > CANVAS_OFFSET_X + CANVAS_WIDTH or
                next_pos.y < CANVAS_OFFSET_Y or
                next_pos.y > CANVAS_OFFSET_Y + CANVAS_HEIGHT):
                # Calculate exact intersection with grid boundary
                edge_pos = self._calculate_edge_intersection(current_pos, next_pos,
                    CANVAS_OFFSET_X, CANVAS_OFFSET_Y,
                    CANVAS_OFFSET_X + CANVAS_WIDTH,
                    CANVAS_OFFSET_Y + CANVAS_HEIGHT)
                if edge_pos:
                    path.append(edge_pos)
                    total_path_length += current_pos.distance_to(edge_pos)
                return path, None, total_path_length, False
            
            # Check for component collision
            hit_component = None
            min_distance = float('inf')
            
            for comp in components:
                dist_to_comp = comp.position.distance_to(next_pos)
                if dist_to_comp < comp.radius and dist_to_comp < min_distance:
                    hit_component = comp
                    min_distance = dist_to_comp
            
            if hit_component:
                # Beam hit a component - stop at its center
                path.append(hit_component.position)
                total_path_length += current_pos.distance_to(hit_component.position)
                return path, hit_component, total_path_length, False
            
            # No collision, continue tracing
            total_path_length += step_size
            current_pos = next_pos
            
            # Add intermediate points for smooth rendering
            if int(distance) % 10 == 0:
                path.append(Vector2(current_pos.x, current_pos.y))
        
        # Reached max distance
        path.append(current_pos)
        return path, None, total_path_length, False
    
    def _calculate_blocked_intersection(self, start, end, blocked_pos):
        """Calculate intersection point with blocked position area."""
        # Treat blocked position as a square with GRID_SIZE dimensions
        half_size = GRID_SIZE / 2
        
        # Define the four edges of the blocked square
        edges = [
            (Vector2(blocked_pos.x - half_size, blocked_pos.y - half_size),
             Vector2(blocked_pos.x + half_size, blocked_pos.y - half_size)),  # Top
            (Vector2(blocked_pos.x + half_size, blocked_pos.y - half_size),
             Vector2(blocked_pos.x + half_size, blocked_pos.y + half_size)),  # Right
            (Vector2(blocked_pos.x + half_size, blocked_pos.y + half_size),
             Vector2(blocked_pos.x - half_size, blocked_pos.y + half_size)),  # Bottom
            (Vector2(blocked_pos.x - half_size, blocked_pos.y + half_size),
             Vector2(blocked_pos.x - half_size, blocked_pos.y - half_size))   # Left
        ]
        
        closest_intersection = None
        min_distance = float('inf')
        
        for edge_start, edge_end in edges:
            intersection = self._line_intersection(start, end, edge_start, edge_end)
            if intersection:
                dist = start.distance_to(intersection)
                if dist < min_distance:
                    min_distance = dist
                    closest_intersection = intersection
        
        return closest_intersection
    
    def _calculate_edge_intersection(self, start, end, x_min, y_min, x_max, y_max):
        """Calculate intersection point with grid boundary."""
        edges = [
            (Vector2(x_min, y_min), Vector2(x_min, y_max)),  # Left
            (Vector2(x_max, y_min), Vector2(x_max, y_max)),  # Right
            (Vector2(x_min, y_min), Vector2(x_max, y_min)),  # Top
            (Vector2(x_min, y_max), Vector2(x_max, y_max))   # Bottom
        ]
        
        closest_intersection = None
        min_distance = float('inf')
        
        for edge_start, edge_end in edges:
            intersection = self._line_intersection(start, end, edge_start, edge_end)
            if intersection:
                dist = start.distance_to(intersection)
                if dist < min_distance:
                    min_distance = dist
                    closest_intersection = intersection
        
        return closest_intersection
    
    def _line_intersection(self, p1, p2, p3, p4):
        """Calculate intersection point of two line segments."""
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        x3, y3 = p3.x, p3.y
        x4, y4 = p4.x, p4.y
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 0.001:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        
        if 0 <= t <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return Vector2(x, y)
        
        return None
