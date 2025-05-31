"""Main game logic and state management."""
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
from ui.sidebar import Sidebar
from ui.controls import ControlPanel
from ui.effects import EffectsManager
from ui.leaderboard_display import LeaderboardDisplay
from ui.right_panel import RightPanel
from utils.vector import Vector2
from utils.assets_loader import AssetsLoader
from config.settings import *

class Game:
    """Main game class."""
    
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        # Load assets
        self.assets_loader = AssetsLoader()
        
        # Game components
        self.laser = Laser(CANVAS_OFFSET_X + GRID_SIZE, CANVAS_OFFSET_Y + 7 * GRID_SIZE)
        
        # Helper modules
        self.effects = EffectsManager()
        self.component_manager = ComponentManager(self.effects)
        self.beam_renderer = BeamRenderer(screen)
        self.debug_display = DebugDisplay(screen)
        self.debug_display.set_assets_loader(self.assets_loader)  # Pass assets loader
        self.challenge_manager = ChallengeManager()
        
        # Leaderboard system
        self.leaderboard_manager = LeaderboardManager()
        self.leaderboard_display = LeaderboardDisplay(self.leaderboard_manager)
        
        # UI elements
        self.grid = Grid()
        self.sidebar = Sidebar()
        self.controls = ControlPanel()
        self.right_panel = RightPanel()
        
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
        self.score = 0  # Score based on detector power, starts at 0
        self.controls.score = self.score  # Update control panel
        if hasattr(self.controls, 'set_gold_bonus'):
            self.controls.set_gold_bonus(0)  # Initialize gold bonus display
        self.show_opd_info = True  # Toggle for OPD display
        
        # Track session high score and completed challenges
        self.session_high_score = 0
        self.completed_challenges = set()  # Track which challenges have been completed
        
        # Challenge display state
        self.current_challenge_display_name = None  # Store the display name separately
        
        # Load gold fields first
        self.challenge_manager.load_gold_fields()
        
        # Load blocked fields (these take precedence over gold if there's a conflict)
        self.challenge_manager.load_blocked_fields()
        
        # Validate configuration (helps level designers spot conflicts)
        self.challenge_manager.validate_field_configurations()
        
        # Create template if it doesn't exist
        if not os.path.exists("config/blocked_fields_template.txt"):
            self.challenge_manager.create_blocked_fields_template()
        
        # Load default challenge (Basic Mach-Zehnder)
        challenges = self.challenge_manager.get_challenge_list()
        if challenges:
            for name, title in challenges:
                if name == "basic_mz":
                    self.challenge_manager.set_current_challenge(name)
                    self.current_challenge_display_name = title  # Store display name
                    self.controls.set_challenge(title)
                    # Set completion status if method exists
                    if hasattr(self.controls, 'set_challenge_completed'):
                        self.controls.set_challenge_completed(False)
                    if hasattr(self.controls, 'set_gold_bonus'):
                        self.controls.set_gold_bonus(0)
                    self.right_panel.add_debug_message(f"Loaded challenge: {title}")
                    break
        
        # Show scoring formula
        self.controls.set_status("Score = Detector Power × 1000 + Gold Bonus")
    
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
                elif self.challenge_manager.is_position_blocked(x, y):
                    self.controls.set_status("Cannot place component here - position blocked!")
                    print(f"Position ({x}, {y}) is blocked")
                elif not self.component_manager.is_position_occupied(x, y, self.laser,
                                                                  self.sidebar.selected == 'laser'):
                    self.component_manager.add_component(
                        self.sidebar.selected, x, y, self.laser)
                    # Score is now based on detector power, not placement
                    print(f"Placed {self.sidebar.selected} at ({x}, {y})")  # Debug
                    self.right_panel.add_debug_message(f"Placed {self.sidebar.selected} at grid ({(x-CANVAS_OFFSET_X)//GRID_SIZE}, {(y-CANVAS_OFFSET_Y)//GRID_SIZE})")
            
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
                    self.right_panel.add_debug_message("Component removed")
                # No score update - score based on detector power
    
    def _is_in_canvas(self, pos):
        """Check if position is within game canvas."""
        return (CANVAS_OFFSET_X <= pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH and
                CANVAS_OFFSET_Y <= pos[1] <= CANVAS_OFFSET_Y + CANVAS_HEIGHT)
    
    def _can_add_component(self):
        """Check if we can add another component based on challenge limits."""
        if not self.challenge_manager.current_challenge:
            return True  # No limits in free play
        
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
            self.score = 0  # Reset score to 0
            self.controls.score = self.score
            if hasattr(self.controls, 'set_gold_bonus'):
                self.controls.set_gold_bonus(0)  # Reset gold bonus display
            # Optionally reset completed challenges when clearing all
            # This allows players to retry challenges in the same session
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                # Shift+Clear All resets completed challenges
                self.completed_challenges.clear()
                if hasattr(self.controls, 'set_challenge_completed'):
                    self.controls.set_challenge_completed(False)  # Reset gold color
                if hasattr(self.controls, 'set_gold_bonus'):
                    self.controls.set_gold_bonus(0)  # Reset gold bonus display
                self.controls.set_status("Setup cleared and challenges reset!")
                self.right_panel.add_debug_message("Session reset - challenges can be completed again")
                print("Completed challenges reset - you can earn points again")
            else:
                self.controls.set_status("Score = Detector Power × 1000 + Gold Bonus")
                self.right_panel.add_debug_message("Setup cleared")
        elif action == 'Check Setup':
            # Check against current challenge (pass beam_tracer for gold field calculation)
            success, message, points = self.challenge_manager.check_setup(
                self.component_manager.components, self.laser, self.beam_tracer)
            if success:
                # Check if this challenge was already completed
                challenge_name = self.challenge_manager.current_challenge
                if challenge_name and challenge_name not in self.completed_challenges:
                    # First time completing this challenge - award points
                    self._update_score(points)
                    self.completed_challenges.add(challenge_name)
                    self.effects.add_success_message()
                    
                    # Update controls to show gold color
                    if hasattr(self.controls, 'set_challenge_completed'):
                        self.controls.set_challenge_completed(True)
                    
                    # Check if this is a high score
                    if self.score > self.session_high_score:
                        self.session_high_score = self.score
                    
                    # Show leaderboard with potential score entry
                    challenge_info = self.challenge_manager.challenges.get(challenge_name, {})
                    self.leaderboard_display.show(
                        auto_add_score=self.score,
                        challenge=challenge_info.get('name', 'Unknown'),
                        components=len(self.component_manager.components)
                    )
                else:
                    # Already completed - just show success without points
                    self.controls.set_status("Challenge already completed this session!")
                    self.effects.add_info_message("Challenge Complete", "No additional points awarded")
                    print("Challenge already completed - no additional points awarded")
                
                print(message)  # Full message to console
            else:
                self.controls.set_status(f"Failed: {message}")
                print(f"Challenge check failed: {message}")
        elif action == 'Toggle Laser':
            if self.laser:
                self.laser.enabled = not self.laser.enabled
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
                self.current_challenge_display_name = challenge_title  # Update display name
                self.controls.set_challenge(challenge_title)
                
                # Update completion status for the controls
                is_completed = challenge_name in self.completed_challenges
                if hasattr(self.controls, 'set_challenge_completed'):
                    self.controls.set_challenge_completed(is_completed)
                
                # Note: We don't reset completed_challenges here to prevent
                # players from farming points by reloading the same challenge
                print(f"Loaded challenge: {challenge_title}")
                self.right_panel.add_debug_message(f"Loaded challenge: {challenge_title}")
    
    def _update_score(self, points):
        """Update game score."""
        self.score = points  # Score is now absolute, not cumulative from placement
        self.controls.score = self.score
        
        # Update session high score
        if self.score > self.session_high_score:
            self.session_high_score = self.score
    
    def update(self, dt):
        """Update game state."""
        self.effects.update(dt)
        
        # Note: Detector intensity is now calculated fresh each frame
        # based on accumulated beam amplitudes, so no decay is needed
    
    def draw(self):
        """Draw the game."""
        # Update challenge completion status for controls
        if self.challenge_manager.current_challenge and hasattr(self.controls, 'set_challenge_completed'):
            is_completed = self.challenge_manager.current_challenge in self.completed_challenges
            self.controls.set_challenge_completed(is_completed)
        
        # Update gold bonus for controls
        if hasattr(self.beam_tracer, 'gold_field_hits') and hasattr(self.controls, 'set_gold_bonus'):
            total_bonus = 0
            for position, intensity in self.beam_tracer.gold_field_hits.items():
                bonus = int(intensity * 100)
                total_bonus += bonus
            self.controls.set_gold_bonus(total_bonus)
        
        # Clear screen
        self.screen.fill(BLACK)
        
        # Draw banner as the bottom-most layer (MOVED HERE)
        self.debug_display.draw_banner()
        
        # Draw game info above canvas
        self._draw_game_info_top()
        
        # Draw challenge name above grid
        self._draw_challenge_name()
        
        # Draw game canvas background (SEMITRANSPARENT)
        canvas_rect = pygame.Rect(CANVAS_OFFSET_X, CANVAS_OFFSET_Y, CANVAS_WIDTH, CANVAS_HEIGHT)
        s = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT), pygame.SRCALPHA)
        s.fill((BLACK[0], BLACK[1], BLACK[2], 60))  # Very transparent - only 60/255 opacity
        self.screen.blit(s, canvas_rect.topleft)
        pygame.draw.rect(self.screen, PURPLE, canvas_rect, 2, border_radius=15)
        
        # Draw grid (pass gold positions)
        laser_pos = self.laser.position.tuple() if self.laser else None
        self.grid.draw(self.screen, self.component_manager.components, laser_pos,
                      self.challenge_manager.get_blocked_positions(),
                      self.challenge_manager.get_gold_positions())  # NEW parameter
        
        # Draw laser
        if self.laser:
            self.laser.draw(self.screen)
        
        # Draw components
        for comp in self.component_manager.components:
            comp.draw(self.screen)
        
        # Trace and draw beams
        if self.laser and self.laser.enabled:
            # Set gold positions on beam tracer (NEW)
            self.beam_tracer.set_gold_positions(self.challenge_manager.get_gold_positions())
            
            self.beam_renderer.draw_beams(self.beam_tracer, self.laser,
                                        self.component_manager.components,
                                        0,  # No phase shift anymore
                                        self.challenge_manager.get_blocked_positions())
        
        # Draw UI
        self.sidebar.draw(self.screen)
        self.controls.draw(self.screen)
        self.right_panel.draw(self.screen)
        
        # Draw dragged component preview
        if self.sidebar.dragging and self.sidebar.selected:
            self._draw_drag_preview()
        
        # Draw effects
        self.effects.draw(self.screen)
        
        # Draw info text and debug info
        self.debug_display.draw_info_text()
        self.debug_display.draw_opd_info(self.component_manager.components, self.show_opd_info)
        
        # Draw session high score
        self._draw_session_high_score()
        
        # Draw challenge completion status
        self._draw_challenge_status()
        
        # Draw component counter (bottom left)
        self._draw_component_counter()
        
        # Draw leaderboard if visible
        self.leaderboard_display.draw(self.screen)
    
    def _draw_challenge_name(self):
        """Draw the current challenge name above the grid."""
        if self.current_challenge_display_name:
            # Check if current challenge is completed
            is_completed = (self.challenge_manager.current_challenge and
                          self.challenge_manager.current_challenge in self.completed_challenges)
            
            # Use gold color if completed, cyan otherwise
            GOLD = (255, 215, 0)
            color = GOLD if is_completed else CYAN
            
            font = pygame.font.Font(None, 32)
            text = font.render(self.current_challenge_display_name, True, color)
            text_rect = text.get_rect(centerx=CANVAS_OFFSET_X + CANVAS_WIDTH // 2,
                                     y=CANVAS_OFFSET_Y - 65)
            
            # Background with glow effect
            bg_rect = text_rect.inflate(40, 12)
            
            # Glow effect
            glow_surf = pygame.Surface((bg_rect.width + 20, bg_rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (color[0], color[1], color[2], 20),
                           glow_surf.get_rect(), border_radius=20)
            self.screen.blit(glow_surf, (bg_rect.x - 10, bg_rect.y - 10))
            
            # Background
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, 200), s.get_rect(), border_radius=15)
            self.screen.blit(s, bg_rect.topleft)
            pygame.draw.rect(self.screen, color, bg_rect, 2, border_radius=15)
            
            # Draw the text
            self.screen.blit(text, text_rect)
            
            # Add decorative elements
            # Left decoration
            deco_left = pygame.Rect(bg_rect.left - 50, bg_rect.centery - 1, 40, 2)
            pygame.draw.rect(self.screen, color, deco_left)
            pygame.draw.circle(self.screen, color, (deco_left.left, deco_left.centery), 3)
            
            # Right decoration
            deco_right = pygame.Rect(bg_rect.right + 10, bg_rect.centery - 1, 40, 2)
            pygame.draw.rect(self.screen, color, deco_right)
            pygame.draw.circle(self.screen, color, (deco_right.right, deco_right.centery), 3)
            
            # Add completed indicator if applicable
            if is_completed:
                # Draw "DONE" text for better compatibility
                done_font = pygame.font.Font(None, 20)
                done_text = done_font.render("DONE", True, GOLD)
                done_rect = done_text.get_rect(left=bg_rect.right + 10, centery=bg_rect.centery)
                
                # Background for DONE text
                done_bg_rect = done_rect.inflate(8, 4)
                s = pygame.Surface((done_bg_rect.width, done_bg_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(s, (GOLD[0]//4, GOLD[1]//4, GOLD[2]//4, 200),
                               s.get_rect(), border_radius=5)
                self.screen.blit(s, done_bg_rect.topleft)
                pygame.draw.rect(self.screen, GOLD, done_bg_rect, 1, border_radius=5)
                
                self.screen.blit(done_text, done_rect)
    
    def _draw_session_high_score(self):
        """Draw session high score indicator."""
        if self.session_high_score > 0:
            font = pygame.font.Font(None, 18)
            text = font.render(f"Session Best: {self.session_high_score}", True, GREEN)
            text_rect = text.get_rect(right=CANVAS_OFFSET_X + CANVAS_WIDTH - 20, y=70)
            
            # Background
            bg_rect = text_rect.inflate(10, 4)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))
            self.screen.blit(s, bg_rect.topleft)
            
            self.screen.blit(text, text_rect)
    
    def _draw_game_info_top(self):
        """Draw detector power above the canvas."""
        info_y = CANVAS_OFFSET_Y - 35
        
        # Calculate total detector power
        detectors = [c for c in self.component_manager.components
                    if c.component_type == 'detector']
        total_power = sum(d.intensity for d in detectors)
        detector_score = int(total_power * 1000)
        
        # Draw detector power info
        if detector_score > 0 or len(detectors) > 0:
            font = pygame.font.Font(None, 20)
            text = font.render(f"Detector Power: {total_power:.2f} = {detector_score} pts",
                             True, CYAN)
            text_rect = text.get_rect(left=CANVAS_OFFSET_X + 20, centery=info_y)
            
            # Background
            bg_rect = text_rect.inflate(20, 8)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, 180), s.get_rect(), border_radius=8)
            self.screen.blit(s, bg_rect.topleft)
            pygame.draw.rect(self.screen, CYAN, bg_rect, 1, border_radius=8)
            
            self.screen.blit(text, text_rect)
    
    def _draw_component_counter(self):
        """Draw component counter in bottom left corner."""
        current_count = len(self.component_manager.components)
        
        # Get challenge limits
        min_components = 0
        max_components = float('inf')
        if self.challenge_manager.current_challenge:
            challenge = self.challenge_manager.challenges.get(self.challenge_manager.current_challenge)
            if challenge:
                min_components = challenge.get('min_components', 0)
                max_components = challenge.get('max_components', float('inf'))
        
        # Position
        counter_x = 20
        counter_y = WINDOW_HEIGHT - 60
        
        # Draw counter
        font = pygame.font.Font(None, 24)
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
        
        # Background
        bg_rect = counter_rect.inflate(20, 10)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 180), s.get_rect(), border_radius=10)
        self.screen.blit(s, bg_rect.topleft)
        pygame.draw.rect(self.screen, color, bg_rect, 1, border_radius=10)
        
        self.screen.blit(counter_text, counter_rect)
        
        # Show min requirement if not met
        if current_count < min_components:
            hint_font = pygame.font.Font(None, 16)
            hint_text = hint_font.render(f"Need at least {min_components}", True, (200, 200, 200))
            hint_rect = hint_text.get_rect(left=counter_x + 10, top=counter_rect.bottom + 5)
            self.screen.blit(hint_text, hint_rect)
    
    def _draw_challenge_status(self):
        """Draw indicator if current challenge is already completed."""
        if (self.challenge_manager.current_challenge and
            self.challenge_manager.current_challenge in self.completed_challenges):
            font = pygame.font.Font(None, 16)
            text = font.render("[DONE] Challenge Completed", True, GREEN)
            text_rect = text.get_rect(right=CANVAS_OFFSET_X + CANVAS_WIDTH - 20,
                                     y=CANVAS_OFFSET_Y + CANVAS_HEIGHT - 15)
            
            # Background
            bg_rect = text_rect.inflate(10, 4)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))
            self.screen.blit(s, bg_rect.topleft)
            
            self.screen.blit(text, text_rect)
    
    def _draw_drag_preview(self):
        """Draw preview of component being dragged."""
        x, y = self.mouse_pos
        comp_type = self.sidebar.selected
        
        # Semi-transparent preview
        alpha = 128
        
        if comp_type == 'laser':
            # Draw laser preview (turquoise)
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (30, 30), 15)
            # Glow effect
            for i in range(3, 0, -1):
                pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha // (i + 1)), (30, 30), 15 + i * 3)
            self.screen.blit(s, (x - 30, y - 30))
            
        elif comp_type == 'beamsplitter':
            # Draw beam splitter preview
            rect = pygame.Rect(x - 20, y - 20, 40, 40)
            s = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], alpha // 2), pygame.Rect(0, 0, 40, 40))
            pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], alpha), pygame.Rect(0, 0, 40, 40), 3)
            pygame.draw.line(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (0, 0), (40, 40), 2)
            self.screen.blit(s, rect.topleft)
            
        elif comp_type == 'mirror/':
            # Draw / mirror preview (turquoise)
            s = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.line(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (5, 45), (45, 5), 6)
            self.screen.blit(s, (x - 25, y - 25))
            
        elif comp_type == 'mirror\\':
            # Draw \ mirror preview (turquoise)
            s = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.line(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (5, 5), (45, 45), 6)
            self.screen.blit(s, (x - 25, y - 25))
            
        elif comp_type == 'detector':
            # Draw detector preview (turquoise)
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha // 2), (30, 30), 25)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (30, 30), 25, 3)
            pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (30, 30), 10)
            self.screen.blit(s, (x - 30, y - 30))
