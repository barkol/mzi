"""Physics engine for beam propagation."""
import math
from utils.vector import Vector2
from config.settings import WAVELENGTH

class BeamTracer:
    """Traces beam paths through optical components."""
    
    def __init__(self):
        self.active_beams = []
        self.beam_splitter_cache = {}
        self.k = 2 * math.pi / WAVELENGTH  # Wave number
    
    def reset(self):
        """Reset beam tracer for new frame."""
        self.active_beams = []
        self.beam_splitter_cache.clear()
    
    def add_beam(self, beam):
        """Add a beam to trace."""
        self.active_beams.append(beam)
    
    def trace_beams(self, components, max_depth=10):
        """Trace all beams through components."""
        traced_beams = []
        beams_to_process = self.active_beams.copy()
        processed = set()
        
        depth = 0
        while beams_to_process and depth < max_depth:
            new_beams = []
            
            for beam in beams_to_process:
                # Create unique beam key
                beam_key = (
                    round(beam['position'].x),
                    round(beam['position'].y),
                    round(beam['direction'].x, 2),
                    round(beam['direction'].y, 2),
                    depth
                )
                
                if beam_key in processed:
                    continue
                
                processed.add(beam_key)
                
                # Trace beam path
                path, hit_component = self._trace_single_beam(beam, components)
                
                if path:
                    traced_beams.append({
                        'path': path,
                        'amplitude': beam['amplitude'],
                        'phase': beam['phase'],
                        'source_type': beam.get('source_type', 'laser')
                    })
                
                # Process component interaction
                if hit_component:
                    output_beams = self._process_component_hit(
                        beam, hit_component, path[-1] if path else beam['position']
                    )
                    new_beams.extend(output_beams)
            
            beams_to_process = new_beams
            depth += 1
        
        return traced_beams
    
    def _trace_single_beam(self, beam, components):
        """Trace a single beam until it hits a component or leaves bounds."""
        path = [beam['position']]
        current_pos = beam['position']
        direction = beam['direction']
        
        step_size = 2
        max_distance = 1000
        distance = 0
        
        while distance < max_distance:
            # Move beam
            next_pos = current_pos + direction * step_size
            distance += step_size
            
            # Check bounds
            if (next_pos.x < 0 or next_pos.x > 1400 or 
                next_pos.y < 0 or next_pos.y > 800):
                path.append(next_pos)
                return path, None
            
            # Check component collision
            for comp in components:
                if comp.contains_point(next_pos.x, next_pos.y):
                    path.append(comp.position)
                    
                    # Update phase based on path length
                    beam['phase'] += self.k * current_pos.distance_to(comp.position)
                    
                    return path, comp
            
            current_pos = next_pos
            
            # Add intermediate points for smooth drawing
            if distance % 20 == 0:
                path.append(current_pos)
        
        path.append(current_pos)
        return path, None
    
    def _process_component_hit(self, beam, component, hit_position):
        """Process beam hitting a component."""
        # Handle beam splitters specially for interference
        if component.component_type == "beamsplitter":
            bs_key = (component.position.x, component.position.y)
            
            if bs_key not in self.beam_splitter_cache:
                self.beam_splitter_cache[bs_key] = []
            
            self.beam_splitter_cache[bs_key].append(beam)
            
            # Process immediately if we have 2 beams
            if len(self.beam_splitter_cache[bs_key]) >= 2:
                beams = self.beam_splitter_cache[bs_key][:2]
                self.beam_splitter_cache[bs_key] = []
                component.pending_beams = beams
        
        # Process beam through component
        return component.process_beam(beam)
