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
        self.score = 0
    
    def handle_event(self, event):
        """Handle game events."""
        # Handle sidebar events
        if self.sidebar.handle_event(event):
            return
        
        # Handle control panel events
        action = self.controls.handle_event(event)
        if action:
            self._handle_control_action(action)
            return
        
        # Handle canvas events
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._is_in_canvas(event.pos):
                self._handle_canvas_click(event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            if self.sidebar.selected:
                self.grid.set_hover(event.pos)
            else:
                self.grid.set_hover(None)
    
    def _is_in_canvas(self, pos):
        """Check if position is within game canvas."""
        return (CANVAS_OFFSET_X <= pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH and
                CANVAS_OFFSET_Y <= pos[1] <= CANVAS_OFFSET_Y + CANVAS_HEIGHT)
    
    def _handle_canvas_click(self, pos):
        """Handle clicks on the game canvas."""
        # Convert to grid coordinates
        x = round((pos[0] - CANVAS_OFFSET_X) / GRID_SIZE) * GRID_SIZE + CANVAS_OFFSET_X
        y = round((pos[1] - CANVAS_OFFSET_Y) / GRID_SIZE) * GRID_SIZE + CANVAS_OFFSET_Y
        
        if self.sidebar.selected:
            # Place component
            if not self._is_position_occupied(x, y):
                self._add_component(self.sidebar.selected, x, y)
                self.sidebar.selected = None
                self.grid.set_hover(None)
        else:
            # Remove component
            self._remove_component_at(pos)
    
    def _is_position_occupied(self, x, y):
        """Check if position is occupied."""
        # Check laser
        if self.laser.position.distance_to(pygame.math.Vector2(x, y)) < GRID_SIZE:
            return True
        
        # Check components
        for comp in self.components:
            if comp.position.distance_to(pygame.math.Vector2(x, y)) < GRID_SIZE:
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
        pygame.draw.rect(self.screen, (*BLACK, 240), canvas_rect)
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
        
        # Draw effects
        self.effects.draw(self.screen)
        
        # Draw title
        self._draw_title()
    
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
            
            # Draw glow
            pygame.draw.line(self.screen, (*color, alpha // 2), start, end, BEAM_WIDTH + 4)
            # Draw beam
            pygame.draw.line(self.screen, (*color, alpha), start, end, BEAM_WIDTH)
    
    def _draw_title(self):
        """Draw game title."""
        font = pygame.font.Font(None, 48)
        title = font.render("PHOTON PATH", True, CYAN)
        subtitle_font = pygame.font.Font(None, 24)
        subtitle = subtitle_font.render("Build a Mach-Zehnder Interferometer", True, (*WHITE, 200))
        
        title_rect = title.get_rect(centerx=CANVAS_OFFSET_X + CANVAS_WIDTH // 2, y=20)
        subtitle_rect = subtitle.get_rect(centerx=CANVAS_OFFSET_X + CANVAS_WIDTH // 2, y=70)
        
        self.screen.blit(title, title_rect)
        self.screen.blit(subtitle, subtitle_rect)