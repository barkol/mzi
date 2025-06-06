"""Sidebar UI for component selection with responsive width support."""
import pygame
import math
from config.settings import *

class Sidebar:
    """Component selection sidebar with responsive width for fullscreen."""
    
    def __init__(self, sound_manager=None):
        self.sound_manager = sound_manager
        self.components = [
            {'type': 'laser', 'name': 'Laser Source', 'desc': 'Move the laser'},
            {'type': 'beamsplitter', 'name': 'Beam Splitter', 'desc': '50/50 split'},
            {'type': 'mirror/', 'name': 'Mirror /', 'desc': 'Diagonal reflection'},
            {'type': 'mirror\\', 'name': 'Mirror \\', 'desc': 'Diagonal reflection'},
            {'type': 'detector', 'name': 'Detector', 'desc': 'Shows interference'}
        ]
        self.selected = None
        self.hover_index = -1
        self.last_hover_index = -1
        self.dragging = False
        self.drag_offset = (0, 0)
        self.last_dragged = None
        self.can_add_callback = None
        
        # Update dimensions
        self._update_dimensions()
    
    def _update_dimensions(self):
        """Update sidebar dimensions based on current scale and display mode."""
        # Use responsive width from settings
        sidebar_width = get_sidebar_width()
        self.rect = pygame.Rect(0, 0, sidebar_width, WINDOW_HEIGHT)
    
    def handle_event(self, event):
        """Handle mouse events."""
        if event.type == pygame.MOUSEMOTION:
            if not self.dragging:
                old_hover = self.hover_index
                self.hover_index = self._get_component_at_pos(event.pos)
                
                # Play hover sound when entering a new component
                if self.hover_index != old_hover and self.hover_index >= 0:
                    if self.sound_manager:
                        self.sound_manager.play('button_hover', volume=0.3)
                        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self._get_component_at_pos(event.pos)
            if index >= 0:
                comp_type = self.components[index]['type']
                # Check if we can add this component (laser always allowed, it moves)
                if comp_type == 'laser' or self._can_add_component():
                    self.selected = comp_type
                    self.last_dragged = self.selected
                    self.dragging = True
                    # Calculate offset from component center
                    comp_rect = self._get_component_rect(index)
                    self.drag_offset = (event.pos[0] - comp_rect.centerx,
                                      event.pos[1] - comp_rect.centery)
                    
                    # Play drag start sound
                    if self.sound_manager:
                        self.sound_manager.play('drag_start')
                    return True
                else:
                    # Can't add - play error sound
                    if self.sound_manager:
                        self.sound_manager.play('invalid_placement')
                        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_dragging = self.dragging
            self.dragging = False
            return was_dragging
        
        return False
    
    def set_can_add_callback(self, callback):
        """Set callback function to check if components can be added."""
        self.can_add_callback = callback
    
    def _can_add_component(self):
        """Check if a component can be added."""
        if self.can_add_callback:
            return self.can_add_callback()
        return True
    
    def clear_selection(self):
        """Clear the current selection."""
        self.selected = None
        self.last_dragged = None
    
    def _get_component_at_pos(self, pos):
        """Get component index at mouse position."""
        if not self.rect.collidepoint(pos):
            return -1
        
        for i, comp in enumerate(self.components):
            comp_rect = self._get_component_rect(i)
            if comp_rect.collidepoint(pos):
                return i
        
        return -1
    
    def _get_component_rect(self, index):
        """Get rectangle for component at index - responsive sizing."""
        # In fullscreen, use more generous spacing
        if IS_FULLSCREEN:
            y_offset = scale(120)
            component_height = scale(90)
            component_spacing = scale(110)
            margin = scale(20)
        else:
            y_offset = scale(100)
            component_height = scale(80)
            component_spacing = scale(100)
            margin = scale(15)
        
        # Component width adapts to sidebar width
        comp_width = self.rect.width - margin * 2
        
        return pygame.Rect(
            self.rect.x + margin, 
            y_offset + index * component_spacing, 
            comp_width, 
            component_height
        )
    
    def get_drag_info(self):
        """Get current drag information."""
        return self.selected, self.dragging
    
    def draw(self, screen):
        """Draw sidebar."""
        # Ensure dimensions are current
        self._update_dimensions()
        
        # Background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((DARK_PURPLE[0], DARK_PURPLE[1], DARK_PURPLE[2], 180))
        screen.blit(s, self.rect.topleft)
        
        # Border
        pygame.draw.line(screen, PURPLE,
                        (self.rect.right, 0),
                        (self.rect.right, WINDOW_HEIGHT), scale(2))
        
        # Title - larger in fullscreen
        title_size = scale_font(32) if IS_FULLSCREEN else scale_font(28)
        font_title = pygame.font.Font(None, title_size)
        title = font_title.render("Components", True, CYAN)
        title_rect = title.get_rect(centerx=self.rect.centerx, y=scale(50))
        screen.blit(title, title_rect)
        
        # Component cards
        name_size = scale_font(22) if IS_FULLSCREEN else scale_font(20)
        desc_size = scale_font(18) if IS_FULLSCREEN else scale_font(16)
        font_name = pygame.font.Font(None, name_size)
        font_desc = pygame.font.Font(None, desc_size)
        
        for i, comp in enumerate(self.components):
            # Card rectangle
            card_rect = self._get_component_rect(i)
            
            # Check if component can be added (laser always allowed)
            can_add = comp['type'] == 'laser' or self._can_add_component()
            
            # Hover/selected effect
            if i == self.hover_index and can_add:
                color = CYAN if comp['type'] == self.selected else PURPLE
                pygame.draw.rect(screen, color, card_rect, scale(2))
                
                # Glow effect
                s = pygame.Surface((card_rect.width + scale(10), card_rect.height + scale(10)), pygame.SRCALPHA)
                pygame.draw.rect(s, (color[0], color[1], color[2], 30), s.get_rect(), border_radius=scale(5))
                screen.blit(s, (card_rect.x - scale(5), card_rect.y - scale(5)))
            else:
                # Draw a faint border
                s = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
                border_color = (100, 100, 100) if not can_add else PURPLE
                pygame.draw.rect(s, (border_color[0], border_color[1], border_color[2], 100), s.get_rect(), scale(1))
                screen.blit(s, card_rect.topleft)
            
            # Fill
            s = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
            fill_alpha = 20 if not can_add else 40
            pygame.draw.rect(s, (PURPLE[0], PURPLE[1], PURPLE[2], fill_alpha), s.get_rect())
            screen.blit(s, card_rect.topleft)
            
            # Component icon - larger in fullscreen
            icon_offset = scale(40) if IS_FULLSCREEN else scale(35)
            icon_center = (card_rect.x + icon_offset, card_rect.centery)
            icon_color = (100, 100, 100) if not can_add and comp['type'] != 'laser' else None
            self._draw_component_icon(screen, comp['type'], icon_center, icon_color)
            
            # Text
            text_color = (150, 150, 150) if not can_add and comp['type'] != 'laser' else WHITE
            desc_color = (100, 100, 100) if not can_add and comp['type'] != 'laser' else (*WHITE, 180)
            
            name = font_name.render(comp['name'], True, text_color)
            desc = font_desc.render(comp['desc'], True, desc_color)
            
            # Position text with more space in fullscreen
            text_offset = scale(70) if IS_FULLSCREEN else scale(65)
            name_x = card_rect.x + text_offset
            
            screen.blit(name, (name_x, card_rect.y + scale(18)))
            screen.blit(desc, (name_x, card_rect.y + scale(45)))
            
            # Show "LIMIT" for disabled components
            if not can_add and comp['type'] != 'laser':
                limit_font = pygame.font.Font(None, scale_font(12))
                limit_text = limit_font.render("LIMIT", True, (255, 100, 100))
                limit_rect = limit_text.get_rect(right=card_rect.right - scale(5), 
                                               bottom=card_rect.bottom - scale(5))
                screen.blit(limit_text, limit_rect)
    
    def _draw_component_icon(self, screen, comp_type, center, override_color=None):
        """Draw simplified component icon - larger in fullscreen."""
        color = override_color if override_color else CYAN
        
        # Scale icons up in fullscreen
        icon_scale = 1.2 if IS_FULLSCREEN else 1.0
        
        if comp_type == 'laser':
            # Laser icon - circle with rays
            radius = scale(int(15 * icon_scale))
            pygame.draw.circle(screen, CYAN, center, radius)
            # Rays
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                start_x = center[0] + radius * math.cos(rad)
                start_y = center[1] + radius * math.sin(rad)
                end_x = center[0] + scale(int(22 * icon_scale)) * math.cos(rad)
                end_y = center[1] + scale(int(22 * icon_scale)) * math.sin(rad)
                pygame.draw.line(screen, CYAN, (start_x, start_y), (end_x, end_y), scale(2))
        elif comp_type == 'beamsplitter':
            size = scale(int(35 * icon_scale))
            half_size = size // 2
            rect = pygame.Rect(center[0] - half_size, center[1] - half_size, size, size)
            pygame.draw.rect(screen, color, rect, scale(2))
            pygame.draw.line(screen, color, rect.topleft, rect.bottomright, scale(2))
        elif comp_type.startswith('mirror'):
            # Mirror icons
            size = scale(int(35 * icon_scale))
            half_size = size // 2
            if '/' in comp_type:
                pygame.draw.line(screen, color,
                               (center[0] - half_size, center[1] + half_size),
                               (center[0] + half_size, center[1] - half_size), scale(4))
            else:
                pygame.draw.line(screen, color,
                               (center[0] - half_size, center[1] - half_size),
                               (center[0] + half_size, center[1] + half_size), scale(4))
        elif comp_type == 'detector':
            radius = scale(int(18 * icon_scale))
            pygame.draw.circle(screen, color, center, radius, scale(2))
            pygame.draw.circle(screen, color, center, scale(int(6 * icon_scale)))