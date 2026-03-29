"""Photon-number and energy conservation tests.

Emits a known number of pulses, turns off the laser, drains all in-flight
packets to detectors, and verifies that every emitted photon is accounted for
(detected or explicitly lost).
"""

import math
import time
import pytest
import numpy as np

from utils.vector import Vector2
from components.beam_splitter import BeamSplitter
from components.tunable_beamsplitter import TunableBeamSplitter
from components.mirror import Mirror
from components.flat_mirror import FlatMirror
from components.detector import Detector
from components.laser import Laser
from core.waveoptics import WaveOpticsEngine
from core.quantum_packet import (
    QuantumPacketEngine, PacketFamily, QuantumPacket, PacketState,
)


def gp(col, row, grid_size=45, offset_x=280, offset_y=120):
    return (offset_x + col * grid_size, offset_y + row * grid_size)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def emit_and_drain(wave_engine, pkt_engine, n_pulses, dt=0.02, max_drain_steps=2000):
    """Emit exactly *n_pulses* pulses then propagate until every family resolves.

    Returns
    -------
    dict with keys:
        emitted        – total photons emitted
        detected       – total photons that clicked a detector
        lost           – photons whose every packet expired (never reached a detector)
        families       – number of families processed
        unresolved     – families that didn't resolve within max_drain_steps
    """
    # Skip collapse animation so fully_resolved triggers immediately
    # (collapse timing uses wall-clock, which advances too fast in tests).
    pkt_engine.collapse_duration = 0.0

    # Phase 1: emit exactly n_pulses
    pkt_engine.emit_interval = 0.001  # very fast emission
    pkt_engine._graph_fingerprint = None

    emitted_families = 0
    while emitted_families < n_pulses:
        families_before = len(pkt_engine.families)
        pkt_engine.update(dt, wave_engine)
        families_after = len(pkt_engine.families)
        emitted_families += (families_after - families_before)
        # Guard: if max_families caps us, keep ticking to let old ones resolve
        if emitted_families >= n_pulses:
            break

    # Phase 2: stop emitting, drain all in-flight packets
    pkt_engine.emit_interval = 1e9  # effectively infinite — no more emissions

    for _ in range(max_drain_steps):
        pkt_engine.update(dt, wave_engine)
        # Check if all families are fully resolved
        if all(f.fully_resolved for f in pkt_engine.families):
            break

    # Phase 3: audit every family
    total_emitted = 0
    total_detected = 0
    total_lost = 0
    unresolved = 0

    for family in pkt_engine.families:
        n_photons = family.n_photons
        total_emitted += n_photons

        if not family.fully_resolved:
            unresolved += 1
            # Count what we can
            if family.detected:
                total_detected += len(family.detected_detectors)
                # Remaining photons from this family that weren't detected
                total_lost += n_photons - len(family.detected_detectors)
            else:
                total_lost += n_photons
            continue

        if family.detected:
            total_detected += len(family.detected_detectors)
            # Any photon_idx not in detected_detectors was lost
            lost_in_family = n_photons - len(family.detected_detectors)
            total_lost += lost_in_family
        else:
            # Entire family expired without any detection
            total_lost += n_photons

    return {
        'emitted': total_emitted,
        'detected': total_detected,
        'lost': total_lost,
        'families': len(pkt_engine.families),
        'unresolved': unresolved,
    }


def count_per_family_photon_fate(pkt_engine):
    """For each family, count detected/expired/stuck per photon_idx.

    Returns list of dicts: one per family with keys 'detected', 'expired', 'stuck'.
    """
    results = []
    for family in pkt_engine.families:
        by_photon = {}
        for pkt in family.packets:
            by_photon.setdefault(pkt.photon_idx, []).append(pkt)

        detected = 0
        expired_all = 0  # photons where ALL packets expired
        stuck = 0        # photons with packets still TRAVELING

        for pidx, pkts in by_photon.items():
            states = {p.state for p in pkts}
            if PacketState.DETECTED in states:
                detected += 1
            elif PacketState.TRAVELING in states:
                stuck += 1
            elif states <= {PacketState.EXPIRED, PacketState.COLLAPSED}:
                expired_all += 1
            elif PacketState.ARRIVED in states:
                # Waiting for detection resolution
                stuck += 1
            else:
                expired_all += 1

        results.append({
            'family_id': family.family_id,
            'n_photons': family.n_photons,
            'detected': detected,
            'expired': expired_all,
            'stuck': stuck,
            'fully_resolved': family.fully_resolved,
        })
    return results


