"""Control panel UI."""
import pygame
from config.settings import *

class ControlPanel:
    """Bottom control panel with buttons and phase slider."""
    
    def __init__(self):
        self.rect = pygame.Rect(
            CANVAS_OFFSET_X, 
            CANVAS_OFFSET_Y + CANVAS_HEIGHT + 20,
            CANVAS_WIDTH, 
            80
        )
        
        self.buttons = [
            {'name': 'Clear All', 'rect': pygame.Rect(self.rect.x + 20, self.rect.y + 20, 100, 40)},
            {'name': 'Check Setup', 'rect': pygame.Rect(self.rect.x + 140, self.rect.y + 20, 120, 40)},
            {'name': 'Toggle Laser', 'rect': pygame.Rect(self.rect.x + 280, self.rect.y + 20, 120, 40)}
        ]
        
        # Phase slider
        self.slider_rect = pygame.Rect(self.rect.x + 450, self.rect.y + 30, 200, 20)
        self.slider_pos = self.slider_rect.x
        self.phase = 0
        self.dragging_slider = False
        
        self.score = 0
    
    def handle_event(self, event):
        """Handle control events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check buttons
            for button in self.buttons:
                if button['rect'].collidepoint(event.pos):
                    return button['name']
            
            # Check slider
            if self.slider_rect.collidepoint(event.pos):
                self.dragging_slider = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_slider = False
        
        elif event.type == pygame.MOUSEMOTION and self.dragging_slider:
            # Update slider
            self.slider_pos = max(self.slider_rect.x, 
                                min(event.pos[0], self.slider_rect.right))
            self.phase = ((self.slider_pos - self.slider_rect.x) / 
                         self.slider_rect.width) * 360
        
        return None
    
    def draw(self, screen):
        """Draw control panel."""
        # Background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*DARK_PURPLE, 180), s.get_rect(), border_radius=10)
        screen.blit(s, self.rect.topleft)
        
        pygame.draw.rect(screen, (*PURPLE, 100), self.rect, 2, border_radius=10)
        
        # Buttons
        font = pygame.font.Font(None, 18)
        for button in self.buttons:
            # Button background
            pygame.draw.rect(screen, PURPLE, button['rect'], border_radius=20)
            
            # Gradient effect
            s = pygame.Surface((button['rect'].width, button['rect'].height), pygame.SRCALPHA)
            for i in range(button['rect'].height // 2):
                alpha = 100 - i * 2
                pygame.draw.rect(s, (*PURPLE, alpha), 
                               pygame.Rect(0, i, button['rect'].width, 1))
            screen.blit(s, button['rect'].topleft)
            
            # Text
            text = font.render(button['name'], True, WHITE)
            text_rect = text.get_rect(center=button['rect'].center)
            screen.blit(text, text_rect)
        
        # Phase slider
        self._draw_slider(screen)
        
        # Score
        self._draw_score(screen)
    
    def _draw_slider(self, screen):
        """Draw phase slider."""
        font = pygame.font.Font(None, 16)
        
        # Label
        label = font.render("Phase Shift:", True, WHITE)
        screen.blit(label, (self.slider_rect.x - 80, self.slider_rect.y))
        
        # Track
        pygame.draw.rect(screen, (*PURPLE, 100), self.slider_rect, border_radius=10)
        
        # Fill
        fill_width = int((self.phase / 360) * self.slider_rect.width)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.slider_rect.x, self.slider_rect.y,
                                  fill_width, self.slider_rect.height)
            pygame.draw.rect(screen, CYAN, fill_rect, border_radius=10)
        
        # Knob
        knob_x = self.slider_rect.x + int((self.phase / 360) * self.slider_rect.width)
        pygame.draw.circle(screen, WHITE, (knob_x, self.slider_rect.centery), 12)
        pygame.draw.circle(screen, CYAN, (knob_x, self.slider_rect.centery), 8)
        
        # Value
        value_text = font.render(f"{int(self.phase)}°", True, CYAN)
        screen.blit(value_text, (self.slider_rect.right + 10, self.slider_rect.y))
    
    def _draw_score(self, screen):
        """Draw score display."""
        font = pygame.font.Font(None, 24)
        score_text = font.render(f"Score: {self.score}", True, CYAN)
        score_rect = score_text.get_rect(right=self.rect.right - 20,
                                        centery=self.rect.centery)
        
        # Background
        bg_rect = score_rect.inflate(20, 10)
        pygame.draw.rect(screen, (*CYAN, 30), bg_rect, border_radius=15)
        pygame.draw.rect(screen, CYAN, bg_rect, 1, border_radius=15)
        
        screen.blit(score_text, score_rect)