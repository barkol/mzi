"""Component management module."""
from components.laser import Laser
from components.beam_splitter import BeamSplitter
from components.mirror import Mirror
from components.detector import Detector
from utils.vector import Vector2
from config.settings import GRID_SIZE, PLACEMENT_SCORE

class ComponentManager:
    """Manages game components - adding, removing, and tracking."""
    
    def __init__(self, effects_manager):
        self.components = []
        self.effects = effects_manager
    
    def add_component(self, comp_type, x, y, laser=None):
        """Add a component to the game."""
        print(f"Adding component: {comp_type} at ({x}, {y})")  # Debug
        
        if comp_type == 'laser':
            # Move existing laser instead of creating new one
            if laser:
                laser.position = Vector2(x, y)
                self.effects.add_placement_effect(x, y)
                print("Laser moved")
                
                # Clear OPD from all beam splitters when laser moves
                self._clear_opd_data()
                
                return 0  # Don't add score for moving
            else:
                # This shouldn't happen in normal flow
                print("Warning: No laser to move")
                return 0
        elif comp_type == 'beamsplitter':
            # Beam splitters always include π/2 phase shift on reflection
            comp = BeamSplitter(x, y)
            self.components.append(comp)
        elif comp_type == 'mirror/':
            comp = Mirror(x, y, '/')
            self.components.append(comp)
        elif comp_type == 'mirror\\':
            comp = Mirror(x, y, '\\')
            self.components.append(comp)
        elif comp_type == 'detector':
            comp = Detector(x, y)
            self.components.append(comp)
        else:
            print(f"Unknown component type: {comp_type}")  # Debug
            return 0
        
        # Clear OPD when adding new components that might affect the path
        if comp_type in ['beamsplitter', 'mirror/', 'mirror\\']:
            self._clear_opd_data()
        
        self.effects.add_placement_effect(x, y)
        
        if comp_type != 'laser':
            print(f"Total components: {len(self.components)}")  # Debug
            
        return PLACEMENT_SCORE
    
    def remove_component_at(self, pos):
        """Remove component at position."""
        for i, comp in enumerate(self.components):
            if comp.contains_point(pos[0], pos[1]):
                # Clear OPD data if removing a beam splitter
                if comp.component_type == 'beamsplitter':
                    comp.last_opd = None
                    comp.last_phase_diff = None
                
                self.components.pop(i)
                
                # Clear OPD from all beam splitters when setup changes
                self._clear_opd_data()
                
                return -PLACEMENT_SCORE
        return 0
    
    def is_position_occupied(self, x, y, laser=None, dragging_laser=False):
        """Check if position is occupied."""
        # When dragging laser, don't count its current position as occupied
        if dragging_laser and laser:
            # Skip laser position check when moving laser
            pass
        elif laser and laser.position.distance_to(Vector2(x, y)) < GRID_SIZE:
            return True
        
        # Check components
        for comp in self.components:
            if comp.position.distance_to(Vector2(x, y)) < GRID_SIZE:
                return True
        
        return False
    
    def clear_all(self, laser):
        """Clear all components."""
        self.components.clear()
        # Keep the laser but move it back to default position
        if laser:
            from config.settings import CANVAS_OFFSET_X, CANVAS_OFFSET_Y, GRID_SIZE
            laser.position = Vector2(CANVAS_OFFSET_X + GRID_SIZE, CANVAS_OFFSET_Y + 7 * GRID_SIZE)
        return PLACEMENT_SCORE  # Reset to initial score
    
    def check_solution(self, laser):
        """Check if player has built a valid interferometer."""
        if not laser:
            print("No laser placed!")
            return False
            
        beam_splitters = sum(1 for c in self.components if c.component_type == 'beamsplitter')
        mirrors = sum(1 for c in self.components if c.component_type == 'mirror')
        detectors = sum(1 for c in self.components if c.component_type == 'detector')
        
        if beam_splitters >= 2 and mirrors >= 2 and detectors >= 1:
            self.effects.add_success_message()
            return True
        return False
    
    def set_debug_mode(self, debug_state):
        """Set debug mode for all components."""
        for comp in self.components:
            comp.debug = debug_state
    
    def _clear_opd_data(self):
        """Clear OPD data from all beam splitters."""
        for c in self.components:
            if c.component_type == 'beamsplitter' and hasattr(c, 'last_opd'):
                c.last_opd = None
                c.last_phase_diff = None