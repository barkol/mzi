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
        self.laser = Laser(CANVAS_OFFSET_X + GRID_SIZE, CANVAS_OFFSET_Y + 7 * GRID_SIZE)  # Start with laser
        
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
        self.score = PLACEMENT_SCORE  # Start with score for initial laser
        self.controls.score = self.score  # Update control panel
        self.show_opd_info = True  # Toggle for OPD display
    
    def handle_event(self, event):
        """Handle game events."""
        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_o:
                self.show_opd_info = not self.show_opd_info
                print(f"OPD display: {'ON' if self.show_opd_info else 'OFF'}")
            elif event.key == pygame.K_v:
                # Visual test: place detectors around beam splitter
                print("\n=== VISUAL DIRECTION TEST ===")
                for comp in self.components:
                    if comp.component_type == 'beamsplitter':
                        bs_pos = comp.position
                        print(f"Placing detectors around beam splitter at {bs_pos}")
                        
                        # Place detectors at all 4 positions
                        detector_positions = [
                            (bs_pos.x - 80, bs_pos.y, "LEFT (A)"),
                            (bs_pos.x, bs_pos.y + 80, "DOWN (B)"),
                            (bs_pos.x + 80, bs_pos.y, "RIGHT (C)"),
                            (bs_pos.x, bs_pos.y - 80, "UP (D)")
                        ]
                        
                        for x, y, label in detector_positions:
                            if not self._is_position_occupied(x, y):
                                det = Detector(x, y)
                                self.components.append(det)
                                print(f"  Placed detector at {label}")
                        
                        print("Now test with laser from different directions to verify routing")
                        break
            elif event.key == pygame.K_i:
                # Test specific interference case: A + D inputs
                print("\n=== INTERFERENCE TEST: A + D inputs ===")
                for comp in self.components:
                    if comp.component_type == 'beamsplitter':
                        comp.reset_frame()
                        
                        # Beam from A (left)
                        beam_A = {
                            'position': comp.position + Vector2(-50, 0),
                            'direction': Vector2(1, 0),
                            'amplitude': 1.0,
                            'phase': 0,
                            'path_length': 0,
                            'total_path_length': 100,
                            'accumulated_phase': 0,
                            'source_type': 'laser'
                        }
                        
                        # Beam from D (top)
                        beam_D = {
                            'position': comp.position + Vector2(0, -50),
                            'direction': Vector2(0, 1),
                            'amplitude': 1.0,
                            'phase': 0,
                            'path_length': 0,
                            'total_path_length': 100,
                            'accumulated_phase': 0,
                            'source_type': 'laser'
                        }
                        
                        comp.add_beam(beam_A)
                        comp.add_beam(beam_D)
                        outputs = comp.finalize_frame()
                        
                        print(f"\nInputs:")
                        print(f"  A (left): amplitude = 1.0, phase = 0°")
                        print(f"  D (top): amplitude = 1.0, phase = 0°")
                        
                        print(f"\nExpected outputs:")
                        print(f"  C = A/√2 + iD/√2 = 0.707 + 0.707i")
                        print(f"  B = iA/√2 + D/√2 = 0.707i + 0.707")
                        
                        print(f"\nActual outputs:")
                        for out in outputs:
                            port = 'Unknown'
                            if out['direction'].x > 0.5: port = 'C (right)'
                            elif out['direction'].x < -0.5: port = 'A (left)'
                            elif out['direction'].y > 0.5: port = 'B (down)'
                            elif out['direction'].y < -0.5: port = 'D (up)'
                            
                            print(f"  {port}: amplitude = {out['amplitude']:.3f}, phase = {out['phase']*180/math.pi:.1f}°")
                        
                        # Calculate what the amplitudes should be
                        E_C_expected = complex(1/math.sqrt(2), 1/math.sqrt(2))  # A/√2 + iD/√2
                        E_B_expected = complex(1/math.sqrt(2), 1/math.sqrt(2))  # D/√2 + iA/√2
                        
                        print(f"\nVerification:")
                        print(f"  |E_C| should be {abs(E_C_expected):.3f} at phase {cmath.phase(E_C_expected)*180/math.pi:.1f}°")
                        print(f"  |E_B| should be {abs(E_B_expected):.3f} at phase {cmath.phase(E_B_expected)*180/math.pi:.1f}°")
                        break
            elif event.key == pygame.K_t:
                # Test beam splitter with beams from all 4 directions
                print("\n=== BEAM SPLITTER TEST MODE ===")
                for comp in self.components:
                    if comp.component_type == 'beamsplitter':
                        print(f"\nTesting beam splitter at {comp.position}")
                        comp.reset_frame()
                        
                        # Test all 4 input directions (corrected for screen coordinates)
                        test_beams = [
                            {'name': 'A (from left, traveling RIGHT)', 'dir': Vector2(1, 0)},
                            {'name': 'B (from bottom, traveling UP)', 'dir': Vector2(0, -1)},
                            {'name': 'C (from right, traveling LEFT)', 'dir': Vector2(-1, 0)},
                            {'name': 'D (from top, traveling DOWN)', 'dir': Vector2(0, 1)}
                        ]
                        
                        for test in test_beams:
                            print(f"\n  Test {test['name']}:")
                            comp.reset_frame()
                            test_beam = {
                                'position': comp.position - test['dir'] * 50,
                                'direction': test['dir'],
                                'amplitude': 1.0,
                                'phase': 0,
                                'path_length': 0,
                                'total_path_length': 0,
                                'source_type': 'laser'
                            }
                            comp.add_beam(test_beam)
                            outputs = comp.finalize_frame()
                            
                            # Calculate total output power
                            total_out_power = sum(out['amplitude']**2 for out in outputs)
                            print(f"    Input power: 1.000")
                            print(f"    Outputs: {len(outputs)} beams")
                            for out in outputs:
                                dir_name = ''
                                if out['direction'].x > 0.5: dir_name = 'RIGHT'
                                elif out['direction'].x < -0.5: dir_name = 'LEFT'
                                elif out['direction'].y > 0.5: dir_name = 'DOWN'
                                elif out['direction'].y < -0.5: dir_name = 'UP'
                                print(f"      → {dir_name}: amp={out['amplitude']:.3f}, power={out['amplitude']**2:.3f}")
                            print(f"    Total output power: {total_out_power:.3f}")
                            print(f"    Energy conserved: {'YES' if abs(total_out_power - 1.0) < 0.001 else 'NO'}")
                        # First test simple two-beam case from same port
                        print(f"\n  Test SIMPLE CASE (two identical beams from port A):")
                        comp.reset_frame()
                        # Two identical beams from left
                        beam1 = {
                            'position': comp.position + Vector2(-50, 0),
                            'direction': Vector2(1, 0),
                            'amplitude': 0.5,
                            'phase': 0,
                            'path_length': 0,
                            'total_path_length': 100,
                            'source_type': 'laser'
                        }
                        beam2 = {
                            'position': comp.position + Vector2(-50, 0),
                            'direction': Vector2(1, 0),
                            'amplitude': 0.5,
                            'phase': 0,
                            'path_length': 0,
                            'total_path_length': 100,
                            'source_type': 'laser'
                        }
                        comp.add_beam(beam1)
                        comp.add_beam(beam2)
                        outputs = comp.finalize_frame()
                        
                        input_power = beam1['amplitude']**2 + beam2['amplitude']**2
                        output_power = sum(out['amplitude']**2 for out in outputs)
                        
                        print(f"    Two identical beams: each amp=0.5, total input power = {input_power:.3f}")
                        print(f"    Expected: combined amplitude = 1.0 at port A")
                        print(f"    Actual outputs:")
                        for out in outputs:
                            dir_name = ''
                            if out['direction'].x > 0.5: dir_name = 'RIGHT'
                            elif out['direction'].x < -0.5: dir_name = 'LEFT'
                            elif out['direction'].y > 0.5: dir_name = 'DOWN'
                            elif out['direction'].y < -0.5: dir_name = 'UP'
                            print(f"      → {dir_name}: amp={out['amplitude']:.3f}, power={out['amplitude']**2:.3f}")
                        print(f"    Total output power: {output_power:.3f}")
                        
                        # Test interference with two beams from different ports
                        print(f"\n  Test INTERFERENCE (two beams from A and B):")
                        
                        # Test with different phase differences
                        phase_tests = [0, math.pi/4, math.pi/2, math.pi]
                        
                        for phase_diff in phase_tests:
                            comp.reset_frame()
                            # Beam from left (port A)
                            beam1 = {
                                'position': comp.position + Vector2(-50, 0),
                                'direction': Vector2(1, 0),
                                'amplitude': 1/math.sqrt(2),
                                'phase': 0,
                                'path_length': 0,
                                'total_path_length': 100,
                                'source_type': 'laser'
                            }
                            # Beam from bottom (port B)
                            beam2 = {
                                'position': comp.position + Vector2(0, 50),
                                'direction': Vector2(0, -1),
                                'amplitude': 1/math.sqrt(2),
                                'phase': phase_diff,
                                'path_length': 0,
                                'total_path_length': 100,
                                'source_type': 'laser'
                            }
                            comp.add_beam(beam1)
                            comp.add_beam(beam2)
                            outputs = comp.finalize_frame()
                            
                            # Calculate powers
                            input_power = beam1['amplitude']**2 + beam2['amplitude']**2
                            output_power = sum(out['amplitude']**2 for out in outputs)
                            
                            print(f"\n    Phase difference: {phase_diff*180/math.pi:.0f}°")
                            print(f"    Input: 2 beams, total power = {input_power:.6f}")
                            print(f"    Outputs: {len(outputs)} beams")
                            for out in outputs:
                                dir_name = ''
                                if out['direction'].x > 0.5: dir_name = 'RIGHT'
                                elif out['direction'].x < -0.5: dir_name = 'LEFT'
                                elif out['direction'].y > 0.5: dir_name = 'DOWN'
                                elif out['direction'].y < -0.5: dir_name = 'UP'
                                print(f"      → {dir_name}: amp={out['amplitude']:.3f}, power={out['amplitude']**2:.3f}")
                            print(f"    Total output power: {output_power:.6f}")
                            print(f"    Energy conserved: {'YES ✓' if abs(output_power - input_power) < 0.001 else 'NO! ✗'}")
                        
                        print("No beam splitter found to test")
        
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
                
                if not self._is_position_occupied(x, y):
                    self._add_component(self.sidebar.selected, x, y)
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
                self._remove_component_at(event.pos)
    
    def _is_in_canvas(self, pos):
        """Check if position is within game canvas."""
        return (CANVAS_OFFSET_X <= pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH and
                CANVAS_OFFSET_Y <= pos[1] <= CANVAS_OFFSET_Y + CANVAS_HEIGHT)
    
    def _is_position_occupied(self, x, y):
        """Check if position is occupied."""
        # When dragging laser, don't count its current position as occupied
        if self.sidebar.selected == 'laser' and self.laser:
            # Skip laser position check when moving laser
            pass
        elif self.laser and self.laser.position.distance_to(Vector2(x, y)) < GRID_SIZE:
            return True
        
        # Check components
        for comp in self.components:
            if comp.position.distance_to(Vector2(x, y)) < GRID_SIZE:
                return True
        
        return False
    
    def _add_component(self, comp_type, x, y):
        """Add a component to the game."""
        print(f"Adding component: {comp_type} at ({x}, {y})")  # Debug
        
        if comp_type == 'laser':
            # Move existing laser instead of creating new one
            if self.laser:
                self.laser.position = Vector2(x, y)
                self.effects.add_placement_effect(x, y)
                print("Laser moved")
                
                # Clear OPD from all beam splitters when laser moves
                for c in self.components:
                    if c.component_type == 'beamsplitter' and hasattr(c, 'last_opd'):
                        c.last_opd = None
                        c.last_phase_diff = None
                
                return  # Don't add score for moving
            else:
                self.laser = Laser(x, y)
                print("Laser placed")
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
            return
        
        # Clear OPD when adding new components that might affect the path
        if comp_type in ['beamsplitter', 'mirror/', 'mirror\\']:
            for c in self.components:
                if c.component_type == 'beamsplitter' and hasattr(c, 'last_opd'):
                    c.last_opd = None
                    c.last_phase_diff = None
        
        self.effects.add_placement_effect(x, y)
        self._update_score(PLACEMENT_SCORE)
        
        if comp_type != 'laser':
            print(f"Total components: {len(self.components)}")  # Debug
    
    def _remove_component_at(self, pos):
        """Remove component at position."""
        # Note: Laser is handled separately (picked up, not removed)
        for i, comp in enumerate(self.components):
            if comp.contains_point(pos[0], pos[1]):
                # Clear OPD data if removing a beam splitter
                if comp.component_type == 'beamsplitter':
                    comp.last_opd = None
                    comp.last_phase_diff = None
                
                self.components.pop(i)
                self._update_score(-PLACEMENT_SCORE)
                
                # Clear OPD from all beam splitters when setup changes
                for c in self.components:
                    if c.component_type == 'beamsplitter' and hasattr(c, 'last_opd'):
                        c.last_opd = None
                        c.last_phase_diff = None
                break
    
    def _handle_control_action(self, action):
        """Handle control panel actions."""
        if action == 'Clear All':
            self.components.clear()
            # Keep the laser but move it back to default position
            if self.laser:
                self.laser.position = Vector2(CANVAS_OFFSET_X + GRID_SIZE, CANVAS_OFFSET_Y + 7 * GRID_SIZE)
            else:
                self.laser = Laser(CANVAS_OFFSET_X + GRID_SIZE, CANVAS_OFFSET_Y + 7 * GRID_SIZE)
            self.score = PLACEMENT_SCORE  # Reset to initial score
            self.controls.score = self.score
        elif action == 'Check Setup':
            self._check_solution()
        elif action == 'Toggle Laser':
            if self.laser:
                self.laser.enabled = not self.laser.enabled
    
    def _check_solution(self):
        """Check if player has built a valid interferometer."""
        if not self.laser:
            print("No laser placed!")
            return
            
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
        
        # Reset components for new frame
        for comp in self.components:
            if comp.component_type == 'detector':
                comp.intensity *= DETECTOR_DECAY_RATE  # Use configurable decay rate
            elif comp.component_type == 'beamsplitter':
                # Don't reset here - let the physics engine handle it
                pass
    
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
        self.grid.draw(self.screen, self.components, laser_pos)
        
        # Draw laser
        if self.laser:
            self.laser.draw(self.screen)
        
        # Draw components
        for comp in self.components:
            comp.draw(self.screen)
        
        # Trace and draw beams
        if self.laser and self.laser.enabled:
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
        
        # Draw debug info
        self._draw_debug_info()
    
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
    
    def _draw_beams(self):
        """Trace and draw laser beams."""
        self.beam_tracer.reset()
        
        # Add laser beam
        laser_beam = self.laser.emit_beam()
        if laser_beam:
            # Apply phase shift from slider to the initial phase
            phase_from_slider = math.radians(self.controls.phase)
            laser_beam['phase'] += phase_from_slider
            laser_beam['accumulated_phase'] = laser_beam['phase']  # Initialize accumulated phase
            self.beam_tracer.add_beam(laser_beam)
            
            # Debug: Draw beam start position
            if hasattr(self.laser, 'debug') and self.laser.debug:
                pygame.draw.circle(self.screen, (255, 255, 0),
                                 laser_beam['position'].tuple(), 3)
        
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
        
        # Skip very weak beams
        if beam_data['amplitude'] < 0.01:
            return
        
        # Color based on source type
        if beam_data['source_type'] == 'shifted':
            color = MAGENTA
        else:
            color = RED
        
        # Adjust alpha based on amplitude
        alpha = int(255 * beam_data['amplitude']**2)
        alpha = max(10, alpha)  # Ensure minimum visibility
        
        # Draw path
        for i in range(len(path) - 1):
            start = path[i].tuple() if hasattr(path[i], 'tuple') else path[i]
            end = path[i+1].tuple() if hasattr(path[i+1], 'tuple') else path[i+1]
            
            # Draw beam with adjusted color intensity based on amplitude
            beam_color = color
            if alpha < 255:
                # Dim the color based on amplitude
                beam_color = tuple(int(c * alpha / 255) for c in color)
            
            # Draw glow effect for stronger beams
            if beam_data['amplitude'] > 0.5:
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
        
        # Show if using ideal components
        info_y = 20
        if IDEAL_COMPONENTS:
            ideal_font = pygame.font.Font(None, 18)
            ideal_text = ideal_font.render("IDEAL COMPONENTS (No Losses)", True, GREEN)
            ideal_rect = ideal_text.get_rect(right=CANVAS_OFFSET_X + CANVAS_WIDTH - 20, y=info_y)
            self.screen.blit(ideal_text, ideal_rect)
            info_y += 25
        
        # Show physics model info
        physics_font = pygame.font.Font(None, 16)
        physics_text = physics_font.render("Physics: BS +90° reflection, Mirror +180° reflection", True, CYAN)
        physics_rect = physics_text.get_rect(right=CANVAS_OFFSET_X + CANVAS_WIDTH - 20, y=info_y)
        self.screen.blit(physics_text, physics_rect)
        
        # Show wavelength info
        info_font = pygame.font.Font(None, 16)
        wave_text = info_font.render(f"λ = {WAVELENGTH}px, Grid = {GRID_SIZE}px", True, WHITE)
        wave_rect = wave_text.get_rect(right=CANVAS_OFFSET_X + CANVAS_WIDTH - 20, y=45)
        self.screen.blit(wave_text, wave_rect)
        
        # Show control hints
        toggle_text = info_font.render("D: debug | O: OPD info | T: test BS | P: phase info | V: visual test", True, WHITE)
        toggle_rect = toggle_text.get_rect(left=CANVAS_OFFSET_X + 20, y=45)
        self.screen.blit(toggle_text, toggle_rect)
    
    def _draw_debug_info(self):
        """Draw optical path difference info if interferometer has interference."""
        if not self.show_opd_info:
            return
            
        # First check for beam splitter with recent interference
        interfering_bs = None
        for comp in self.components:
            if (comp.component_type == 'beamsplitter' and
                hasattr(comp, 'last_opd') and
                comp.last_opd is not None):
                interfering_bs = comp
                break
        
        if interfering_bs:
            # Get OPD from the beam splitter where interference happened
            opd = interfering_bs.last_opd
            phase_diff = interfering_bs.last_phase_diff
            
            # Calculate phase contribution from OPD
            phase_from_opd = (abs(opd) * 2 * math.pi / WAVELENGTH) % (2 * math.pi)
            
            # Find detectors to show output intensities
            detectors = [c for c in self.components if c.component_type == 'detector' and c.intensity > 0.01]
            
            # Draw info box
            font = pygame.font.Font(None, 18)
            info_y = CANVAS_OFFSET_Y + CANVAS_HEIGHT - 120
            
            # Background
            bg_rect = pygame.Rect(CANVAS_OFFSET_X + 10, info_y, 360, 110)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 200))
            pygame.draw.rect(s, CYAN, s.get_rect(), 1)
            self.screen.blit(s, bg_rect.topleft)
            
            # Text
            title_text = font.render("Interferometer Status (at beam splitter):", True, CYAN)
            opd_text = font.render(f"Optical Path Difference: {abs(opd):.1f} px = {abs(opd)/WAVELENGTH:.2f}λ", True, WHITE)
            phase_from_opd = abs(opd) * 2 * math.pi / WAVELENGTH
            phase_opd_text = font.render(f"Phase from path difference: {phase_from_opd*180/math.pi:.1f}°", True, WHITE)
            phase_text = font.render(f"Total phase difference (including components): {phase_diff*180/math.pi:.1f}°", True, GREEN)
            
            self.screen.blit(title_text, (bg_rect.x + 10, bg_rect.y + 5))
            self.screen.blit(opd_text, (bg_rect.x + 10, bg_rect.y + 25))
            self.screen.blit(phase_opd_text, (bg_rect.x + 10, bg_rect.y + 45))
            self.screen.blit(phase_text, (bg_rect.x + 10, bg_rect.y + 65))
            
            # Show detector intensities if available
            if len(detectors) >= 2:
                total_intensity = sum(d.intensity for d in detectors)
                detector_text = font.render(f"Detector Intensities: {detectors[0].intensity:.2f} + {detectors[1].intensity:.2f} = {total_intensity:.2f}", True, CYAN)
                self.screen.blit(detector_text, (bg_rect.x + 10, bg_rect.y + 85))
        else:
            # Fallback: Show detector-based OPD if available
            active_detectors = [c for c in self.components
                              if c.component_type == 'detector' and c.intensity > 0.01]
            
            if len(active_detectors) >= 2:
                # Calculate optical path difference from detectors
                path1 = active_detectors[0].total_path_length
                path2 = active_detectors[1].total_path_length
                opd = abs(path1 - path2)
                
                # Calculate phase difference from OPD
                phase_from_opd = (opd * 2 * math.pi / WAVELENGTH) % (2 * math.pi)
                
                # Draw info box
                font = pygame.font.Font(None, 18)
                info_y = CANVAS_OFFSET_Y + CANVAS_HEIGHT - 60
                
                # Background
                bg_rect = pygame.Rect(CANVAS_OFFSET_X + 10, info_y, 280, 50)
                s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                s.fill((0, 0, 0, 200))
                pygame.draw.rect(s, CYAN, s.get_rect(), 1)
                self.screen.blit(s, bg_rect.topleft)
                
                # Text
                opd_text = font.render(f"Optical Path Difference: {opd:.1f} px", True, CYAN)
                phase_text = font.render(f"Phase from OPD: {phase_from_opd*180/math.pi:.1f}° ({opd/WAVELENGTH:.2f}λ)", True, WHITE)
                
                self.screen.blit(opd_text, (bg_rect.x + 10, bg_rect.y + 5))
                self.screen.blit(phase_text, (bg_rect.x + 10, bg_rect.y + 25))
            else:
                # Show hint if no interference yet
                font = pygame.font.Font(None, 16)
                hint_text = f"Tip: Create asymmetric paths for non-zero OPD (λ={WAVELENGTH}px ≠ grid={GRID_SIZE}px)"
                hint = font.render(hint_text, True, WHITE)
                hint_rect = hint.get_rect(center=(CANVAS_OFFSET_X + CANVAS_WIDTH // 2,
                                                 CANVAS_OFFSET_Y + CANVAS_HEIGHT - 20))
                
                # Background for hint
                bg_rect = hint_rect.inflate(20, 10)
                s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                s.fill((0, 0, 0, 150))
                self.screen.blit(s, bg_rect.topleft)
                
                self.screen.blit(hint, hint_rect)
