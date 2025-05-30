"""Physics engine for beam propagation."""
import math
import cmath
from utils.vector import Vector2
from config.settings import WAVELENGTH, IDEAL_COMPONENTS

class BeamTracer:
    """Traces beam paths through optical components."""
    
    def __init__(self):
        self.active_beams = []
        self.k = 2 * math.pi / WAVELENGTH  # Wave number
        self.debug = False  # Debug flag for detailed output
    
    def reset(self):
        """Reset beam tracer for new frame."""
        self.active_beams = []
    
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
                
                # Trace beam to next component
                path, hit_component, path_length = self._trace_single_beam(beam, components)
                
                if path and len(path) >= 2:
                    # Calculate phase change from propagation
                    phase_change = self.k * path_length
                    new_accumulated_phase = beam.get('accumulated_phase', beam['phase']) + phase_change
                    
                    # Store path for visualization
                    all_traced_paths.append({
                        'path': path,
                        'amplitude': abs(beam['amplitude']),
                        'phase': new_accumulated_phase,
                        'source_type': beam.get('source_type', 'laser')
                    })
                    
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
                                        'source_type': out_beam.get('source_type', 'laser')
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
                            
                            # Show what beams are being processed
                            total_input_intensity = 0
                            for port_idx, port_beams in comp.all_beams_by_port.items():
                                port_name = ['A', 'B', 'C', 'D'][port_idx]
                                if port_beams:
                                    print(f"      Port {port_name}: {len(port_beams)} beams")
                                    for beam in port_beams:
                                        intensity = beam['amplitude']**2
                                        total_input_intensity += intensity
                            print(f"    Total input intensity: {total_input_intensity*100:.1f}%")
                        
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
                                'source_type': out_beam.get('source_type', 'laser')
                            })
                            
                            new_beams.append(out_beam)
                            
                            if self.debug:
                                dir_str = self._direction_to_string(out_beam['direction'])
                                print(f"    Output {dir_str}: amp={abs(out_beam['amplitude']):.3f}, intensity={intensity*100:.1f}%")
                        
                        if self.debug:
                            print(f"    Total output intensity: {total_output_intensity*100:.1f}%")
                            if abs(total_output_intensity - total_input_intensity) > 0.01:
                                print(f"    WARNING: Energy not conserved! Difference = {(total_output_intensity - total_input_intensity)*100:.1f}%")
            
            # Trace the new beams from beam splitters
            if new_beams:
                active_beams = new_beams
                
                # Trace these new beams to see if they hit other components
                while active_beams:
                    next_beams = []
                    
                    for beam in active_beams:
                        if abs(beam['amplitude']) < 0.01:
                            continue
                        
                        path, hit_component, path_length = self._trace_single_beam(beam, components)
                        
                        if path and len(path) >= 2:
                            phase_change = self.k * path_length
                            new_accumulated_phase = beam.get('accumulated_phase', beam['phase']) + phase_change
                            
                            all_traced_paths.append({
                                'path': path,
                                'amplitude': abs(beam['amplitude']),
                                'phase': new_accumulated_phase,
                                'source_type': beam.get('source_type', 'laser')
                            })
                            
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
                                                'source_type': out_beam.get('source_type', 'laser')
                                            })
                                            
                                            next_beams.append(out_beam)
                    
                    active_beams = next_beams
            
            bs_iteration += 1
        
        # Phase 3: Process all detectors
        for comp in components:
            if comp.component_type == "detector" and hasattr(comp, 'finalize_frame'):
                comp.finalize_frame()
                
                if self.debug and (comp.intensity > 0 or len(comp.incoming_amplitudes) > 0):
                    print(f"\nDetector at {comp.position}:")
                    print(f"  Intensity: {comp.intensity*100:.1f}%")
                    print(f"  Beams: {len(comp.incoming_amplitudes)}")
        
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
        """Trace a single beam until it hits a component or leaves bounds."""
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
            
            # Check grid bounds
            from config.settings import CANVAS_OFFSET_X, CANVAS_OFFSET_Y, CANVAS_WIDTH, CANVAS_HEIGHT
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
                return path, None, total_path_length
            
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
                return path, hit_component, total_path_length
            
            # No collision, continue tracing
            total_path_length += step_size
            current_pos = next_pos
            
            # Add intermediate points for smooth rendering
            if int(distance) % 10 == 0:
                path.append(Vector2(current_pos.x, current_pos.y))
        
        # Reached max distance
        path.append(current_pos)
        return path, None, total_path_length
    
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
