"""Component management module with sound support and grid-based positioning."""
from components.laser import Laser
from components.beam_splitter import BeamSplitter
from components.mirror import Mirror
from components.detector import Detector
from utils.vector import Vector2
from config.settings import GRID_SIZE, CANVAS_OFFSET_X, CANVAS_OFFSET_Y

class ComponentManager:
    """Manages game components - adding, removing, and tracking with scaling support."""
    
    def __init__(self, effects_manager, sound_manager=None):
        self.components = []
        self.effects = effects_manager
        self.sound_manager = sound_manager
        # Store component grid positions for scaling
        self.component_grid_positions = []
    
    def add_component(self, comp_type, x, y, laser=None):
        """Add a component to the game."""
        print(f"Adding component: {comp_type} at ({x}, {y})")  # Debug
        
        # Calculate grid position from screen coordinates
        grid_x = round((x - CANVAS_OFFSET_X) / GRID_SIZE)
        grid_y = round((y - CANVAS_OFFSET_Y) / GRID_SIZE)
        
        if comp_type == 'laser':
            # Move existing laser instead of creating new one
            if laser:
                laser.position = Vector2(x, y)
                self.effects.add_placement_effect(x, y)
                if self.sound_manager:
                    self.sound_manager.play('place_component')
                print(f"Laser moved to grid ({grid_x}, {grid_y})")
                
                # Clear OPD from all beam splitters when laser moves
                self._clear_opd_data()
                
                return  # No scoring for placement
            else:
                # This shouldn't happen in normal flow
                print("Warning: No laser to move")
                return
        elif comp_type == 'beamsplitter':
            # Beam splitters always include π/2 phase shift on reflection
            comp = BeamSplitter(x, y)
            self.components.append(comp)
            self.component_grid_positions.append({'type': comp_type, 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        elif comp_type == 'mirror/':
            comp = Mirror(x, y, '/')
            self.components.append(comp)
            self.component_grid_positions.append({'type': 'mirror/', 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        elif comp_type == 'mirror\\':
            comp = Mirror(x, y, '\\')
            self.components.append(comp)
            self.component_grid_positions.append({'type': 'mirror\\', 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        elif comp_type == 'detector':
            comp = Detector(x, y)
            self.components.append(comp)
            self.component_grid_positions.append({'type': comp_type, 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        else:
            print(f"Unknown component type: {comp_type}")  # Debug
            return
        
        # Clear OPD when adding new components that might affect the path
        if comp_type in ['beamsplitter', 'mirror/', 'mirror\\']:
            self._clear_opd_data()
        
        self.effects.add_placement_effect(x, y)
        
        if comp_type != 'laser':
            print(f"Total components: {len(self.components)}")  # Debug
            print(f"Component placed at grid position ({grid_x}, {grid_y})")
    
    def remove_component_at(self, pos):
        """Remove component at position."""
        for i, comp in enumerate(self.components):
            if comp.contains_point(pos[0], pos[1]):
                # Clear OPD data if removing a beam splitter
                if comp.component_type == 'beamsplitter':
                    comp.last_opd = None
                    comp.last_phase_diff = None
                
                self.components.pop(i)
                self.component_grid_positions.pop(i)
                
                # Play removal sound
                if self.sound_manager:
                    self.sound_manager.play('remove_component')
                
                # Clear OPD from all beam splitters when setup changes
                self._clear_opd_data()
                
                return True  # Return success instead of score
        return False  # No component removed
    
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
        # Clean up any detector sounds first
        if self.sound_manager and hasattr(self.sound_manager, 'detector_channels'):
            self.sound_manager.cleanup_detector_sounds(set())
        
        self.components.clear()
        self.component_grid_positions.clear()
        
        # Keep the laser but move it back to default position
        if laser:
            # Use current scaled values
            laser.position = Vector2(CANVAS_OFFSET_X + GRID_SIZE, 
                                   CANVAS_OFFSET_Y + 7 * GRID_SIZE)
        
        # Play clear sound
        if self.sound_manager:
            self.sound_manager.play('remove_component')
        
        # No score returned - scoring is based on detector power

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
    
    def update_component_positions(self):
        """Update all component positions based on their grid positions and current scale."""
        print(f"Updating {len(self.components)} component positions with scale")
        print(f"Canvas offset: ({CANVAS_OFFSET_X}, {CANVAS_OFFSET_Y}), Grid size: {GRID_SIZE}")
        
        for i, (comp, grid_pos) in enumerate(zip(self.components, self.component_grid_positions)):
            # Calculate new screen position from grid position
            new_x = CANVAS_OFFSET_X + grid_pos['grid_x'] * GRID_SIZE
            new_y = CANVAS_OFFSET_Y + grid_pos['grid_y'] * GRID_SIZE
            
            old_pos = comp.position.tuple()
            comp.position = Vector2(new_x, new_y)
            
            print(f"  Component {i} ({grid_pos['type']}): grid ({grid_pos['grid_x']}, {grid_pos['grid_y']}) -> screen ({new_x}, {new_y}) [was {old_pos}]")