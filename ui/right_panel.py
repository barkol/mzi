"""Right panel for help and debug information with responsive width."""
import pygame
from config.settings import *

class RightPanel:
    """Right panel displaying help and debug information with responsive sizing."""
    
    def __init__(self, sound_manager=None):
        self.sound_manager = sound_manager
        self.debug_messages = []
        self.max_debug_messages = 20
        self.show_help = True
        self.scroll_offset = 0
        
        # Initialize dimensions
        self._update_dimensions()
        
    def _update_dimensions(self):
        """Update panel dimensions based on current scale and display mode."""
        # Get responsive width
        panel_width = get_right_panel_width()
        
        if IS_FULLSCREEN:
            # In fullscreen, justify to the right edge
            panel_x = WINDOW_WIDTH - panel_width
            self.rect = pygame.Rect(
                panel_x,
                0,
                panel_width,
                WINDOW_HEIGHT
            )
        else:
            # In windowed mode, position after canvas
            panel_x = CANVAS_OFFSET_X + CANVAS_WIDTH + scale(30)
            
            # Make sure panel fits
            if panel_x + panel_width > WINDOW_WIDTH:
                panel_width = WINDOW_WIDTH - panel_x
                if panel_width < scale(200):  # Minimum width
                    panel_width = scale(250)
                    panel_x = WINDOW_WIDTH - panel_width
            
            self.rect = pygame.Rect(
                panel_x,
                0,
                panel_width,
                WINDOW_HEIGHT
            )
    
    def add_debug_message(self, message):
        """Add a debug message to the panel."""
        self.debug_messages.append(message)
        if len(self.debug_messages) > self.max_debug_messages:
            self.debug_messages.pop(0)
    
    def clear_debug_messages(self):
        """Clear all debug messages."""
        self.debug_messages = []
        
    def toggle_help(self):
        """Toggle between help and debug view."""
        self.show_help = not self.show_help
        if self.sound_manager:
            self.sound_manager.play('panel_open')
        
    def handle_event(self, event):
        """Handle scroll events."""
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset += event.y * scale(20)
                self.scroll_offset = max(0, self.scroll_offset)
                return True
        return False
    
    def draw(self, screen):
        """Draw the right panel."""
        # Update dimensions in case scale changed
        self._update_dimensions()
        
        # Background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((DARK_PURPLE[0], DARK_PURPLE[1], DARK_PURPLE[2], 180))
        screen.blit(s, self.rect.topleft)
        
        # Border
        pygame.draw.line(screen, PURPLE,
                        (self.rect.left, 0),
                        (self.rect.left, WINDOW_HEIGHT), scale(2))
        
        # Title - larger in fullscreen
        title_size = scale_font(28) if IS_FULLSCREEN else scale_font(24)
        font_title = pygame.font.Font(None, title_size)
        title_text = "MaZeInvader: Help" if self.show_help else "MaZeInvader: Debug Log"
        title = font_title.render(title_text, True, CYAN)
        title_rect = title.get_rect(centerx=self.rect.centerx, y=scale(20))
        
        # Make sure title fits
        if title_rect.width > self.rect.width - scale(20):
            # Use smaller font if title doesn't fit
            font_title = pygame.font.Font(None, scale_font(20))
            title = font_title.render(title_text, True, CYAN)
            title_rect = title.get_rect(centerx=self.rect.centerx, y=scale(20))
        
        screen.blit(title, title_rect)
        
        # Content area
        content_y = scale(60)
        
        if self.show_help:
            self._draw_help_content(screen, content_y)
        else:
            self._draw_debug_content(screen, content_y)
    
    def _draw_help_content(self, screen, start_y):
        """Draw help information - responsive text sizing."""
        header_size = scale_font(22) if IS_FULLSCREEN else scale_font(20)
        text_size = scale_font(18) if IS_FULLSCREEN else scale_font(16)
        
        font_header = pygame.font.Font(None, header_size)
        font_text = pygame.font.Font(None, text_size)
        
        y = start_y - self.scroll_offset
        x_margin = self.rect.x + scale(15)
        line_height = scale_font(22) if IS_FULLSCREEN else scale_font(20)
        
        # Clip content to panel
        clip_rect = pygame.Rect(self.rect.x, start_y, self.rect.width, self.rect.height - start_y)
        screen.set_clip(clip_rect)
        
        # Controls section
        if y > 0:
            header = font_header.render("CONTROLS", True, CYAN)
            if x_margin + header.get_width() <= self.rect.right - scale(10):
                screen.blit(header, (x_margin, y))
        y += line_height + scale(5)
        
        controls = [
            ("Drag & Drop", "Place components"),
            ("Left Click", "Remove component"),
            ("L", "Toggle leaderboard"),
            ("G", "Toggle debug mode"),
            ("O", "Toggle OPD display"),
            ("H", "Show help"),
            ("Shift+H", "Toggle help/debug"),
            ("Shift+N", "New session"),
            ("", ""),
            ("BUTTONS", ""),
            ("Clear All", "Remove all components"),
            ("Check Setup", "Verify challenge"),
            ("Toggle Laser", "Turn laser on/off"),
            ("Load Challenge", "Cycle challenges"),
            ("Load Fields", "Cycle map layouts"),
            ("", ""),
            ("SOUND CONTROLS", ""),
            ("Shift+S", "Toggle sound"),
            ("Shift+V", "Volume up 10%"),
            ("Ctrl+Shift+V", "Volume down 10%"),
            ("", ""),
            ("WINDOW", ""),
            ("F11", "Enter fullscreen"),
            ("ESC", "Exit fullscreen"),
        ]
        
        # Show current sound status
        if self.sound_manager:
            sound_status = "ON" if self.sound_manager.enabled else "OFF"
            volume_percent = int(self.sound_manager.master_volume * 100)
            controls.append(("", ""))
            controls.append(("Sound:", f"{sound_status} ({volume_percent}%)"))
        
        # Add fullscreen info
        if IS_FULLSCREEN:
            controls.append(("", ""))
            controls.append(("Mode:", "FULLSCREEN"))
            controls.append(("Canvas:", f"{CANVAS_GRID_COLS}×{CANVAS_GRID_ROWS} cells"))
        
        # Add map features info
        controls.append(("", ""))
        controls.append(("MAP FEATURES", ""))
        controls.append(("Red Blocks", "Block beam paths"))
        controls.append(("Gold Fields", "+100 pts × intensity"))
        controls.append(("Leaderboard", "Tracks map used"))
        controls.append(("", ""))
        controls.append(("TIP", ""))
        controls.append(("", "Use Load Fields to"))
        controls.append(("", "cycle through maps!"))
        
        for key, desc in controls:
            if key == "" and desc == "":
                y += line_height // 2
                continue
            elif desc == "":  # Section header
                if y > 0 and y < self.rect.height:
                    text = font_header.render(key, True, CYAN)
                    if x_margin + text.get_width() <= self.rect.right - scale(10):
                        screen.blit(text, (x_margin, y))
                y += line_height + scale(5)
            else:
                if y > 0 and y < self.rect.height:
                    # Adjust spacing based on panel width
                    key_width = scale(110) if IS_FULLSCREEN else scale(90)
                    if self.rect.width < scale(350):
                        key_width = scale(70)
                    
                    key_surface = font_text.render(f"{key:13}", True, WHITE)
                    desc_surface = font_text.render(desc, True, (200, 200, 200))
                    
                    # Draw key
                    if x_margin + key_surface.get_width() <= self.rect.right - scale(10):
                        screen.blit(key_surface, (x_margin, y))
                    
                    # Draw description (wrap if needed)
                    desc_x = x_margin + key_width
                    if desc_x + desc_surface.get_width() > self.rect.right - scale(10):
                        # Text too long, use smaller font or truncate
                        max_width = self.rect.right - desc_x - scale(10)
                        if max_width > scale(50):
                            # Truncate text
                            while desc_surface.get_width() > max_width and len(desc) > 5:
                                desc = desc[:-1]
                                desc_surface = font_text.render(desc + "...", True, (200, 200, 200))
                    
                    if desc_x + desc_surface.get_width() <= self.rect.right - scale(10):
                        screen.blit(desc_surface, (desc_x, y))
                    
                y += line_height
        
        # Remove clipping
        screen.set_clip(None)
    
    def _draw_debug_content(self, screen, start_y):
        """Draw debug log messages - responsive sizing."""
        text_size = scale_font(16) if IS_FULLSCREEN else scale_font(14)
        font = pygame.font.Font(None, text_size)
        y = start_y
        x_margin = self.rect.x + scale(10)
        line_height = scale_font(18) if IS_FULLSCREEN else scale_font(16)
        
        # Clip content to panel
        clip_rect = pygame.Rect(self.rect.x, start_y, self.rect.width, self.rect.height - start_y - scale(40))
        screen.set_clip(clip_rect)
        
        if not self.debug_messages:
            no_msg = font.render("No debug messages", True, (150, 150, 150))
            if x_margin + no_msg.get_width() <= self.rect.right - scale(10):
                screen.blit(no_msg, (x_margin, y))
            hint = font.render("Press G to enable debug", True, (100, 100, 100))
            if x_margin + hint.get_width() <= self.rect.right - scale(10):
                screen.blit(hint, (x_margin, y + scale(20)))
        else:
            # Draw messages from bottom to top (newest first)
            for i, message in enumerate(reversed(self.debug_messages)):
                if y > self.rect.height - scale(40):
                    break
                
                # Calculate max chars based on panel width
                char_width = font.size('W')[0]  # Use widest character
                max_chars = max(20, (self.rect.width - scale(20)) // char_width)
                
                # Truncate long messages
                if len(message) > max_chars:
                    message = message[:max_chars-3] + "..."
                
                # Color code messages
                color = WHITE
                if "WARNING" in message:
                    color = (255, 200, 0)
                elif "ERROR" in message:
                    color = (255, 100, 100)
                elif "SUCCESS" in message:
                    color = (100, 255, 100)
                elif "Sound:" in message or "Volume:" in message:
                    color = (100, 200, 255)
                elif "Fullscreen" in message:
                    color = CYAN
                elif "Loaded fields:" in message:
                    color = (255, 200, 100)  # Orange for field loading
                elif "map layouts available" in message:
                    color = (100, 255, 100)  # Green for available maps
                
                text = font.render(message, True, color)
                if x_margin + text.get_width() <= self.rect.right - scale(10):
                    screen.blit(text, (x_margin, y))
                y += line_height
        
        # Remove clipping
        screen.set_clip(None)
        
        # Show message count at bottom
        count_text = font.render(f"Messages: {len(self.debug_messages)}/{self.max_debug_messages}",
                               True, (150, 150, 150))
        count_y = self.rect.height - scale(30)
        if x_margin + count_text.get_width() <= self.rect.right - scale(10):
            screen.blit(count_text, (x_margin, count_y))