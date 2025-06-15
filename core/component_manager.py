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
        
        # Ensure the component is centered in the grid cell
        centered_x = CANVAS_OFFSET_X + grid_x * GRID_SIZE + GRID_SIZE // 2
        centered_y = CANVAS_OFFSET_Y + grid_y * GRID_SIZE + GRID_SIZE // 2
        
        print(f"Grid position: ({grid_x}, {grid_y})")
        print(f"Centered position: ({centered_x}, {centered_y})")
        
        if comp_type == 'laser':
            # Move existing laser instead of creating new one
            if laser:
                laser.position = Vector2(centered_x, centered_y)  # Use centered position
                self.effects.add_placement_effect(centered_x, centered_y)
                if self.sound_manager:
                    self.sound_manager.play('place_component')
                print(f"Laser moved to grid ({grid_x}, {grid_y})")
                
                # Reset all components when laser moves
                self._reset_all_components()
                
                return  # No scoring for placement
            else:
                # This shouldn't happen in normal flow
                print("Warning: No laser to move")
                return
        elif comp_type == 'beamsplitter':
            # Beam splitters always include π/2 phase shift on reflection
            comp = BeamSplitter(centered_x, centered_y)  # Use centered position
            self.components.append(comp)
            self.component_grid_positions.append({'type': comp_type, 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        elif comp_type == 'mirror/':
            comp = Mirror(centered_x, centered_y, '/')  # Use centered position
            self.components.append(comp)
            self.component_grid_positions.append({'type': 'mirror/', 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        elif comp_type == 'mirror\\':
            comp = Mirror(centered_x, centered_y, '\\')  # Use centered position
            self.components.append(comp)
            self.component_grid_positions.append({'type': 'mirror\\', 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        elif comp_type == 'detector':
            comp = Detector(centered_x, centered_y)  # Use centered position
            self.components.append(comp)
            self.component_grid_positions.append({'type': comp_type, 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        else:
            print(f"Unknown component type: {comp_type}")  # Debug
            return
        
        # Reset all components when adding new ones
        self._reset_all_components()
        
        self.effects.add_placement_effect(centered_x, centered_y)
        
        if comp_type != 'laser':
            print(f"Total components: {len(self.components)}")  # Debug
            print(f"Component placed at grid position ({grid_x}, {grid_y})")
    
    def remove_component_at(self, pos):
        """Remove component at position."""
        for i, comp in enumerate(self.components):
            if comp.contains_point(pos[0], pos[1]):
                self.components.pop(i)
                self.component_grid_positions.pop(i)
                
                # Play removal sound
                if self.sound_manager:
                    self.sound_manager.play('remove_component')
                
                # Reset all remaining components when setup changes
                self._reset_all_components()
                
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
        
        # Keep the laser but move it back to default position (centered in grid cell)
        if laser:
            # Calculate centered position for default laser location
            default_grid_x = 1
            default_grid_y = 7
            centered_x = CANVAS_OFFSET_X + default_grid_x * GRID_SIZE + GRID_SIZE // 2
            centered_y = CANVAS_OFFSET_Y + default_grid_y * GRID_SIZE + GRID_SIZE // 2
            laser.position = Vector2(centered_x, centered_y)
        
        # Play clear sound
        if self.sound_manager:
            self.sound_manager.play('remove_component')
        
        # No score returned - scoring is based on detector power

    def set_debug_mode(self, debug_state):
        """Set debug mode for all components."""
        for comp in self.components:
            comp.debug = debug_state
    
    def _reset_all_components(self):
        """Reset all components to clear their accumulated state."""
        print("Resetting all components due to setup change")
        for comp in self.components:
            if hasattr(comp, 'reset_frame'):
                comp.reset_frame()
            # Clear any cached data
            if hasattr(comp, 'last_opd'):
                comp.last_opd = None
            if hasattr(comp, 'last_phase_diff'):
                comp.last_phase_diff = None
            # Reset detector intensities immediately
            if comp.component_type == 'detector':
                comp.intensity = 0
                comp.incoming_beams = []
    
    def update_component_positions(self):
        """Update all component positions based on their grid positions and current scale."""
        print(f"Updating {len(self.components)} component positions with scale")
        print(f"Canvas offset: ({CANVAS_OFFSET_X}, {CANVAS_OFFSET_Y}), Grid size: {GRID_SIZE}")
        
        for i, (comp, grid_pos) in enumerate(zip(self.components, self.component_grid_positions)):
            # Calculate new screen position from grid position (centered in cell)
            new_x = CANVAS_OFFSET_X + grid_pos['grid_x'] * GRID_SIZE + GRID_SIZE // 2
            new_y = CANVAS_OFFSET_Y + grid_pos['grid_y'] * GRID_SIZE + GRID_SIZE // 2
            
            old_pos = comp.position.tuple()
            comp.position = Vector2(new_x, new_y)
            
            print(f"  Component {i} ({grid_pos['type']}): grid ({grid_pos['grid_x']}, {grid_pos['grid_y']}) -> screen ({new_x}, {new_y}) [was {old_pos}]")
        
        # Reset all components after position update
        self._reset_all_components()