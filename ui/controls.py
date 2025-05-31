"""Control panel UI with sound support."""
import pygame
from config.settings import *

class ControlPanel:
    """Bottom control panel with buttons and sound effects."""
    
    def __init__(self, sound_manager=None):
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
            {'name': 'Load Challenge', 'rect': pygame.Rect(self.rect.x + 370, self.rect.y + 20, 115, 40)}
        ]
        
        self.score = 0
        self.current_challenge = None
        self.challenge_status = ""
        self.challenge_completed = False
        self.gold_bonus = 0
        self.sound_manager = sound_manager
        
        # Track hover state for buttons
        self.hover_button = None
        self.last_hover_button = None
    
    def handle_event(self, event):
        """Handle control events."""
        if event.type == pygame.MOUSEMOTION:
            # Check button hover
            old_hover = self.hover_button
            self.hover_button = None
            
            for button in self.buttons:
                if button['rect'].collidepoint(event.pos):
                    self.hover_button = button['name']
                    break
            
            # Play hover sound when entering a new button
            if self.hover_button != old_hover and self.hover_button and self.sound_manager:
                self.sound_manager.play('button_hover', volume=0.3)
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check buttons
            for button in self.buttons:
                if button['rect'].collidepoint(event.pos):
                    if self.sound_manager:
                        self.sound_manager.play('button_click')
                    return button['name']
        
        return None
    
    def set_challenge(self, challenge_name):
        """Set the current challenge being attempted."""
        self.current_challenge = challenge_name
    
    def set_status(self, status):
        """Set status message."""
        self.challenge_status = status
    
    def set_challenge_completed(self, completed):
        """Set whether the current challenge is completed."""
        self.challenge_completed = completed
    
    def set_gold_bonus(self, bonus):
        """Set the current gold bonus value."""
        self.gold_bonus = bonus
    
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
            # Button background with hover effect
            if button['name'] == self.hover_button:
                # Highlighted button
                pygame.draw.rect(screen, CYAN, button['rect'], border_radius=20)
                
                # Brighter gradient for hover
                s = pygame.Surface((button['rect'].width, button['rect'].height), pygame.SRCALPHA)
                for i in range(button['rect'].height // 2):
                    alpha = 150 - i * 3
                    pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], alpha),
                                   pygame.Rect(0, i, button['rect'].width, 1))
                screen.blit(s, button['rect'].topleft)
            else:
                # Normal button
                pygame.draw.rect(screen, PURPLE, button['rect'], border_radius=20)
                
                # Gradient effect
                s = pygame.Surface((button['rect'].width, button['rect'].height), pygame.SRCALPHA)
                for i in range(button['rect'].height // 2):
                    alpha = 100 - i * 2
                    pygame.draw.rect(s, (PURPLE[0], PURPLE[1], PURPLE[2], alpha),
                                   pygame.Rect(0, i, button['rect'].width, 1))
                screen.blit(s, button['rect'].topleft)
            
            # Text
            text = font.render(button['name'], True, WHITE)
            text_rect = text.get_rect(center=button['rect'].center)
            
            screen.blit(text, text_rect)
        
        # Score
        self._draw_score(screen)
    
    def _draw_score(self, screen):
        """Draw score display."""
        # Use gold color if challenge is completed, cyan otherwise
        GOLD = (255, 215, 0)
        score_color = GOLD if self.challenge_completed else CYAN
        
        font = pygame.font.Font(None, 24)
        score_text = font.render(f"Score: {self.score}", True, score_color)
        score_rect = score_text.get_rect(right=self.rect.right - 20,
                                        centery=self.rect.centery + 10)
        
        # Draw gold bonus above score if present
        if self.gold_bonus > 0:
            bonus_font = pygame.font.Font(None, 18)
            bonus_text = bonus_font.render(f"Gold Bonus: +{self.gold_bonus}", True, GOLD)
            bonus_rect = bonus_text.get_rect(right=self.rect.right - 20,
                                            bottom=score_rect.top - 5)
            
            # Background for gold bonus
            bonus_bg_rect = bonus_rect.inflate(16, 6)
            
            # Glow effect for gold bonus
            glow_surf = pygame.Surface((bonus_bg_rect.width + 8, bonus_bg_rect.height + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (GOLD[0], GOLD[1], GOLD[2], 25),
                           glow_surf.get_rect(), border_radius=10)
            screen.blit(glow_surf, (bonus_bg_rect.x - 4, bonus_bg_rect.y - 4))
            
            # Background
            s = pygame.Surface((bonus_bg_rect.width, bonus_bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (GOLD[0]//4, GOLD[1]//4, GOLD[2]//4, 200),
                           s.get_rect(), border_radius=10)
            screen.blit(s, bonus_bg_rect.topleft)
            pygame.draw.rect(screen, GOLD, bonus_bg_rect, 1, border_radius=10)
            
            screen.blit(bonus_text, bonus_rect)
        
        # Background with glow effect for score
        bg_rect = score_rect.inflate(20, 10)
        
        # Glow
        glow_surf = pygame.Surface((bg_rect.width + 10, bg_rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (score_color[0], score_color[1], score_color[2], 20),
                        glow_surf.get_rect(), border_radius=15)
        screen.blit(glow_surf, (bg_rect.x - 5, bg_rect.y - 5))
        
        # Background
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (score_color[0], score_color[1], score_color[2], 30),
                        s.get_rect(), border_radius=15)
        screen.blit(s, bg_rect.topleft)
        pygame.draw.rect(screen, score_color, bg_rect, 1, border_radius=15)
        
        screen.blit(score_text, score_rect)
        
        # Add "WIN!" text if challenge is completed
        if self.challenge_completed:
            win_font = pygame.font.Font(None, 18)
            win_text = win_font.render("WIN!", True, GOLD)
            win_rect = win_text.get_rect(right=bg_rect.left - 10, centery=bg_rect.centery)
            
            # Background for WIN text
            win_bg_rect = win_rect.inflate(8, 4)
            s = pygame.Surface((win_bg_rect.width, win_bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (GOLD[0]//4, GOLD[1]//4, GOLD[2]//4, 200),
                           s.get_rect(), border_radius=5)
            screen.blit(s, win_bg_rect.topleft)
            pygame.draw.rect(screen, GOLD, win_bg_rect, 1, border_radius=5)
            
            screen.blit(win_text, win_rect)
