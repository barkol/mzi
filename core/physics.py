"""Physics engine for beam propagation."""
import math
from utils.vector import Vector2
from config.settings import WAVELENGTH

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
        """Trace all beams through components."""
        all_traced_beams = []
        current_beams = self.active_beams.copy()
        
        # Reset all components that need frame-based accumulation
        for comp in components:
            if hasattr(comp, 'reset_frame'):
                comp.reset_frame()
        
        for depth in range(max_depth):
            if not current_beams:
                break
                
            # Trace all beams at current depth and collect component hits
            traced_this_depth = []
            component_hits = {}  # component -> list of beams
            
            for beam in current_beams:
                # Skip very weak beams
                if beam['amplitude'] < 0.01:
                    continue
                    
                # Trace beam to next component or boundary
                path, hit_component, path_length = self._trace_single_beam(beam, components)
                
                if path and len(path) >= 2:
                    # Update beam's phase based on distance traveled
                    # Phase change = k * path_length where k = 2π/λ
                    phase_change = self.k * path_length
                    
                    # Update the beam's accumulated phase
                    beam['accumulated_phase'] = beam.get('accumulated_phase', beam['phase']) + phase_change
                    beam['total_path_length'] = beam.get('total_path_length', 0) + path_length
                    
                    # Record the traced path with the beam's amplitude BEFORE hitting the component
                    traced_this_depth.append({
                        'path': path,
                        'amplitude': beam['amplitude'],
                        'phase': beam.get('accumulated_phase', beam['phase']),
                        'source_type': beam.get('source_type', 'laser')
                    })
                    
                    # If hit a component, record it for processing
                    if hit_component:
                        if hit_component not in component_hits:
                            component_hits[hit_component] = []
                        component_hits[hit_component].append(beam)
            
            # Add this depth's traced beams to results
            all_traced_beams.extend(traced_this_depth)
            
            # First, add all beams to components that accumulate (beam splitters and detectors)
            for component, hitting_beams in component_hits.items():
                if component.component_type in ["beamsplitter", "detector"]:
                    for beam in hitting_beams:
                        component.add_beam(beam)
            
            # Process all components to generate new beams
            next_beams = []
            output_paths = []  # Store output beam paths for visualization
            
            # Process ALL beam splitters (not just those hit this depth)
            for component in components:
                if component.component_type == "beamsplitter" and len(component.incoming_beams) > 0:
                    # Get the position for output beam paths
                    bs_pos = component.position
                    
                    # Finalize processing with amplitude accumulation
                    output_beams = component.finalize_frame()
                    
                    # Create paths for output beams
                    for out_beam in output_beams:
                        # Create a short path segment for the output beam
                        output_path = [bs_pos, out_beam['position']]
                        output_paths.append({
                            'path': output_path,
                            'amplitude': out_beam['amplitude'],
                            'phase': out_beam['phase'],
                            'source_type': out_beam.get('source_type', 'laser')
                        })
                    
                    next_beams.extend(output_beams)
            
            # Process other components (mirrors only - detectors accumulate)
            for component, hitting_beams in component_hits.items():
                if component.component_type not in ["beamsplitter", "detector"]:
                    for beam in hitting_beams:
                        # Pass the beam with its accumulated phase
                        beam_to_process = beam.copy()
                        beam_to_process['phase'] = beam.get('accumulated_phase', beam['phase'])
                        
                        output_beams = component.process_beam(beam_to_process)
                        
                        # Propagate accumulated phase and path length to output beams
                        for out_beam in output_beams:
                            out_beam['accumulated_phase'] = out_beam['phase']
                            out_beam['total_path_length'] = beam.get('total_path_length', 0)
                            
                            # Create a short path for the output beam
                            output_path = [component.position, out_beam['position']]
                            output_paths.append({
                                'path': output_path,
                                'amplitude': out_beam['amplitude'],
                                'phase': out_beam['phase'],
                                'source_type': out_beam.get('source_type', 'laser')
                            })
                        
                        next_beams.extend(output_beams)
            
            # Add output paths to traced beams (these show the correct amplitudes)
            all_traced_beams.extend(output_paths)
            
            # Continue with next depth
            current_beams = next_beams
        
        # Finalize all components that accumulate beams (detectors)
        for comp in components:
            if hasattr(comp, 'finalize_frame'):
                comp.finalize_frame()
        
        return all_traced_beams
    
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
            
            # Check grid bounds (stop at canvas edges)
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
                # Check if beam will hit this component
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
            
            # Add intermediate points for smooth rendering every 10 pixels
            if int(distance) % 10 == 0:
                path.append(Vector2(current_pos.x, current_pos.y))
        
        # Reached max distance
        path.append(current_pos)
        return path, None, total_path_length
    
    def _calculate_edge_intersection(self, start, end, x_min, y_min, x_max, y_max):
        """Calculate intersection point with grid boundary."""
        # Check each edge
        edges = [
            # Left edge
            (Vector2(x_min, y_min), Vector2(x_min, y_max)),
            # Right edge
            (Vector2(x_max, y_min), Vector2(x_max, y_max)),
            # Top edge
            (Vector2(x_min, y_min), Vector2(x_max, y_min)),
            # Bottom edge
            (Vector2(x_min, y_max), Vector2(x_max, y_max))
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
