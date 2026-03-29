"""Asset loading utility with dynamic scaling support."""
import logging
import pygame
import os
from config.settings import CANVAS_OFFSET_X, CANVAS_WIDTH, WINDOW_WIDTH, WINDOW_HEIGHT

logger = logging.getLogger(__name__)

class AssetsLoader:
    """Handles loading and caching of game assets with scaling support."""
    
    def __init__(self):
        self.assets_path = "assets"
        self.images = {}
        self._cached_banner = None  # Cache the resized banner
        self._cached_banner_size = None  # Track the size it was cached for
        self._ensure_assets_folder()
    
    def _ensure_assets_folder(self):
        """Ensure assets folder exists."""
        if not os.path.exists(self.assets_path):
            os.makedirs(self.assets_path)
            logger.debug("Created assets folder at: %s", self.assets_path)
            
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
            
            try:
                pygame.image.save(banner, banner_path)
                logger.debug("Created placeholder banner at: %s", banner_path)
            except Exception as e:
                logger.error("Could not save placeholder banner: %s", e)
    
    def load_image(self, filename):
        """Load an image from the assets folder."""
        if filename in self.images:
            return self.images[filename]
        
        filepath = os.path.join(self.assets_path, filename)
        
        try:
            image = pygame.image.load(filepath)
            self.images[filename] = image
            logger.debug("Loaded image: %s", filename)
            return image
        except pygame.error as e:
            logger.error("Error loading image %s: %s", filename, e)
            # Return a placeholder surface
            placeholder = pygame.Surface((100, 100))
            placeholder.fill((255, 0, 255))  # Magenta for missing images
            return placeholder
    
    def get_banner(self, screen_size=None):
        """Get the banner image, resized to fill entire game window."""
        # Use provided screen size or fall back to window settings
        if screen_size:
            current_size = screen_size
        else:
            current_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Validate size
        if current_size[0] <= 0 or current_size[1] <= 0:
            logger.warning("Invalid screen size for banner: %s, using default", current_size)
            current_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        
        if self._cached_banner is None or self._cached_banner_size != current_size:
            try:
                # Load or reload the banner
                raw_image = self.load_image("banner.png")
                
                # Resize the banner to fill the entire game window
                self._cached_banner = pygame.transform.smoothscale(raw_image, current_size)
                self._cached_banner_size = current_size
                
                logger.debug("Banner resized to: %s", current_size)
            except Exception as e:
                logger.error("Error resizing banner: %s", e)
                # Create a simple colored surface as fallback
                self._cached_banner = pygame.Surface(current_size)
                self._cached_banner.fill((0, 50, 75))  # Dark blue-ish
                self._cached_banner_size = current_size
        
        return self._cached_banner
    
    def clear_cache(self):
        """Clear the image cache. Useful when changing display modes."""
        self.images.clear()
        self._cached_banner = None
        self._cached_banner_size = None
        logger.debug("Asset cache cleared")