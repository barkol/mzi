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
        
        Components remember all beams they've processed and reprocess
        everything when new beams arrive.
        """
        # Reset components for new frame (but they keep their beam history)
        for comp in components:
            if hasattr(comp, 'reset_frame'):
                comp.reset_frame()
        
        # Storage for visualization
        all_traced_paths = []
        
        if self.debug:
            print(f"\n=== NEW FRAME - Beam tracing with memory ===")
        
        # Start with initial beams
        active_beams = self.active_beams.copy()
        iteration = 0
        
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
                        
                        # Add beam to component
                        if hit_component.component_type in ["mirror", "beamsplitter", "detector"]:
                            hit_component.add_beam(beam_at_component)
                            # Note: add_beam automatically marks component as not processed
            
            # Process components that have beams and aren't processed
            for comp in components:
                if hasattr(comp, 'processed_this_frame') and not comp.processed_this_frame:
                    if comp.component_type == "mirror" and len(comp.incoming_beams) > 0:
                        if self.debug:
                            print(f"\n  Processing mirror at {comp.position}")
                            print(f"    Input beams: {len(comp.incoming_beams)}")
                        
                        # Process mirror
                        output_beams = comp.finalize_frame()
                        
                        for out_beam in output_beams:
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
                                print(f"    Output {dir_str}: amp={abs(out_beam['amplitude']):.3f}")
                    
                    elif comp.component_type == "beamsplitter" and len(comp.incoming_beams) > 0:
                        # Beam splitter will process ALL beams (history + new)
                        if self.debug:
                            print(f"\n  Processing beam splitter at {comp.position}")
                            new_count = len(comp.incoming_beams)
                            total_count = len(comp.all_processed_beams) + new_count
                            print(f"    Processing {total_count} beams ({len(comp.all_processed_beams)} historical + {new_count} new)")
                            
                            # Show what beams are being processed
                            all_beams = comp.all_processed_beams + comp.incoming_beams
                            total_input_intensity = 0
                            for i, beam in enumerate(all_beams):
                                intensity = beam['amplitude']**2
                                total_input_intensity += intensity
                                status = "old" if i < len(comp.all_processed_beams) else "NEW"
                                print(f"      Beam {i+1} ({status}): amp={beam['amplitude']:.3f}, phase={beam.get('accumulated_phase', 0)*180/math.pi:.1f}°, intensity={intensity*100:.1f}%")
                            print(f"    Total input intensity: {total_input_intensity*100:.1f}%")
                        
                        # Process with ALL beams (finalize_frame handles history)
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
            
            # Continue with new beams
            active_beams = new_beams
            iteration += 1
        
        # Process all detectors
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
