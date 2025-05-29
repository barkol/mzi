"""Main game logic and state management."""
import pygame
import math
from components.laser import Laser
from components.beam_splitter import BeamSplitter
from components.mirror import Mirror
from components.detector import Detector
from core.grid import Grid
from core.physics import BeamTracer
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
        self.components = []
        self.laser = Laser(CANVAS_OFFSET_X + GRID_SIZE, CANVAS_OFFSET_Y + 7 * GRID_SIZE)
        
        # UI elements
        self.grid = Grid()
        self.sidebar = Sidebar()
        self.controls = ControlPanel()
        self.effects = EffectsManager()
        
        # Physics
        self.beam_tracer = BeamTracer()
        
        # Game state
        self.dragging = False
        self.drag_component = None
        self.mouse_pos = (0, 0)
        self.score = 0
    
    def handle_event(self, event):
        """Handle game events."""
        # Update mouse position
        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            
            # Update grid hover if dragging
            if self.sidebar.dragging:
                self.grid.set_hover(event.pos)
            else:
                self.grid.set_hover(None)
        
        # Handle sidebar events first
        sidebar_handled = self.sidebar.handle_event(event)
        
        # Handle control panel events
        action = self.controls.handle_event(event)
        if action:
            self._handle_control_action(action)
            return
        
        # Handle component drop
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.sidebar.selected and self._is_in_canvas(event.pos):
                # Place component at grid position
                x = round((event.pos[0] - CANVAS_OFFSET_X) / GRID_SIZE) * GRID_SIZE + CANVAS_OFFSET_X
                y = round((event.pos[1] - CANVAS_OFFSET_Y) / GRID_SIZE) * GRID_SIZE + CANVAS_OFFSET_Y
                
                if not self._is_position_occupied(x, y):
                    self._add_component(self.sidebar.selected, x, y)
                    print(f"Placed {self.sidebar.selected} at ({x}, {y})")  # Debug
            
            # Clear grid hover after drop
            self.grid.set_hover(None)
        
        # Handle canvas clicks (for removing components)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._is_in_canvas(event.pos) and not self.sidebar.selected:
                self._remove_component_at(event.pos)
    
    def _is_in_canvas(self, pos):
        """Check if position is within game canvas."""
        return (CANVAS_OFFSET_X <= pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH and
                CANVAS_OFFSET_Y <= pos[1] <= CANVAS_OFFSET_Y + CANVAS_HEIGHT)
    
    def _is_position_occupied(self, x, y):
        """Check if position is occupied."""
        # Check laser
        if self.laser.position.distance_to(Vector2(x, y)) < GRID_SIZE:
            return True
        
        # Check components
        for comp in self.components:
            if comp.position.distance_to(Vector2(x, y)) < GRID_SIZE:
                return True
        
        return False
    
    def _add_component(self, comp_type, x, y):
        """Add a component to the game."""
        if comp_type == 'beamsplitter':
            comp = BeamSplitter(x, y)
        elif comp_type == 'mirror/':
            comp = Mirror(x, y, '/')
        elif comp_type == 'mirror\\':
            comp = Mirror(x, y, '\\')
        elif comp_type == 'detector':
            comp = Detector(x, y)
        else:
            return
        
        self.components.append(comp)
        self.effects.add_placement_effect(x, y)
        self._update_score(PLACEMENT_SCORE)
    
    def _remove_component_at(self, pos):
        """Remove component at position."""
        for i, comp in enumerate(self.components):
            if comp.contains_point(pos[0], pos[1]):
                self.components.pop(i)
                self._update_score(-PLACEMENT_SCORE)
                break
    
    def _handle_control_action(self, action):
        """Handle control panel actions."""
        if action == 'Clear All':
            self.components.clear()
            self.score = 0
            self.controls.score = 0
        elif action == 'Check Setup':
            self._check_solution()
        elif action == 'Toggle Laser':
            self.laser.enabled = not self.laser.enabled
    
    def _check_solution(self):
        """Check if player has built a valid interferometer."""
        beam_splitters = sum(1 for c in self.components if c.component_type == 'beamsplitter')
        mirrors = sum(1 for c in self.components if c.component_type == 'mirror')
        detectors = sum(1 for c in self.components if c.component_type == 'detector')
        
        if beam_splitters >= 2 and mirrors >= 2 and detectors >= 1:
            self.effects.add_success_message()
            self._update_score(COMPLETION_SCORE)
    
    def _update_score(self, points):
        """Update game score."""
        self.score = max(0, self.score + points)
        self.controls.score = self.score
    
    def update(self, dt):
        """Update game state."""
        self.effects.update(dt)
        
        # Update detectors
        for comp in self.components:
            if comp.component_type == 'detector':
                comp.intensity *= 0.95  # Decay old values
    
    def draw(self):
        """Draw the game."""
        # Clear screen
        self.screen.fill(BLACK)
        
        # Draw game canvas background
        canvas_rect = pygame.Rect(CANVAS_OFFSET_X, CANVAS_OFFSET_Y, CANVAS_WIDTH, CANVAS_HEIGHT)
        s = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT), pygame.SRCALPHA)
        s.fill((BLACK[0], BLACK[1], BLACK[2], 240))
        screen.blit(s, canvas_rect.topleft)
        pygame.draw.rect(self.screen, PURPLE, canvas_rect, 2, border_radius=15)
        
        # Draw grid
        self.grid.draw(self.screen, self.components, self.laser.position.tuple())
        
        # Draw laser
        self.laser.draw(self.screen)
        
        # Draw components
        for comp in self.components:
            comp.draw(self.screen)
        
        # Trace and draw beams
        if self.laser.enabled:
            self._draw_beams()
        
        # Draw UI
        self.sidebar.draw(self.screen)
        self.controls.draw(self.screen)
        
        # Draw dragged component preview
        if self.sidebar.dragging and self.sidebar.selected:
            self._draw_drag_preview()
        
        # Draw effects
        self.effects.draw(self.screen)
        
        # Draw title
        self._draw_title()
    
    def _draw_drag_preview(self):
        """Draw preview of component being dragged."""
        x, y = self.mouse_pos
        comp_type = self.sidebar.selected
        
        # Semi-transparent preview
        alpha = 128
        
        if comp_type == 'beamsplitter':
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
    
    def _draw_beams(self):
        """Trace and draw laser beams."""
        self.beam_tracer.reset()
        
        # Add laser beam
        laser_beam = self.laser.emit_beam()
        if laser_beam:
            # Apply phase shift
            laser_beam['phase'] += math.radians(self.controls.phase)
            self.beam_tracer.add_beam(laser_beam)
        
        # Trace beams
        traced_beams = self.beam_tracer.trace_beams(self.components)
        
        # Draw beams
        for beam_data in traced_beams:
            self._draw_beam_path(beam_data)
    
    def _draw_beam_path(self, beam_data):
        """Draw a single beam path."""
        path = beam_data['path']
        if len(path) < 2:
            return
        
        # Color based on source type
        if beam_data['source_type'] == 'shifted':
            color = MAGENTA
        else:
            color = RED
        
        # Adjust alpha based on amplitude
        alpha = int(255 * beam_data['amplitude']**2)
        
        # Draw path
        for i in range(len(path) - 1):
            start = path[i].tuple() if hasattr(path[i], 'tuple') else path[i]
            end = path[i+1].tuple() if hasattr(path[i+1], 'tuple') else path[i+1]
            
            # Draw beam with adjusted color intensity based on amplitude
            beam_color = color
            if alpha < 255:
                # Dim the color based on amplitude
                beam_color = tuple(int(c * alpha / 255) for c in color)
            
            # Draw glow
            pygame.draw.line(self.screen, beam_color, start, end, BEAM_WIDTH + 2)
            # Draw beam core
            pygame.draw.line(self.screen, beam_color, start, end, BEAM_WIDTH)
    
    def _draw_title(self):
        """Draw game title."""
        font = pygame.font.Font(None, 48)
        title = font.render("PHOTON PATH", True, CYAN)
        subtitle_font = pygame.font.Font(None, 24)
        subtitle = subtitle_font.render("Build a Mach-Zehnder Interferometer", True, WHITE)
        
        title_rect = title.get_rect(centerx=CANVAS_OFFSET_X + CANVAS_WIDTH // 2, y=20)
        subtitle_rect = subtitle.get_rect(centerx=CANVAS_OFFSET_X + CANVAS_WIDTH // 2, y=70)
        
        self.screen.blit(title, title_rect)
        self.screen.blit(subtitle, subtitle_rect)
