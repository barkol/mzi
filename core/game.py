"""Main game logic and state management."""
import pygame
from components.laser import Laser
from core.grid import Grid
from core.physics import BeamTracer
from core.beam_renderer import BeamRenderer
from core.component_manager import ComponentManager
from core.keyboard_handler import KeyboardHandler
from core.debug_display import DebugDisplay
from ui.sidebar import Sidebar
from ui.controls import ControlPanel
from ui.effects import EffectsManager
from utils.vector import Vector2
from config.settings import *

class Game:
    """Main game class."""
    
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        # Game components
        self.laser = Laser(CANVAS_OFFSET_X + GRID_SIZE, CANVAS_OFFSET_Y + 7 * GRID_SIZE)
        
        # Helper modules
        self.effects = EffectsManager()
        self.component_manager = ComponentManager(self.effects)
        self.beam_renderer = BeamRenderer(screen)
        self.debug_display = DebugDisplay(screen)
        
        # UI elements
        self.grid = Grid()
        self.sidebar = Sidebar()
        self.controls = ControlPanel()
        
        # Physics
        self.beam_tracer = BeamTracer()
        
        # Keyboard handler
        self.keyboard_handler = KeyboardHandler(self)
        
        # Game state
        self.dragging = False
        self.drag_component = None
        self.mouse_pos = (0, 0)
        self.score = PLACEMENT_SCORE  # Start with score for initial laser
        self.controls.score = self.score  # Update control panel
        self.show_opd_info = True  # Toggle for OPD display
    
    def handle_event(self, event):
        """Handle game events."""
        # Handle keyboard events first
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
                
                if not self.component_manager.is_position_occupied(x, y, self.laser, 
                                                                  self.sidebar.selected == 'laser'):
                    score_delta = self.component_manager.add_component(
                        self.sidebar.selected, x, y, self.laser)
                    self._update_score(score_delta)
                    print(f"Placed {self.sidebar.selected} at ({x}, {y})")  # Debug
            
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
                score_delta = self.component_manager.remove_component_at(event.pos)
                self._update_score(score_delta)
    
    def _is_in_canvas(self, pos):
        """Check if position is within game canvas."""
        return (CANVAS_OFFSET_X <= pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH and
                CANVAS_OFFSET_Y <= pos[1] <= CANVAS_OFFSET_Y + CANVAS_HEIGHT)
    
    def _handle_control_action(self, action):
        """Handle control panel actions."""
        if action == 'Clear All':
            new_score = self.component_manager.clear_all(self.laser)
            self.score = new_score
            self.controls.score = self.score
        elif action == 'Check Setup':
            if self.component_manager.check_solution(self.laser):
                self._update_score(COMPLETION_SCORE)
        elif action == 'Toggle Laser':
            if self.laser:
                self.laser.enabled = not self.laser.enabled
    
    def _update_score(self, points):
        """Update game score."""
        self.score = max(0, self.score + points)
        self.controls.score = self.score
    
    def update(self, dt):
        """Update game state."""
        self.effects.update(dt)
        
        # Note: Detector intensity is now calculated fresh each frame
        # based on accumulated beam amplitudes, so no decay is needed
    
    def draw(self):
        """Draw the game."""
        # Clear screen
        self.screen.fill(BLACK)
        
        # Draw game canvas background
        canvas_rect = pygame.Rect(CANVAS_OFFSET_X, CANVAS_OFFSET_Y, CANVAS_WIDTH, CANVAS_HEIGHT)
        s = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT), pygame.SRCALPHA)
        s.fill((BLACK[0], BLACK[1], BLACK[2], 240))
        self.screen.blit(s, canvas_rect.topleft)
        pygame.draw.rect(self.screen, PURPLE, canvas_rect, 2, border_radius=15)
        
        # Draw grid
        laser_pos = self.laser.position.tuple() if self.laser else None
        self.grid.draw(self.screen, self.component_manager.components, laser_pos)
        
        # Draw laser
        if self.laser:
            self.laser.draw(self.screen)
        
        # Draw components
        for comp in self.component_manager.components:
            comp.draw(self.screen)
        
        # Trace and draw beams
        if self.laser and self.laser.enabled:
            self.beam_renderer.draw_beams(self.beam_tracer, self.laser, 
                                        self.component_manager.components, 
                                        self.controls.phase)
        
        # Draw UI
        self.sidebar.draw(self.screen)
        self.controls.draw(self.screen)
        
        # Draw dragged component preview
        if self.sidebar.dragging and self.sidebar.selected:
            self._draw_drag_preview()
        
        # Draw effects
        self.effects.draw(self.screen)
        
        # Draw title and debug info
        self.debug_display.draw_title_info()
        self.debug_display.draw_opd_info(self.component_manager.components, self.show_opd_info)
    
    def _draw_drag_preview(self):
        """Draw preview of component being dragged."""
        x, y = self.mouse_pos
        comp_type = self.sidebar.selected
        
        # Semi-transparent preview
        alpha = 128
        
        if comp_type == 'laser':
            # Draw laser preview
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(s, (RED[0], RED[1], RED[2], alpha), (30, 30), 15)
            # Glow effect
            for i in range(3, 0, -1):
                pygame.draw.circle(s, (RED[0], RED[1], RED[2], alpha // (i + 1)), (30, 30), 15 + i * 3)
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
            # Draw / mirror preview
            s = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.line(s, (MAGENTA[0], MAGENTA[1], MAGENTA[2], alpha), (5, 45), (45, 5), 6)
            self.screen.blit(s, (x - 25, y - 25))
            
        elif comp_type == 'mirror\\':
            # Draw \ mirror preview
            s = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.line(s, (MAGENTA[0], MAGENTA[1], MAGENTA[2], alpha), (5, 5), (45, 45), 6)
            self.screen.blit(s, (x - 25, y - 25))
            
        elif comp_type == 'detector':
            # Draw detector preview
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(s, (GREEN[0], GREEN[1], GREEN[2], alpha // 2), (30, 30), 25)
            pygame.draw.circle(s, (GREEN[0], GREEN[1], GREEN[2], alpha), (30, 30), 25, 3)
            pygame.draw.circle(s, (GREEN[0], GREEN[1], GREEN[2], alpha), (30, 30), 10)
            self.screen.blit(s, (x - 30, y - 30))