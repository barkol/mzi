"""Renderer for quantum wave packets with trails, collapse effects, and histogram."""

import math
import cmath
import time
import pygame
from typing import List, Dict, Optional, Tuple
import config.settings as _settings
from config.settings import CYAN, WHITE, GOLD, scale, scale_font
from core.quantum_packet import (
    QuantumPacketEngine, PacketFamily, QuantumPacket,
    PacketState,
)


class PacketRenderer:
    """Draws quantum wave packets, trails, collapse animations, and detection histogram."""

    # Packet visual length in pixels
    PACKET_LENGTH = 30
    # Trail fade behind the packet (0..1 alpha at tail)
    TRAIL_ALPHA_MIN = 30

    def __init__(self, screen):
        self.screen = screen
        self._start_time = time.time()

    @staticmethod
    def _phase_to_color(phase: float, brightness: float = 1.0) -> Tuple[int, int, int]:
        """Map quantum phase angle to RGB color on a hue wheel.

        phase=0 → cyan, π/2 → magenta, π → red-orange, 3π/2 → green.
        This keeps cyan as the dominant color (matching the game's palette)
        while making phase differences clearly visible.
        """
        # Normalize phase to 0..2π
        hue = (phase % (2 * math.pi)) / (2 * math.pi)  # 0..1
        # Shift so 0 phase = cyan (hue ≈ 0.5)
        hue = (hue + 0.5) % 1.0
        # HSV to RGB (saturation=0.7 to keep colors vivid but not garish)
        s = 0.7
        v = brightness
        h_i = int(hue * 6) % 6
        f = hue * 6 - int(hue * 6)
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        if h_i == 0:
            r, g, b = v, t, p
        elif h_i == 1:
            r, g, b = q, v, p
        elif h_i == 2:
            r, g, b = p, v, t
        elif h_i == 3:
            r, g, b = p, q, v
        elif h_i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        return (int(r * 255), int(g * 255), int(b * 255))

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def draw_packets(self, engine: QuantumPacketEngine, ghost_beams=None):
        """Draw everything related to quantum packet mode.

        *ghost_beams*: optional list of beam dicts from the wave engine to draw
        as dim guide paths.
        """
        now = time.time()
        t = now - self._start_time

        # 1. Ghost beams (steady-state topology)
        if ghost_beams:
            self._draw_ghost_beams(ghost_beams, t)

        # 2. For each family draw trails, packets, collapse effects
        self._engine = engine
        self._theory_cache = None  # recompute once per frame if needed
        for family in engine.families:
            self._draw_family(family, now, t)

        # 3. Detection histogram near each detector
        self._draw_histogram(engine)

    # ------------------------------------------------------------------
    # Ghost beams
    # ------------------------------------------------------------------

    def _draw_ghost_beams(self, beams, t):
        for beam in beams:
            path = beam['path']
            if len(path) < 2 or beam['amplitude'] < 0.01:
                continue
            # dim cyan with gentle pulse
            pulse = 0.12 + 0.04 * math.sin(t * 1.5)
            alpha = max(10, min(60, int(255 * pulse * beam['amplitude'])))
            color = (0, 180, 200, alpha)

            for i in range(len(path) - 1):
                p1 = path[i].tuple() if hasattr(path[i], 'tuple') else path[i]
                p2 = path[i+1].tuple() if hasattr(path[i+1], 'tuple') else path[i+1]
                # Use a surface with alpha
                self._draw_alpha_line(p1, p2, color, max(1, _settings.BEAM_WIDTH // 2))

    def _draw_alpha_line(self, p1, p2, color, width):
        """Draw a line with per-pixel alpha."""
        # Compute bounding rect
        x1, y1 = p1
        x2, y2 = p2
        min_x = min(x1, x2) - width
        min_y = min(y1, y2) - width
        max_x = max(x1, x2) + width
        max_y = max(y1, y2) + width
        w = max(1, max_x - min_x + 1)
        h = max(1, max_y - min_y + 1)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        local_p1 = (x1 - min_x, y1 - min_y)
        local_p2 = (x2 - min_x, y2 - min_y)
        pygame.draw.line(surf, color, local_p1, local_p2, width)
        self.screen.blit(surf, (min_x, min_y))

    # ------------------------------------------------------------------
    # Per-family drawing
    # ------------------------------------------------------------------

    def _draw_family(self, family: PacketFamily, now: float, t: float):
        # Count photons per detector in this family for flash gating
        photons_per_det: dict = {}
        for pkt in family.packets:
            if pkt.state == PacketState.DETECTED and pkt.detector is not None:
                det_id = id(pkt.detector)
                photons_per_det[det_id] = photons_per_det.get(det_id, 0) + 1

        # Count co-traveling photons per connection for number labels
        photons_per_conn: dict = {}
        for pkt in family.packets:
            if pkt.state == PacketState.TRAVELING:
                photons_per_conn[pkt.connection_index] = \
                    photons_per_conn.get(pkt.connection_index, 0) + 1

        # Track which connections already have a label drawn
        labeled_conns: set = set()

        for pkt in family.packets:
            if pkt.state == PacketState.TRAVELING:
                n = photons_per_conn.get(pkt.connection_index, 1)
                # In multi-photon mode, skip pulses that carry 0 photons
                if family.n_photons > 1 and n <= 0:
                    continue
                # Suppress pulses heading to zero-probability detectors.
                # After interference, a detector may receive 0 photons
                # even though individual superposition packets still
                # travel toward it.  Scale the visual by the detection
                # probability so that zero-probability paths are invisible.
                if self._packet_visibility(pkt) < 0.01:
                    continue
                self._draw_trail(pkt, t)
                self._draw_packet(pkt, t)
                # Draw photon-number label once per connection
                if family.n_photons > 1 and n > 0 and pkt.connection_index not in labeled_conns:
                    labeled_conns.add(pkt.connection_index)
                    self._draw_photon_number(pkt, n)
            elif pkt.state == PacketState.ARRIVED:
                self._draw_trail(pkt, t)
                self._draw_arrived_glow(pkt, t)
            elif pkt.state == PacketState.DETECTED:
                self._draw_trail(pkt, t, detected=True)
            elif pkt.state == PacketState.COLLAPSED:
                elapsed = now - pkt.detection_time
                self._draw_collapse_trail(pkt, elapsed, family)

    # ------------------------------------------------------------------
    # Photon-number-aware visibility
    # ------------------------------------------------------------------

    def _packet_visibility(self, pkt: QuantumPacket) -> float:
        """Return 0..1 visibility for a traveling packet.

        Uses the wave-optics theoretical probabilities to determine
        whether this packet's destination detector will actually receive
        a photon after interference.  Packets heading to non-detector
        components (mirrors, BSes) are always visible.
        """
        engine = getattr(self, '_engine', None)
        if engine is None:
            return 1.0
        graph = engine._network_graph
        if graph is None:
            return 1.0
        conns = graph['connections']
        if pkt.connection_index >= len(conns):
            return 1.0
        dest = conns[pkt.connection_index]['dest_component']
        if dest.component_type != 'detector':
            return 1.0
        # Look up the theoretical probability for this detector
        theory = getattr(self, '_theory_cache', None)
        if theory is None:
            theory = engine.get_theoretical_probs()
            self._theory_cache = theory
        prob = theory.get(dest, None)
        if prob is None:
            return 1.0
        return prob

    # ------------------------------------------------------------------
    # Traveling packet
    # ------------------------------------------------------------------

    def _draw_packet(self, pkt: QuantumPacket, t: float):
        """Draw the moving wave packet as a glowing segment with phase-encoded color."""
        path = pkt.path
        if not path or len(path) < 2:
            return

        amp = abs(pkt.amplitude)
        if amp < 0.01:
            return

        # Get head position
        head = self._position_on_path(path, pkt.progress)
        if head is None:
            return

        # Get tail position (slightly behind)
        total_len = self._path_total_length(path)
        pkt_frac = self.PACKET_LENGTH / total_len if total_len > 0 else 0.1
        tail_progress = max(0, pkt.progress - pkt_frac)
        tail = self._position_on_path(path, tail_progress)
        if tail is None:
            tail = head

        # Phase-based color — the hue encodes the quantum phase
        phase = cmath.phase(pkt.amplitude)
        # Oscillating brightness for wave nature
        wave_osc = 0.75 + 0.25 * math.sin(t * 8.0 + pkt.id * 0.7)
        color = self._phase_to_color(phase, brightness=wave_osc)

        width = max(2, int(_settings.BEAM_WIDTH * amp * 1.2))

        hx, hy = int(head.x), int(head.y)
        tx, ty = int(tail.x), int(tail.y)

        # Outer glow (dimmer version of phase color)
        glow_w = width + 6
        glow_color = (color[0] // 3, color[1] // 3, color[2] // 3)
        pygame.draw.line(self.screen, glow_color, (tx, ty), (hx, hy), glow_w)

        # Main body
        pygame.draw.line(self.screen, color, (tx, ty), (hx, hy), width)

        # Bright core (whiter version)
        core_w = max(1, width // 2)
        core_color = (min(255, color[0] + 80), min(255, color[1] + 80),
                      min(255, color[2] + 80))
        pygame.draw.line(self.screen, core_color, (tx, ty), (hx, hy), core_w)

        # Head dot
        pygame.draw.circle(self.screen, core_color, (hx, hy), max(2, width))

    def _draw_photon_number(self, pkt: QuantumPacket, n: int):
        """Draw a small circled number near the packet head showing photon count."""
        if n <= 0:
            return
        path = pkt.path
        if not path or len(path) < 2:
            return
        head = self._position_on_path(path, pkt.progress)
        if head is None:
            return

        hx, hy = int(head.x), int(head.y)
        label_font = pygame.font.Font(None, scale_font(13))
        text = label_font.render(str(n), True, WHITE)
        tw, th = text.get_size()

        # Draw background circle
        r = max(tw, th) // 2 + 3
        cx, cy = hx + 8, hy - 10
        pygame.draw.circle(self.screen, (40, 0, 60), (cx, cy), r)
        pygame.draw.circle(self.screen, (180, 100, 255), (cx, cy), r, 1)
        self.screen.blit(text, (cx - tw // 2, cy - th // 2))

    # ------------------------------------------------------------------
    # Trail
    # ------------------------------------------------------------------

    def _draw_trail(self, pkt: QuantumPacket, t: float, detected=False):
        """Draw a fading trail behind a traveling/arrived packet, colored by phase."""
        # Combine history paths + current trail
        all_points = []
        for hp in pkt.history_paths:
            all_points.extend(hp)
        all_points.extend(pkt.trail_points)

        if len(all_points) < 2:
            return

        amp = abs(pkt.amplitude)
        phase = cmath.phase(pkt.amplitude)
        base_color = self._phase_to_color(phase, brightness=0.6)
        base_alpha = int(min(180, 80 + 100 * amp))
        if detected:
            base_alpha = min(220, base_alpha + 60)

        n = len(all_points)
        width = max(1, _settings.BEAM_WIDTH // 2)

        # Draw segments with fading alpha from tail to head
        for i in range(n - 1):
            frac = i / max(1, n - 2)  # 0 at tail, 1 at head
            alpha = int(self.TRAIL_ALPHA_MIN + frac * (base_alpha - self.TRAIL_ALPHA_MIN))
            # Blend from dim to full phase color
            r = int(base_color[0] * (0.3 + 0.7 * frac))
            g = int(base_color[1] * (0.3 + 0.7 * frac))
            b = int(base_color[2] * (0.3 + 0.7 * frac))
            color = (r, g, b, alpha)

            p1 = all_points[i]
            p2 = all_points[i + 1]
            pt1 = p1.tuple() if hasattr(p1, 'tuple') else (int(p1[0]), int(p1[1]))
            pt2 = p2.tuple() if hasattr(p2, 'tuple') else (int(p2[0]), int(p2[1]))

            self._draw_alpha_line(pt1, pt2, color, width)

    # ------------------------------------------------------------------
    # Arrived glow (waiting for siblings)
    # ------------------------------------------------------------------

    def _draw_arrived_glow(self, pkt: QuantumPacket, t: float):
        if pkt.detector is None:
            return
        pos = pkt.detector.position.tuple()
        pulse = 0.6 + 0.4 * math.sin(t * 6)
        radius = int(12 + 8 * pulse)
        alpha = int(100 * pulse)
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (0, 255, 255, alpha), (radius, radius), radius)
        self.screen.blit(s, (pos[0] - radius, pos[1] - radius))

    # ------------------------------------------------------------------
    # Detection flash
    # ------------------------------------------------------------------

    def _draw_detection_flash(self, pkt: QuantumPacket, now: float):
        if pkt.detector is None:
            return
        elapsed = now - pkt.detection_time
        if elapsed > 0.8:
            return
        pos = pkt.detector.position.tuple()

        # Expanding ring
        t_frac = elapsed / 0.8
        radius = int(15 + 40 * t_frac)
        alpha = int(255 * (1 - t_frac))
        ring_w = max(1, int(4 * (1 - t_frac)))

        s = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        center = (radius + 2, radius + 2)
        pygame.draw.circle(s, (100, 255, 255, alpha), center, radius, ring_w)
        # Bright inner flash
        if t_frac < 0.3:
            inner_alpha = int(255 * (1 - t_frac / 0.3))
            inner_r = int(10 * (1 - t_frac / 0.3))
            if inner_r > 0:
                pygame.draw.circle(s, (200, 255, 255, inner_alpha), center, inner_r)
        self.screen.blit(s, (pos[0] - radius - 2, pos[1] - radius - 2))

    # ------------------------------------------------------------------
    # Collapse animation (fade trails that led to non-detected detectors)
    # ------------------------------------------------------------------

    def _draw_collapse_trail(self, pkt: QuantumPacket, elapsed: float, family: PacketFamily):
        """Draw collapse animation: brief white flash then rapid desaturation."""
        collapse_dur = 0.3
        if elapsed > collapse_dur:
            return

        all_points = []
        for hp in pkt.history_paths:
            all_points.extend(hp)
        all_points.extend(pkt.trail_points)

        if len(all_points) < 2:
            return

        n = len(all_points)
        width = max(1, _settings.BEAM_WIDTH // 2)

        flash_end = 0.08  # first 80ms is white flash

        if elapsed < flash_end:
            # Phase 1: bright white flash
            flash_intensity = 1.0 - (elapsed / flash_end)
            alpha = int(200 * flash_intensity)
            color = (255, 255, 255, alpha)
            for i in range(n - 1):
                p1 = all_points[i]
                p2 = all_points[i + 1]
                pt1 = p1.tuple() if hasattr(p1, 'tuple') else (int(p1[0]), int(p1[1]))
                pt2 = p2.tuple() if hasattr(p2, 'tuple') else (int(p2[0]), int(p2[1]))
                self._draw_alpha_line(pt1, pt2, color, width + 2)
        else:
            # Phase 2: rapid desaturation to gray, then vanish
            t = (elapsed - flash_end) / (collapse_dur - flash_end)  # 0→1
            fade = 1.0 - t
            alpha = int(60 * fade)
            if alpha < 2:
                return
            gray = int(120 * fade)
            color = (gray, gray, gray, alpha)
            for i in range(n - 1):
                p1 = all_points[i]
                p2 = all_points[i + 1]
                pt1 = p1.tuple() if hasattr(p1, 'tuple') else (int(p1[0]), int(p1[1]))
                pt2 = p2.tuple() if hasattr(p2, 'tuple') else (int(p2[0]), int(p2[1]))
                self._draw_alpha_line(pt1, pt2, color, width)

    # ------------------------------------------------------------------
    # Detection histogram
    # ------------------------------------------------------------------

    def _draw_histogram(self, engine: QuantumPacketEngine):
        """Draw bar charts near each detector with empirical rate and theory marker.

        In multi-photon mode the bar shows the average photon number per
        pulse at each detector (e.g. 1.0 out of 2 photons = 50%).
        """
        stats = engine.get_detection_stats()
        if not stats or engine._total_detections < 1:
            return

        theory = engine.get_theoretical_probs()
        font = pygame.font.Font(None, scale_font(14))
        bar_w = scale(30)
        bar_max_h = scale(40)
        n_ph = engine.photons_per_pulse

        screen_h = self.screen.get_height()

        for det, (count, frac) in stats.items():
            if not hasattr(det, 'position'):
                continue
            pos = det.position.tuple()

            # In multi-photon mode, show mean photons per pulse / n_photons
            if n_ph > 1 and engine._total_pulses > 0:
                mean_per_pulse = count / engine._total_pulses
                display_frac = mean_per_pulse / n_ph
                pct_text = f"{mean_per_pulse:.1f}/{n_ph}"
            else:
                display_frac = frac
                pct_text = f"{int(frac * 100)}%"

            total_h = bar_max_h + scale(30)

            if pos[1] + scale(65) + total_h > screen_h - scale(10):
                by = pos[1] - scale(85) - bar_max_h
            else:
                by = pos[1] + scale(65)

            bx = pos[0] - bar_w // 2

            # Background
            bg_h = bar_max_h + scale(16)
            bg_rect = pygame.Rect(bx - scale(4), by - scale(2), bar_w + scale(8), bg_h)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 140))
            self.screen.blit(s, bg_rect.topleft)

            # Empirical bar
            bar_h = max(1, int(bar_max_h * min(1.0, display_frac)))
            bar_rect = pygame.Rect(bx, by + bar_max_h - bar_h, bar_w, bar_h)
            bar_g = int(min(255, 150 + display_frac * 105))
            pygame.draw.rect(self.screen, (0, bar_g, 200), bar_rect)
            pygame.draw.rect(self.screen, CYAN, bar_rect, 1)

            # Theoretical probability marker (gold horizontal line)
            theo_p = theory.get(det, None)
            if theo_p is not None:
                theo_y = int(by + bar_max_h - bar_max_h * min(1.0, theo_p))
                pygame.draw.line(self.screen, GOLD,
                                 (bx - scale(3), theo_y),
                                 (bx + bar_w + scale(3), theo_y), 2)

            # Label
            label = font.render(pct_text, True, WHITE)
            label_rect = label.get_rect(centerx=bx + bar_w // 2, top=by + bar_max_h + scale(2))
            self.screen.blit(label, label_rect)

            # Count
            count_text = f"n={count}"
            clabel = font.render(count_text, True, (160, 160, 160))
            crect = clabel.get_rect(centerx=bx + bar_w // 2, top=label_rect.bottom + 1)
            self.screen.blit(clabel, crect)

        # Coincidence and PNR statistics for multi-photon mode
        if engine.photons_per_pulse > 1:
            self._draw_coincidences(engine)
            self._draw_pnr(engine)

    # ------------------------------------------------------------------
    # Coincidence display
    # ------------------------------------------------------------------

    def _draw_coincidences(self, engine: QuantumPacketEngine):
        """Draw coincidence rates for multi-photon mode in the top-right corner."""
        coinc = engine.get_coincidence_stats()
        if not coinc or engine._total_pulses < 1:
            return

        font = pygame.font.Font(None, scale_font(13))
        x = self.screen.get_width() - scale(200)
        y = scale(10)

        # Header
        n = engine.photons_per_pulse
        header = font.render(f"Coincidences ({n} photons/pulse, {engine._total_pulses} pulses)",
                             True, GOLD)
        self.screen.blit(header, (x, y))
        y += scale(16)

        for det_set, (count, rate) in sorted(coinc.items(), key=lambda kv: -kv[1][1]):
            # Build label from detector positions
            det_labels = []
            for det in det_set:
                if hasattr(det, 'position'):
                    pos = det.position.tuple()
                    det_labels.append(f"D({int(pos[0])},{int(pos[1])})")
                else:
                    det_labels.append("D?")
            label = " & ".join(sorted(det_labels))
            text = f"{label}: {count} ({int(rate * 100)}%)"
            surf = font.render(text, True, WHITE)
            self.screen.blit(surf, (x, y))
            y += scale(14)

    # ------------------------------------------------------------------
    # PNR (photon-number-resolved) display
    # ------------------------------------------------------------------

    def _draw_pnr(self, engine: QuantumPacketEngine):
        """Draw photon-number-resolved detection statistics per detector."""
        pnr = engine.get_pnr_stats()
        if not pnr or engine._total_pulses < 1:
            return

        font = pygame.font.Font(None, scale_font(12))
        bar_w = scale(10)
        bar_max_h = scale(28)
        gap = scale(2)

        for det, dist in pnr.items():
            if not hasattr(det, 'position'):
                continue
            pos = det.position.tuple()

            # Skip n=0 for display; only show n>=1 entries
            entries = {n: (cnt, rate) for n, (cnt, rate) in dist.items() if n >= 1}
            if not entries:
                continue

            n_max = max(entries.keys())
            n_bars = n_max  # bars for n=1..n_max
            total_w = n_bars * (bar_w + gap) - gap

            # Place to the right of the detector, or left if near right edge
            screen_w = self.screen.get_width()
            bx_start = int(pos[0]) + scale(55)
            if bx_start + total_w + scale(10) > screen_w:
                bx_start = int(pos[0]) - scale(55) - total_w
            by_top = int(pos[1]) - bar_max_h // 2

            # Background
            bg_rect = pygame.Rect(bx_start - scale(4), by_top - scale(14),
                                  total_w + scale(8), bar_max_h + scale(30))
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 140))
            self.screen.blit(s, bg_rect.topleft)

            # Title
            title = font.render("PNR", True, GOLD)
            title_rect = title.get_rect(centerx=bx_start + total_w // 2,
                                        bottom=by_top - scale(2))
            self.screen.blit(title, title_rect)

            for n in range(1, n_max + 1):
                cnt, rate = entries.get(n, (0, 0.0))
                bx = bx_start + (n - 1) * (bar_w + gap)

                # Bar height proportional to rate
                bh = max(1, int(bar_max_h * rate))
                bar_rect = pygame.Rect(bx, by_top + bar_max_h - bh, bar_w, bh)

                # Colour gradient: green for n=1, cyan for n=2, magenta for n≥3
                if n == 1:
                    colour = (0, 200, 100)
                elif n == 2:
                    colour = (0, 200, 255)
                else:
                    colour = (200, 100, 255)

                pygame.draw.rect(self.screen, colour, bar_rect)
                pygame.draw.rect(self.screen, WHITE, bar_rect, 1)

                # n label below bar
                nlabel = font.render(str(n), True, WHITE)
                nlabel_rect = nlabel.get_rect(centerx=bx + bar_w // 2,
                                              top=by_top + bar_max_h + scale(2))
                self.screen.blit(nlabel, nlabel_rect)

                # Percentage above bar
                if rate >= 0.005:
                    pct = font.render(f"{int(rate * 100)}%", True, (180, 180, 180))
                    pct_rect = pct.get_rect(centerx=bx + bar_w // 2,
                                            bottom=by_top + bar_max_h - bh - 1)
                    self.screen.blit(pct, pct_rect)

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _position_on_path(path, progress) -> Optional['Vector2']:
        from utils.vector import Vector2
        if not path or len(path) < 2:
            return path[0] if path else None
        total = 0.0
        segs = []
        for i in range(len(path) - 1):
            sl = path[i].distance_to(path[i+1])
            segs.append(sl)
            total += sl
        if total < 0.001:
            return path[0]
        target = progress * total
        accum = 0.0
        for i, sl in enumerate(segs):
            if accum + sl >= target or i == len(segs) - 1:
                t = (target - accum) / sl if sl > 0 else 0
                t = max(0, min(1, t))
                p1, p2 = path[i], path[i+1]
                return Vector2(p1.x + t * (p2.x - p1.x),
                               p1.y + t * (p2.y - p1.y))
            accum += sl
        return path[-1]

    @staticmethod
    def _path_total_length(path) -> float:
        total = 0.0
        for i in range(len(path) - 1):
            total += path[i].distance_to(path[i+1])
        return total