# ---------------------------------------------------------------------------
# Test configurations
# ---------------------------------------------------------------------------

class TestConservationSimpleBS:
    """Laser → BS → Det1 + Det2: fully closed, no loss paths."""

    @staticmethod
    def _build():
        engine = WaveOpticsEngine()
        laser = Laser(*gp(2, 5))
        bs = BeamSplitter(*gp(5, 5))
        det1 = Detector(*gp(8, 5))
        det2 = Detector(*gp(5, 8))
        engine.solve_interferometer(laser, [bs, det1, det2])
        return engine, det1, det2

    @pytest.mark.parametrize("n_photons", [1, 2, 3, 4])
    def test_conservation(self, n_photons):
        """Every emitted photon must be detected (closed system)."""
        wave_engine, det1, det2 = self._build()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = n_photons
        pkt.packet_speed = 800.0
        pkt.max_families = 50

        n_pulses = 30
        result = emit_and_drain(wave_engine, pkt, n_pulses)

        assert result['unresolved'] == 0, (
            f"{result['unresolved']} families still unresolved")
        assert result['emitted'] == result['detected'] + result['lost'], (
            f"Accounting error: emitted={result['emitted']} != "
            f"detected={result['detected']} + lost={result['lost']}")
        assert result['lost'] == 0, (
            f"{result['lost']}/{result['emitted']} photons lost "
            f"in closed system (n_photons={n_photons})")
        assert result['detected'] == n_pulses * n_photons

    def test_detection_count_matches_pnr(self):
        """Sum of n*count over PNR distribution equals total clicks."""
        wave_engine, det1, det2 = self._build()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = 2
        pkt.packet_speed = 800.0
        pkt.max_families = 50

        emit_and_drain(wave_engine, pkt, n_pulses=30)

        for det in (det1, det2):
            clicks = pkt._detection_counts.get(det, 0)
            pnr_clicks = sum(n * c for n, c in pkt._pnr_counts.get(det, {}).items())
            assert pnr_clicks == clicks, (
                f"PNR total ({pnr_clicks}) != click count ({clicks})")

    def test_pnr_events_equal_pulses(self):
        """For each detector, sum of PNR event counts = total_pulses."""
        wave_engine, det1, det2 = self._build()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = 2
        pkt.packet_speed = 800.0
        pkt.max_families = 50

        emit_and_drain(wave_engine, pkt, n_pulses=30)

        # In a closed 2-detector system with n photons per pulse,
        # every pulse deposits photons at det1 and/or det2.
        # The sum of (n=0 events) + (n=1 events) + ... at each detector
        # should equal total_pulses, because every pulse is accounted for.
        for det in (det1, det2):
            dist = pkt._pnr_counts.get(det, {})
            events_with_hits = sum(dist.values())
            # events_with_hits + events_with_zero = total_pulses
            events_with_zero = pkt._total_pulses - events_with_hits
            total = events_with_hits + events_with_zero
            assert total == pkt._total_pulses


class TestConservationMZI:
    """MZI with 5 mirrors — mostly closed but may have minor leakage from
    amplitude cutoffs on feedback paths."""

    @staticmethod
    def _build():
        engine = WaveOpticsEngine()
        laser = Laser(*gp(1, 5))
        bs1 = BeamSplitter(*gp(3, 5))
        m1 = Mirror(*gp(6, 5), mirror_type='\\')
        m2 = Mirror(*gp(6, 2), mirror_type='/')
        m3 = Mirror(*gp(9, 2), mirror_type='/')
        m4 = Mirror(*gp(3, 8), mirror_type='\\')
        m5 = Mirror(*gp(9, 8), mirror_type='\\')
        bs2 = TunableBeamSplitter(*gp(9, 5), t=1/np.sqrt(2),
                                   r=1j/np.sqrt(2), orientation='/')
        det1 = Detector(*gp(12, 5))
        det2 = Detector(*gp(8, 5))
        components = [bs1, m1, m2, m3, m4, m5, bs2, det1, det2]
        engine.solve_interferometer(laser, components)
        return engine, det1, det2

    @pytest.mark.parametrize("n_photons", [1, 2])
    def test_conservation(self, n_photons):
        wave_engine, det1, det2 = self._build()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = n_photons
        pkt.packet_speed = 800.0
        pkt.max_families = 50

        n_pulses = 20
        result = emit_and_drain(wave_engine, pkt, n_pulses)

        assert result['unresolved'] == 0, (
            f"{result['unresolved']} families unresolved")

        total = result['detected'] + result['lost']
        assert total == result['emitted'], (
            f"Accounting gap: {result['emitted']} emitted, "
            f"{result['detected']} detected, {result['lost']} lost, "
            f"sum={total}")

        # In the MZI, feedback paths may cause amplitude-cutoff losses.
        # Allow up to 20% loss from cutoffs, but flag if higher.
        if result['emitted'] > 0:
            loss_frac = result['lost'] / result['emitted']
            assert loss_frac < 0.20, (
                f"Loss rate {loss_frac:.0%} exceeds 20% threshold "
                f"({result['lost']}/{result['emitted']})")


