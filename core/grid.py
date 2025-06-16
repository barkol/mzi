"""Grid system for component placement with dynamic canvas support."""
import pygame
import math
import random
from config.settings import *
from utils.colors import pulse_alpha
from utils.vector import Vector2

# Define GOLD color if not in settings
GOLD = (255, 215, 0)

# Make sure we have essential variables
if 'GRID_SIZE' not in globals():
    GRID_SIZE = 40
if 'CANVAS_GRID_COLS' not in globals():
    CANVAS_GRID_COLS = 20
if 'CANVAS_GRID_ROWS' not in globals():
    CANVAS_GRID_ROWS = 15
if 'IS_FULLSCREEN' not in globals():
    IS_FULLSCREEN = False

# Make sure scale and scale_font are available
if 'scale' not in globals():
    def scale(value):
        """Default scale function if not imported."""
        return int(value)

if 'scale_font' not in globals():
    def scale_font(size):
        """Default font scale function if not imported."""
        return max(8, int(size))

class Grid:
    """Grid system for the game canvas with dynamic sizing."""
    
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
            # Snap to grid CENTER
            grid_x = round((pos[0] - CANVAS_OFFSET_X) / GRID_SIZE)
            grid_y = round((pos[1] - CANVAS_OFFSET_Y) / GRID_SIZE)
            # Center in the grid cell
            x = CANVAS_OFFSET_X + grid_x * GRID_SIZE + GRID_SIZE // 2
            y = CANVAS_OFFSET_Y + grid_y * GRID_SIZE + GRID_SIZE // 2
            self.hover_pos = (x, y)
        else:
            self.hover_pos = None
    
    def draw(self, screen, components, laser_pos=None, blocked_positions=None, gold_positions=None):
        """Draw grid with hover effects, blocked positions, and gold fields."""
        # Update canvas rect in case it changed
        self.canvas_rect = pygame.Rect(
            CANVAS_OFFSET_X, CANVAS_OFFSET_Y,
            CANVAS_WIDTH, CANVAS_HEIGHT
        )
        
        # Debug print
        if gold_positions and len(gold_positions) > 0:
            if not hasattr(self, '_gold_logged'):
                self._gold_logged = True
                print(f"Grid.draw called with {len(gold_positions)} gold positions")
        
        # Draw grid lines
        self._draw_grid_lines(screen)
        
        # Draw grid info in fullscreen mode
        if IS_FULLSCREEN:
            self._draw_grid_info(screen)
        
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
        """Draw the background grid with dynamic dimensions."""
        # Vertical lines - use dynamic grid columns
        for col in range(CANVAS_GRID_COLS + 1):
            x = CANVAS_OFFSET_X + col * GRID_SIZE
            is_major = col % 4 == 0
            color = GRID_MAJOR_COLOR if is_major else GRID_COLOR
            pygame.draw.line(screen, color,
                           (x, CANVAS_OFFSET_Y),
                           (x, CANVAS_OFFSET_Y + CANVAS_HEIGHT))
        
        # Horizontal lines - use dynamic grid rows
        for row in range(CANVAS_GRID_ROWS + 1):
            y = CANVAS_OFFSET_Y + row * GRID_SIZE
            is_major = row % 4 == 0
            color = GRID_MAJOR_COLOR if is_major else GRID_COLOR
            pygame.draw.line(screen, color,
                           (CANVAS_OFFSET_X, y),
                           (CANVAS_OFFSET_X + CANVAS_WIDTH, y))
        
        # Draw intersection dots
        for col in range(CANVAS_GRID_COLS + 1):
            for row in range(CANVAS_GRID_ROWS + 1):
                x = CANVAS_OFFSET_X + col * GRID_SIZE
                y = CANVAS_OFFSET_Y + row * GRID_SIZE
                is_major = (col % 4 == 0 and row % 4 == 0)
                radius = 3 if is_major else 2
                pygame.draw.circle(screen, GRID_MAJOR_COLOR if is_major else GRID_COLOR,
                                 (x, y), radius)
    
    def _draw_grid_info(self, screen):
        """Draw grid configuration info in fullscreen mode."""
        try:
            font_size = scale_font(14) if 'scale_font' in globals() else 14
            font = pygame.font.Font(None, font_size)
        except:
            font = pygame.font.Font(None, 14)
            
        info_text = f"Grid: {CANVAS_GRID_COLS}×{CANVAS_GRID_ROWS} cells ({GRID_SIZE}px)"
        text_surface = font.render(info_text, True, WHITE)
        text_rect = text_surface.get_rect(
            right=CANVAS_OFFSET_X + CANVAS_WIDTH - 10,
            bottom=CANVAS_OFFSET_Y - 5
        )
        
        # Background for readability
        bg_rect = text_rect.inflate(10, 4)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        screen.blit(s, bg_rect.topleft)
        
        screen.blit(text_surface, text_rect)
    
    def _draw_coin(self, screen, x, y, size=12, highlight=False):
        """Draw a simple, highly visible coin."""
        # Use raw size values without scaling for testing
        coin_size = int(size * 0.5)  # Make coins bigger
        
        # Ensure minimum size
        if coin_size < 8:
            coin_size = 8
        
        # Draw black shadow/outline for contrast
        pygame.draw.circle(screen, (0, 0, 0), (x + 2, y + 2), coin_size + 2)
        
        # Draw main coin - bright yellow/gold
        pygame.draw.circle(screen, (255, 215, 0), (x, y), coin_size)
        
        # Draw inner lighter circle for 3D effect
        if coin_size > 12:
            inner_size = coin_size - 6
            pygame.draw.circle(screen, (255, 255, 150), (x - 2, y - 2), inner_size)
        
        # Draw shine highlight
        if coin_size > 16:
            pygame.draw.circle(screen, (255, 255, 255), 
                             (x - coin_size//3, y - coin_size//3), 
                             4)
        
        # Draw black outline for definition
        pygame.draw.circle(screen, (0, 0, 0), (x, y), coin_size, 2)
    
    def _draw_gold_positions(self, screen, gold_positions):
        """Draw gold field positions as piles of coins."""
        if not gold_positions:
            return
            
        # Use current grid size for field size
        field_size = int(GRID_SIZE * 0.9) if GRID_SIZE else 36  # Fallback size
        
        for pos in gold_positions:
            try:
                x, y = int(pos.x), int(pos.y)
            except:
                print(f"Invalid gold position: {pos}")
                continue
            
            # Get or create coin positions for this grid cell
            grid_key = (x, y)
            if grid_key not in self.coin_cache:
                # Generate random coin positions
                random.seed(x * 1000 + y)  # Consistent randomness per position
                coins = []
                
                # Bottom layer - 3-4 coins more tightly grouped
                for i in range(random.randint(3, 4)):
                    offset_x = random.randint(-field_size//4, field_size//4)
                    offset_y = random.randint(-field_size//6, field_size//6)
                    coins.append((x + offset_x, y + offset_y, 15, 0))  # x, y, size, layer
                
                # Middle layer - 2-3 coins
                for i in range(random.randint(2, 3)):
                    offset_x = random.randint(-field_size//5, field_size//5)
                    offset_y = random.randint(-field_size//8, field_size//8) - 4
                    coins.append((x + offset_x, y + offset_y, 14, 1))
                
                # Top layer - 1-2 coins
                for i in range(random.randint(1, 2)):
                    offset_x = random.randint(-field_size//6, field_size//6)
                    offset_y = random.randint(-field_size//8, -field_size//12) - 8
                    coins.append((x + offset_x, y + offset_y, 13, 2))
                
                # Sort by y position for proper layering
                coins.sort(key=lambda c: (c[1], c[3]))  # Sort by y and layer
                self.coin_cache[grid_key] = coins
            
            # Draw background field with rounded corners - very dark, almost black
            field_rect = pygame.Rect(x - field_size // 2, y - field_size // 2, field_size, field_size)
            
            # Almost black background with very slight brown tint
            pygame.draw.rect(screen, (20, 15, 5), field_rect, border_radius=8)
            
            # Don't add any inner rectangles that might cover coins
            
            # Draw coins from cache AFTER background
            coins = self.coin_cache[grid_key]
            # Debug: print coin count on first draw
            if len(coins) > 0 and grid_key not in getattr(self, '_printed_coins', set()):
                if not hasattr(self, '_printed_coins'):
                    self._printed_coins = set()
                self._printed_coins.add(grid_key)
                print(f"Drawing {len(coins)} coins at gold field {grid_key}")
            
            for coin_x, coin_y, coin_size, layer in coins:
                self._draw_coin(screen, coin_x, coin_y, coin_size, layer == 2)
            
            # Draw contrastive border with rounded corners - bright gold, not filled
            pygame.draw.rect(screen, (255, 215, 0), field_rect, 2, border_radius=8)
            
            # Draw "100" text below the field
            try:
                if 'scale_font' in globals() and callable(scale_font):
                    font_size = scale_font(14)
                else:
                    font_size = 16
                font = pygame.font.Font(None, font_size)
                text = font.render("100", True, (255, 255, 255))
                text_rect = text.get_rect(center=(x, y + field_size // 2 + 10))
                
                # Shadow for text
                shadow_text = font.render("100", True, (0, 0, 0))
                screen.blit(shadow_text, (text_rect.x + 1, text_rect.y + 1))
                
                # Main text
                screen.blit(text, text_rect)
            except Exception as e:
                print(f"Error drawing text: {e}")
                pass  # Skip text if there's an error
    
    def _draw_vine(self, screen, start_x, start_y, length, direction, thickness=1):
        """Draw a curvy vine."""
        points = []
        vine_color = (150, 20, 20)  # Dark red
        
        x, y = start_x, start_y
        for i in range(length):
            # Add some curve to the vine
            offset = math.sin(i * 0.4) * 3  # Small curves
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
            pygame.draw.lines(screen, vine_color, False, points, thickness)
            
            # Add some leaves/thorns (smaller, less frequent)
            for i in range(0, len(points), 15):
                if i < len(points):
                    px, py = points[i]
                    # Small thorn/leaf
                    pygame.draw.circle(screen, vine_color, (int(px), int(py)), thickness)
    
    def _draw_blocked_positions(self, screen, blocked_positions):
        """Draw blocked positions as onyx blocks with red vines."""
        # Use current grid size for field size
        field_size = int(GRID_SIZE * 0.9)  # 90% of grid cell
        
        for pos in blocked_positions:
            x, y = int(pos.x), int(pos.y)
            
            # Main onyx block with rounded corners
            block_rect = pygame.Rect(x - field_size // 2, y - field_size // 2, field_size, field_size)
            
            # Base color - very dark purple/black
            pygame.draw.rect(screen, (20, 10, 25), block_rect, border_radius=8)
            
            # Add marble-like veins directly on screen
            random.seed(x * 100 + y)  # Consistent pattern per block
            for i in range(3):
                vein_start_x = block_rect.left + random.randint(5, field_size - 5)
                vein_start_y = block_rect.top
                vein_end_x = block_rect.left + random.randint(5, field_size - 5)
                vein_end_y = block_rect.bottom
                
                # Draw vein with varying thickness
                vein_color = (60 + random.randint(0, 20), 50 + random.randint(0, 20), 70 + random.randint(0, 20))
                pygame.draw.line(screen, vein_color, 
                               (vein_start_x, vein_start_y),
                               (vein_end_x, vein_end_y), random.randint(1, 3))
            
            # Draw 3D effect edges
            # Highlight (top-left) - lighter edge
            offset = 4
            highlight_points = [
                (block_rect.left + offset, block_rect.bottom - offset),
                (block_rect.left + offset, block_rect.top + offset),
                (block_rect.right - offset, block_rect.top + offset)
            ]
            pygame.draw.lines(screen, (40, 30, 45), False, highlight_points, 2)
            
            # Shadow (bottom-right) - darker edge
            shadow_points = [
                (block_rect.right - offset, block_rect.top + offset),
                (block_rect.right - offset, block_rect.bottom - offset),
                (block_rect.left + offset, block_rect.bottom - offset)
            ]
            pygame.draw.lines(screen, (10, 5, 15), False, shadow_points, 2)
            
            # Main contrastive border - bright red for contrast
            pygame.draw.rect(screen, (255, 50, 50), block_rect, 2, border_radius=8)
            
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
        """Draw hover highlight for component placement."""
        x, y = self.hover_pos
        
        # Calculate the grid cell bounds
        grid_x = round((x - CANVAS_OFFSET_X) / GRID_SIZE)
        grid_y = round((y - CANVAS_OFFSET_Y) / GRID_SIZE)
        cell_x = CANVAS_OFFSET_X + grid_x * GRID_SIZE
        cell_y = CANVAS_OFFSET_Y + grid_y * GRID_SIZE
        
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
        
        # Draw highlight square for the entire grid cell
        s = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(s, (color[0], color[1], color[2], alpha), 
                        pygame.Rect(0, 0, GRID_SIZE, GRID_SIZE))
        screen.blit(s, (cell_x, cell_y))
        
        # Draw border around the grid cell
        rect = pygame.Rect(cell_x, cell_y, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, color[:3], rect, 2)
        
        # Draw center crosshair to show exact placement position
        pygame.draw.line(screen, color[:3], (x - 10, y), (x + 10, y), 1)
        pygame.draw.line(screen, color[:3], (x, y - 10), (x, y + 10), 1)
        
        # Draw small circle at center to emphasize placement point
        pygame.draw.circle(screen, color[:3], (int(x), int(y)), 3)
        
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
        try:
            font_size = scale_font(14) if 'scale_font' in globals() else 14
            font = pygame.font.Font(None, font_size)
        except:
            font = pygame.font.Font(None, 14)
            
        text = font.render("BEAM OBSTACLE", True, (255, 0, 0))
        text_rect = text.get_rect(topleft=(x + 15, y - 25))
        
        # Background
        padding = 5
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        pygame.draw.rect(screen, BLACK, bg_rect)
        pygame.draw.rect(screen, (255, 0, 0), bg_rect, 1)
        
        screen.blit(text, text_rect)
        
        # Draw prohibition symbol
        pygame.draw.circle(screen, (255, 0, 0), (x, y), 20, 3)
        pygame.draw.line(screen, (255, 0, 0), 
                        (x - 14, y - 14), 
                        (x + 14, y + 14), 3)
    
    def _draw_occupied_text(self, screen, x, y):
        """Draw occupied warning."""
        try:
            font_size = scale_font(14) if 'scale_font' in globals() else 14
            font = pygame.font.Font(None, font_size)
        except:
            font = pygame.font.Font(None, 14)
            
        text = font.render("OCCUPIED", True, (255, 0, 0))
        text_rect = text.get_rect(topleft=(x + 15, y - 25))
        
        # Background
        padding = 5
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        pygame.draw.rect(screen, BLACK, bg_rect)
        pygame.draw.rect(screen, (255, 0, 0), bg_rect, 1)
        
        screen.blit(text, text_rect)
        
        # Draw X mark
        pygame.draw.line(screen, (255, 0, 0), 
                        (x - 15, y - 15), 
                        (x + 15, y + 15), 3)
        pygame.draw.line(screen, (255, 0, 0), 
                        (x + 15, y - 15), 
                        (x - 15, y + 15), 3)
    
    def _draw_coords_text(self, screen, x, y):
        """Draw coordinate display with grid coordinates."""
        try:
            font_size = scale_font(14) if 'scale_font' in globals() else 14
            font = pygame.font.Font(None, font_size)
        except:
            font = pygame.font.Font(None, 14)
            
        # Convert to grid coordinates - x,y are already centered in cell
        grid_x = round((x - CANVAS_OFFSET_X - GRID_SIZE // 2) / GRID_SIZE)
        grid_y = round((y - CANVAS_OFFSET_Y - GRID_SIZE // 2) / GRID_SIZE)
        coords_text = f"({grid_x}, {grid_y})"
        text = font.render(coords_text, True, CYAN)
        text_rect = text.get_rect(topleft=(x + 15, y - 25))
        
        # Background
        padding = 5
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        pygame.draw.rect(screen, BLACK, bg_rect)
        pygame.draw.rect(screen, CYAN, bg_rect, 1)
        
        screen.blit(text, text_rect)