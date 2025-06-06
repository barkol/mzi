"""Visual effects for the game with scaling support."""
import pygame
import math
import time
from config.settings import CYAN, WHITE, BLACK, scale, scale_font

class EffectsManager:
    """Manages visual effects like placement animations with scaling."""
    
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
    
    def add_info_message(self, title, subtitle):
        """Add informational message effect."""
        self.active_effects.append({
            'type': 'info',
            'title': title,
            'subtitle': subtitle,
            'start_time': time.time(),
            'duration': 2.5
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
            elif effect['type'] == 'info':
                self._draw_info_message(screen, effect)
    
    def _draw_placement_effect(self, screen, effect):
        """Draw placement ring effect with scaling."""
        progress = (time.time() - effect['start_time']) / effect['duration']
        if progress >= 1:
            return
        
        alpha = int((1 - progress) * 128)
        radius = int(scale(20) + progress * scale(30))
        
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (CYAN[0], CYAN[1], CYAN[2], alpha), 
                         (radius, radius), radius, scale(2))
        screen.blit(s, (effect['x'] - radius, effect['y'] - radius))
    
    def _draw_success_message(self, screen, effect):
        """Draw success message with scaling."""
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
        font_title = pygame.font.Font(None, scale_font(48))
        font_text = pygame.font.Font(None, scale_font(24))
        
        title = font_title.render("Interferometer Complete!", True, CYAN)
        text = font_text.render("Adjust the phase shift to see interference patterns",
                               True, WHITE)
        
        # Position
        title_rect = title.get_rect(center=(screen.get_width() // 2,
                                          screen.get_height() // 2 - scale(50)))
        text_rect = text.get_rect(center=(screen.get_width() // 2,
                                         screen.get_height() // 2 + scale(20)))
        
        # Background
        bg_rect = title_rect.union(text_rect).inflate(scale(60), scale(40))
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        
        # Draw background with proper alpha handling
        bg_alpha = max(0, min(255, alpha // 2))
        border_alpha = max(0, min(255, alpha // 3))
        
        pygame.draw.rect(s, (BLACK[0], BLACK[1], BLACK[2], bg_alpha), 
                        s.get_rect(), border_radius=scale(20))
        pygame.draw.rect(s, (CYAN[0], CYAN[1], CYAN[2], border_alpha), 
                        s.get_rect(), scale(2), border_radius=scale(20))
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
    
    def _draw_info_message(self, screen, effect):
        """Draw informational message with scaling."""
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
        font_title = pygame.font.Font(None, scale_font(36))
        font_text = pygame.font.Font(None, scale_font(20))
        
        title = font_title.render(f"[OK] {effect['title']}", True, (255, 200, 100))  # Orange-ish color
        text = font_text.render(effect['subtitle'], True, WHITE)
        
        # Position
        title_rect = title.get_rect(center=(screen.get_width() // 2,
                                          screen.get_height() // 2 - scale(40)))
        text_rect = text.get_rect(center=(screen.get_width() // 2,
                                         screen.get_height() // 2))
        
        # Background
        bg_rect = title_rect.union(text_rect).inflate(scale(50), scale(30))
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        
        # Draw background with proper alpha handling
        bg_alpha = max(0, min(255, alpha // 2))
        border_alpha = max(0, min(255, alpha // 3))
        
        pygame.draw.rect(s, (BLACK[0], BLACK[1], BLACK[2], bg_alpha), 
                        s.get_rect(), border_radius=scale(15))
        pygame.draw.rect(s, (255, 200, 100, border_alpha), 
                        s.get_rect(), scale(2), border_radius=scale(15))
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