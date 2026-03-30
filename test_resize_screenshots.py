#!/usr/bin/env python
"""
Resize & drag diagnostic tool.

Runs the game in a window, progressively resizes it, and at each size
moves the laser through several random grid positions via direct
position setting (bypassing drag events for reliability). Takes a
screenshot after each move to verify beam alignment.

Usage:
    python test_resize_screenshots.py [--sizes 800x600,1200x675,1600x900]
"""

import os
import sys
import random
import zipfile
import argparse
import platform
from io import BytesIO
from datetime import datetime

# DPI awareness (Windows) — must be before pygame.init()
if platform.system() == "Windows":
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
    os.environ.setdefault('SDL_WINDOWS_DPI_AWARENESS', 'permonitorv2')

import pygame
import config.settings as _settings
from config.settings import update_scaled_values, DESIGN_WIDTH, DESIGN_HEIGHT
from core.game import Game
from utils.vector import Vector2

# ---------------------------------------------------------------------------

def parse_sizes(s):
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

N_MOVES = 6  # number of random laser moves per window size


def screenshot(screen, label, shots):
    buf = BytesIO()
    pygame.image.save(screen, buf, "screenshot.bmp")
    buf.seek(0)
    shots.append((label, buf.getvalue()))


def pump_frames(game, screen, clock, n=5):
    """Advance the game n frames so beams are solved and drawn."""
    for _ in range(n):
        game.update(1 / 60)
        game.draw()
        pygame.display.flip()
        clock.tick(60)
        pygame.event.pump()


def move_laser_directly(game, col, row):
    """Move laser to grid cell (col, row) by setting position directly."""
    G  = _settings.GRID_SIZE
    OX = _settings.CANVAS_OFFSET_X
    OY = _settings.CANVAS_OFFSET_Y
    x = OX + col * G + G // 2
    y = OY + row * G + G // 2
    game.laser.position = Vector2(x, y)
    if hasattr(game.laser, '_ports'):
        game.laser._ports = None
    game.beam_tracer._network_valid = False
    game.beam_tracer._last_component_set = None
    game.beam_tracer._last_component_positions = None


def check_beam_alignment(game, tag, log_lines):
    """Check all beam connections for diagonal beams. Returns True if OK."""
    ok = True
    for i, c in enumerate(game.beam_tracer.connections):
        amp = game.beam_tracer.beam_amplitudes.get(f'beam_{i}', 0j)
        if abs(amp) < 0.001:
            continue
        p1 = c.port1.position
        p2 = c.port2.position
        dx = abs(p1.x - p2.x)
        dy = abs(p1.y - p2.y)
        if dx > 1 and dy > 1:
            msg = (f"DIAGONAL {tag}: beam {i} "
                   f"({p1.x},{p1.y})->({p2.x},{p2.y}) "
                   f"dx={dx:.0f} dy={dy:.0f} "
                   f"GRID={_settings.GRID_SIZE} "
                   f"laser=({game.laser.position.x},{game.laser.position.y}) "
                   f"types=({type(game.laser.position.x).__name__},"
                   f"{type(game.laser.position.y).__name__})")
            print(f"  *** {msg}")
            log_lines.append(msg)
            ok = False
    return ok


def run(sizes):
    pygame.init()
    clock = pygame.time.Clock()
    shots = []
    log_lines = []
    rng = random.Random(42)  # deterministic

    # Start at first size
    w0, h0 = sizes[0]
    sf = min(w0 / DESIGN_WIDTH, h0 / DESIGN_HEIGHT)
    update_scaled_values(sf, window_width=w0, window_height=h0, fullscreen=False)
    screen = pygame.display.set_mode((w0, h0), pygame.RESIZABLE)
    pygame.display.set_caption("Resize Diagnostic")
    game = Game(screen, sf)
    pump_frames(game, screen, clock, 10)

    total_ok = 0
    total_tests = 0

    for idx, (w, h) in enumerate(sizes):
        tag_base = f"{idx + 1:02d}_{w}x{h}"
        print(f"Testing {w}x{h} ...")

        # Resize
        sf = min(w / DESIGN_WIDTH, h / DESIGN_HEIGHT)
        update_scaled_values(sf, window_width=w, window_height=h, fullscreen=False)
        screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        game.update_scale(sf)
        game.update_screen_references(screen, screen)
        pump_frames(game, screen, clock, 8)

        screenshot(screen, f"{tag_base}_00_resized", shots)

        max_col = _settings.CANVAS_GRID_COLS - 2
        max_row = _settings.CANVAS_GRID_ROWS - 2

        # Generate random positions
        positions = []
        for _ in range(N_MOVES):
            c = rng.randint(1, max(1, max_col))
            r = rng.randint(1, max(1, max_row))
            positions.append((c, r))

        for mi, (col, row) in enumerate(positions):
            tag = f"{tag_base}_m{mi + 1}_g{col}x{row}"
            move_laser_directly(game, col, row)
            pump_frames(game, screen, clock, 5)
            screenshot(screen, tag, shots)

            total_tests += 1
            if check_beam_alignment(game, tag, log_lines):
                total_ok += 1

        pygame.event.pump()

    pygame.quit()

    # Summary
    print(f"\n{'='*60}")
    print(f"Results: {total_ok}/{total_tests} tests OK")
    if log_lines:
        print(f"DIAGONAL BEAMS FOUND ({len(log_lines)}):")
        for line in log_lines:
            print(f"  {line}")
    else:
        print("All beams perfectly aligned!")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"{'='*60}")

    # Save ZIP
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"resize_diag_{ts}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in shots:
            zf.writestr(f"{name}.bmp", data)
        if log_lines:
            zf.writestr("diagonal_beams.txt", "\n".join(log_lines))
    print(f"Saved {len(shots)} screenshots to {zip_name}")
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
