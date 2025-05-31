"""Emoji support utility for pygame."""
import pygame
import platform
import os
import math

class EmojiSupport:
    """Provides emoji rendering support across different platforms."""
    
    _emoji_font = None
    _fallback_font = None
    _system = platform.system()
    
    @classmethod
    def get_emoji_font(cls, size=20):
        """Get a font that supports emoji for the current platform."""
        if cls._emoji_font and cls._emoji_font.get_height() == size:
            return cls._emoji_font
        
        # Platform-specific emoji fonts
        emoji_fonts = {
            'Windows': ['Segoe UI Emoji', 'Segoe UI Symbol'],
            'Darwin': ['Apple Color Emoji', 'Apple Symbols'],  # macOS
            'Linux': ['Noto Color Emoji', 'Noto Emoji', 'Symbola']
        }
        
        # Try platform-specific fonts first
        font_list = emoji_fonts.get(cls._system, [])
        
        # Add some common fallbacks
        font_list.extend(['DejaVu Sans', 'Arial Unicode MS', 'Unifont'])
        
        # Try to load each font
        for font_name in font_list:
            try:
                cls._emoji_font = pygame.font.SysFont(font_name, size)
                # Test if it can render emojis by checking if it renders differently than default
                test_surface = cls._emoji_font.render("🏆", True, (255, 255, 255))
                if test_surface.get_width() > 5:  # Basic check if something was rendered
                    return cls._emoji_font
            except:
                continue
        
        # If no emoji font found, return default font
        cls._emoji_font = pygame.font.Font(None, size)
        return cls._emoji_font
    
    @classmethod
    def render_with_fallback(cls, text, emoji_replacement, size, color, use_emoji=True):
        """
        Render text with emoji, falling back to text if emoji not supported.
        
        Args:
            text: The emoji or text to render
            emoji_replacement: Text to use if emoji rendering fails
            size: Font size
            color: Text color
            use_emoji: Whether to attempt emoji rendering
        
        Returns:
            pygame.Surface with rendered text
        """
        if not use_emoji:
            font = pygame.font.Font(None, size)
            return font.render(emoji_replacement, True, color)
        
        # Try emoji font
        emoji_font = cls.get_emoji_font(size)
        surface = emoji_font.render(text, True, color)
        
        # Check if emoji was rendered properly (very basic check)
        if surface.get_width() < 5 or surface.get_height() < 5:
            # Fallback to text
            font = pygame.font.Font(None, size)
            return font.render(emoji_replacement, True, color)
        
        return surface
    
    @classmethod
    def get_trophy_surface(cls, size=20, color=(255, 215, 0)):
        """Get a surface with trophy symbol."""
        return cls.render_with_fallback("🏆", "[T]", size, color)
    
    @classmethod
    def get_checkmark_surface(cls, size=24, color=(255, 215, 0)):
        """Get a surface with checkmark symbol."""
        # Checkmark usually works better than emoji
        font = pygame.font.Font(None, size)
        return font.render("✓", True, color)
    
    @classmethod
    def get_star_surface(cls, size=20, color=(255, 215, 0)):
        """Get a surface with star symbol."""
        # Star character usually works in most fonts
        font = pygame.font.Font(None, size)
        return font.render("★", True, color)
    
    @classmethod
    def draw_trophy_icon(cls, screen, x, y, size=20, color=(255, 215, 0)):
        """Draw a trophy icon using shapes if emoji not available."""
        # Draw a simple trophy shape
        # Cup part
        cup_rect = pygame.Rect(x - size//2, y - size//2, size, int(size * 0.7))
        pygame.draw.rect(screen, color, cup_rect, 0, border_radius=5)
        
        # Handles
        handle_width = size // 4
        # Left handle
        pygame.draw.arc(screen, color,
                       pygame.Rect(x - size//2 - handle_width//2, y - size//2,
                                  handle_width, size//2),
                       -1.57, 1.57, 2)
        # Right handle
        pygame.draw.arc(screen, color,
                       pygame.Rect(x + size//2 - handle_width//2, y - size//2,
                                  handle_width, size//2),
                       1.57, 4.71, 2)
        
        # Base
        base_width = int(size * 0.6)
        base_rect = pygame.Rect(x - base_width//2, y + int(size * 0.15),
                               base_width, int(size * 0.2))
        pygame.draw.rect(screen, color, base_rect)
        
        # Star on trophy
        star_size = size // 3
        star_y = y - size//4
        # Simple star shape
        points = []
        for i in range(5):
            angle = -1.57 + (i * 4 * 3.14159 / 5)  # Start from top
            if i % 2 == 0:  # Outer points
                px = x + star_size * 0.5 * math.cos(angle)
                py = star_y + star_size * 0.5 * math.sin(angle)
            else:  # Inner points
                px = x + star_size * 0.2 * math.cos(angle)
                py = star_y + star_size * 0.2 * math.sin(angle)
            points.append((px, py))
        
        pygame.draw.polygon(screen, (255, 255, 255), points)
