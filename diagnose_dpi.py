#!/usr/bin/env python
"""
DPI diagnostic — run this on Windows to detect coordinate mismatch.

Draws a grid and tracks mouse position vs expected grid cell.
If DPI scaling causes a mismatch, it will be visible immediately:
the red crosshair (actual mouse) won't align with the green
highlight (snapped grid cell).

Press Q to quit. Output is printed to console.
"""
import os
import sys
import platform

# Try DPI awareness BEFORE pygame
dpi_method = "none"
if platform.system() == "Windows":
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            dpi_method = "shcore(2)"
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
                dpi_method = "shcore(1)"
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
                dpi_method = "user32"
    except Exception:
        dpi_method = "failed"
    os.environ.setdefault('SDL_WINDOWS_DPI_AWARENESS', 'permonitorv2')

import pygame

def main():
    pygame.init()
    info = pygame.display.Info()
    sw, sh = info.current_w, info.current_h

    # Use a moderate window size
    win_w, win_h = min(1200, sw - 100), min(700, sh - 100)
    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    pygame.display.set_caption("DPI Diagnostic")

    GRID = 50
    OFFSET_X = 100
    OFFSET_Y = 80
    COLS = (win_w - OFFSET_X - 50) // GRID
    ROWS = (win_h - OFFSET_Y - 50) // GRID

    font = pygame.font.Font(None, 20)
    big_font = pygame.font.Font(None, 28)

    clock = pygame.time.Clock()
    running = True
    mismatch_count = 0
    total_moves = 0

    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"DPI method: {dpi_method}")
    print(f"Display: {sw}x{sh}")
    print(f"Window: {win_w}x{win_h}")
    print(f"Grid: {COLS}x{ROWS} cells, {GRID}px each")
    print(f"Offset: ({OFFSET_X},{OFFSET_Y})")
    print()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                win_w, win_h = event.w, event.h
                screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
                COLS = (win_w - OFFSET_X - 50) // GRID
                ROWS = (win_h - OFFSET_Y - 50) // GRID

        mx, my = pygame.mouse.get_pos()

        # Grid snap
        gx = (mx - OFFSET_X) // GRID
        gy = (my - OFFSET_Y) // GRID
        snap_x = OFFSET_X + gx * GRID + GRID // 2
        snap_y = OFFSET_Y + gy * GRID + GRID // 2

        # Check: is the mouse actually inside the snapped cell?
        cell_left = OFFSET_X + gx * GRID
        cell_top = OFFSET_Y + gy * GRID
        in_cell = (cell_left <= mx < cell_left + GRID and
                   cell_top <= my < cell_top + GRID)

        if 0 <= gx < COLS and 0 <= gy < ROWS:
            total_moves += 1
            if not in_cell:
                mismatch_count += 1
                if mismatch_count <= 10:
                    print(f"MISMATCH: mouse=({mx},{my}) -> grid({gx},{gy}) "
                          f"cell=[{cell_left},{cell_top}]-[{cell_left+GRID},{cell_top+GRID}] "
                          f"mouse_in_cell={in_cell}")

        # Draw
        screen.fill((20, 10, 30))

        # Grid lines
        for col in range(COLS + 1):
            x = OFFSET_X + col * GRID
            pygame.draw.line(screen, (40, 40, 60), (x, OFFSET_Y), (x, OFFSET_Y + ROWS * GRID))
        for row in range(ROWS + 1):
            y = OFFSET_Y + row * GRID
            pygame.draw.line(screen, (40, 40, 60), (OFFSET_X, y), (OFFSET_X + COLS * GRID, y))

        # Highlighted cell (green)
        if 0 <= gx < COLS and 0 <= gy < ROWS:
            cell_rect = pygame.Rect(cell_left, cell_top, GRID, GRID)
            color = (0, 100, 0) if in_cell else (100, 0, 0)  # green if match, red if mismatch
            s = pygame.Surface((GRID, GRID), pygame.SRCALPHA)
            s.fill((*color, 80))
            screen.blit(s, cell_rect.topleft)
            pygame.draw.rect(screen, (0, 255, 0) if in_cell else (255, 0, 0), cell_rect, 2)

        # Mouse crosshair (red)
        pygame.draw.line(screen, (255, 50, 50), (mx - 10, my), (mx + 10, my), 1)
        pygame.draw.line(screen, (255, 50, 50), (mx, my - 10), (mx, my + 10), 1)

        # Snap position (cyan dot)
        if 0 <= gx < COLS and 0 <= gy < ROWS:
            pygame.draw.circle(screen, (0, 255, 255), (snap_x, snap_y), 4)

        # Info text
        texts = [
            f"Mouse: ({mx}, {my})",
            f"Grid cell: ({gx}, {gy})",
            f"Snap: ({snap_x}, {snap_y})",
            f"In cell: {in_cell}",
            f"DPI: {dpi_method}",
            f"Window: {win_w}x{win_h}",
            f"Mismatches: {mismatch_count}/{total_moves}",
        ]
        for i, txt in enumerate(texts):
            color = (255, 100, 100) if "False" in txt else (200, 200, 200)
            surf = font.render(txt, True, color)
            screen.blit(surf, (10, 10 + i * 20))

        # Title
        title = big_font.render("Move mouse over grid - green=OK, red=DPI mismatch", True, (255, 255, 255))
        screen.blit(title, (OFFSET_X, OFFSET_Y - 30))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

    print(f"\nFinal: {mismatch_count} mismatches out of {total_moves} mouse positions")
    if mismatch_count > 0:
        print("DPI SCALING IS CAUSING COORDINATE MISMATCH!")
        print("The game's grid snap will be wrong at this DPI setting.")
    else:
        print("No DPI issues detected.")

if __name__ == "__main__":
    main()
