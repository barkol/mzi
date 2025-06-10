"""Main game logic and state management with sound effects, energy monitoring, and scaling support."""
import pygame
import os
import math
from components.laser import Laser
from core.grid import Grid
from core.physics import BeamTracer
from core.beam_renderer import BeamRenderer
from core.component_manager import ComponentManager
from core.keyboard_handler import KeyboardHandler
from core.debug_display import DebugDisplay
from core.challenge_manager import ChallengeManager
from core.leaderboard import LeaderboardManager
from core.sound_manager import SoundManager
from ui.sidebar import Sidebar
from ui.controls import ControlPanel
from ui.effects import EffectsManager
from ui.leaderboard_display import LeaderboardDisplay
from ui.right_panel import RightPanel
from utils.vector import Vector2
from utils.assets_loader import AssetsLoader
from config.settings import (
    BLACK, WHITE, PURPLE, CYAN, MAGENTA, RED, GREEN, DARK_PURPLE,
    GRID_COLOR, GRID_MAJOR_COLOR, HOVER_VALID_COLOR, HOVER_INVALID_COLOR,
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    GRID_SIZE, CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_OFFSET_X, CANVAS_OFFSET_Y,
    COMPONENT_RADIUS, BEAM_WIDTH,
    WAVELENGTH, SPEED_OF_LIGHT,
    MIRROR_LOSS, BEAM_SPLITTER_LOSS, DETECTOR_DECAY_RATE,
    IDEAL_COMPONENTS, REALISTIC_BEAM_SPLITTER,
    PLACEMENT_SCORE, COMPLETION_SCORE,
    # New imports for scaling
    scale, scale_font, update_scaled_values,
    BASE_GRID_SIZE, BASE_CANVAS_WIDTH, BASE_CANVAS_HEIGHT,
    BASE_CANVAS_OFFSET_X, BASE_CANVAS_OFFSET_Y,
    BASE_COMPONENT_RADIUS, BASE_BEAM_WIDTH,
    SCALE_FACTOR, FONT_SCALE,
    # New imports for dynamic canvas
    CANVAS_GRID_COLS, CANVAS_GRID_ROWS, IS_FULLSCREEN
)

# Define GOLD color if not already defined
GOLD = (255, 215, 0)

