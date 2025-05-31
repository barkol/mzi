"""Leaderboard display UI with sound support."""
import pygame
import math
from datetime import datetime
from config.settings import *

class LeaderboardDisplay:
    """UI component for displaying the leaderboard."""
    
    def __init__(self, leaderboard_manager, sound_manager=None):
        self.leaderboard = leaderboard_manager
        self.sound_manager = sound_manager
        self.visible = False
        self.rect = pygame.Rect(
            CANVAS_OFFSET_X + 100,
            CANVAS_OFFSET_Y + 50,
            600,
            500
        )
        self.close_button = pygame.Rect(
            self.rect.right - 40,
            self.rect.top + 10,
            30,
            30
        )
        
        # Input field for name entry
        self.name_input_active = False
        self.player_name = ""
        self.pending_score = None
        self.pending_challenge = None
        self.pending_components = 0
        self.name_input_rect = pygame.Rect(
            self.rect.centerx - 100,
            self.rect.bottom - 80,
            200,
            30
        )
        self.submit_button = pygame.Rect(
            self.rect.centerx - 50,
            self.rect.bottom - 40,
            100,
            30
        )
    
    def show(self, auto_add_score=None, challenge=None, components=0):
        """Show the leaderboard."""
        self.visible = True
        if self.sound_manager:
            self.sound_manager.play('panel_open')
            
        if auto_add_score and self.leaderboard.check_if_high_score(auto_add_score):
            self.name_input_active = True
            self.pending_score = auto_add_score
            self.pending_challenge = challenge
            self.pending_components = components
            self.player_name = ""
            if self.sound_manager:
                self.sound_manager.play('high_score')
    
    def hide(self):
        """Hide the leaderboard."""
        self.visible = False
        self.name_input_active = False
        self.player_name = ""
        self.pending_score = None
        if self.sound_manager:
            self.sound_manager.play('panel_close')
    
    def handle_event(self, event):
        """Handle events for the leaderboard display."""
        if not self.visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check close button
            if self.close_button.collidepoint(event.pos):
                self.hide()
                return True
            
            # Check name input activation
            if self.name_input_active:
                if self.name_input_rect.collidepoint(event.pos):
                    # Keep input active
                    if self.sound_manager:
                        self.sound_manager.play('button_click', volume=0.3)
                elif self.submit_button.collidepoint(event.pos) and self.player_name:
                    # Submit score
                    self._submit_score()
                    return True
                    
        elif event.type == pygame.KEYDOWN and self.name_input_active:
            if event.key == pygame.K_RETURN and self.player_name:
                self._submit_score()
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
                if self.sound_manager:
                    self.sound_manager.play('button_click', volume=0.2)
            elif event.key == pygame.K_ESCAPE:
                self.name_input_active = False
                self.player_name = ""
                if self.sound_manager:
                    self.sound_manager.play('error', volume=0.5)
            elif len(self.player_name) < 15:  # Limit name length
                if event.unicode and event.unicode.isprintable():
                    self.player_name += event.unicode
                    if self.sound_manager:
                        self.sound_manager.play('button_click', volume=0.2)
            return True
        
        return False
    
    def _submit_score(self):
        """Submit the pending score."""
        if self.pending_score and self.player_name:
            made_it, position = self.leaderboard.add_score(
                self.player_name,
                self.pending_score,
                self.pending_challenge,
                self.pending_components
            )
            if self.sound_manager:
                self.sound_manager.play('success')
            self.name_input_active = False
            self.player_name = ""
            self.pending_score = None
    
    def _draw_trophy(self, screen, x, y, size=30, color=(255, 215, 0)):
        """Draw a simple trophy shape."""
        # Cup part
        cup_width = size
        cup_height = int(size * 0.7)
        cup_rect = pygame.Rect(x - cup_width//2, y - cup_height//2, cup_width, cup_height)
        
        # Draw cup with gradient effect
        for i in range(cup_height // 2):
            shade = int(255 - i * 2)
            gradient_color = (min(255, color[0]), min(255, int(color[1] * shade / 255)), 0)
            pygame.draw.rect(screen, gradient_color,
                           pygame.Rect(cup_rect.x + 2, cup_rect.y + i, cup_rect.width - 4, 2))
        
        pygame.draw.rect(screen, color, cup_rect, 2, border_radius=5)
        
        # Handles
        handle_size = size // 3
        # Left handle
        pygame.draw.arc(screen, color,
                       pygame.Rect(x - cup_width//2 - handle_size//2, y - cup_height//2,
                                  handle_size, cup_height//2),
                       -1.57, 1.57, 2)
        # Right handle
        pygame.draw.arc(screen, color,
                       pygame.Rect(x + cup_width//2 - handle_size//2, y - cup_height//2,
                                  handle_size, cup_height//2),
                       1.57, 4.71, 2)
        
        # Base
        base_width = int(cup_width * 0.8)
        base_height = size // 5
        base_rect = pygame.Rect(x - base_width//2, y + cup_height//2 - 2, base_width, base_height)
        pygame.draw.rect(screen, color, base_rect)
        
        # Star on trophy
        star_size = size // 3
        self._draw_star(screen, x, y - size//6, star_size, (255, 255, 255))
    
    def _draw_star(self, screen, x, y, size, color):
        """Draw a star shape."""
        points = []
        for i in range(10):
            angle = -1.57 + (i * 3.14159 / 5)
            if i % 2 == 0:  # Outer points
                radius = size
            else:  # Inner points
                radius = size * 0.5
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))
        pygame.draw.polygon(screen, color, points)
    
    def draw(self, screen):
        """Draw the leaderboard."""
        if not self.visible:
            return
        
        # Background overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Main panel with shadow effect
        shadow = pygame.Surface((self.rect.width + 10, self.rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 100), shadow.get_rect(), border_radius=20)
        screen.blit(shadow, (self.rect.x - 5, self.rect.y + 5))
        
        panel = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (DARK_PURPLE[0], DARK_PURPLE[1], DARK_PURPLE[2], 240),
                        panel.get_rect(), border_radius=20)
        screen.blit(panel, self.rect.topleft)
        
        # Border
        pygame.draw.rect(screen, CYAN, self.rect, 3, border_radius=20)
        
        # Title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("LEADERBOARD", True, CYAN)
        title_rect = title.get_rect(centerx=self.rect.centerx, y=self.rect.y + 20)
        screen.blit(title, title_rect)
        
        # Trophy symbols on sides
        trophy_y = title_rect.centery
        # Left trophy
        self._draw_trophy(screen, title_rect.left - 40, trophy_y, size=30)
        # Right trophy
        self._draw_trophy(screen, title_rect.right + 40, trophy_y, size=30)
        
        # Close button
        pygame.draw.rect(screen, RED, self.close_button, border_radius=5)
        close_font = pygame.font.Font(None, 24)
        close_text = close_font.render("X", True, WHITE)
        close_rect = close_text.get_rect(center=self.close_button.center)
        screen.blit(close_text, close_rect)
        
        # Leaderboard entries
        entries = self.leaderboard.get_entries()
        
        if entries:
            # Headers
            header_font = pygame.font.Font(None, 20)
            headers = ["Rank", "Name", "Score", "Challenge", "Date"]
            header_x = [self.rect.x + 30, self.rect.x + 80, self.rect.x + 250,
                       self.rect.x + 350, self.rect.x + 480]
            header_y = self.rect.y + 80
            
            for i, (header, x) in enumerate(zip(headers, header_x)):
                text = header_font.render(header, True, WHITE)
                screen.blit(text, (x, header_y))
            
            # Divider
            pygame.draw.line(screen, PURPLE,
                           (self.rect.x + 20, header_y + 25),
                           (self.rect.right - 20, header_y + 25), 2)
            
            # Entries
            entry_font = pygame.font.Font(None, 18)
            y_offset = header_y + 40
            
            for i, entry in enumerate(entries):
                # Highlight recent entries
                entry_date = datetime.fromisoformat(entry['date'])
                is_recent = (datetime.now() - entry_date).total_seconds() < 300  # 5 minutes
                
                color = CYAN if is_recent else WHITE
                
                # Rank with medals for top 3
                if i == 0:  # Gold medal
                    self._draw_star(screen, header_x[0] - 15, y_offset + 9, 8, (255, 215, 0))
                    rank_text = entry_font.render("1st", True, (255, 215, 0))
                elif i == 1:  # Silver medal
                    self._draw_star(screen, header_x[0] - 15, y_offset + 9, 8, (192, 192, 192))
                    rank_text = entry_font.render("2nd", True, (192, 192, 192))
                elif i == 2:  # Bronze medal
                    self._draw_star(screen, header_x[0] - 15, y_offset + 9, 8, (205, 127, 50))
                    rank_text = entry_font.render("3rd", True, (205, 127, 50))
                else:
                    rank_text = entry_font.render(f"#{i+1}", True, color)
                
                screen.blit(rank_text, (header_x[0], y_offset))
                
                # Name
                name_text = entry_font.render(entry['name'], True, color)
                screen.blit(name_text, (header_x[1], y_offset))
                
                # Score
                score_text = entry_font.render(str(entry['score']), True, color)
                screen.blit(score_text, (header_x[2], y_offset))
                
                # Challenge
                challenge_text = entry_font.render(entry.get('challenge', 'Free Play')[:12], True, color)
                screen.blit(challenge_text, (header_x[3], y_offset))
                
                # Date
                date_str = entry_date.strftime("%m/%d %I:%M%p")
                date_text = entry_font.render(date_str, True, color)
                screen.blit(date_text, (header_x[4], y_offset))
                
                y_offset += 30
        
        else:
            # No entries message
            no_entries_font = pygame.font.Font(None, 24)
            no_entries = no_entries_font.render("No high scores yet!", True, WHITE)
            no_entries_rect = no_entries.get_rect(center=(self.rect.centerx, self.rect.centery))
            screen.blit(no_entries, no_entries_rect)
        
        # Name input if active
        if self.name_input_active and self.pending_score:
            self._draw_name_input(screen)
        
        # Stats
        self._draw_stats(screen)
    
    def _draw_name_input(self, screen):
        """Draw name input dialog."""
        # Background for input area
        input_bg = pygame.Surface((400, 150), pygame.SRCALPHA)
        pygame.draw.rect(input_bg, (BLACK[0], BLACK[1], BLACK[2], 220),
                        input_bg.get_rect(), border_radius=10)
        input_bg_rect = input_bg.get_rect(center=(self.rect.centerx, self.rect.bottom - 100))
        screen.blit(input_bg, input_bg_rect)
        pygame.draw.rect(screen, CYAN, input_bg_rect, 2, border_radius=10)
        
        # Congratulations text
        congrats_font = pygame.font.Font(None, 24)
        rank = self.leaderboard.get_rank_for_score(self.pending_score)
        congrats_text = congrats_font.render(f"NEW HIGH SCORE! Rank #{rank}", True, CYAN)
        congrats_rect = congrats_text.get_rect(centerx=self.rect.centerx,
                                              y=input_bg_rect.y + 10)
        screen.blit(congrats_text, congrats_rect)
        
        # Score display
        score_font = pygame.font.Font(None, 20)
        score_text = score_font.render(f"Score: {self.pending_score}", True, WHITE)
        score_rect = score_text.get_rect(centerx=self.rect.centerx,
                                        y=input_bg_rect.y + 40)
        screen.blit(score_text, score_rect)
        
        # Input label
        label_font = pygame.font.Font(None, 18)
        label = label_font.render("Enter your name:", True, WHITE)
        label_rect = label.get_rect(centerx=self.rect.centerx - 60,
                                   y=self.name_input_rect.y - 25)
        screen.blit(label, label_rect)
        
        # Input field
        pygame.draw.rect(screen, WHITE, self.name_input_rect, 2)
        if self.player_name:
            name_font = pygame.font.Font(None, 24)
            name_surface = name_font.render(self.player_name, True, WHITE)
            name_rect = name_surface.get_rect(midleft=(self.name_input_rect.x + 10,
                                                       self.name_input_rect.centery))
            screen.blit(name_surface, name_rect)
        
        # Cursor
        if pygame.time.get_ticks() % 1000 < 500:  # Blinking cursor
            cursor_x = self.name_input_rect.x + 10
            if self.player_name:
                name_font = pygame.font.Font(None, 24)
                text_width = name_font.size(self.player_name)[0]
                cursor_x += text_width
            pygame.draw.line(screen, WHITE,
                           (cursor_x, self.name_input_rect.y + 5),
                           (cursor_x, self.name_input_rect.bottom - 5), 2)
        
        # Submit button
        button_color = GREEN if self.player_name else (100, 100, 100)
        pygame.draw.rect(screen, button_color, self.submit_button, border_radius=15)
        button_font = pygame.font.Font(None, 20)
        button_text = button_font.render("Submit", True, WHITE)
        button_rect = button_text.get_rect(center=self.submit_button.center)
        screen.blit(button_text, button_rect)
    
    def _draw_stats(self, screen):
        """Draw leaderboard statistics."""
        stats = self.leaderboard.get_stats()
        if stats['total_entries'] == 0:
            return
        
        # Stats background
        stats_rect = pygame.Rect(self.rect.x + 20, self.rect.bottom - 50,
                                self.rect.width - 40, 40)
        pygame.draw.rect(screen, (PURPLE[0], PURPLE[1], PURPLE[2], 100),
                        stats_rect, border_radius=10)
        
        # Stats text
        stats_font = pygame.font.Font(None, 16)
        stats_text = (f"Highest: {stats['highest_score']} | "
                     f"Average: {stats['average_score']} | "
                     f"Most Played: {stats['most_common_challenge']}")
        text_surface = stats_font.render(stats_text, True, WHITE)
        text_rect = text_surface.get_rect(center=stats_rect.center)
        screen.blit(text_surface, text_rect)
