"""Visual effects for the game."""
import pygame
import math
import time
from config.settings import CYAN, WHITE, BLACK  # Added BLACK import

class EffectsManager:
    """Manages visual effects like placement animations."""
    
    def __init__(self):
        self.active_effects = []
    
    def add_placement_effect(self, x, y):
        """Add a component placement effect."""
        self.active_effects.append({
            'type': 'placement',
            'x': x,
            'y': y,
            'start_time': time.time(),
            'duration': 0.5
        })
    
    def add_success_message(self):
        """Add success message effect."""
        self.active_effects.append({
            'type': 'success',
            'start_time': time.time(),
            'duration': 3.0
        })
    
    def update(self, dt):
        """Update active effects."""
        current_time = time.time()
        self.active_effects = [
            effect for effect in self.active_effects
            if current_time - effect['start_time'] < effect['duration']
        ]
    
    def draw(self, screen):
        """Draw all active effects."""
        for effect in self.active_effects:
            if effect['type'] == 'placement':
                self._draw_placement_effect(screen, effect)
            elif effect['type'] == 'success':
                self._draw_success_message(screen, effect)
    
    def _draw_placement_effect(self, screen, effect):
        """Draw placement ring effect."""
        progress = (time.time() - effect['start_time']) / effect['duration']
        if progress >= 1:
            return
        
        alpha = int((1 - progress) * 128)
        radius = int(20 + progress * 30)
        
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), (radius, radius), radius, 2)
        screen.blit(s, (effect['x'] - radius, effect['y'] - radius))
    
    def _draw_success_message(self, screen, effect):
        """Draw success message."""
        progress = (time.time() - effect['start_time']) / effect['duration']
        
        # Fade in/out
        if progress < 0.2:
            alpha = int(progress * 5 * 255)
        elif progress > 0.8:
            alpha = int((1 - progress) * 5 * 255)
        else:
            alpha = 255
        
        # Clamp alpha to valid range
        alpha = max(0, min(255, alpha))
        
        # Create message surface
        font_title = pygame.font.Font(None, 48)
        font_text = pygame.font.Font(None, 24)
        
        title = font_title.render("🎉 Interferometer Complete!", True, CYAN)
        text = font_text.render("Adjust the phase shift to see interference patterns", 
                               True, WHITE)
        
        # Position
        title_rect = title.get_rect(center=(screen.get_width() // 2, 
                                          screen.get_height() // 2 - 50))
        text_rect = text.get_rect(center=(screen.get_width() // 2,
                                         screen.get_height() // 2 + 20))
        
        # Background
        bg_rect = title_rect.union(text_rect).inflate(60, 40)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        
        # Draw background with proper alpha handling
        bg_alpha = max(0, min(255, alpha // 2))
        border_alpha = max(0, min(255, alpha // 3))
        
        pygame.draw.rect(s, (BLACK[0], BLACK[1], BLACK[2], bg_alpha), s.get_rect(), border_radius=20)
        pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], border_alpha), s.get_rect(), 2, border_radius=20)
        screen.blit(s, bg_rect.topleft)
        
        # Draw text with alpha blending
        title_surface = pygame.Surface(title.get_size(), pygame.SRCALPHA)
        title_surface.blit(title, (0, 0))
        title_surface.set_alpha(alpha)
        
        text_surface = pygame.Surface(text.get_size(), pygame.SRCALPHA)
        text_surface.blit(text, (0, 0))
        text_surface.set_alpha(alpha)
        
        screen.blit(title_surface, title_rect)
        screen.blit(text_surface, text_rect)