class Game:
    """Main game class with sound support, energy monitoring, and scaling."""
    # Updated __init__ method for core/game.py (partial)

    def __init__(self, screen, scale_factor=1.0):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.scale_factor = scale_factor
        
        # Initialize sound manager first
        self.sound_manager = SoundManager(volume=0.7)
        self.sound_manager.start_ambient()
        
        # Load assets
        self.assets_loader = AssetsLoader()
        
        # Game components - use dynamic positioning
        # Center laser vertically based on actual canvas rows
        laser_x = CANVAS_OFFSET_X + GRID_SIZE
        laser_row = CANVAS_GRID_ROWS // 2  # Center vertically in dynamic grid
        laser_y = CANVAS_OFFSET_Y + laser_row * GRID_SIZE
        self.laser = Laser(laser_x, laser_y)
        
        # Helper modules
        self.effects = EffectsManager()
        self.component_manager = ComponentManager(self.effects, self.sound_manager)
        self.beam_renderer = BeamRenderer(self.screen)
        self.debug_display = DebugDisplay(self.screen)
        self.debug_display.set_assets_loader(self.assets_loader)
        self.challenge_manager = ChallengeManager()
        
        # Leaderboard system
        self.leaderboard_manager = LeaderboardManager()
        self.leaderboard_display = LeaderboardDisplay(self.leaderboard_manager, self.sound_manager)
        
        # UI elements with sound support
        self.grid = Grid()
        self.sidebar = Sidebar(self.sound_manager)
        self.controls = ControlPanel(self.sound_manager)
        self.right_panel = RightPanel(self.sound_manager)
        
        # Set up sidebar callback for component limits
        self.sidebar.set_can_add_callback(self._can_add_component)
        
        # Physics
        self.beam_tracer = BeamTracer()
        
        # Keyboard handler
        self.keyboard_handler = KeyboardHandler(self)
        
        # Game state
        self.dragging = False
        self.drag_component = None
        self.mouse_pos = (0, 0)
        self.score = 0
        self.controls.score = self.score
        if hasattr(self.controls, 'set_gold_bonus'):
            self.controls.set_gold_bonus(0)
        self.show_opd_info = True
        
        # Track session high score and completed challenges
        self.session_high_score = 0
        self.completed_challenges = set()
        
        # Challenge display state
        self.current_challenge_display_name = None
        
        # Track gold field hits for sound
        self.last_gold_hits = {}
        
        # Load gold fields first
        self.challenge_manager.load_gold_fields()
        
        # Load blocked fields
        self.challenge_manager.load_blocked_fields()
        
        # Validate configuration
        self.challenge_manager.validate_field_configurations()
        
        # Set initial field configuration in controls
        self.controls.set_field_config("Default Fields")
        
        # NOTE: Removed file creation - just search for existing configurations
        # The challenge manager will only search for and load existing field configuration files
        
        # Load default challenge
        challenges = self.challenge_manager.get_challenge_list()
        if challenges:
            for name, title in challenges:
                if name == "basic_mz":
                    self.challenge_manager.set_current_challenge(name)
                    self.current_challenge_display_name = title
                    self.controls.set_challenge(title)
                    if hasattr(self.controls, 'set_challenge_completed'):
                        self.controls.set_challenge_completed(False)
                    if hasattr(self.controls, 'set_gold_bonus'):
                        self.controls.set_gold_bonus(0)
                    self.right_panel.add_debug_message(f"Loaded challenge: {title}")
                    break
        
        # Show scoring formula
        self.controls.set_status("Score = Detector Power × 1000 + Gold Bonus")
        
        # Log initial canvas configuration
        self.right_panel.add_debug_message(f"Canvas: {CANVAS_GRID_COLS}×{CANVAS_GRID_ROWS} cells")
        self.right_panel.add_debug_message(f"Display: {'Fullscreen' if IS_FULLSCREEN else 'Windowed'}")


    def update_scale(self, new_scale_factor):
        """Update the scale factor and all dependent values."""
        self.scale_factor = new_scale_factor
        
        # Update laser position based on new grid dimensions
        laser_x = CANVAS_OFFSET_X + GRID_SIZE
        laser_row = CANVAS_GRID_ROWS // 2  # Use dynamic row count
        laser_y = CANVAS_OFFSET_Y + laser_row * GRID_SIZE
        self.laser.position = Vector2(laser_x, laser_y)
        
        # Clear components to avoid scaling issues
        self.component_manager.clear_all(self.laser)
        
        # Update UI components
        self.grid = Grid()
        self.sidebar = Sidebar(self.sound_manager)
        self.controls = ControlPanel(self.sound_manager)
        self.right_panel = RightPanel(self.sound_manager)
        
        # Update leaderboard display position
        self.leaderboard_display.update_scale()
        
        # Clear asset cache
        self.assets_loader.clear_cache()
        
        # Log the new canvas configuration
        print(f"Canvas updated: {CANVAS_GRID_COLS}×{CANVAS_GRID_ROWS} cells")
        print(f"Grid size: {GRID_SIZE}px")
        print(f"Display mode: {'Fullscreen' if IS_FULLSCREEN else 'Windowed'}")
        self.right_panel.add_debug_message(f"Canvas: {CANVAS_GRID_COLS}×{CANVAS_GRID_ROWS} cells")
        self.right_panel.add_debug_message(f"Grid: {GRID_SIZE}px")
        self.right_panel.add_debug_message(f"Display: {'Fullscreen' if IS_FULLSCREEN else 'Windowed'}")

    def update_screen_references(self, new_screen, actual_screen=None):
        """Update all screen references when display mode changes."""
        self.screen = new_screen
        self._actual_screen = actual_screen or new_screen
        
        # Update beam renderer
        if hasattr(self, 'beam_renderer'):
            self.beam_renderer.screen = new_screen
        
        # Update debug display
        if hasattr(self, 'debug_display'):
            self.debug_display.screen = new_screen
            if hasattr(actual_screen, 'get_size'):
                self.debug_display._actual_screen_size = actual_screen.get_size()
            elif hasattr(new_screen, 'get_size'):
                self.debug_display._actual_screen_size = new_screen.get_size()
            else:
                self.debug_display._actual_screen_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Clear asset cache
        if hasattr(self, 'assets_loader'):
            self.assets_loader.clear_cache()
    
    def get_canvas_info(self):
        """Get current canvas configuration info."""
        return {
            'grid_cols': CANVAS_GRID_COLS,
            'grid_rows': CANVAS_GRID_ROWS,
            'canvas_width': CANVAS_WIDTH,
            'canvas_height': CANVAS_HEIGHT,
            'grid_size': GRID_SIZE,
            'is_fullscreen': IS_FULLSCREEN
        }
    
    def handle_event(self, event):
        """Handle game events."""
        # Handle right panel events first
        if self.right_panel.handle_event(event):
            return
            
        # Handle leaderboard events
        if self.leaderboard_display.handle_event(event):
            return
        
        # Handle keyboard events
        if self.keyboard_handler.handle_key(event):
            return
        
        # Update mouse position
        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            
            # Update grid hover if dragging
            if self.sidebar.dragging:
                self.grid.set_hover(event.pos)
            else:
                self.grid.set_hover(None)
        
        # Handle component drop BEFORE sidebar processes the event
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # Check if we were dragging something
            if self.sidebar.dragging and self.sidebar.selected and self._is_in_canvas(event.pos):
                # Place component at grid position
                x = round((event.pos[0] - CANVAS_OFFSET_X) / GRID_SIZE) * GRID_SIZE + CANVAS_OFFSET_X
                y = round((event.pos[1] - CANVAS_OFFSET_Y) / GRID_SIZE) * GRID_SIZE + CANVAS_OFFSET_Y
                
                # Check component limits
                if self.sidebar.selected != 'laser' and not self._can_add_component():
                    self.controls.set_status("Component limit reached for this challenge!")
                    self.right_panel.add_debug_message("Cannot add component - limit reached")
                    self.sound_manager.play('invalid_placement')
                elif self.challenge_manager.is_position_blocked(x, y):
                    self.controls.set_status("Cannot place component here - position blocked!")
                    self.sound_manager.play('beam_blocked')
                    print(f"Position ({x}, {y}) is blocked")
                elif not self.component_manager.is_position_occupied(x, y, self.laser,
                                                                  self.sidebar.selected == 'laser'):
                    # Reset gold collection when any component is placed (changes beam paths)
                    self.beam_tracer.reset_gold_collection()
                    if hasattr(self.controls, 'set_gold_bonus'):
                        self.controls.set_gold_bonus(0)
                    self.last_gold_hits.clear()
                    
                    if self.sidebar.selected == 'laser':
                        self.right_panel.add_debug_message("Gold bonus reset - laser moved")
                    else:
                        self.right_panel.add_debug_message("Gold bonus reset - beam path changed")
                    
                    self.component_manager.add_component(
                        self.sidebar.selected, x, y, self.laser)
                    self.sound_manager.play('drag_end')
                    print(f"Placed {self.sidebar.selected} at ({x}, {y})")
                    self.right_panel.add_debug_message(f"Placed {self.sidebar.selected} at grid ({(x-CANVAS_OFFSET_X)//GRID_SIZE}, {(y-CANVAS_OFFSET_Y)//GRID_SIZE})")
                else:
                    self.sound_manager.play('invalid_placement')
            
            # Clear grid hover after drop
            self.grid.set_hover(None)
        
        # Handle sidebar events
        sidebar_handled = self.sidebar.handle_event(event)
        
        # Clear sidebar selection after handling drop
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and sidebar_handled:
            self.sidebar.clear_selection()
        
        # Handle control panel events
        action = self.controls.handle_event(event)
        if action:
            self._handle_control_action(action)
            return
        
        # Handle canvas clicks (for removing components)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._is_in_canvas(event.pos) and not self.sidebar.selected:
                if self.component_manager.remove_component_at(event.pos):
                    # Reset gold collection when component is removed (changes beam paths)
                    self.beam_tracer.reset_gold_collection()
                    if hasattr(self.controls, 'set_gold_bonus'):
                        self.controls.set_gold_bonus(0)
                    self.last_gold_hits.clear()
                    self.right_panel.add_debug_message("Component removed - gold bonus reset")
    
    def _is_in_canvas(self, pos):
        """Check if position is within game canvas."""
        return (CANVAS_OFFSET_X <= pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH and
                CANVAS_OFFSET_Y <= pos[1] <= CANVAS_OFFSET_Y + CANVAS_HEIGHT)
    
    def _can_add_component(self):
        """Check if we can add another component based on challenge limits."""
        if not self.challenge_manager.current_challenge:
            return True
        
        challenge = self.challenge_manager.challenges.get(self.challenge_manager.current_challenge)
        if not challenge:
            return True
        
        max_components = challenge.get('max_components', float('inf'))
        current_count = len(self.component_manager.components)
        
        return current_count < max_components
    
    def _handle_control_action(self, action):
        """Handle control panel actions."""
        if action == 'Clear All':
            self.component_manager.clear_all(self.laser)
            self.score = 0
            self.controls.score = self.score
            # Reset gold collection
            self.beam_tracer.reset_gold_collection()
            if hasattr(self.controls, 'set_gold_bonus'):
                self.controls.set_gold_bonus(0)
            self.last_gold_hits.clear()
            
            # Reset completed challenges with Shift
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                self.completed_challenges.clear()
                if hasattr(self.controls, 'set_challenge_completed'):
                    self.controls.set_challenge_completed(False)
                if hasattr(self.controls, 'set_gold_bonus'):
                    self.controls.set_gold_bonus(0)
                self.controls.set_status("Setup cleared and challenges reset!")
                self.right_panel.add_debug_message("Session reset - challenges can be completed again")
                self.sound_manager.play('notification')
                print("Completed challenges reset - you can earn points again")
            else:
                self.controls.set_status("Score = Detector Power × 1000 + Gold Bonus")
                self.right_panel.add_debug_message("Setup cleared")
                
        elif action == 'Check Setup':
            # Check against current challenge
            success, message, points = self.challenge_manager.check_setup(
                self.component_manager.components, self.laser, self.beam_tracer)
            if success:
                # Check if this challenge was already completed
                challenge_name = self.challenge_manager.current_challenge
                if challenge_name and challenge_name not in self.completed_challenges:
                    # First time completing
                    self._update_score(points)
                    self.completed_challenges.add(challenge_name)
                    self.effects.add_success_message()
                    self.sound_manager.play('challenge_complete')
                    
                    if hasattr(self.controls, 'set_challenge_completed'):
                        self.controls.set_challenge_completed(True)
                    
                    # Check high score
                    if self.score > self.session_high_score:
                        self.session_high_score = self.score
                        self.sound_manager.play('high_score')
                    
                    # Show leaderboard
                    challenge_info = self.challenge_manager.challenges.get(challenge_name, {})
                    self.leaderboard_display.show(
                        auto_add_score=self.score,
                        challenge=challenge_info.get('name', 'Unknown'),
                        components=len(self.component_manager.components)
                    )
                else:
                    # Already completed
                    self.controls.set_status("Challenge already completed this session!")
                    self.effects.add_info_message("Challenge Complete", "No additional points awarded")
                    self.sound_manager.play('notification')
                    print("Challenge already completed - no additional points awarded")
                
                print(message)
            else:
                self.controls.set_status(f"Failed: {message}")
                self.sound_manager.play('challenge_failed')
                print(f"Challenge check failed: {message}")
                
        elif action == 'Toggle Laser':
            if self.laser:
                self.laser.enabled = not self.laser.enabled
                if self.laser.enabled:
                    self.sound_manager.play('laser_on')
                else:
                    self.sound_manager.play('laser_off')
                    # Clear per-frame gold field tracking when laser is turned off
                    if hasattr(self.beam_tracer, 'gold_field_hits_this_frame'):
                        self.beam_tracer.gold_field_hits_this_frame.clear()
                    # Clear last gold hits for sound tracking
                    self.last_gold_hits.clear()
                    # Note: We do NOT reset gold_field_hits or collected_gold_fields
                    # The gold bonus persists until explicitly reset
                    
        elif action == 'Load Challenge':
            # Cycle through challenges
            challenges = self.challenge_manager.get_challenge_list()
            if challenges:
                current_idx = -1
                if self.challenge_manager.current_challenge:
                    for i, (name, _) in enumerate(challenges):
                        if name == self.challenge_manager.current_challenge:
                            current_idx = i
                            break
                
                # Go to next challenge
                next_idx = (current_idx + 1) % len(challenges)
                challenge_name, challenge_title = challenges[next_idx]
                self.challenge_manager.set_current_challenge(challenge_name)
                self.current_challenge_display_name = challenge_title
                self.controls.set_challenge(challenge_title)
                
                # Update completion status
                is_completed = challenge_name in self.completed_challenges
                if hasattr(self.controls, 'set_challenge_completed'):
                    self.controls.set_challenge_completed(is_completed)
                
                # Reset gold collection when loading new challenge
                self.beam_tracer.reset_gold_collection()
                if hasattr(self.controls, 'set_gold_bonus'):
                    self.controls.set_gold_bonus(0)
                self.last_gold_hits.clear()
                
                self.sound_manager.play('panel_open')
                print(f"Loaded challenge: {challenge_title}")
                self.right_panel.add_debug_message(f"Loaded challenge: {challenge_title}")
                
        elif action == 'Load Fields':
            # Cycle through field configurations
            field_configs = self.challenge_manager.get_available_field_configs()
            print(f"Available field configurations: {len(field_configs)}")
            for config in field_configs:
                print(f"  - {config['name']}: {config['display_name']}")
            
            if field_configs:
                # Find current configuration
                current_idx = -1
                current_config = self.challenge_manager.current_field_config
                for i, config in enumerate(field_configs):
                    if config['name'] == current_config:
                        current_idx = i
                        break
                
                # Go to next configuration
                next_idx = (current_idx + 1) % len(field_configs)
                next_config = field_configs[next_idx]
                
                print(f"Switching from '{current_config}' to '{next_config['name']}'")
                
                # Clear components before loading new field configuration
                self.component_manager.clear_all(self.laser)
                
                # Load the new field configuration
                success = self.challenge_manager.load_field_config(next_config['name'])
                
                if success:
                    # Update UI
                    self.controls.set_field_config(next_config['display_name'])
                    self.sound_manager.play('panel_open')
                    self.right_panel.add_debug_message(f"Loaded fields: {next_config['display_name']}")
                    
                    # Clear score when changing field configuration
                    self.score = 0
                    self.controls.score = self.score
                    # Reset gold collection
                    self.beam_tracer.reset_gold_collection()
                    if hasattr(self.controls, 'set_gold_bonus'):
                        self.controls.set_gold_bonus(0)
                    self.last_gold_hits.clear()
                    
                    # Show status message
                    self.controls.set_status(f"Loaded: {next_config['display_name']}")
                else:
                    self.controls.set_status("Failed to load field configuration!")
                    self.sound_manager.play('error')
                    self.right_panel.add_debug_message("Error loading field configuration")
            else:
                print("No field configurations available!")
                self.controls.set_status("No field configurations available!")
                self.sound_manager.play('error')
    
    def _update_score(self, points):
        """Update game score."""
        self.score = points
        self.controls.score = self.score
        
        # Update session high score
        if self.score > self.session_high_score:
            self.session_high_score = self.score
    
    def update(self, dt):
        """Update game state."""
        self.effects.update(dt)
        
        # Update keyboard handler (for energy monitor)
        self.keyboard_handler.update()
        
        # Update detector sounds
        detectors = [c for c in self.component_manager.components if c.component_type == 'detector']
        for i, detector in enumerate(detectors):
            self.sound_manager.update_detector_sound(
                detector_id=id(detector),
                intensity=detector.intensity,
                position=detector.position.tuple()
            )
        
        # Check for gold field hits this frame and play sounds
        if hasattr(self.beam_tracer, 'gold_field_hits_this_frame'):
            # Play sound only for gold fields that are newly hit (weren't hit last frame)
            for pos, intensity in self.beam_tracer.gold_field_hits_this_frame.items():
                if intensity > 0:
                    # Check if this field was NOT hit in the last frame
                    last_intensity = self.last_gold_hits.get(pos, 0)
                    
                    if last_intensity == 0:  # Field was not hit last frame
                        # Play coin sound - this is a new hit
                        volume = min(0.8, 0.5 + intensity * 0.3)
                        self.sound_manager.play('gold_field_hit', volume=volume)
                        
                        # Check if this is a first-time collection for bonus
                        if pos in self.beam_tracer.collected_gold_fields:
                            self.right_panel.add_debug_message(f"Gold bonus collected at {pos}!")
                        else:
                            self.right_panel.add_debug_message(f"Gold field hit at {pos}")
            
            # Clear entries from last_gold_hits that are not hit this frame
            # This ensures sounds play again when beams re-enter fields
            for pos in list(self.last_gold_hits.keys()):
                if pos not in self.beam_tracer.gold_field_hits_this_frame:
                    del self.last_gold_hits[pos]
            
            # Update tracking for next frame
            self.last_gold_hits = self.beam_tracer.gold_field_hits_this_frame.copy()
        else:
            # No gold field tracking - clear last hits
            self.last_gold_hits.clear()
    
    def draw(self):
        """Draw the game with fixed rendering order."""
        # Update challenge completion status for controls
        if self.challenge_manager.current_challenge and hasattr(self.controls, 'set_challenge_completed'):
            is_completed = self.challenge_manager.current_challenge in self.completed_challenges
            self.controls.set_challenge_completed(is_completed)
        
        # Update gold bonus for controls
        if hasattr(self.beam_tracer, 'gold_field_hits') and hasattr(self.controls, 'set_gold_bonus'):
            total_bonus = 0
            for position, intensity in self.beam_tracer.gold_field_hits.items():
                bonus = round(intensity * 100)
                total_bonus += bonus
            self.controls.set_gold_bonus(total_bonus)
        
        # Clear screen
        self.screen.fill(BLACK)
        
        # Layer 1: Draw banner as the bottom-most layer
        self.debug_display.draw_banner()
        
        # Layer 2: Draw UI panels (sidebar and right panel backgrounds)
        self.sidebar.draw(self.screen)
        self.right_panel.draw(self.screen)
        
        # Layer 3: Draw game area outline (no fill to not obscure grid elements)
        canvas_rect = pygame.Rect(CANVAS_OFFSET_X, CANVAS_OFFSET_Y, CANVAS_WIDTH, CANVAS_HEIGHT)
        pygame.draw.rect(self.screen, PURPLE, canvas_rect, scale(2), border_radius=scale(15))
        
        # Layer 4: Draw game info above canvas
        self._draw_game_info_top()
        
        # Layer 5: Draw challenge name above grid
        self._draw_challenge_name()
        
        # Layer 6: Draw grid (includes gold fields, blocked fields, and grid lines)
        laser_pos = self.laser.position.tuple() if self.laser else None
        self.grid.draw(self.screen, self.component_manager.components, laser_pos,
                      self.challenge_manager.get_blocked_positions(),
                      self.challenge_manager.get_gold_positions())
        
        # Layer 7: Draw laser
        if self.laser:
            self.laser.draw(self.screen)
        
        # Layer 8: Draw components
        for comp in self.component_manager.components:
            comp.draw(self.screen)
        
        # Layer 9: Trace and draw beams
        if self.laser and self.laser.enabled:
            # Set gold positions on beam tracer
            self.beam_tracer.set_gold_positions(self.challenge_manager.get_gold_positions())
            
            # Ensure beam renderer has correct screen reference
            if self.beam_renderer.screen != self.screen:
                print(f"WARNING: Beam renderer screen mismatch! Updating...")
                self.beam_renderer.screen = self.screen
            
            self.beam_renderer.draw_beams(self.beam_tracer, self.laser,
                                        self.component_manager.components,
                                        0,
                                        self.challenge_manager.get_blocked_positions())
        
        # Layer 10: Draw control panel
        self.controls.draw(self.screen)
        
        # Layer 11: Draw dragged component preview
        if self.sidebar.dragging and self.sidebar.selected:
            self._draw_drag_preview()
        
        # Layer 12: Draw effects
        self.effects.draw(self.screen)
        
        # Layer 13: Draw info text and debug info
        self.debug_display.draw_info_text()
        self.debug_display.draw_opd_info(self.component_manager.components, self.show_opd_info)
        
        # Layer 14: Draw session high score
        self._draw_session_high_score()
        
        # Layer 15: Draw challenge completion status
        self._draw_challenge_status()
        
        # Layer 16: Draw component counter in bottom left
        self._draw_component_counter()
        
        # Layer 17: Draw leaderboard if visible (modal overlay)
        self.leaderboard_display.draw(self.screen)
        
        # Layer 18: Draw keyboard handler overlays (energy monitor)
        self.keyboard_handler.draw(self.screen)
        
        # Layer 19: Draw canvas info in fullscreen mode
        if self.debug_display and IS_FULLSCREEN:
            font = pygame.font.Font(None, scale_font(14))
            info_text = f"Canvas: {CANVAS_GRID_COLS}×{CANVAS_GRID_ROWS} | Grid: {GRID_SIZE}px"
            text_surface = font.render(info_text, True, WHITE)
            text_rect = text_surface.get_rect(
                centerx=CANVAS_OFFSET_X + CANVAS_WIDTH // 2,
                bottom=CANVAS_OFFSET_Y - scale(5)
            )
            
            # Solid background for readability
            bg_rect = text_rect.inflate(scale(10), scale(4))
            pygame.draw.rect(self.screen, (40, 40, 40), bg_rect)
            pygame.draw.rect(self.screen, WHITE, bg_rect, 1)
            
            self.screen.blit(text_surface, text_rect)
    
    def _draw_challenge_name(self):
            """Draw the current challenge name above the grid."""
            if self.current_challenge_display_name:
                # Check if current challenge is completed
                is_completed = (self.challenge_manager.current_challenge and
                            self.challenge_manager.current_challenge in self.completed_challenges)
                
                # Use gold color if completed, cyan otherwise
                color = GOLD if is_completed else CYAN
                
                # Prepare main text
                font = pygame.font.Font(None, scale_font(32))
                text = font.render(self.current_challenge_display_name, True, color)
                text_rect = text.get_rect(centerx=CANVAS_OFFSET_X + CANVAS_WIDTH // 2,
                                        y=CANVAS_OFFSET_Y - scale(65))
                
                # Background rect
                bg_rect = text_rect.inflate(scale(40), scale(12))
                
                # Draw solid background
                pygame.draw.rect(self.screen, (20, 20, 20), bg_rect, border_radius=scale(15))
                
                # Draw border
                pygame.draw.rect(self.screen, color, bg_rect, scale(3), border_radius=scale(15))
                
                # Draw the main text
                self.screen.blit(text, text_rect)
                
                # Add decorative elements
                # Left decoration
                deco_left = pygame.Rect(bg_rect.left - scale(50), bg_rect.centery - scale(1), scale(40), scale(2))
                pygame.draw.rect(self.screen, color, deco_left)
                pygame.draw.circle(self.screen, color, (deco_left.left, deco_left.centery), scale(3))
                
                # Right decoration
                deco_right = pygame.Rect(bg_rect.right + scale(10), bg_rect.centery - scale(1), scale(40), scale(2))
                pygame.draw.rect(self.screen, color, deco_right)
                pygame.draw.circle(self.screen, color, (deco_right.right, deco_right.centery), scale(3))
                
                # Add completed indicator if applicable
                if is_completed:
                    # Prepare DONE text
                    done_font = pygame.font.Font(None, scale_font(20))
                    done_text = done_font.render("DONE", True, GOLD)
                    done_rect = done_text.get_rect(left=bg_rect.right + scale(10), centery=bg_rect.centery)
                    
                    # Draw DONE background
                    done_bg_rect = done_rect.inflate(scale(8), scale(4))
                    pygame.draw.rect(self.screen, (60, 50, 0), done_bg_rect, border_radius=scale(5))
                    
                    # Draw DONE border
                    pygame.draw.rect(self.screen, GOLD, done_bg_rect, scale(2), border_radius=scale(5))
                    
                    # Draw DONE text
                    self.screen.blit(done_text, done_rect)
        
    def _draw_session_high_score(self):
        """Draw session high score indicator."""
        if self.session_high_score > 0:
            # Prepare text
            font = pygame.font.Font(None, scale_font(18))
            text = font.render(f"Session Best: {self.session_high_score}", True, GREEN)
            text_rect = text.get_rect(right=CANVAS_OFFSET_X + CANVAS_WIDTH - scale(20), y=scale(70))
            
            # Draw solid background
            bg_rect = text_rect.inflate(scale(10), scale(4))
            pygame.draw.rect(self.screen, (40, 40, 40), bg_rect)
            pygame.draw.rect(self.screen, GREEN, bg_rect, scale(1))
            
            # Draw text
            self.screen.blit(text, text_rect)
    
    def _draw_game_info_top(self):
        """Draw detector power above the canvas."""
        info_y = CANVAS_OFFSET_Y - scale(35)
        
        # Calculate total detector power
        detectors = [c for c in self.component_manager.components
                    if c.component_type == 'detector']
        total_power = sum(d.intensity for d in detectors)
        detector_score = round(total_power * 1000)
        
        # Draw detector power info
        if detector_score > 0 or len(detectors) > 0:
            # Prepare text
            font = pygame.font.Font(None, scale_font(20))
            text = font.render(f"Detector Power: {total_power:.2f} = {detector_score} pts",
                             True, CYAN)
            text_rect = text.get_rect(left=CANVAS_OFFSET_X + scale(20), centery=info_y)
            
            # Draw solid background
            bg_rect = text_rect.inflate(scale(20), scale(8))
            pygame.draw.rect(self.screen, (40, 40, 40), bg_rect, border_radius=scale(8))
            
            # Draw border
            pygame.draw.rect(self.screen, CYAN, bg_rect, scale(2), border_radius=scale(8))
            
            # Draw text
            self.screen.blit(text, text_rect)

    def _draw_component_counter(self):
        """Draw component counter in bottom left corner of the screen."""
        current_count = len(self.component_manager.components)
        
        # Get challenge limits
        min_components = 0
        max_components = float('inf')
        if self.challenge_manager.current_challenge:
            challenge = self.challenge_manager.challenges.get(self.challenge_manager.current_challenge)
            if challenge:
                min_components = challenge.get('min_components', 0)
                max_components = challenge.get('max_components', float('inf'))
        
        # Position - in the bottom left of the entire screen
        counter_x = scale(20)
        counter_y = WINDOW_HEIGHT - scale(60)
        
        # Prepare text
        font = pygame.font.Font(None, scale_font(24))
        if max_components == float('inf'):
            text = f"Components: {current_count}"
        else:
            text = f"Components: {current_count}/{max_components}"
        
        # Color based on status
        if current_count < min_components:
            color = (255, 100, 100)  # Red - too few
        elif current_count >= max_components:
            color = (255, 200, 0)  # Orange - at limit
        else:
            color = CYAN  # Good
        
        counter_text = font.render(text, True, color)
        counter_rect = counter_text.get_rect(left=counter_x, centery=counter_y)
        
        # Draw solid background (dark gray)
        bg_rect = counter_rect.inflate(scale(20), scale(10))
        pygame.draw.rect(self.screen, (40, 40, 40), bg_rect, border_radius=scale(10))
        
        # Draw border
        pygame.draw.rect(self.screen, color, bg_rect, scale(2), border_radius=scale(10))
        
        # Draw text
        self.screen.blit(counter_text, counter_rect)
        
        # Show min requirement if not met
        if current_count < min_components:
            hint_font = pygame.font.Font(None, scale_font(16))
            hint_text = hint_font.render(f"Need at least {min_components}", True, (200, 200, 200))
            hint_rect = hint_text.get_rect(left=counter_x + scale(10), top=counter_rect.bottom + scale(5))
            self.screen.blit(hint_text, hint_rect)

    def _draw_challenge_status(self):
        """Draw indicator if current challenge is already completed."""
        if (self.challenge_manager.current_challenge and
            self.challenge_manager.current_challenge in self.completed_challenges):
            # Prepare text
            font = pygame.font.Font(None, scale_font(16))
            text = font.render("[DONE] Challenge Completed", True, GREEN)
            text_rect = text.get_rect(right=CANVAS_OFFSET_X + CANVAS_WIDTH - scale(20),
                                     y=CANVAS_OFFSET_Y + CANVAS_HEIGHT - scale(15))
            
            # Draw solid background
            bg_rect = text_rect.inflate(scale(10), scale(4))
            pygame.draw.rect(self.screen, (40, 40, 40), bg_rect)
            pygame.draw.rect(self.screen, GREEN, bg_rect, scale(1))
            
            # Draw text
            self.screen.blit(text, text_rect)
    
    def _draw_drag_preview(self):
        """Draw preview of component being dragged."""
        x, y = self.mouse_pos
        comp_type = self.sidebar.selected
        
        # Semi-transparent preview
        alpha = 128
        
        if comp_type == 'laser':
            # Draw laser preview (turquoise)
            radius = scale(15)
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (radius, radius), radius)
            # Glow effect
            for i in range(3, 0, -1):
                glow_radius = radius + scale(i * 3)
                s2 = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(s2, (CYAN[0], CYAN[1], CYAN[2], alpha // (i + 1)), 
                                 (glow_radius, glow_radius), glow_radius)
                self.screen.blit(s2, (x - glow_radius, y - glow_radius))
            self.screen.blit(s, (x - radius, y - radius))
            
        elif comp_type == 'beamsplitter':
            # Draw beam splitter preview
            size = scale(40)
            half_size = size // 2
            rect = pygame.Rect(x - half_size, y - half_size, size, size)
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], alpha // 2), pygame.Rect(0, 0, size, size))
            pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], alpha), pygame.Rect(0, 0, size, size), scale(3))
            pygame.draw.line(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (0, 0), (size, size), scale(2))
            self.screen.blit(s, rect.topleft)
            
        elif comp_type.startswith('mirror'):
            # Mirror icons
            size = scale(50)
            half_size = size // 2
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            if '/' in comp_type:
                pygame.draw.line(s, (CYAN[0], CYAN[1], CYAN[2], alpha), 
                               (scale(5), size - scale(5)), (size - scale(5), scale(5)), scale(6))
            else:
                pygame.draw.line(s, (CYAN[0], CYAN[1], CYAN[2], alpha), 
                               (scale(5), scale(5)), (size - scale(5), size - scale(5)), scale(6))
            self.screen.blit(s, (x - half_size, y - half_size))
            
        elif comp_type == 'detector':
            # Draw detector preview (turquoise)
            radius = scale(25)
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha // 2), (radius, radius), radius)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (radius, radius), radius, scale(3))
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (radius, radius), scale(10))
            self.screen.blit(s, (x - radius, y - radius))