"""Component management module with sound support and grid-based positioning."""
import logging
from components.laser import Laser
from components.beam_splitter import BeamSplitter
from components.mirror import Mirror
from components.flat_mirror import FlatMirror
from components.detector import Detector
from utils.vector import Vector2
import config.settings as _settings

logger = logging.getLogger(__name__)

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
        logger.debug("Adding component: %s at (%d, %d)", comp_type, x, y)
        
        # Calculate grid position from screen coordinates
        grid_x = (x - _settings.CANVAS_OFFSET_X) // _settings.GRID_SIZE
        grid_y = (y - _settings.CANVAS_OFFSET_Y) // _settings.GRID_SIZE
        
        # Ensure the component is centered in the grid cell
        centered_x = _settings.CANVAS_OFFSET_X + grid_x * _settings.GRID_SIZE + _settings.GRID_SIZE // 2
        centered_y = _settings.CANVAS_OFFSET_Y + grid_y * _settings.GRID_SIZE + _settings.GRID_SIZE // 2
        
        logger.debug("Grid position: (%d, %d) -> centered: (%d, %d)", grid_x, grid_y, centered_x, centered_y)
        
        if comp_type == 'laser':
            # Move existing laser instead of creating new one
            if laser:
                laser.position = Vector2(centered_x, centered_y)  # Use centered position
                self.effects.add_placement_effect(centered_x, centered_y)
                if self.sound_manager:
                    self.sound_manager.play('place_component')
                logger.debug("Laser moved to grid (%d, %d)", grid_x, grid_y)
                
                # Reset all components when laser moves
                self._reset_all_components()
                
                return  # No scoring for placement
            else:
                logger.warning("No laser to move")
                return
        elif comp_type in ('beamsplitter', 'beamsplitter/'):
            orient = '/' if comp_type.endswith('/') else '\\'
            comp = BeamSplitter(centered_x, centered_y, orientation=orient)
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
        elif comp_type == 'mirror|':
            comp = FlatMirror(centered_x, centered_y, '|')
            self.components.append(comp)
            self.component_grid_positions.append({'type': comp_type, 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        elif comp_type == 'mirror-':
            comp = FlatMirror(centered_x, centered_y, '-')
            self.components.append(comp)
            self.component_grid_positions.append({'type': comp_type, 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        elif comp_type == 'detector':
            comp = Detector(centered_x, centered_y)  # Use centered position
            self.components.append(comp)
            self.component_grid_positions.append({'type': comp_type, 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        elif comp_type.startswith('laser_'):
            # Additional laser source with direction (for HOM etc.)
            # e.g. 'laser_right', 'laser_down', 'laser_left', 'laser_up'
            direction = comp_type.split('_', 1)[1] if '_' in comp_type else 'right'
            comp = Laser(centered_x, centered_y, direction=direction)
            self.components.append(comp)
            self.component_grid_positions.append({'type': comp_type, 'grid_x': grid_x, 'grid_y': grid_y})
            if self.sound_manager:
                self.sound_manager.play('place_component')
        else:
            logger.warning("Unknown component type: %s", comp_type)
            return
        
        # Reset all components when adding new ones
        self._reset_all_components()
        
        self.effects.add_placement_effect(centered_x, centered_y)
        
        if comp_type != 'laser':
            logger.debug("Total components: %d, placed at grid (%d, %d)", len(self.components), grid_x, grid_y)
    
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
        elif laser and laser.position.distance_to(Vector2(x, y)) < _settings.GRID_SIZE:
            return True
        
        # Check components
        for comp in self.components:
            if comp.position.distance_to(Vector2(x, y)) < _settings.GRID_SIZE:
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
            centered_x = _settings.CANVAS_OFFSET_X + default_grid_x * _settings.GRID_SIZE + _settings.GRID_SIZE // 2
            centered_y = _settings.CANVAS_OFFSET_Y + default_grid_y * _settings.GRID_SIZE + _settings.GRID_SIZE // 2
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
        logger.debug("Resetting all components due to setup change")
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
        logger.debug("Updating %d component positions (offset: %d,%d, grid: %d)",
                     len(self.components), _settings.CANVAS_OFFSET_X, _settings.CANVAS_OFFSET_Y, _settings.GRID_SIZE)
        
        for i, (comp, grid_pos) in enumerate(zip(self.components, self.component_grid_positions)):
            # Calculate new screen position from grid position (centered in cell)
            new_x = _settings.CANVAS_OFFSET_X + grid_pos['grid_x'] * _settings.GRID_SIZE + _settings.GRID_SIZE // 2
            new_y = _settings.CANVAS_OFFSET_Y + grid_pos['grid_y'] * _settings.GRID_SIZE + _settings.GRID_SIZE // 2
            
            old_pos = comp.position.tuple()
            comp.position = Vector2(new_x, new_y)
            
            logger.debug("  Component %d (%s): grid (%d,%d) -> screen (%d,%d) [was %s]",
                         i, grid_pos['type'], grid_pos['grid_x'], grid_pos['grid_y'], new_x, new_y, old_pos)
        
        # Reset all components after position update
        self._reset_all_components()