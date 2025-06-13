"""Fixed physics engine for beam propagation with proper multi-beamsplitter handling."""
import math
import cmath
from utils.vector import Vector2
from config.settings import WAVELENGTH, IDEAL_COMPONENTS, GRID_SIZE, CANVAS_OFFSET_X, CANVAS_OFFSET_Y, CANVAS_WIDTH, CANVAS_HEIGHT, scale

class BeamTracer:
    """Traces beam paths through optical components with proper interference handling."""
    
    def __init__(self):
        self.active_beams = []
        self.k = 2 * math.pi / WAVELENGTH  # Wave number
        self.debug = False  # Debug flag for detailed output
        self.blocked_positions = []  # Positions that block beams
        self.gold_positions = []  # Positions that award points
        self.gold_field_hits = {}  # Track gold field hits: {position: total_intensity}
        self.collected_gold_fields = set()  # Track which fields have been collected
        self.gold_field_hits_this_frame = {}  # Track new gold field hits this frame for sounds
    
    def set_blocked_positions(self, blocked_positions):
        """Set positions that block beam propagation."""
        self.blocked_positions = blocked_positions
    
    def set_gold_positions(self, gold_positions):
        """Set positions that award points when beams pass through."""
        self.gold_positions = gold_positions
    
    def reset(self):
        """Reset beam tracer for new frame."""
        self.active_beams = []
        # Clear this frame's gold field hits
        self.gold_field_hits_this_frame = {}
    
    def reset_gold_collection(self):
        """Reset gold field collection state."""
        self.gold_field_hits.clear()
        self.collected_gold_fields.clear()
        self.gold_field_hits_this_frame.clear()
    
    def add_beam(self, beam):
        """Add a beam to trace."""
        self.active_beams.append(beam)
    
    def trace_beams(self, components, max_depth=10):
        """
        Trace all beams through components with proper multi-beamsplitter interference.
        
        FIXED: Ensure beams from all sources reach their destination beam splitters
        before those beam splitters are processed.
        """
        # Reset components for new frame
        for comp in components:
            if hasattr(comp, 'reset_frame'):
                comp.reset_frame()
        
        # Storage for visualization
        all_traced_paths = []
        
        if self.debug:
            print(f"\n=== NEW FRAME - Beam tracing with fixed accumulation ===")
        
        # Start with initial beams
        active_beams = self.active_beams.copy()
        
        # FIXED: First, trace ALL beams to their destinations and accumulate them
        # This includes beams from laser and ALL outputs from components
        all_beams_to_trace = active_beams.copy()
        traced_beam_ids = set()
        
        iteration = 0
        while all_beams_to_trace and iteration < max_depth * 2:
            if self.debug:
                print(f"\n--- Full trace iteration {iteration} ---")
                print(f"Beams to trace: {len(all_beams_to_trace)}")
            
            new_beams_to_trace = []
            
            for beam in all_beams_to_trace:
                # Skip if already traced
                if 'unique_id' not in beam:
                    beam['unique_id'] = f"beam_{id(beam)}"
                
                if beam['unique_id'] in traced_beam_ids:
                    continue
                
                traced_beam_ids.add(beam['unique_id'])
                
                # Skip very weak beams
                if abs(beam['amplitude']) < 0.01:
                    continue
                
                # Trace beam to next component
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
                        'blocked': blocked
                    })
                    
                    if blocked:
                        if self.debug:
                            print(f"  Beam blocked at position {path[-1]}")
                        continue
                    
                    if hit_component:
                        # Update beam with new phase
                        beam_at_component = beam.copy()
                        beam_at_component['accumulated_phase'] = new_accumulated_phase
                        beam_at_component['total_path_length'] = beam.get('total_path_length', 0) + path_length
                        beam_at_component['unique_id'] = beam['unique_id']
                        
                        if self.debug:
                            print(f"  Beam {beam['unique_id']} hit {hit_component.component_type} at {hit_component.position}")
                        
                        # Add beam to component accumulation
                        if hasattr(hit_component, 'add_beam'):
                            hit_component.add_beam(beam_at_component)
                        
                        # If it's a mirror, process it immediately and get output beams
                        if hit_component.component_type == "mirror" and not hit_component.processed_this_frame:
                            if hasattr(hit_component, 'finalize_frame'):
                                output_beams = hit_component.finalize_frame()
                                
                                for out_beam in output_beams:
                                    # Ensure unique ID
                                    out_beam['unique_id'] = f"{beam['unique_id']}_mirror_{id(out_beam)}"
                                    
                                    # Visualization
                                    output_path = [hit_component.position, out_beam['position']]
                                    all_traced_paths.append({
                                        'path': output_path,
                                        'amplitude': abs(out_beam['amplitude']),
                                        'phase': out_beam['phase'],
                                        'source_type': out_beam.get('source_type', 'laser'),
                                        'blocked': False
                                    })
                                    
                                    # Add to beams to trace
                                    new_beams_to_trace.append(out_beam)
                                    
                                    if self.debug:
                                        dir_str = self._direction_to_string(out_beam['direction'])
                                        print(f"    Mirror output {dir_str}: amp={abs(out_beam['amplitude']):.3f}")
            
            # Continue with new beams
            all_beams_to_trace = new_beams_to_trace
            iteration += 1
        
        # FIXED: Now process ALL beam splitters after ALL beams have been accumulated
        if self.debug:
            print(f"\n=== PROCESSING ALL BEAM SPLITTERS - After full accumulation ===")
        
        # Get all beam splitters
        beam_splitters = [c for c in components if c.component_type == "beamsplitter"]
        
        # Process beam splitters and trace their outputs
        bs_iteration = 0
        bs_processed = True
        
        while bs_processed and bs_iteration < max_depth:
            bs_processed = False
            new_beams_from_bs = []
            
            if self.debug:
                print(f"\n--- Beam splitter processing iteration {bs_iteration} ---")
            
            for bs in beam_splitters:
                if not bs.processed_this_frame:
                    # Check if this beam splitter has any beams
                    total_beams = sum(len(beams) for beams in bs.all_beams_by_port.values())
                    
                    if total_beams > 0:
                        bs_processed = True
                        
                        if self.debug:
                            print(f"\n  Processing beam splitter at {bs.position}")
                            print(f"    Total accumulated beams: {total_beams}")
                            port_names = ['A', 'B', 'C', 'D']
                            for i, beams in enumerate(bs.all_beams_by_port.values()):
                                if beams:
                                    print(f"    Port {port_names[i]}: {len(beams)} beams")
                        
                        # Process the beam splitter
                        output_beams = bs.finalize_frame()
                        
                        for out_beam in output_beams:
                            # Ensure unique ID
                            out_beam['unique_id'] = f"bs_{id(bs)}_out_{id(out_beam)}"
                            
                            # Visualization
                            output_path = [bs.position, out_beam['position']]
                            all_traced_paths.append({
                                'path': output_path,
                                'amplitude': abs(out_beam['amplitude']),
                                'phase': out_beam['phase'],
                                'source_type': out_beam.get('source_type', 'laser'),
                                'blocked': False
                            })
                            
                            new_beams_from_bs.append(out_beam)
                            
                            if self.debug:
                                dir_str = self._direction_to_string(out_beam['direction'])
                                print(f"    BS output {dir_str}: amp={abs(out_beam['amplitude']):.3f}")
            
            # Trace the new beams from beam splitters to see if they hit other components
            if new_beams_from_bs:
                if self.debug:
                    print(f"\n  Tracing {len(new_beams_from_bs)} beams from beam splitters")
                
                for beam in new_beams_from_bs:
                    # Trace to next component
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
                                print(f"    Beam blocked at position {path[-1]}")
                            continue
                        
                        if hit_component:
                            beam_at_component = beam.copy()
                            beam_at_component['accumulated_phase'] = new_accumulated_phase
                            beam_at_component['total_path_length'] = beam.get('total_path_length', 0) + path_length
                            beam_at_component['unique_id'] = beam['unique_id']
                            
                            if self.debug:
                                print(f"    Beam {beam['unique_id']} reached {hit_component.component_type} at {hit_component.position}")
                            
                            # Add to component
                            if hasattr(hit_component, 'add_beam'):
                                hit_component.add_beam(beam_at_component)
                            
                            # Process mirrors immediately
                            if hit_component.component_type == "mirror" and not hit_component.processed_this_frame:
                                if hasattr(hit_component, 'finalize_frame'):
                                    mirror_outputs = hit_component.finalize_frame()
                                    for out_beam in mirror_outputs:
                                        out_beam['unique_id'] = f"{beam['unique_id']}_mirror_{id(out_beam)}"
                                        new_beams_from_bs.append(out_beam)
            
            bs_iteration += 1
        
        # Process all detectors
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
                    
                    # Calculate beam intensity
                    intensity = beam['amplitude'] ** 2  # Intensity is amplitude squared
                    
                    # Track for this frame (for sound effects)
                    if gold_key not in self.gold_field_hits_this_frame:
                        self.gold_field_hits_this_frame[gold_key] = 0
                    self.gold_field_hits_this_frame[gold_key] += intensity
                    
                    # Only count for scoring if not already collected
                    if gold_key not in self.collected_gold_fields:
                        self.collected_gold_fields.add(gold_key)
                        # Add beam intensity to total gold field hits
                        if gold_key not in self.gold_field_hits:
                            self.gold_field_hits[gold_key] = 0
                        self.gold_field_hits[gold_key] += intensity
                        
                        if self.debug:
                            print(f"  Beam hit gold field at grid ({grid_x}, {grid_y}) with intensity {intensity:.3f}")
            
            # Check if beam hits a blocked position
            for blocked_pos in self.blocked_positions:
                if blocked_pos.distance_to(next_pos) < GRID_SIZE / 2:
                    # Beam hit a blocked position
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