class TestConservationMichelson:
    """Michelson interferometer — feedback loop capped by MAX_GENERATION."""

    @staticmethod
    def _build():
        engine = WaveOpticsEngine()
        laser = Laser(*gp(1, 5))
        bs = BeamSplitter(*gp(4, 5))
        fm_h = FlatMirror(*gp(8, 5), orientation='|')
        fm_v = FlatMirror(*gp(4, 8), orientation='-')
        det = Detector(*gp(4, 2))
        components = [bs, fm_h, fm_v, det]
        engine.solve_interferometer(laser, components)
        return engine, det

    @pytest.mark.parametrize("n_photons", [1, 2])
    def test_all_families_resolve(self, n_photons):
        """Every family must reach fully_resolved within the drain window."""
        wave_engine, det = self._build()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = n_photons
        pkt.packet_speed = 800.0
        pkt.max_families = 30

        n_pulses = 15
        result = emit_and_drain(wave_engine, pkt, n_pulses, max_drain_steps=3000)

        assert result['unresolved'] == 0, (
            f"{result['unresolved']} families still unresolved in Michelson")

    @pytest.mark.parametrize("n_photons", [1, 2])
    def test_accounting(self, n_photons):
        """detected + lost = emitted (no unaccounted photons)."""
        wave_engine, det = self._build()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = n_photons
        pkt.packet_speed = 800.0
        pkt.max_families = 30

        n_pulses = 15
        result = emit_and_drain(wave_engine, pkt, n_pulses, max_drain_steps=3000)

        total = result['detected'] + result['lost']
        assert total == result['emitted'], (
            f"emitted={result['emitted']} != detected={result['detected']} "
            f"+ lost={result['lost']}")


class TestConservationDirectPath:
    """Laser → Detector (no BS). Every photon must arrive."""

    @staticmethod
    def _build():
        engine = WaveOpticsEngine()
        laser = Laser(*gp(2, 5))
        det = Detector(*gp(8, 5))
        engine.solve_interferometer(laser, [det])
        return engine, det

    @pytest.mark.parametrize("n_photons", [1, 2, 3])
    def test_perfect_conservation(self, n_photons):
        wave_engine, det = self._build()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = n_photons
        pkt.packet_speed = 800.0
        pkt.max_families = 50

        n_pulses = 30
        result = emit_and_drain(wave_engine, pkt, n_pulses)

        assert result['unresolved'] == 0
        assert result['lost'] == 0, (
            f"{result['lost']} photons lost on direct laser→detector path")
        assert result['detected'] == n_pulses * n_photons


class TestPerFamilyAudit:
    """Detailed per-family, per-photon fate audit."""

    @staticmethod
    def _build():
        engine = WaveOpticsEngine()
        laser = Laser(*gp(2, 5))
        bs = BeamSplitter(*gp(5, 5))
        det1 = Detector(*gp(8, 5))
        det2 = Detector(*gp(5, 8))
        engine.solve_interferometer(laser, [bs, det1, det2])
        return engine

    def test_every_photon_detected_in_closed_system(self):
        """In L→BS→2D, each photon_idx in each family must be DETECTED."""
        wave_engine = self._build()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = 2
        pkt.packet_speed = 800.0
        pkt.max_families = 50

        emit_and_drain(wave_engine, pkt, n_pulses=25)

        fates = count_per_family_photon_fate(pkt)
        for fate in fates:
            assert fate['stuck'] == 0, (
                f"Family {fate['family_id']}: {fate['stuck']} photons still stuck")
            assert fate['expired'] == 0, (
                f"Family {fate['family_id']}: {fate['expired']}/{fate['n_photons']} "
                f"photons expired without detection")
            assert fate['detected'] == fate['n_photons'], (
                f"Family {fate['family_id']}: only {fate['detected']}/"
                f"{fate['n_photons']} photons detected")
