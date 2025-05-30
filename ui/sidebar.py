"""Sidebar UI for component selection."""
import pygame
import math
from config.settings import *

class Sidebar:
    """Component selection sidebar."""
    
    def __init__(self):
        self.rect = pygame.Rect(0, 0, CANVAS_OFFSET_X - 50, WINDOW_HEIGHT)
        self.components = [
            {'type': 'laser', 'name': 'Laser Source', 'desc': 'Move the laser'},
            {'type': 'beamsplitter', 'name': 'Beam Splitter', 'desc': '50/50 split'},
            {'type': 'mirror/', 'name': 'Mirror /', 'desc': 'Diagonal reflection'},
            {'type': 'mirror\\', 'name': 'Mirror \\', 'desc': 'Diagonal reflection'},
            {'type': 'detector', 'name': 'Detector', 'desc': 'Shows interference'}
        ]
        self.selected = None
        self.hover_index = -1
        self.dragging = False
        self.drag_offset = (0, 0)
        self.last_dragged = None  # Track what was dragged
    
    def handle_event(self, event):
        """Handle mouse events."""
        if event.type == pygame.MOUSEMOTION:
            if not self.dragging:
                self.hover_index = self._get_component_at_pos(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self._get_component_at_pos(event.pos)
            if index >= 0:
                self.selected = self.components[index]['type']
                self.last_dragged = self.selected  # Remember what we're dragging
                self.dragging = True
                # Calculate offset from component center
                comp_rect = self._get_component_rect(index)
                self.drag_offset = (event.pos[0] - comp_rect.centerx,
                                  event.pos[1] - comp_rect.centery)
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_dragging = self.dragging
            self.dragging = False
            # Don't clear selected immediately - let game handle it first
            return was_dragging
        
        return False
    
    def clear_selection(self):
        """Clear the current selection."""
        self.selected = None
        self.last_dragged = None
    
    def _get_component_at_pos(self, pos):
        """Get component index at mouse position."""
        if not self.rect.collidepoint(pos):
            return -1
        
        y_offset = 120
        for i, comp in enumerate(self.components):
            comp_rect = pygame.Rect(20, y_offset + i * 90, self.rect.width - 40, 70)
            if comp_rect.collidepoint(pos):
                return i
        
        return -1
    
    def _get_component_rect(self, index):
        """Get rectangle for component at index."""
        y_offset = 120
        return pygame.Rect(20, y_offset + index * 90, self.rect.width - 40, 70)
    
    def get_drag_info(self):
        """Get current drag information."""
        return self.selected, self.dragging
    
    def draw(self, screen):
        """Draw sidebar."""
        # Background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((DARK_PURPLE[0], DARK_PURPLE[1], DARK_PURPLE[2], 180))
        screen.blit(s, self.rect.topleft)
        
        # Border
        pygame.draw.line(screen, PURPLE,
                        (self.rect.right, 0),
                        (self.rect.right, WINDOW_HEIGHT), 2)
        
        # Title
        font_title = pygame.font.Font(None, 28)
        title = font_title.render("Components", True, CYAN)
        title_rect = title.get_rect(centerx=self.rect.centerx, y=50)
        screen.blit(title, title_rect)
        
        # Component cards
        y_offset = 120
        font_name = pygame.font.Font(None, 20)
        font_desc = pygame.font.Font(None, 16)
        
        for i, comp in enumerate(self.components):
            # Card rectangle
            card_rect = pygame.Rect(20, y_offset + i * 90, self.rect.width - 40, 70)
            
            # Hover/selected effect
            if i == self.hover_index or (comp['type'] == self.selected and not self.dragging):
                color = CYAN if comp['type'] == self.selected else PURPLE
                pygame.draw.rect(screen, color, card_rect, 2)
                
                # Glow effect
                s = pygame.Surface((card_rect.width + 10, card_rect.height + 10), pygame.SRCALPHA)
                pygame.draw.rect(s, (color[0], color[1], color[2], 30), s.get_rect(), border_radius=5)
                screen.blit(s, (card_rect.x - 5, card_rect.y - 5))
            else:
                # Draw a faint border
                s = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(s, (PURPLE[0], PURPLE[1], PURPLE[2], 100), s.get_rect(), 1)
                screen.blit(s, card_rect.topleft)
            
            # Fill
            s = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (PURPLE[0], PURPLE[1], PURPLE[2], 40), s.get_rect())
            screen.blit(s, card_rect.topleft)
            
            # Component icon (simplified)
            icon_center = (card_rect.x + 35, card_rect.centery)
            self._draw_component_icon(screen, comp['type'], icon_center)
            
            # Text
            name = font_name.render(comp['name'], True, WHITE)
            desc = font_desc.render(comp['desc'], True, (*WHITE, 180))
            
            screen.blit(name, (card_rect.x + 65, card_rect.y + 15))
            screen.blit(desc, (card_rect.x + 65, card_rect.y + 40))
    
    def _draw_component_icon(self, screen, comp_type, center):
        """Draw simplified component icon."""
        if comp_type == 'laser':
            # Laser icon - circle with rays (turquoise)
            pygame.draw.circle(screen, CYAN, center, 12)
            # Rays
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                start_x = center[0] + 12 * math.cos(rad)
                start_y = center[1] + 12 * math.sin(rad)
                end_x = center[0] + 18 * math.cos(rad)
                end_y = center[1] + 18 * math.sin(rad)
                pygame.draw.line(screen, CYAN, (start_x, start_y), (end_x, end_y), 2)
        elif comp_type == 'beamsplitter':
            rect = pygame.Rect(center[0] - 15, center[1] - 15, 30, 30)
            pygame.draw.rect(screen, CYAN, rect, 2)
            pygame.draw.line(screen, CYAN, rect.topleft, rect.bottomright, 2)
        elif comp_type.startswith('mirror'):
            # Mirror icons in turquoise
            if '/' in comp_type:
                pygame.draw.line(screen, CYAN,
                               (center[0] - 15, center[1] + 15),
                               (center[0] + 15, center[1] - 15), 4)
            else:
                pygame.draw.line(screen, CYAN,
                               (center[0] - 15, center[1] - 15),
                               (center[0] + 15, center[1] + 15), 4)
        elif comp_type == 'detector':
            pygame.draw.circle(screen, CYAN, center, 15, 2)
            pygame.draw.circle(screen, CYAN, center, 5)
