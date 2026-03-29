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
        # Port input convention: beam going DOWN enters port D (top face),
        # beam going UP enters port B (bottom face).
        if orientation == '|':
            # Vertical flat mirror — retroreflects horizontal beams.
            # Vertical beams pass through unchanged (unitarity).
            #   RIGHT(A) → LEFT(A)   retroreflection
            #   LEFT(C)  → RIGHT(C)  retroreflection
            #   DOWN(D)  → DOWN(B)   pass through
            #   UP(B)    → UP(D)     pass through
            self.S = np.array([
                [-1,  0,  0,  0],
                [ 0,  0,  0,  1],
                [ 0,  0, -1,  0],
                [ 0,  1,  0,  0],
            ], dtype=complex)
        else:  # '-'
            # Horizontal flat mirror — retroreflects vertical beams.
            # Horizontal beams pass through unchanged.
            #   DOWN(D) → UP(D)    retroreflection
            #   UP(B)   → DOWN(B)  retroreflection
            #   RIGHT(A)→ RIGHT(C) pass through
            #   LEFT(C) → LEFT(A)  pass through
            self.S = np.array([
                [ 0,  0,  1,  0],
                [ 0, -1,  0,  0],
                [ 1,  0,  0,  0],
                [ 0,  0,  0, -1],
            ], dtype=complex)

    def draw(self, screen):
        """Draw flat mirror as a thick reflective surface with hatching backing.

        Follows the standard optics-diagram convention: a solid reflective face
        with close-spaced diagonal hatching on the substrate (non-reflective)
        side.
        """
        size = int(GRID_SIZE * 0.8)
        half = size // 2
        cx, cy = int(self.position.x), int(self.position.y)

        line_thickness = scale(4)
        hatch_color = (CYAN[0] // 2, CYAN[1] // 2, CYAN[2] // 2)
        hatch_len = scale(8)
        num_hatches = 7

        if self.orientation == '|':
            # Vertical reflective surface
            pygame.draw.line(screen, CYAN, (cx, cy - half), (cx, cy + half), line_thickness)
            # Dense hatching on the right (substrate side)
            for i in range(num_hatches):
                t = (i + 0.5) / num_hatches
                hy = int(cy - half + t * size)
                pygame.draw.line(screen, hatch_color,
                                 (cx + scale(2), hy),
                                 (cx + hatch_len, hy - hatch_len), scale(1))
        else:
            # Horizontal reflective surface
            pygame.draw.line(screen, CYAN, (cx - half, cy), (cx + half, cy), line_thickness)
            # Dense hatching below (substrate side)
            for i in range(num_hatches):
                t = (i + 0.5) / num_hatches
                hx = int(cx - half + t * size)
                pygame.draw.line(screen, hatch_color,
                                 (hx, cy + scale(2)),
                                 (hx - hatch_len, cy + hatch_len), scale(1))

        # Debug info
        if self.debug:
            font = pygame.font.Font(None, scale_font(10))
            info = font.render(f"Flat {self.orientation}", True, CYAN)
            screen.blit(info, (cx - scale(20), cy + scale(25)))
