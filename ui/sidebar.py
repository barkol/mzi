"""Sidebar UI for component selection."""
import pygame
from config.settings import *

class Sidebar:
    """Component selection sidebar."""
    
    def __init__(self):
        self.rect = pygame.Rect(0, 0, CANVAS_OFFSET_X - 50, WINDOW_HEIGHT)
        self.components = [
            {'type': 'beamsplitter', 'name': 'Beam Splitter', 'desc': '50/50 split'},
            {'type': 'mirror/', 'name': 'Mirror /', 'desc': 'Diagonal reflection'},
            {'type': 'mirror\\', 'name': 'Mirror \\', 'desc': 'Diagonal reflection'},
            {'type': 'detector', 'name': 'Detector', 'desc': 'Shows interference'}
        ]
        self.selected = None
        self.hover_index = -1
    
    def handle_event(self, event):
        """Handle mouse events."""
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = self._get_component_at_pos(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            index = self._get_component_at_pos(event.pos)
            if index >= 0:
                self.selected = self.components[index]['type']
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.selected = None
        
        return False
    
    def _get_component_at_pos(self, pos):
        """Get component index at mouse position."""
        if not self.rect.collidepoint(pos):
            return -1
        
        y_offset = 150
        for i, comp in enumerate(self.components):
            comp_rect = pygame.Rect(20, y_offset + i * 100, self.rect.width - 40, 80)
            if comp_rect.collidepoint(pos):
                return i
        
        return -1
    
    def draw(self, screen):
        """Draw sidebar."""
        # Background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*DARK_PURPLE, 180), self.rect)
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
        y_offset = 150
        font_name = pygame.font.Font(None, 20)
        font_desc = pygame.font.Font(None, 16)
        
        for i, comp in enumerate(self.components):
            # Card rectangle
            card_rect = pygame.Rect(20, y_offset + i * 100, self.rect.width - 40, 80)
            
            # Hover/selected effect
            if i == self.hover_index or comp['type'] == self.selected:
                color = CYAN if comp['type'] == self.selected else PURPLE
                pygame.draw.rect(screen, color, card_rect, 2)
                
                # Glow effect
                s = pygame.Surface((card_rect.width + 10, card_rect.height + 10), pygame.SRCALPHA)
                pygame.draw.rect(s, (*color, 30), s.get_rect(), border_radius=5)
                screen.blit(s, (card_rect.x - 5, card_rect.y - 5))
            else:
                pygame.draw.rect(screen, (*PURPLE, 100), card_rect, 1)
            
            # Fill
            s = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (*PURPLE, 40), s.get_rect())
            screen.blit(s, card_rect.topleft)
            
            # Component icon (simplified)
            icon_center = (card_rect.x + 40, card_rect.centery)
            self._draw_component_icon(screen, comp['type'], icon_center)
            
            # Text
            name = font_name.render(comp['name'], True, WHITE)
            desc = font_desc.render(comp['desc'], True, (*WHITE, 180))
            
            screen.blit(name, (card_rect.x + 70, card_rect.y + 20))
            screen.blit(desc, (card_rect.x + 70, card_rect.y + 45))
    
    def _draw_component_icon(self, screen, comp_type, center):
        """Draw simplified component icon."""
        if comp_type == 'beamsplitter':
            rect = pygame.Rect(center[0] - 15, center[1] - 15, 30, 30)
            pygame.draw.rect(screen, CYAN, rect, 2)
            pygame.draw.line(screen, CYAN, rect.topleft, rect.bottomright, 2)
        elif comp_type.startswith('mirror'):
            if '/' in comp_type:
                pygame.draw.line(screen, MAGENTA, 
                               (center[0] - 15, center[1] + 15),
                               (center[0] + 15, center[1] - 15), 4)
            else:
                pygame.draw.line(screen, MAGENTA,
                               (center[0] - 15, center[1] - 15),
                               (center[0] + 15, center[1] + 15), 4)
        elif comp_type == 'detector':
            pygame.draw.circle(screen, GREEN, center, 15, 2)
            pygame.draw.circle(screen, GREEN, center, 5)