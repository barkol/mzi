#!/usr/bin/env python
"""
Resize & drag diagnostic tool.

Runs the game in a window, progressively resizes it, and at each size
simulates a slow mouse drag of the laser to a new grid position.
Screenshots are taken at key moments and saved into a timestamped
ZIP archive for diagnostics.

Usage:
    python test_resize_screenshots.py [--sizes 800x600,1200x675,1600x900]
"""

import os
import sys
import time
import zipfile
import argparse
import platform
from io import BytesIO
from datetime import datetime

# DPI awareness (Windows)
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

os.environ.setdefault("SDL_VIDEODRIVER", "x11")  # use real display

import pygame
import config.settings as _settings
from config.settings import update_scaled_values, scale, DESIGN_WIDTH, DESIGN_HEIGHT
from core.game import Game

# ---------------------------------------------------------------------------

def parse_sizes(s):
    """Parse '800x600,1200x675' into list of (w,h) tuples."""
    sizes = []
    for tok in s.split(","):
        w, h = tok.strip().split("x")
        sizes.append((int(w), int(h)))
    return sizes


DEFAULT_SIZES = [
    (800,  500),
    (1000, 600),
    (1200, 675),
    (1400, 800),
    (1600, 900),
]


def screenshot(screen, label, shots):
    """Capture a screenshot and store in the shots list."""
    buf = BytesIO()
    pygame.image.save(screen, buf, "screenshot.bmp")
    buf.seek(0)
    # Convert BMP bytes → we'll save as-is (zip handles compression)
    shots.append((label, buf.getvalue()))


def simulate_drag(game, screen, clock, shots, label_prefix,
                  from_grid, to_grid, steps=15):
    """Simulate a slow mouse drag from one grid cell to another."""
    G  = _settings.GRID_SIZE
    OX = _settings.CANVAS_OFFSET_X
    OY = _settings.CANVAS_OFFSET_Y

    # Pixel centers
    sx = OX + from_grid[0] * G + G // 2
    sy = OY + from_grid[1] * G + G // 2
    ex = OX + to_grid[0] * G + G // 2
    ey = OY + to_grid[1] * G + G // 2

    # --- mouse down on source ---
    evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                             button=1, pos=(sx, sy))
    game.handle_event(evt)
    # pump a few frames so the pick-up registers
    for _ in range(3):
        game.update(1 / 60)
        game.draw()
        pygame.display.flip()
        clock.tick(60)

    screenshot(screen, f"{label_prefix}_1_pickup", shots)

    # --- slow mouse motion ---
    for i in range(1, steps + 1):
        t = i / steps
        mx = int(sx + (ex - sx) * t)
        my = int(sy + (ey - sy) * t)
        evt = pygame.event.Event(pygame.MOUSEMOTION,
                                 pos=(mx, my), rel=(1, 0), buttons=(1, 0, 0))
        game.handle_event(evt)
        game.update(1 / 60)
        game.draw()
        pygame.display.flip()
        clock.tick(60)
        if i == steps // 2:
            screenshot(screen, f"{label_prefix}_2_midway", shots)

    screenshot(screen, f"{label_prefix}_3_predrop", shots)

    # --- mouse up (drop) ---
    evt = pygame.event.Event(pygame.MOUSEBUTTONUP,
                             button=1, pos=(ex, ey))
    game.handle_event(evt)
    # pump frames for the drop to take effect + beam to render
    for _ in range(5):
        game.update(1 / 60)
        game.draw()
        pygame.display.flip()
        clock.tick(60)

    screenshot(screen, f"{label_prefix}_4_dropped", shots)


def run(sizes):
    pygame.init()
    clock = pygame.time.Clock()
    shots = []  # list of (filename, bmp_bytes)

    # Start at first size
    w0, h0 = sizes[0]
    sf = min(w0 / DESIGN_WIDTH, h0 / DESIGN_HEIGHT)
    update_scaled_values(sf, window_width=w0, window_height=h0, fullscreen=False)
    screen = pygame.display.set_mode((w0, h0), pygame.RESIZABLE)
    pygame.display.set_caption("Resize Diagnostic")
    game = Game(screen, sf)

    # Let the game render a few frames to stabilize
    for _ in range(10):
        game.update(1 / 60)
        game.draw()
        pygame.display.flip()
        clock.tick(60)

    screenshot(screen, f"00_initial_{w0}x{h0}", shots)

    for idx, (w, h) in enumerate(sizes):
        tag = f"{idx + 1:02d}_{w}x{h}"
        print(f"Testing {w}x{h} ...")

        # --- resize ---
        sf = min(w / DESIGN_WIDTH, h / DESIGN_HEIGHT)
        update_scaled_values(sf, window_width=w, window_height=h, fullscreen=False)
        screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        game.update_scale(sf)
        game.update_screen_references(screen, screen)

        # Render a few frames at new size
        for _ in range(8):
            game.update(1 / 60)
            game.draw()
            pygame.display.flip()
            clock.tick(60)

        screenshot(screen, f"{tag}_a_after_resize", shots)

        # --- drag laser from its current position to (3, 3) ---
        laser_gx = (_settings.CANVAS_OFFSET_X
                     and int((game.laser.position.x - _settings.CANVAS_OFFSET_X)
                             // _settings.GRID_SIZE))
        laser_gy = int((game.laser.position.y - _settings.CANVAS_OFFSET_Y)
                       // _settings.GRID_SIZE)

        target = (3, 3)
        if (laser_gx, laser_gy) == target:
            target = (5, 5)  # pick a different cell if already there

        simulate_drag(game, screen, clock, shots,
                      f"{tag}_drag",
                      from_grid=(laser_gx, laser_gy),
                      to_grid=target)

        # --- now drag laser to another row to check beam alignment ---
        target2 = (target[0], target[1] + 3)
        if target2[1] >= _settings.CANVAS_GRID_ROWS:
            target2 = (target[0], target[1] - 3)
        simulate_drag(game, screen, clock, shots,
                      f"{tag}_drag2",
                      from_grid=target,
                      to_grid=target2)

        # Flush pygame events
        pygame.event.pump()

    pygame.quit()

    # --- save ZIP ---
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"resize_diag_{ts}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in shots:
            # Save as BMP inside zip (smaller than uncompressed, fast)
            zf.writestr(f"{name}.bmp", data)
    print(f"\nSaved {len(shots)} screenshots to {zip_name}")
    return zip_name


def main():
    parser = argparse.ArgumentParser(description="Resize & drag diagnostic")
    parser.add_argument("--sizes", type=str, default=None,
                        help="Comma-separated WxH sizes, e.g. 800x600,1200x675")
    args = parser.parse_args()

    sizes = parse_sizes(args.sizes) if args.sizes else DEFAULT_SIZES
    run(sizes)


if __name__ == "__main__":
    main()
