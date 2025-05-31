"""Right panel for help and debug information with sound support."""
import pygame
from config.settings import *

class RightPanel:
    """Right panel displaying help and debug information."""
    
    def __init__(self, sound_manager=None):
        self.rect = pygame.Rect(
            CANVAS_OFFSET_X + CANVAS_WIDTH + 50,
            0,
            WINDOW_WIDTH - (CANVAS_OFFSET_X + CANVAS_WIDTH + 50),
            WINDOW_HEIGHT
        )
        self.debug_messages = []
        self.max_debug_messages = 20
        self.show_help = True
        self.scroll_offset = 0
        self.sound_manager = sound_manager
        
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
                self.scroll_offset += event.y * 20
                self.scroll_offset = max(0, self.scroll_offset)
                return True
        return False
    
    def draw(self, screen):
        """Draw the right panel."""
        # Background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((DARK_PURPLE[0], DARK_PURPLE[1], DARK_PURPLE[2], 180))
        screen.blit(s, self.rect.topleft)
        
        # Border
        pygame.draw.line(screen, PURPLE,
                        (self.rect.left, 0),
                        (self.rect.left, WINDOW_HEIGHT), 2)
        
        # Title
        font_title = pygame.font.Font(None, 24)
        title_text = "Photon Path: Help" if self.show_help else "Photon Path: Debug Log"
        title = font_title.render(title_text, True, CYAN)
        title_rect = title.get_rect(centerx=self.rect.centerx, y=20)
        screen.blit(title, title_rect)
        
        # Content area
        content_y = 60
        
        if self.show_help:
            self._draw_help_content(screen, content_y)
        else:
            self._draw_debug_content(screen, content_y)
    
    def _draw_help_content(self, screen, start_y):
        """Draw help information."""
        font_header = pygame.font.Font(None, 20)
        font_text = pygame.font.Font(None, 16)
        
        y = start_y - self.scroll_offset
        x_margin = self.rect.x + 10
        line_height = 20
        
        # Controls section
        if y > 0:
            header = font_header.render("CONTROLS", True, CYAN)
            screen.blit(header, (x_margin, y))
        y += line_height + 5
        
        controls = [
            ("Drag & Drop", "Place components"),
            ("Left Click", "Remove component"),
            ("L", "Toggle leaderboard"),
            ("G", "Toggle debug mode"),
            ("O", "Toggle OPD display"),
            ("H", "Show help"),
            ("Shift+H", "Toggle help/debug view"),
            ("Shift+N", "New session"),
            ("", ""),
            ("SOUND CONTROLS", ""),
            ("Shift+S", "Toggle sound on/off"),
            ("Shift+V", "Increase volume 10%"),
            ("Ctrl+Shift+V", "Decrease volume 10%"),
            ("", ""),
            ("WINDOW CONTROLS", ""),
            ("F11", "Toggle fullscreen"),
            ("ESC", "Exit fullscreen"),
        ]
        
        # Show current sound status
        if self.sound_manager:
            sound_status = "ON" if self.sound_manager.enabled else "OFF"
            volume_percent = int(self.sound_manager.master_volume * 100)
            controls.append(("", ""))
            controls.append(("Sound Status:", f"{sound_status} ({volume_percent}%)"))
        
        for key, desc in controls:
            if key == "" and desc == "":
                y += line_height // 2
                continue
            elif desc == "":  # Section header
                if y > 0 and y < self.rect.height:
                    text = font_header.render(key, True, CYAN)
                    screen.blit(text, (x_margin, y))
                y += line_height + 5
            else:
                if y > 0 and y < self.rect.height:
                    key_surface = font_text.render(f"{key:13}", True, WHITE)
                    desc_surface = font_text.render(desc, True, (200, 200, 200))
                    screen.blit(key_surface, (x_margin, y))
                    screen.blit(desc_surface, (x_margin + 90, y))
                y += line_height
        
        # Physics info
        y += line_height
        if y > 0 and y < self.rect.height:
            physics_header = font_header.render("PHYSICS", True, CYAN)
            screen.blit(physics_header, (x_margin, y))
        y += line_height + 5
        
        physics_info = [
            f"Wavelength: {WAVELENGTH}px",
            f"Grid size: {GRID_SIZE}px",
            "BS: +90° phase on reflection",
            "Mirror: +180° phase",
            "Ideal components: " + ("ON" if IDEAL_COMPONENTS else "OFF"),
        ]
        
        for info in physics_info:
            if y > 0 and y < self.rect.height:
                text = font_text.render(info, True, (200, 200, 200))
                screen.blit(text, (x_margin, y))
            y += line_height
        
        # Scoring info
        y += line_height
        if y > 0 and y < self.rect.height:
            score_header = font_header.render("SCORING", True, CYAN)
            screen.blit(score_header, (x_margin, y))
        y += line_height + 5
        
        scoring_info = [
            "Base: Detector Power × 1000",
            "Gold fields: +100 per intensity",
            "Complete challenges for bonus",
            "Interference bonus: varies",
            "Challenges can only be",
            "completed once per session",
        ]
        
        for info in scoring_info:
            if y > 0 and y < self.rect.height:
                text = font_text.render(info, True, (200, 200, 200))
                screen.blit(text, (x_margin, y))
            y += line_height
        
        # Tips section
        y += line_height
        if y > 0 and y < self.rect.height:
            tips_header = font_header.render("TIPS", True, CYAN)
            screen.blit(tips_header, (x_margin, y))
        y += line_height + 5
        
        tips = [
            "• Build a Mach-Zehnder",
            "  interferometer with 2 beam",
            "  splitters and 2 mirrors",
            "• Interference occurs when",
            "  beams enter the same beam",
            "  splitter from different ports",
            "• Constructive interference:",
            "  beams with same phase",
            "• Destructive interference:",
            "  beams with opposite phase",
            "• Path length differences",
            "  create phase shifts",
            "• Gold fields award bonus",
            "  points based on intensity",
            "• Sound enhances gameplay -",
            "  use Shift+S to toggle",
        ]
        
        for tip in tips:
            if y > 0 and y < self.rect.height:
                text = font_text.render(tip, True, (200, 200, 200))
                screen.blit(text, (x_margin, y))
            y += line_height
    
    def _draw_debug_content(self, screen, start_y):
        """Draw debug log messages."""
        font = pygame.font.Font(None, 14)
        y = start_y
        x_margin = self.rect.x + 10
        line_height = 16
        
        if not self.debug_messages:
            no_msg = font.render("No debug messages", True, (150, 150, 150))
            screen.blit(no_msg, (x_margin, y))
            hint = font.render("Press G to enable debug mode", True, (100, 100, 100))
            screen.blit(hint, (x_margin, y + 20))
            return
        
        # Draw messages from bottom to top (newest first)
        for i, message in enumerate(reversed(self.debug_messages)):
            if y > self.rect.height - 20:
                break
                
            # Truncate long messages
            if len(message) > 40:
                message = message[:37] + "..."
            
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
            
            text = font.render(message, True, color)
            screen.blit(text, (x_margin, y))
            y += line_height
        
        # Show message count
        count_text = font.render(f"Messages: {len(self.debug_messages)}/{self.max_debug_messages}",
                               True, (150, 150, 150))
        screen.blit(count_text, (x_margin, self.rect.height - 30))
