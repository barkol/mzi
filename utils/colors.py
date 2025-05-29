"""Color utilities and effects."""
import math
import time

def pulse_alpha(base_alpha, speed=0.005):
    """Create pulsing alpha effect."""
    return int(base_alpha * (0.5 + 0.5 * math.sin(time.time() * speed * 1000)))

def blend_colors(color1, color2, factor):
    """Blend two colors based on factor (0-1)."""
    return tuple(
        int(c1 * (1 - factor) + c2 * factor)
        for c1, c2 in zip(color1, color2)
    )