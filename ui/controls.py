"""Control panel UI with sound support and fixed scaling."""
import pygame
from config.settings import *

class ControlPanel:
    """Bottom control panel with buttons, sound effects, and proper scaling."""
    
    def __init__(self, sound_manager=None):
        self.sound_manager = sound_manager
        self.score = 0
        self.current_challenge = None
        self.challenge_status = ""
        self.challenge_completed = False
        self.gold_bonus = 0
        self.current_field_config = "Default Fields"
        
        # Track hover state for buttons
        self.hover_button = None
        self.last_hover_button = None
        
        # Initialize dimensions and buttons
        self._update_dimensions()
    
    def _update_dimensions(self):
        """Update control panel dimensions and button positions based on current scale."""
        # Control panel position - below the canvas
        panel_y = CANVAS_OFFSET_Y + CANVAS_HEIGHT + scale(20)
        panel_height = scale(80)
        
        # Make sure panel doesn't go off screen
        if panel_y + panel_height > WINDOW_HEIGHT:
            panel_y = WINDOW_HEIGHT - panel_height - scale(10)
        
        self.rect = pygame.Rect(
            CANVAS_OFFSET_X,
            panel_y,
            CANVAS_WIDTH,
            panel_height
        )
        
        # Scale button dimensions
        button_height = scale(40)
        button_spacing = scale(10)
        button_y = self.rect.y + scale(20)
        start_x = self.rect.x + scale(20)
        
        # Calculate button positions
        self.buttons = []
        button_configs = [
            ('Clear All', scale(100)),
            ('Check Setup', scale(110)),
            ('Toggle Laser', scale(110)),
            ('Load Challenge', scale(115)),
            ('Load Fields', scale(95))
        ]
        
        current_x = start_x
        for name, width in button_configs:
            # Make sure buttons fit within panel
            if current_x + width > self.rect.right - scale(150):  # Leave space for score
                break
            
            self.buttons.append({
                'name': name,
                'rect': pygame.Rect(current_x, button_y, width, button_height)
            })
            current_x += width + button_spacing
    
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
    
    def set_field_config(self, config_name):
        """Set the current field configuration name."""
        self.current_field_config = config_name
    
    def draw(self, screen):
        """Draw control panel."""
        # Update dimensions in case scale changed
        self._update_dimensions()
        
        # Background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (DARK_PURPLE[0], DARK_PURPLE[1], DARK_PURPLE[2], 180), 
                        s.get_rect(), border_radius=scale(10))
        screen.blit(s, self.rect.topleft)
        
        # Border
        border_color = (PURPLE[0], PURPLE[1], PURPLE[2], 100)
        s2 = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s2, border_color, s2.get_rect(), scale(2), border_radius=scale(10))
        screen.blit(s2, self.rect.topleft)
        
        # Buttons
        font = pygame.font.Font(None, scale_font(18))
        for button in self.buttons:
            # Button background with hover effect
            if button['name'] == self.hover_button:
                # Highlighted button
                pygame.draw.rect(screen, CYAN, button['rect'], border_radius=scale(20))
                
                # Brighter gradient for hover
                s = pygame.Surface((button['rect'].width, button['rect'].height), pygame.SRCALPHA)
                for i in range(button['rect'].height // 2):
                    alpha = 150 - i * 3
                    pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], alpha),
                                   pygame.Rect(0, i, button['rect'].width, 1))
                screen.blit(s, button['rect'].topleft)
            else:
                # Normal button
                pygame.draw.rect(screen, PURPLE, button['rect'], border_radius=scale(20))
                
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
        
        # Field configuration indicator
        self._draw_field_config(screen)
    
    def _draw_score(self, screen):
        """Draw score display."""
        # Use gold color if challenge is completed, cyan otherwise
        score_color = GOLD if self.challenge_completed else CYAN
        
        font = pygame.font.Font(None, scale_font(24))
        score_text = font.render(f"Score: {self.score}", True, score_color)
        score_rect = score_text.get_rect(right=self.rect.right - scale(20),
                                        centery=self.rect.centery + scale(10))
        
        # Draw gold bonus above score if present
        if self.gold_bonus > 0:
            bonus_font = pygame.font.Font(None, scale_font(18))
            bonus_text = bonus_font.render(f"Gold Bonus: +{self.gold_bonus}", True, GOLD)
            bonus_rect = bonus_text.get_rect(right=self.rect.right - scale(20),
                                            bottom=score_rect.top - scale(5))
            
            # Background for gold bonus
            bonus_bg_rect = bonus_rect.inflate(scale(16), scale(6))
            
            # Glow effect for gold bonus
            glow_surf = pygame.Surface((bonus_bg_rect.width + scale(8), 
                                      bonus_bg_rect.height + scale(8)), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (GOLD[0], GOLD[1], GOLD[2], 25),
                           glow_surf.get_rect(), border_radius=scale(10))
            screen.blit(glow_surf, (bonus_bg_rect.x - scale(4), bonus_bg_rect.y - scale(4)))
            
            # Background
            s = pygame.Surface((bonus_bg_rect.width, bonus_bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (GOLD[0]//4, GOLD[1]//4, GOLD[2]//4, 200),
                           s.get_rect(), border_radius=scale(10))
            screen.blit(s, bonus_bg_rect.topleft)
            pygame.draw.rect(screen, GOLD, bonus_bg_rect, scale(1), border_radius=scale(10))
            
            screen.blit(bonus_text, bonus_rect)
        
        # Background with glow effect for score
        bg_rect = score_rect.inflate(scale(20), scale(10))
        
        # Glow
        glow_surf = pygame.Surface((bg_rect.width + scale(10), bg_rect.height + scale(10)), 
                                 pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (score_color[0], score_color[1], score_color[2], 20),
                        glow_surf.get_rect(), border_radius=scale(15))
        screen.blit(glow_surf, (bg_rect.x - scale(5), bg_rect.y - scale(5)))
        
        # Background
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (score_color[0], score_color[1], score_color[2], 30),
                        s.get_rect(), border_radius=scale(15))
        screen.blit(s, bg_rect.topleft)
        pygame.draw.rect(screen, score_color, bg_rect, scale(1), border_radius=scale(15))
        
        screen.blit(score_text, score_rect)
        
        # Add "WIN!" text if challenge is completed
        if self.challenge_completed:
            win_font = pygame.font.Font(None, scale_font(18))
            win_text = win_font.render("WIN!", True, GOLD)
            win_rect = win_text.get_rect(right=bg_rect.left - scale(10), centery=bg_rect.centery)
            
            # Background for WIN text
            win_bg_rect = win_rect.inflate(scale(8), scale(4))
            s = pygame.Surface((win_bg_rect.width, win_bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (GOLD[0]//4, GOLD[1]//4, GOLD[2]//4, 200),
                           s.get_rect(), border_radius=scale(5))
            screen.blit(s, win_bg_rect.topleft)
            pygame.draw.rect(screen, GOLD, win_bg_rect, scale(1), border_radius=scale(5))
            
            screen.blit(win_text, win_rect)
    
    def _draw_field_config(self, screen):
        """Draw current field configuration name."""
        font = pygame.font.Font(None, scale_font(16))
        config_text = font.render(f"Fields: {self.current_field_config}", True, PURPLE)
        config_rect = config_text.get_rect(left=self.rect.x + scale(20), 
                                         bottom=self.rect.bottom - scale(5))
        
        # Background for better readability
        bg_rect = config_rect.inflate(scale(10), scale(4))
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        screen.blit(s, bg_rect.topleft)
        
        screen.blit(config_text, config_rect)