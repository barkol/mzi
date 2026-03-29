"""Flat mirror component for retroreflection (Michelson interferometer arms)."""
import pygame
import numpy as np
from components.tunable_beamsplitter import TunableBeamSplitter
from config.settings import CYAN, MIRROR_LOSS, scale, scale_font, GRID_SIZE


class FlatMirror(TunableBeamSplitter):
    """Flat mirror that reflects a beam 180 degrees back along the same axis.

    Orientations:
        '|' (vertical)  — reflects beams on the horizontal axis (left <-> right)
        '-' (horizontal) — reflects beams on the vertical axis  (top <-> bottom)

    Port order: [A (left), B (bottom), C (right), D (top)]
    """

    def __init__(self, x, y, orientation='|'):
        t = 0.0
        r = -1.0
        super().__init__(x, y, t=t, r=r, orientation=orientation, loss=MIRROR_LOSS)
        self.component_type = "flat_mirror"
        self.orientation = orientation

        # S-matrix for retroreflection.
        # Port layout: A(left, dir=left), B(bottom, dir=down),
        #              C(right, dir=right), D(top, dir=up).
        #
        # A beam going RIGHT enters port A (left). To send it back LEFT,
        # it must exit from the port whose direction is LEFT — that's port A.
        # But port A is already used as the input destination.
        #
        # With the updated connection system (separate in/out per port),
        # port A CAN be both an incoming destination and an outgoing source.
        # The trace from port A goes LEFT, which hits the BS's port C
        # (right) — exactly the retroreflection we want.
        # For retroreflection in the port model, the output must use the
        # OPPOSITE port on the same axis so the beam direction reverses:
        #   Port A (left, dir=LEFT) ↔ Port C (right, dir=RIGHT)
        #   Port B (bottom, dir=DOWN) ↔ Port D (top, dir=UP)
        #
        # A beam arriving at port A (from the left, going right) must exit
        # through port C (which points right)? No — port C points RIGHT,
        # but we want the beam to go LEFT (back the way it came).
        #
        # Actually: a beam going RIGHT enters port A. To go back LEFT it
        # must exit from a port pointing LEFT. Only port A points left.
        # But the connection finder can now handle port A being both source
        # and destination. The trace from port A goes LEFT, which is correct.
        #
        # The problem is that for the HORIZONTAL flat mirror, input comes
        # at port B (from the top, beam going DOWN). The mirror must send
        # it back UP. Port D points UP. So: S[3,1] = -1 (input B → output D).
        if orientation == '|':
            # Vertical flat mirror — retroreflects horizontal beams
            # Input port A (beam from left) → Output port A (exits left)
            # Input port C (beam from right) → Output port C (exits right)
            # Port A can serve as both input dest and output source.
            self.S = np.array([
                [-1,  0,  0,  0],
                [ 0,  0,  0,  0],
                [ 0,  0, -1,  0],
                [ 0,  0,  0,  0],
            ], dtype=complex)
        else:  # '-'
            # Horizontal flat mirror — retroreflects vertical beams
            # Input port B (beam from top, going down) → Output port D (exits up)
            # Input port D (beam from bottom, going up) → Output port B (exits down)
            self.S = np.array([
                [ 0,  0,  0,  0],
                [ 0,  0,  0, -1],
                [ 0,  0,  0,  0],
                [ 0, -1,  0,  0],
            ], dtype=complex)

    def draw(self, screen):
        """Draw flat mirror as a thick straight line perpendicular to its axis."""
        size = int(GRID_SIZE * 0.8)
        half = size // 2
        cx, cy = int(self.position.x), int(self.position.y)

        if self.orientation == '|':
            # Vertical bar
            start = (cx, cy - half)
            end = (cx, cy + half)
        else:
            # Horizontal bar
            start = (cx - half, cy)
            end = (cx + half, cy)

        # Thick reflective line
        pygame.draw.line(screen, CYAN, start, end, scale(6))

        # Hatching on the non-reflective side to indicate "wall" backing
        hatch_len = scale(6)
        num_hatches = 5
        if self.orientation == '|':
            for i in range(num_hatches):
                t = (i + 0.5) / num_hatches
                hy = int(cy - half + t * size)
                pygame.draw.line(screen, (CYAN[0] // 2, CYAN[1] // 2, CYAN[2] // 2),
                                 (cx + 2, hy), (cx + hatch_len, hy - hatch_len), scale(1))
        else:
            for i in range(num_hatches):
                t = (i + 0.5) / num_hatches
                hx = int(cx - half + t * size)
                pygame.draw.line(screen, (CYAN[0] // 2, CYAN[1] // 2, CYAN[2] // 2),
                                 (hx, cy + 2), (hx - hatch_len, cy + hatch_len), scale(1))

        # Arrow hints showing retroreflection
        arrow_off = int(GRID_SIZE * 0.35)
        arrow_len = scale(8)
        arrow_color = (CYAN[0], CYAN[1], CYAN[2], 160)

        if self.orientation == '|':
            # Left-side double-headed arrow (horizontal retro)
            for dy in [-arrow_len, arrow_len]:
                # incoming arrow
                pygame.draw.line(screen, CYAN,
                                 (cx - arrow_off - arrow_len, cy + dy),
                                 (cx - arrow_off, cy + dy), scale(1))
                # outgoing arrow
                pygame.draw.line(screen, CYAN,
                                 (cx - arrow_off, cy + dy),
                                 (cx - arrow_off - arrow_len // 2, cy + dy - arrow_len // 3 * (1 if dy < 0 else -1)),
                                 scale(1))
        else:
            for dx in [-arrow_len, arrow_len]:
                pygame.draw.line(screen, CYAN,
                                 (cx + dx, cy - arrow_off - arrow_len),
                                 (cx + dx, cy - arrow_off), scale(1))

        # Debug info
        if self.debug:
            font = pygame.font.Font(None, scale_font(10))
            info = font.render(f"Flat {self.orientation}", True, CYAN)
            screen.blit(info, (cx - scale(20), cy + scale(25)))
