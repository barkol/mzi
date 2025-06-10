"""Control panel UI with responsive sizing for fullscreen."""
import pygame
from config.settings import *

class ControlPanel:
    """Bottom control panel with responsive height and button sizing."""
    
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
        """Update control panel dimensions based on current scale and display mode."""
        # Use responsive height from settings
        panel_height = get_control_panel_height()
        
        if IS_FULLSCREEN:
            # In fullscreen, control panel is at the very bottom of the screen
            panel_y = WINDOW_HEIGHT - panel_height - scale(20)  # Small margin from bottom
            
            # Panel spans the width between sidebar and right panel
            sidebar_width = get_sidebar_width()
            right_panel_width = get_right_panel_width()
            panel_x = sidebar_width
            panel_width = WINDOW_WIDTH - sidebar_width - right_panel_width
            
            self.rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        else:
            # Windowed mode - below the canvas
            panel_y = CANVAS_OFFSET_Y + CANVAS_HEIGHT + scale(15)
            
            # Make sure panel doesn't go off screen
            if panel_y + panel_height > WINDOW_HEIGHT:
                panel_y = WINDOW_HEIGHT - panel_height - scale(10)
            
            self.rect = pygame.Rect(
                CANVAS_OFFSET_X,
                panel_y,
                CANVAS_WIDTH,
                panel_height
            )
        
        # Scale button dimensions - larger in fullscreen
        if IS_FULLSCREEN:
            button_height = scale(50)
            button_spacing = scale(15)
            button_y_offset = (panel_height - button_height) // 2  # Center vertically
        else:
            button_height = scale(40)
            button_spacing = scale(10)
            button_y_offset = scale(20)
        
        button_y = self.rect.y + button_y_offset
        start_x = self.rect.x + scale(20)
        
        # Calculate button positions with responsive widths
        self.buttons = []
        button_configs = [
            ('Clear All', scale(110) if IS_FULLSCREEN else scale(100)),
            ('Check Setup', scale(120) if IS_FULLSCREEN else scale(110)),
            ('Toggle Laser', scale(120) if IS_FULLSCREEN else scale(110)),
            ('Load Challenge', scale(130) if IS_FULLSCREEN else scale(115)),
            ('Load Fields', scale(110) if IS_FULLSCREEN else scale(95))
        ]
        
        current_x = start_x
        for name, width in button_configs:
            # Make sure buttons fit within panel
            if current_x + width > self.rect.right - scale(200):  # Leave space for score
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
        
        # Background - solid dark purple
        pygame.draw.rect(screen, DARK_PURPLE, self.rect, border_radius=scale(10))
        
        # Border
        pygame.draw.rect(screen, PURPLE, self.rect, scale(2), border_radius=scale(10))
        
        # Buttons
        button_font_size = scale_font(20) if IS_FULLSCREEN else scale_font(18)
        font = pygame.font.Font(None, button_font_size)
        
        for button in self.buttons:
            # Button background with hover effect
            if button['name'] == self.hover_button:
                # Highlighted button
                pygame.draw.rect(screen, CYAN, button['rect'], border_radius=scale(20))
            else:
                # Normal button
                pygame.draw.rect(screen, PURPLE, button['rect'], border_radius=scale(20))
            
            # Button text
            text = font.render(button['name'], True, WHITE)
            text_rect = text.get_rect(center=button['rect'].center)
            screen.blit(text, text_rect)
        
        # Score display
        self._draw_score(screen)
        
        # Field configuration
        self._draw_field_config(screen)
    
    def _draw_score(self, screen):
        """Draw score display with solid backgrounds."""
        # Colors
        score_color = GOLD if self.challenge_completed else CYAN
        bg_color = (40, 40, 40)  # Dark gray background
        
        # Score text
        score_font_size = scale_font(28) if IS_FULLSCREEN else scale_font(24)
        font = pygame.font.Font(None, score_font_size)
        score_text = font.render(f"Score: {self.score}", True, score_color)
        score_rect = score_text.get_rect(right=self.rect.right - scale(20),
                                        centery=self.rect.centery + scale(10))
        
        # Score background
        bg_rect = score_rect.inflate(scale(20), scale(10))
        pygame.draw.rect(screen, bg_color, bg_rect, border_radius=scale(15))
        pygame.draw.rect(screen, score_color, bg_rect, scale(2), border_radius=scale(15))
        
        # Draw score text
        screen.blit(score_text, score_rect)
        
        # Gold bonus if present
        if self.gold_bonus > 0:
            bonus_font_size = scale_font(20) if IS_FULLSCREEN else scale_font(18)
            bonus_font = pygame.font.Font(None, bonus_font_size)
            bonus_text = bonus_font.render(f"Gold Bonus: +{self.gold_bonus}", True, GOLD)
            bonus_rect = bonus_text.get_rect(right=self.rect.right - scale(20),
                                            bottom=score_rect.top - scale(5))
            
            # Bonus background
            bonus_bg_rect = bonus_rect.inflate(scale(16), scale(6))
            pygame.draw.rect(screen, bg_color, bonus_bg_rect, border_radius=scale(10))
            pygame.draw.rect(screen, GOLD, bonus_bg_rect, scale(2), border_radius=scale(10))
            
            # Draw bonus text
            screen.blit(bonus_text, bonus_rect)
        
        # WIN indicator if completed
        if self.challenge_completed:
            win_font_size = scale_font(20) if IS_FULLSCREEN else scale_font(18)
            win_font = pygame.font.Font(None, win_font_size)
            win_text = win_font.render("WIN!", True, GOLD)
            win_rect = win_text.get_rect(right=bg_rect.left - scale(10), centery=bg_rect.centery)
            
            # WIN background
            win_bg_rect = win_rect.inflate(scale(8), scale(4))
            pygame.draw.rect(screen, bg_color, win_bg_rect, border_radius=scale(5))
            pygame.draw.rect(screen, GOLD, win_bg_rect, scale(2), border_radius=scale(5))
            
            # Draw WIN text
            screen.blit(win_text, win_rect)
    
    def _draw_field_config(self, screen):
        """Draw current field configuration name."""
        config_font_size = scale_font(18) if IS_FULLSCREEN else scale_font(16)
        font = pygame.font.Font(None, config_font_size)
        
        # Color code the field config
        field_color = WHITE
        if 'Treasure' in self.current_field_config:
            field_color = (255, 215, 0)  # Gold
        elif 'Maze' in self.current_field_config:
            field_color = (255, 100, 100)  # Red
        else:  # Default
            field_color = (100, 200, 255)  # Light blue
        
        config_text = font.render(f"Map: {self.current_field_config}", True, field_color)
        config_rect = config_text.get_rect(left=self.rect.x + scale(20), 
                                         bottom=self.rect.bottom - scale(5))
        
        # Simple background
        bg_rect = config_rect.inflate(scale(10), scale(4))
        pygame.draw.rect(screen, (40, 40, 40), bg_rect)
        pygame.draw.rect(screen, field_color, bg_rect, 1)
        
        # Draw text
        screen.blit(config_text, config_rect)