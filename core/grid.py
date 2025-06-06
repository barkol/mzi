"""Grid system for component placement with scaling support."""
import pygame
import math
import random
from config.settings import *
from utils.colors import pulse_alpha
from utils.vector import Vector2

class Grid:
    """Grid system for the game canvas with scaling."""
    
    def __init__(self):
        self.hover_pos = None
        self.canvas_rect = pygame.Rect(
            CANVAS_OFFSET_X, CANVAS_OFFSET_Y,
            CANVAS_WIDTH, CANVAS_HEIGHT
        )
        # Cache for coin positions (to keep them consistent)
        self.coin_cache = {}
    
    def set_hover(self, pos):
        """Set hover position for drag preview."""
        if pos and self.canvas_rect.collidepoint(pos):
            # Snap to grid
            x = round((pos[0] - CANVAS_OFFSET_X) / GRID_SIZE) * GRID_SIZE + CANVAS_OFFSET_X
            y = round((pos[1] - CANVAS_OFFSET_Y) / GRID_SIZE) * GRID_SIZE + CANVAS_OFFSET_Y
            self.hover_pos = (x, y)
        else:
            self.hover_pos = None
    
    def draw(self, screen, components, laser_pos=None, blocked_positions=None, gold_positions=None):
        """Draw grid with hover effects, blocked positions, and gold fields."""
        # Draw grid lines
        self._draw_grid_lines(screen)
        
        # Draw gold positions (draw before blocked so blocked are on top)
        if gold_positions:
            self._draw_gold_positions(screen, gold_positions)
        
        # Draw blocked positions
        if blocked_positions:
            self._draw_blocked_positions(screen, blocked_positions)
        
        # Draw hover highlight
        if self.hover_pos:
            self._draw_hover_highlight(screen, components, laser_pos, blocked_positions)
    
    def _draw_grid_lines(self, screen):
        """Draw the background grid."""
        # Vertical lines
        for x in range(CANVAS_OFFSET_X, CANVAS_OFFSET_X + CANVAS_WIDTH + 1, GRID_SIZE):
            is_major = ((x - CANVAS_OFFSET_X) / GRID_SIZE) % 4 == 0
            color = GRID_MAJOR_COLOR if is_major else GRID_COLOR
            pygame.draw.line(screen, color,
                           (x, CANVAS_OFFSET_Y),
                           (x, CANVAS_OFFSET_Y + CANVAS_HEIGHT))
        
        # Horizontal lines
        for y in range(CANVAS_OFFSET_Y, CANVAS_OFFSET_Y + CANVAS_HEIGHT + 1, GRID_SIZE):
            is_major = ((y - CANVAS_OFFSET_Y) / GRID_SIZE) % 4 == 0
            color = GRID_MAJOR_COLOR if is_major else GRID_COLOR
            pygame.draw.line(screen, color,
                           (CANVAS_OFFSET_X, y),
                           (CANVAS_OFFSET_X + CANVAS_WIDTH, y))
        
        # Draw intersection dots
        for x in range(CANVAS_OFFSET_X, CANVAS_OFFSET_X + CANVAS_WIDTH + 1, GRID_SIZE):
            for y in range(CANVAS_OFFSET_Y, CANVAS_OFFSET_Y + CANVAS_HEIGHT + 1, GRID_SIZE):
                is_major = (((x - CANVAS_OFFSET_X) / GRID_SIZE) % 4 == 0 and
                           ((y - CANVAS_OFFSET_Y) / GRID_SIZE) % 4 == 0)
                radius = scale(3) if is_major else scale(2)
                pygame.draw.circle(screen, GRID_MAJOR_COLOR if is_major else GRID_COLOR,
                                 (x, y), radius)
    
    def _draw_coin(self, screen, x, y, size=12, highlight=False):
        """Draw a single coin with scaling."""
        # Scale the size
        scaled_size = scale(size)
        
        # Coin colors
        coin_edge = (184, 134, 11)  # Dark gold
        coin_center = (255, 215, 0)  # Gold
        coin_highlight = (255, 255, 150)  # Light gold
        
        # Draw coin base (darker edge)
        pygame.draw.circle(screen, coin_edge, (x, y), scaled_size)
        
        # Draw coin top (lighter center)
        pygame.draw.circle(screen, coin_center, (x, y - scale(2)), scaled_size - scale(2))
        
        # Draw highlight
        highlight_x = x - scaled_size // 3
        highlight_y = y - scaled_size // 3 - scale(2)
        pygame.draw.circle(screen, coin_highlight, (highlight_x, highlight_y), scaled_size // 3)
        
        # Draw embossed detail (simple design)
        if scaled_size > scale(8):
            # Draw a simple "$" or star pattern
            detail_color = coin_edge
            # Vertical line
            pygame.draw.line(screen, detail_color, 
                           (x, y - scaled_size//2), 
                           (x, y + scaled_size//2 - scale(2)), scale(1))
            # Horizontal lines for "$"
            pygame.draw.line(screen, detail_color, 
                           (x - scaled_size//4, y - scale(2)), 
                           (x + scaled_size//4, y - scale(2)), scale(1))
    
    def _draw_gold_positions(self, screen, gold_positions):
        """Draw gold field positions as piles of coins with scaling."""
        field_size = scale(40)  # Scaled field size
        
        for pos in gold_positions:
            x, y = int(pos.x), int(pos.y)
            
            # Get or create coin positions for this grid cell
            grid_key = (x, y)
            if grid_key not in self.coin_cache:
                # Generate random coin positions
                random.seed(x * 1000 + y)  # Consistent randomness per position
                coins = []
                
                # Bottom layer - 2-3 coins
                for i in range(random.randint(2, 3)):
                    offset_x = random.randint(-field_size//4, field_size//4)
                    offset_y = random.randint(field_size//8, field_size//4)
                    coins.append((x + offset_x, y + offset_y, 8, 0))  # x, y, size, layer
                
                # Top layer - 1-2 coins
                for i in range(random.randint(1, 2)):
                    offset_x = random.randint(-field_size//6, field_size//6)
                    offset_y = random.randint(-field_size//6, 0)
                    coins.append((x + offset_x, y + offset_y - scale(4), 7, 1))
                
                # Sort by y position for proper layering
                coins.sort(key=lambda c: c[1])
                self.coin_cache[grid_key] = coins
            
            # Draw background field with rounded corners
            field_rect = pygame.Rect(x - field_size // 2, y - field_size // 2, field_size, field_size)
            
            # Golden background with transparency
            field_surf = pygame.Surface((field_size, field_size), pygame.SRCALPHA)
            pygame.draw.rect(field_surf, (255, 215, 0, 60), 
                           field_surf.get_rect(), border_radius=scale(8))
            screen.blit(field_surf, field_rect.topleft)
            
            # Draw coins from cache
            coins = self.coin_cache[grid_key]
            for coin_x, coin_y, coin_size, layer in coins:
                self._draw_coin(screen, coin_x, coin_y, coin_size, layer == 1)
            
            # Draw contrastive border with rounded corners
            pygame.draw.rect(screen, (184, 134, 11), field_rect, scale(3), border_radius=scale(8))
            
            # Draw inner highlight border
            inner_rect = field_rect.inflate(-scale(4), -scale(4))
            pygame.draw.rect(screen, (255, 255, 150), inner_rect, scale(1), border_radius=scale(6))
            
            # Draw "100" text below the field
            font = pygame.font.Font(None, scale_font(12))
            text = font.render("100", True, (255, 255, 200))
            text_rect = text.get_rect(center=(x, y + field_size // 2 + scale(8)))
            # Background for text
            bg_rect = text_rect.inflate(scale(4), scale(2))
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))
            screen.blit(s, bg_rect.topleft)
            screen.blit(text, text_rect)
    
    def _draw_vine(self, screen, start_x, start_y, length, direction, thickness=1):
        """Draw a curvy vine with scaling."""
        points = []
        vine_color = (150, 20, 20)  # Dark red
        
        x, y = start_x, start_y
        for i in range(length):
            # Add some curve to the vine
            offset = math.sin(i * 0.4) * scale(3)  # Scaled curves
            if direction == 'horizontal':
                x += 1
                y_pos = y + offset
            else:  # vertical
                y += 1
                x_pos = x + offset
                
            if direction == 'horizontal':
                points.append((x, y_pos))
            else:
                points.append((x_pos, y))
        
        if len(points) > 1:
            pygame.draw.lines(screen, vine_color, False, points, scale(thickness))
            
            # Add some leaves/thorns (smaller, less frequent)
            for i in range(0, len(points), 15):
                if i < len(points):
                    px, py = points[i]
                    # Small thorn/leaf
                    pygame.draw.circle(screen, vine_color, (int(px), int(py)), scale(thickness))
    
    def _draw_blocked_positions(self, screen, blocked_positions):
        """Draw blocked positions as onyx blocks with red vines and scaling."""
        field_size = scale(40)  # Scaled field size
        
        for pos in blocked_positions:
            x, y = int(pos.x), int(pos.y)
            
            # Main onyx block with rounded corners
            block_rect = pygame.Rect(x - field_size // 2, y - field_size // 2, field_size, field_size)
            
            # Draw onyx texture - dark with lighter veins
            # Create surface for block with transparency
            block_surf = pygame.Surface((field_size, field_size), pygame.SRCALPHA)
            
            # Base color - very dark purple/black with rounded corners
            pygame.draw.rect(block_surf, (20, 10, 25), 
                           block_surf.get_rect(), border_radius=scale(8))
            
            # Add marble-like veins
            random.seed(x * 100 + y)  # Consistent pattern per block
            for i in range(2):
                vein_start_x = random.randint(0, field_size)
                vein_start_y = 0
                vein_end_x = random.randint(0, field_size)
                vein_end_y = field_size
                
                # Draw vein with some thickness variation
                for t in range(3):
                    alpha = 30 - t * 10
                    offset = t * 0.5
                    pygame.draw.line(block_surf, (60, 50, 70, alpha),
                                   (vein_start_x + offset, vein_start_y),
                                   (vein_end_x + offset, vein_end_y), scale(1))
            
            screen.blit(block_surf, block_rect.topleft)
            
            # Draw 3D effect edges on rounded rect
            # Inner highlight (top-left)
            inner_rect = block_rect.inflate(-scale(6), -scale(6))
            pygame.draw.rect(screen, (40, 30, 45), inner_rect, scale(1), border_radius=scale(6))
            
            # Outer shadow (bottom-right)
            shadow_rect = block_rect.inflate(scale(2), scale(2))
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 100), 
                           shadow_surf.get_rect(), scale(2), border_radius=scale(9))
            screen.blit(shadow_surf, shadow_rect.topleft)
            
            # Main contrastive border - bright red for contrast
            pygame.draw.rect(screen, (255, 50, 50), block_rect, scale(3), border_radius=scale(8))
            
            # Inner dark border for definition
            inner_border = block_rect.inflate(-scale(4), -scale(4))
            pygame.draw.rect(screen, (10, 5, 15), inner_border, scale(1), border_radius=scale(6))
            
            # Draw smaller, more subtle vines
            random.seed(x * 200 + y)  # Different seed for vines
            
            # Horizontal vine (thinner, shorter)
            if random.random() > 0.5:
                vine_y = y + random.randint(-field_size//4, field_size//4)
                self._draw_vine(screen, x - field_size//2, vine_y, field_size, 'horizontal', 1)
            
            # Vertical vine (thinner, shorter)
            if random.random() > 0.5:
                vine_x = x + random.randint(-field_size//4, field_size//4)
                self._draw_vine(screen, vine_x, y - field_size//2, field_size, 'vertical', 1)
    
    def _draw_hover_highlight(self, screen, components, laser_pos, blocked_positions=None):
        """Draw hover highlight for component placement with scaling."""
        x, y = self.hover_pos
        
        # Check if position is occupied or blocked
        occupied = self._is_position_occupied(x, y, components, laser_pos)
        blocked = False
        if blocked_positions:
            test_pos = Vector2(x, y)
            for blocked_pos in blocked_positions:
                if blocked_pos.distance_to(test_pos) < scale(40) / 2:  # Use scaled field size
                    blocked = True
                    break
        
        # Note: Gold positions do NOT block component placement
        
        # Pulsing effect
        alpha = pulse_alpha(80)
        color = HOVER_INVALID_COLOR if (occupied or blocked) else HOVER_VALID_COLOR
        
        # Draw highlight square
        s = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(s, (color[0], color[1], color[2], alpha), 
                        pygame.Rect(0, 0, GRID_SIZE, GRID_SIZE))
        screen.blit(s, (x - GRID_SIZE // 2, y - GRID_SIZE // 2))
        
        # Draw border
        rect = pygame.Rect(x - GRID_SIZE // 2, y - GRID_SIZE // 2, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, color[:3], rect, scale(2))
        
        # Draw crosshair
        pygame.draw.line(screen, color[:3], (x - scale(10), y), (x + scale(10), y), scale(1))
        pygame.draw.line(screen, color[:3], (x, y - scale(10)), (x, y + scale(10)), scale(1))
        
        # Draw status text
        if blocked:
            self._draw_blocked_text(screen, x, y)
        elif occupied:
            self._draw_occupied_text(screen, x, y)
        else:
            self._draw_coords_text(screen, x, y)
    
    def _is_position_occupied(self, x, y, components, laser_pos):
        """Check if grid position is occupied."""
        # Check laser position
        if laser_pos:
            dist = ((x - laser_pos[0])**2 + (y - laser_pos[1])**2)**0.5
            if dist < GRID_SIZE:
                return True
        
        # Check components
        for comp in components:
            dist = comp.position.distance_to(Vector2(x, y))
            if dist < GRID_SIZE:
                return True
        
        return False
    
    def _draw_blocked_text(self, screen, x, y):
        """Draw blocked position warning with scaling."""
        font = pygame.font.Font(None, scale_font(14))
        text = font.render("BEAM OBSTACLE", True, (255, 0, 0))
        text_rect = text.get_rect(topleft=(x + scale(15), y - scale(25)))
        
        # Background
        padding = scale(5)
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((BLACK[0], BLACK[1], BLACK[2], 200))
        screen.blit(s, bg_rect.topleft)
        pygame.draw.rect(screen, (255, 0, 0), bg_rect, scale(1))
        
        screen.blit(text, text_rect)
        
        # Draw prohibition symbol
        pygame.draw.circle(screen, (255, 0, 0), (x, y), scale(20), scale(3))
        pygame.draw.line(screen, (255, 0, 0), 
                        (x - scale(14), y - scale(14)), 
                        (x + scale(14), y + scale(14)), scale(3))
    
    def _draw_occupied_text(self, screen, x, y):
        """Draw occupied warning with scaling."""
        font = pygame.font.Font(None, scale_font(14))
        text = font.render("OCCUPIED", True, (255, 0, 0))
        text_rect = text.get_rect(topleft=(x + scale(15), y - scale(25)))
        
        # Background
        padding = scale(5)
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((BLACK[0], BLACK[1], BLACK[2], 200))
        screen.blit(s, bg_rect.topleft)
        pygame.draw.rect(screen, (255, 0, 0), bg_rect, scale(1))
        
        screen.blit(text, text_rect)
        
        # Draw X mark
        pygame.draw.line(screen, (255, 0, 0), 
                        (x - scale(15), y - scale(15)), 
                        (x + scale(15), y + scale(15)), scale(3))
        pygame.draw.line(screen, (255, 0, 0), 
                        (x + scale(15), y - scale(15)), 
                        (x - scale(15), y + scale(15)), scale(3))
    
    def _draw_coords_text(self, screen, x, y):
        """Draw coordinate display with scaling."""
        font = pygame.font.Font(None, scale_font(14))
        coords_text = f"{x - CANVAS_OFFSET_X}, {y - CANVAS_OFFSET_Y}"
        text = font.render(coords_text, True, CYAN)
        text_rect = text.get_rect(topleft=(x + scale(15), y - scale(25)))
        
        # Background
        padding = scale(5)
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((BLACK[0], BLACK[1], BLACK[2], 200))
        screen.blit(s, bg_rect.topleft)
        
        screen.blit(text, text_rect)