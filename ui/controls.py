"""Control panel UI."""
import pygame
from config.settings import *

class ControlPanel:
    """Bottom control panel with buttons."""
    
    def __init__(self):
        self.rect = pygame.Rect(
            CANVAS_OFFSET_X,
            CANVAS_OFFSET_Y + CANVAS_HEIGHT + 20,
            CANVAS_WIDTH,
            80
        )
        
        self.buttons = [
            {'name': 'Clear All', 'rect': pygame.Rect(self.rect.x + 20, self.rect.y + 20, 100, 40)},
            {'name': 'Check Setup', 'rect': pygame.Rect(self.rect.x + 130, self.rect.y + 20, 110, 40)},
            {'name': 'Toggle Laser', 'rect': pygame.Rect(self.rect.x + 250, self.rect.y + 20, 110, 40)},
            {'name': 'Load Challenge', 'rect': pygame.Rect(self.rect.x + 370, self.rect.y + 20, 115, 40)},
            {'name': 'Leaderboard', 'rect': pygame.Rect(self.rect.x + 495, self.rect.y + 20, 110, 40)}
        ]
        
        self.score = 0
        self.current_challenge = None
        self.challenge_status = ""
    
    def handle_event(self, event):
        """Handle control events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check buttons
            for button in self.buttons:
                if button['rect'].collidepoint(event.pos):
                    return button['name']
        
        return None
    
    def set_challenge(self, challenge_name):
        """Set the current challenge being attempted."""
        self.current_challenge = challenge_name
        self.challenge_status = f"Challenge: {challenge_name}"
    
    def set_status(self, status):
        """Set status message."""
        self.challenge_status = status
    
    def draw(self, screen):
        """Draw control panel."""
        # Background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (DARK_PURPLE[0], DARK_PURPLE[1], DARK_PURPLE[2], 180), s.get_rect(), border_radius=10)
        screen.blit(s, self.rect.topleft)
        
        # Border
        border_color = (PURPLE[0], PURPLE[1], PURPLE[2], 100)
        s2 = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s2, border_color, s2.get_rect(), 2, border_radius=10)
        screen.blit(s2, self.rect.topleft)
        
        # Buttons
        font = pygame.font.Font(None, 18)
        for button in self.buttons:
            # Button background
            color = CYAN if button['name'] == 'Leaderboard' else PURPLE
            pygame.draw.rect(screen, color, button['rect'], border_radius=20)
            
            # Gradient effect
            s = pygame.Surface((button['rect'].width, button['rect'].height), pygame.SRCALPHA)
            for i in range(button['rect'].height // 2):
                alpha = 100 - i * 2
                pygame.draw.rect(s, (color[0], color[1], color[2], alpha),
                               pygame.Rect(0, i, button['rect'].width, 1))
            screen.blit(s, button['rect'].topleft)
            
            # Add icon for leaderboard button
            if button['name'] == 'Leaderboard':
                # Draw trophy icon as [T]
                icon_font = pygame.font.Font(None, 20)
                icon = icon_font.render("[T]", True, (255, 215, 0))  # Gold color
                icon_rect = icon.get_rect(midleft=(button['rect'].x + 5, button['rect'].centery))
                screen.blit(icon, icon_rect)
                
                # Adjust text position
                text = font.render("Scores", True, WHITE)
                text_rect = text.get_rect(center=(button['rect'].centerx + 10, button['rect'].centery))
            else:
                # Text
                text = font.render(button['name'], True, WHITE)
                text_rect = text.get_rect(center=button['rect'].center)
            
            screen.blit(text, text_rect)
        
        # Challenge status
        if self.challenge_status:
            status_font = pygame.font.Font(None, 16)
            status_text = status_font.render(self.challenge_status, True, CYAN)
            status_rect = status_text.get_rect(left=self.rect.x + 620, centery=self.rect.centery - 10)
            screen.blit(status_text, status_rect)
        
        # Score
        self._draw_score(screen)
    
    def _draw_score(self, screen):
        """Draw score display."""
        font = pygame.font.Font(None, 24)
        score_text = font.render(f"Score: {self.score}", True, CYAN)
        score_rect = score_text.get_rect(right=self.rect.right - 20,
                                        centery=self.rect.centery + 10)
        
        # Background with glow effect
        bg_rect = score_rect.inflate(20, 10)
        
        # Glow
        glow_surf = pygame.Surface((bg_rect.width + 10, bg_rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (CYAN[0], CYAN[1], CYAN[2], 20), glow_surf.get_rect(), border_radius=15)
        screen.blit(glow_surf, (bg_rect.x - 5, bg_rect.y - 5))
        
        # Background
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], 30), s.get_rect(), border_radius=15)
        screen.blit(s, bg_rect.topleft)
        pygame.draw.rect(screen, CYAN, bg_rect, 1, border_radius=15)
        
        screen.blit(score_text, score_rect)
