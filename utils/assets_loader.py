"""Asset loading utility."""
import pygame
import os
from config.settings import CANVAS_OFFSET_X, CANVAS_WIDTH, WINDOW_WIDTH, WINDOW_HEIGHT

class AssetsLoader:
    """Handles loading and caching of game assets."""
    
    def __init__(self):
        self.assets_path = "assets"
        self.images = {}
        self._ensure_assets_folder()
    
    def _ensure_assets_folder(self):
        """Ensure assets folder exists."""
        if not os.path.exists(self.assets_path):
            os.makedirs(self.assets_path)
            print(f"Created assets folder at: {self.assets_path}")
            
            # Create placeholder images if they don't exist
            self._create_placeholder_images()
    
    def _create_placeholder_images(self):
        """Create placeholder images if actual assets don't exist."""
        # Banner placeholder
        banner_path = os.path.join(self.assets_path, "banner.png")
        if not os.path.exists(banner_path):
            banner = pygame.Surface((760, 80))
            banner.fill((0, 100, 150))  # Dark cyan background
            
            # Add some text to the placeholder
            pygame.font.init()
            font = pygame.font.Font(None, 48)
            text = font.render("PHOTON PATH", True, (0, 255, 255))
            text_rect = text.get_rect(center=(380, 30))
            banner.blit(text, text_rect)
            
            subtitle_font = pygame.font.Font(None, 24)
            subtitle = subtitle_font.render("Mach-Zehnder Interferometer", True, (255, 255, 255))
            subtitle_rect = subtitle.get_rect(center=(380, 55))
            banner.blit(subtitle, subtitle_rect)
            
            # Add border
            pygame.draw.rect(banner, (0, 255, 255), banner.get_rect(), 3)
            
            pygame.image.save(banner, banner_path)
            print(f"Created placeholder banner at: {banner_path}")
    
    def load_image(self, filename):
        """Load an image from the assets folder."""
        if filename in self.images:
            return self.images[filename]
        
        filepath = os.path.join(self.assets_path, filename)
        
        try:
            image = pygame.image.load(filepath)
            self.images[filename] = image
            print(f"Loaded image: {filename}")
            return image
        except pygame.error as e:
            print(f"Error loading image {filename}: {e}")
            # Return a placeholder surface
            placeholder = pygame.Surface((100, 100))
            placeholder.fill((255, 0, 255))  # Magenta for missing images
            return placeholder
    
    def get_banner(self):
        """Get the banner image, resized to fill entire game window."""
        raw_image = self.load_image("banner.png")
        
        # Resize the banner to fill the entire game window
        resized_banner = pygame.transform.smoothscale(raw_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
        return resized_banner
