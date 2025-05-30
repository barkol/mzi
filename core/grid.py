"""Grid system for component placement."""
import pygame
import math
from config.settings import *
from utils.colors import pulse_alpha
from utils.vector import Vector2

# Define gold color
GOLD = (255, 215, 0)

class Grid:
    """Grid system for the game canvas."""
    
    def __init__(self):
        self.hover_pos = None
        self.canvas_rect = pygame.Rect(
            CANVAS_OFFSET_X, CANVAS_OFFSET_Y,
            CANVAS_WIDTH, CANVAS_HEIGHT
        )
    
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
                radius = 3 if is_major else 2
                pygame.draw.circle(screen, GRID_MAJOR_COLOR if is_major else GRID_COLOR,
                                 (x, y), radius)
    
    def _draw_gold_positions(self, screen, gold_positions):
        """Draw gold field positions on the grid."""
        for pos in gold_positions:
            x, y = int(pos.x), int(pos.y)
            
            # Draw main gold square
            gold_rect = pygame.Rect(x - GRID_SIZE // 2, y - GRID_SIZE // 2, GRID_SIZE, GRID_SIZE)
            
            # Golden gradient background
            for i in range(GRID_SIZE // 2):
                alpha = 255 - i * 10
                color = (GOLD[0], GOLD[1], GOLD[2], min(alpha, 180))
                inner_rect = pygame.Rect(
                    gold_rect.x + i,
                    gold_rect.y + i,
                    gold_rect.width - i * 2,
                    gold_rect.height - i * 2
                )
                if inner_rect.width > 0 and inner_rect.height > 0:
                    s = pygame.Surface((inner_rect.width, inner_rect.height), pygame.SRCALPHA)
                    s.fill(color)
                    screen.blit(s, inner_rect.topleft)
            
            # Draw golden border
            pygame.draw.rect(screen, GOLD, gold_rect, 3)
            
            # Draw inner decorative pattern (star/diamond)
            center_x, center_y = x, y
            # Draw a small 4-pointed star
            star_size = GRID_SIZE // 4
            star_points = [
                (center_x, center_y - star_size),  # Top
                (center_x + star_size // 2, center_y - star_size // 2),
                (center_x + star_size, center_y),  # Right
                (center_x + star_size // 2, center_y + star_size // 2),
                (center_x, center_y + star_size),  # Bottom
                (center_x - star_size // 2, center_y + star_size // 2),
                (center_x - star_size, center_y),  # Left
                (center_x - star_size // 2, center_y - star_size // 2),
            ]
            pygame.draw.polygon(screen, GOLD, star_points)
            
            # Pulsing glow effect
            pulse = pulse_alpha(150)
            glow_surf = pygame.Surface((GRID_SIZE + 20, GRID_SIZE + 20), pygame.SRCALPHA)
            for r in range(3):
                glow_alpha = pulse // (r + 1)
                pygame.draw.rect(glow_surf, (GOLD[0], GOLD[1], GOLD[2], glow_alpha),
                               pygame.Rect(r * 3, r * 3,
                                         GRID_SIZE + 20 - r * 6,
                                         GRID_SIZE + 20 - r * 6),
                               border_radius=5)
            screen.blit(glow_surf, (x - GRID_SIZE // 2 - 10, y - GRID_SIZE // 2 - 10))
            
            # Draw "100" text to indicate point value
            font = pygame.font.Font(None, 12)
            text = font.render("100", True, (255, 255, 200))
            text_rect = text.get_rect(center=(x, y + GRID_SIZE // 2 + 8))
            # Background for text
            bg_rect = text_rect.inflate(4, 2)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))
            screen.blit(s, bg_rect.topleft)
            screen.blit(text, text_rect)
    
    def _draw_blocked_positions(self, screen, blocked_positions):
        """Draw blocked positions on the grid as beam obstacles."""
        for pos in blocked_positions:
            # Draw as solid obstacle that will block beams
            x, y = int(pos.x), int(pos.y)
            
            # Draw main obstacle square
            obstacle_rect = pygame.Rect(x - GRID_SIZE // 2, y - GRID_SIZE // 2, GRID_SIZE, GRID_SIZE)
            
            # Draw multiple layers for 3D effect
            # Shadow layer
            shadow_rect = obstacle_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect)
            
            # Main obstacle - solid dark red/black
            pygame.draw.rect(screen, (40, 0, 0), obstacle_rect)
            pygame.draw.rect(screen, (80, 10, 10), obstacle_rect, 3)
            
            # Inner pattern - cross-hatch to show it's solid
            for i in range(0, GRID_SIZE, 8):
                pygame.draw.line(screen, (60, 5, 5),
                               (obstacle_rect.left + i, obstacle_rect.top),
                               (obstacle_rect.left, obstacle_rect.top + i), 1)
                pygame.draw.line(screen, (60, 5, 5),
                               (obstacle_rect.right - i, obstacle_rect.bottom),
                               (obstacle_rect.right, obstacle_rect.bottom - i), 1)
            
            # Bright border to make it stand out
            pygame.draw.rect(screen, (200, 20, 20), obstacle_rect, 2)
            
            # Corner highlights for 3D effect
            corner_size = 5
            # Top-left corner
            pygame.draw.lines(screen, (255, 50, 50), False, [
                (obstacle_rect.left, obstacle_rect.top + corner_size),
                (obstacle_rect.left, obstacle_rect.top),
                (obstacle_rect.left + corner_size, obstacle_rect.top)
            ], 2)
            
            # Warning symbol in center
            font = pygame.font.Font(None, 20)
            warning = font.render("⚡", True, (255, 100, 100))
            warning_rect = warning.get_rect(center=(x, y))
            screen.blit(warning, warning_rect)
            
            # Pulsing glow effect
            pulse = pulse_alpha(100)
            glow_surf = pygame.Surface((GRID_SIZE + 10, GRID_SIZE + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (255, 0, 0, pulse // 2), glow_surf.get_rect(), border_radius=5)
            screen.blit(glow_surf, (x - GRID_SIZE // 2 - 5, y - GRID_SIZE // 2 - 5))
    
    def _draw_hover_highlight(self, screen, components, laser_pos, blocked_positions=None):
        """Draw hover highlight for component placement."""
        x, y = self.hover_pos
        
        # Check if position is occupied or blocked
        occupied = self._is_position_occupied(x, y, components, laser_pos)
        blocked = False
        if blocked_positions:
            test_pos = Vector2(x, y)
            for blocked_pos in blocked_positions:
                if blocked_pos.distance_to(test_pos) < GRID_SIZE / 2:
                    blocked = True
                    break
        
        # Note: Gold positions do NOT block component placement
        
        # Pulsing effect
        alpha = pulse_alpha(80)
        color = HOVER_INVALID_COLOR if (occupied or blocked) else HOVER_VALID_COLOR
        
        # Draw highlight square
        s = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(s, (color[0], color[1], color[2], alpha), pygame.Rect(0, 0, GRID_SIZE, GRID_SIZE))
        screen.blit(s, (x - GRID_SIZE // 2, y - GRID_SIZE // 2))
        
        # Draw border
        rect = pygame.Rect(x - GRID_SIZE // 2, y - GRID_SIZE // 2, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, color[:3], rect, 2)
        
        # Draw crosshair
        pygame.draw.line(screen, color[:3], (x - 10, y), (x + 10, y), 1)
        pygame.draw.line(screen, color[:3], (x, y - 10), (x, y + 10), 1)
        
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
        """Draw blocked position warning."""
        font = pygame.font.Font(None, 14)
        text = font.render("BEAM OBSTACLE", True, (255, 0, 0))
        text_rect = text.get_rect(topleft=(x + 15, y - 25))
        
        # Background
        padding = 5
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((BLACK[0], BLACK[1], BLACK[2], 200))
        screen.blit(s, bg_rect.topleft)
        pygame.draw.rect(screen, (255, 0, 0), bg_rect, 1)
        
        screen.blit(text, text_rect)
        
        # Draw prohibition symbol
        pygame.draw.circle(screen, (255, 0, 0), (x, y), 20, 3)
        pygame.draw.line(screen, (255, 0, 0), (x - 14, y - 14), (x + 14, y + 14), 3)
    
    def _draw_occupied_text(self, screen, x, y):
        """Draw occupied warning."""
        font = pygame.font.Font(None, 14)
        text = font.render("OCCUPIED", True, (255, 0, 0))
        text_rect = text.get_rect(topleft=(x + 15, y - 25))
        
        # Background
        padding = 5
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((BLACK[0], BLACK[1], BLACK[2], 200))
        screen.blit(s, bg_rect.topleft)
        pygame.draw.rect(screen, (255, 0, 0), bg_rect, 1)
        
        screen.blit(text, text_rect)
        
        # Draw X mark
        pygame.draw.line(screen, (255, 0, 0), (x - 15, y - 15), (x + 15, y + 15), 3)
        pygame.draw.line(screen, (255, 0, 0), (x + 15, y - 15), (x - 15, y + 15), 3)
    
    def _draw_coords_text(self, screen, x, y):
        """Draw coordinate display."""
        font = pygame.font.Font(None, 14)
        coords_text = f"{x - CANVAS_OFFSET_X}, {y - CANVAS_OFFSET_Y}"
        text = font.render(coords_text, True, CYAN)
        text_rect = text.get_rect(topleft=(x + 15, y - 25))
        
        # Background
        padding = 5
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((BLACK[0], BLACK[1], BLACK[2], 200))
        screen.blit(s, bg_rect.topleft)
        
        screen.blit(text, text_rect)
