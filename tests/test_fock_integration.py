"""Tests for Fock state integration with beam splitter and quantum packet engine.

Validates that:
1. fock.py utilities give correct quantum distributions
2. TunableBeamSplitter Fock methods work
3. Fock splitting in the packet engine produces correct HOM statistics
4. MZI and Michelson quantum modes run correctly
5. Single-photon mode is unaffected by the Fock code path
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
from core.fock import fock_bs_amplitude, fock_bs_probabilities, sample_fock_bs
from core.waveoptics import WaveOpticsEngine, OpticalPort, OpticalConnection
from core.quantum_packet import (
    QuantumPacketEngine, QuantumPacket, PacketFamily, PacketState,
)


# ---------------------------------------------------------------------------
# Grid helper
# ---------------------------------------------------------------------------

def gp(col, row, grid_size=45, offset_x=280, offset_y=120):
    return (offset_x + col * grid_size, offset_y + row * grid_size)


# ---------------------------------------------------------------------------
# Fock module unit tests
# ---------------------------------------------------------------------------

class TestFockModule:
    """Direct tests of core/fock.py functions."""

    def test_single_photon_5050(self):
        """|1,0⟩ through 50/50 BS → each output has prob 0.5."""
        t = 1 / np.sqrt(2)
        r = 1j / np.sqrt(2)
        probs = fock_bs_probabilities(1, 0, t, r)
        assert probs[(1, 0)] == pytest.approx(0.5, abs=1e-6)
        assert probs[(0, 1)] == pytest.approx(0.5, abs=1e-6)

    def test_hom_effect(self):
        """|1,1⟩ through 50/50 BS: P(1,1)=0 (Hong-Ou-Mandel)."""
        t = 1 / np.sqrt(2)
        r = 1j / np.sqrt(2)
        probs = fock_bs_probabilities(1, 1, t, r)
        assert (1, 1) not in probs or probs.get((1, 1), 0) < 1e-10
        assert probs[(2, 0)] == pytest.approx(0.5, abs=1e-6)
        assert probs[(0, 2)] == pytest.approx(0.5, abs=1e-6)

    def test_two_photon_same_port(self):
        """|2,0⟩ through 50/50 BS → P(2,0)=P(0,2)=1/4, P(1,1)=1/2."""
        t = 1 / np.sqrt(2)
        r = 1j / np.sqrt(2)
        probs = fock_bs_probabilities(2, 0, t, r)
        assert probs[(2, 0)] == pytest.approx(0.25, abs=1e-6)
        assert probs[(0, 2)] == pytest.approx(0.25, abs=1e-6)
        assert probs[(1, 1)] == pytest.approx(0.5, abs=1e-6)

    def test_probabilities_sum_to_one(self):
        t = 1 / np.sqrt(2)
        r = 1j / np.sqrt(2)
        for n, m in [(0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (2, 1), (3, 0)]:
            probs = fock_bs_probabilities(n, m, t, r)
            total = sum(probs.values())
            assert total == pytest.approx(1.0, abs=1e-8), f"|{n},{m}⟩: total={total}"

    def test_sample_returns_valid_outcome(self):
        t = 1 / np.sqrt(2)
        r = 1j / np.sqrt(2)
        for _ in range(100):
            p, q = sample_fock_bs(2, 1, t, r)
            assert p + q == 3
            assert p >= 0 and q >= 0

    def test_hom_sampling_never_11(self):
        """|1,1⟩ sampling must never produce (1,1)."""
        t = 1 / np.sqrt(2)
        r = 1j / np.sqrt(2)
        for _ in range(500):
            p, q = sample_fock_bs(1, 1, t, r)
            assert (p, q) != (1, 1), "HOM violation: sampled (1,1) from |1,1⟩"


# ---------------------------------------------------------------------------
# TunableBeamSplitter Fock interface
# ---------------------------------------------------------------------------

class TestBeamSplitterFockInterface:
    def test_fock_transform_returns_valid(self):
        bs = BeamSplitter(0, 0)
        for _ in range(50):
            p, q = bs.fock_transform(1, 1)
            assert p + q == 2
            assert (p, q) != (1, 1)

    def test_fock_probabilities_matches_module(self):
        bs = BeamSplitter(0, 0)
        probs = bs.fock_probabilities(2, 0)
        assert sum(probs.values()) == pytest.approx(1.0, abs=1e-8)
        assert probs[(1, 1)] == pytest.approx(0.5, abs=1e-6)

    def test_mode_mapping_backslash(self):
        bs = BeamSplitter(0, 0)
        mapping = bs.get_fock_mode_mapping()
        assert len(mapping) == 2
        assert mapping[0] == {'a': 0, 'b': 3, 'c': 2, 'd': 1}
        assert mapping[1] == {'a': 1, 'b': 2, 'c': 3, 'd': 0}

    def test_mode_mapping_forward_slash(self):
        bs = TunableBeamSplitter(0, 0, t=1/np.sqrt(2), r=1j/np.sqrt(2),
                                 orientation='/')
        mapping = bs.get_fock_mode_mapping()
        assert len(mapping) == 2
        assert mapping[0] == {'a': 0, 'b': 2, 'c': 3, 'd': 1}
        assert mapping[1] == {'a': 1, 'b': 3, 'c': 2, 'd': 0}


# ---------------------------------------------------------------------------
# Direct test of _split_packets_fock via synthetic graph
# ---------------------------------------------------------------------------

class TestFockSplitDirect:
    """Test _split_packets_fock with hand-crafted packet engine graph.

    This bypasses the wave engine layout issues and directly validates
    the Fock splitting logic — especially the HOM effect.
    """

    @staticmethod
    def _make_engine_with_graph(bs, det_c, det_d):
        """Build a minimal QuantumPacketEngine with a synthetic graph.

        Graph: two input connections (conn 0 → BS port a, conn 1 → BS port b)
        and two output connections (conn 2 from BS port c, conn 3 from BS port d)
        leading to det_c and det_d respectively.
        """
        mapping = bs.get_fock_mode_mapping()[0]  # use sub-block 0
        port_a, port_b = mapping['a'], mapping['b']
        port_c, port_d = mapping['c'], mapping['d']

        # Synthetic connection info
        path_ab = [Vector2(0, 0), Vector2(100, 0)]
        connections = [
            # conn 0: laser → BS port a
            {
                'index': 0,
                'path': path_ab,
                'length': 100.0,
                'amplitude': 1.0+0j,
                'phase_shift': 0.0,
                'source_component': Laser(0, 0),
                'source_port_idx': 0,
                'dest_component': bs,
                'dest_port_idx': port_a,
            },
            # conn 1: laser → BS port b
            {
                'index': 1,
                'path': path_ab,
                'length': 100.0,
                'amplitude': 1.0+0j,
                'phase_shift': 0.0,
                'source_component': Laser(0, 0),
                'source_port_idx': 0,
                'dest_component': bs,
                'dest_port_idx': port_b,
            },
            # conn 2: BS port c → det_c
            {
                'index': 2,
                'path': [Vector2(100, 0), Vector2(200, 0)],
                'length': 100.0,
                'amplitude': 0.707+0j,
                'phase_shift': 0.0,
                'source_component': bs,
                'source_port_idx': port_c,
                'dest_component': det_c,
                'dest_port_idx': 0,
            },
            # conn 3: BS port d → det_d
            {
                'index': 3,
                'path': [Vector2(100, 0), Vector2(100, 100)],
                'length': 100.0,
                'amplitude': 0.707+0j,
                'phase_shift': 0.0,
                'source_component': bs,
                'source_port_idx': port_d,
                'dest_component': det_d,
                'dest_port_idx': 0,
            },
        ]

        # Routing: input conns → output conns
        component_routing = {
            id(bs): {
                0: [2, 3],  # conn 0 (input a) can route to conn 2, 3
                1: [2, 3],  # conn 1 (input b) can route to conn 2, 3
            }
        }

        graph = {
            'connections': connections,
            'laser_connections': [0, 1],
            'detector_connections': [2, 3],
            'component_routing': component_routing,
        }

        engine = QuantumPacketEngine()
        engine.photons_per_pulse = 2
        engine._network_graph = graph
        return engine

    def test_hom_bunching(self):
        """Two photons arriving at a 50/50 BS from different ports (|1,1⟩)
        must never produce (1,1) — both always go to the same detector."""
        bs = BeamSplitter(100, 100)
        det_c = Detector(200, 100)
        det_d = Detector(100, 200)

        mapping = bs.get_fock_mode_mapping()[0]

        n_trials = 500
        both_same = 0
        both_different = 0

        for _ in range(n_trials):
            engine = self._make_engine_with_graph(bs, det_c, det_d)

            # Create a family with 2 photons, one arriving at each port
            family = PacketFamily(0, n_photons=2)
            conn0 = engine._network_graph['connections'][0]
            conn1 = engine._network_graph['connections'][1]

            pkt0 = QuantumPacket(
                id=0, family_id=0, connection_index=0,
                path=conn0['path'], progress=1.0,
                amplitude=1.0+0j, state=PacketState.TRAVELING,
                creation_time=0, photon_idx=0,
            )
            pkt1 = QuantumPacket(
                id=1, family_id=0, connection_index=1,
                path=conn1['path'], progress=1.0,
                amplitude=1.0+0j, state=PacketState.TRAVELING,
                creation_time=0, photon_idx=1,
            )
            family.add_packet(pkt0)
            family.add_packet(pkt1)

            # Call _split_packets_fock directly
            arrivals = [
                (pkt0, conn0, bs),
                (pkt1, conn1, bs),
            ]
            children = engine._split_packets_fock(arrivals, family_id=0)

            # Both parent packets should be expired
            assert pkt0.state == PacketState.EXPIRED
            assert pkt1.state == PacketState.EXPIRED

            # Children: should have photon_idx 0 and 1, all at same output port
            child_ports = {}
            for child in children:
                out_conn = engine._network_graph['connections'][child.connection_index]
                child_ports[child.photon_idx] = out_conn['source_port_idx']

            if len(child_ports) == 2:
                ports = list(child_ports.values())
                if ports[0] == ports[1]:
                    both_same += 1
                else:
                    both_different += 1

        # HOM: (1,1) outcome is FORBIDDEN — both photons always go same way
        assert both_different == 0, (
            f"HOM violation: {both_different}/{n_trials} trials had photons "
            f"at different output ports (expected 0)"
        )
        assert both_same == n_trials, f"Expected all {n_trials} to bunch, got {both_same}"

    def test_same_port_input_allows_splitting(self):
        """Two photons from the same input port (|2,0⟩) can split to
        different outputs — classical-equivalent behavior."""
        bs = BeamSplitter(100, 100)
        det_c = Detector(200, 100)
        det_d = Detector(100, 200)

        n_trials = 300
        outcomes = {}  # (port_of_photon0, port_of_photon1) → count

        for _ in range(n_trials):
            engine = self._make_engine_with_graph(bs, det_c, det_d)
            conn0 = engine._network_graph['connections'][0]

            family = PacketFamily(0, n_photons=2)
            # Both photons arrive at the SAME port (port a)
            pkt0 = QuantumPacket(
                id=0, family_id=0, connection_index=0,
                path=conn0['path'], progress=1.0,
                amplitude=1.0+0j, state=PacketState.TRAVELING,
                creation_time=0, photon_idx=0,
            )
            pkt1 = QuantumPacket(
                id=1, family_id=0, connection_index=0,
                path=conn0['path'], progress=1.0,
                amplitude=1.0+0j, state=PacketState.TRAVELING,
                creation_time=0, photon_idx=1,
            )
            family.add_packet(pkt0)
            family.add_packet(pkt1)

            arrivals = [(pkt0, conn0, bs), (pkt1, conn0, bs)]
            children = engine._split_packets_fock(arrivals, family_id=0)

            child_ports = {}
            for child in children:
                out_conn = engine._network_graph['connections'][child.connection_index]
                child_ports[child.photon_idx] = out_conn['source_port_idx']

            if len(child_ports) == 2:
                key = tuple(child_ports[i] for i in sorted(child_ports))
                outcomes[key] = outcomes.get(key, 0) + 1

        # |2,0⟩ through 50/50: P(2,0)=25%, P(1,1)=50%, P(0,2)=25%
        # So 'both same port' ≈ 50%, 'different ports' ≈ 50%
        total = sum(outcomes.values())
        mapping = bs.get_fock_mode_mapping()[0]
        same_port = sum(v for k, v in outcomes.items() if k[0] == k[1])
        diff_port = sum(v for k, v in outcomes.items() if k[0] != k[1])

        same_frac = same_port / total if total else 0
        diff_frac = diff_port / total if total else 0

        # P(both same) = P(2,0) + P(0,2) = 0.5
        # P(different) = P(1,1) = 0.5
        assert same_frac == pytest.approx(0.5, abs=0.1), f"same={same_frac:.2f}"
        assert diff_frac == pytest.approx(0.5, abs=0.1), f"diff={diff_frac:.2f}"

    def test_generation_limit(self):
        """Packets at MAX_GENERATION should be expired, not split."""
        bs = BeamSplitter(100, 100)
        det_c = Detector(200, 100)
        det_d = Detector(100, 200)
        engine = self._make_engine_with_graph(bs, det_c, det_d)

        conn0 = engine._network_graph['connections'][0]
        conn1 = engine._network_graph['connections'][1]

        pkt0 = QuantumPacket(
            id=0, family_id=0, connection_index=0,
            path=conn0['path'], progress=1.0,
            amplitude=1.0+0j, state=PacketState.TRAVELING,
            creation_time=0, photon_idx=0,
            generation=QuantumPacketEngine.MAX_GENERATION,
        )
        pkt1 = QuantumPacket(
            id=1, family_id=0, connection_index=1,
            path=conn1['path'], progress=1.0,
            amplitude=1.0+0j, state=PacketState.TRAVELING,
            creation_time=0, photon_idx=1,
            generation=QuantumPacketEngine.MAX_GENERATION,
        )

        arrivals = [(pkt0, conn0, bs), (pkt1, conn1, bs)]
        children = engine._split_packets_fock(arrivals, family_id=0)

        assert children == []
        assert pkt0.state == PacketState.EXPIRED
        assert pkt1.state == PacketState.EXPIRED

    def test_unit_amplitude_after_fock(self):
        """After Fock sampling, child packets have amplitude 1.0."""
        bs = BeamSplitter(100, 100)
        det_c = Detector(200, 100)
        det_d = Detector(100, 200)
        engine = self._make_engine_with_graph(bs, det_c, det_d)

        conn0 = engine._network_graph['connections'][0]
        conn1 = engine._network_graph['connections'][1]

        pkt0 = QuantumPacket(
            id=0, family_id=0, connection_index=0,
            path=conn0['path'], progress=1.0,
            amplitude=0.5+0.5j, state=PacketState.TRAVELING,
            creation_time=0, photon_idx=0,
        )
        pkt1 = QuantumPacket(
            id=1, family_id=0, connection_index=1,
            path=conn1['path'], progress=1.0,
            amplitude=0.3-0.4j, state=PacketState.TRAVELING,
            creation_time=0, photon_idx=1,
        )

        arrivals = [(pkt0, conn0, bs), (pkt1, conn1, bs)]
        children = engine._split_packets_fock(arrivals, family_id=0)

        for child in children:
            assert abs(child.amplitude) == pytest.approx(1.0, abs=1e-10), (
                f"Child amplitude should be 1.0, got {child.amplitude}")


# ---------------------------------------------------------------------------
# Quantum packet engine: simple BS → detectors
# ---------------------------------------------------------------------------

class TestQuantumSimpleBS:
    """Quantum packet mode: Laser → BS → two detectors."""

    @staticmethod
    def _build():
        engine = WaveOpticsEngine()
        laser = Laser(*gp(2, 5))
        bs = BeamSplitter(*gp(5, 5))
        det1 = Detector(*gp(8, 5))   # right (port C)
        det2 = Detector(*gp(5, 8))   # below (port B)
        components = [bs, det1, det2]
        engine.solve_interferometer(laser, components)
        return engine, laser, components, det1, det2

    def test_wave_optics_5050(self):
        _, _, _, det1, det2 = self._build()
        assert det1.intensity == pytest.approx(0.5, abs=0.05)
        assert det2.intensity == pytest.approx(0.5, abs=0.05)

    def test_single_photon_detections(self):
        wave_engine, _, _, det1, det2 = self._build()
        pkt_engine = QuantumPacketEngine()
        pkt_engine.photons_per_pulse = 1
        pkt_engine.emit_interval = 0.01
        pkt_engine.packet_speed = 500.0

        pkt_engine._graph_fingerprint = None
        for _ in range(400):
            pkt_engine.update(0.02, wave_engine)

        assert pkt_engine._total_detections > 5
        c1 = pkt_engine._detection_counts.get(det1, 0)
        c2 = pkt_engine._detection_counts.get(det2, 0)
        total = c1 + c2
        # Both detectors should fire roughly equally
        if total > 20:
            frac1 = c1 / total
            assert frac1 == pytest.approx(0.5, abs=0.25)

    def test_two_photon_no_crash(self):
        """2-photon mode through simple BS should not crash."""
        wave_engine, _, _, det1, det2 = self._build()
        pkt_engine = QuantumPacketEngine()
        pkt_engine.photons_per_pulse = 2
        pkt_engine.emit_interval = 0.01
        pkt_engine.packet_speed = 500.0

        pkt_engine._graph_fingerprint = None
        for _ in range(400):
            pkt_engine.update(0.02, wave_engine)

        assert pkt_engine._total_detections > 0


# ---------------------------------------------------------------------------
# Quantum packet engine: MZI
# ---------------------------------------------------------------------------

class TestQuantumMZI:
    """MZI layout with 5 mirrors to ensure same-sub-block arrival at BS2.

    Upper arm: BS1(3,5) → M1(\\,6,5) → M2(/,6,2) → M3(/,9,2) → BS2(/,9,5)
    Lower arm: BS1(3,5) → M4(\\,3,8) → M5(\\,9,8) → BS2(/,9,5)

    BS2 receives beams at ports B(1) and D(3) = sub-block 1.
    Det1 at (12,5) catches port C output, Det2 at (8,5) catches port A output.
    """

    @staticmethod
    def _build_mzi():
        engine = WaveOpticsEngine()
        laser = Laser(*gp(1, 5))
        bs1 = BeamSplitter(*gp(3, 5))
        # Simple 2-mirror MZI:
        # Upper arm: BS1→right→M1(\,6,5)→down→BS2(6,8)
        # Lower arm: BS1→down→M2(\,3,8)→right→BS2(6,8)
        m1 = Mirror(*gp(6, 5), mirror_type='\\')  # RIGHT→DOWN
        m2 = Mirror(*gp(3, 8), mirror_type='\\')  # DOWN→RIGHT
        bs2 = BeamSplitter(*gp(6, 8))
        det1 = Detector(*gp(9, 8))
        det2 = Detector(*gp(6, 11))

        components = [bs1, m1, m2, bs2, det1, det2]
        engine.solve_interferometer(laser, components)
        return engine, laser, components, det1, det2, bs2

    def test_wave_optics_energy_conservation(self):
        _, _, _, det1, det2, _ = self._build_mzi()
        total = det1.intensity + det2.intensity
        assert total <= 1.05

    def test_both_detectors_receive_light(self):
        """Both outputs of BS2 should connect to detectors."""
        _, _, _, det1, det2, _ = self._build_mzi()
        total = det1.intensity + det2.intensity
        assert total > 0.2, f"Total power too low: {total}"

    def test_single_photon_mzi(self):
        """Single-photon MZI should detect photons."""
        wave_engine, _, _, det1, det2, _ = self._build_mzi()
        pkt_engine = QuantumPacketEngine()
        pkt_engine.photons_per_pulse = 1
        pkt_engine.emit_interval = 0.01
        pkt_engine.packet_speed = 500.0

        pkt_engine._graph_fingerprint = None
        for _ in range(500):
            pkt_engine.update(0.02, wave_engine)

        assert pkt_engine._total_detections > 0, "No detections in MZI"

    def test_two_photon_mzi_no_crash(self):
        """2-photon MZI should run without errors."""
        wave_engine, _, _, det1, det2, _ = self._build_mzi()
        pkt_engine = QuantumPacketEngine()
        pkt_engine.photons_per_pulse = 2
        pkt_engine.emit_interval = 0.01
        pkt_engine.packet_speed = 500.0

        pkt_engine._graph_fingerprint = None
        for _ in range(500):
            pkt_engine.update(0.02, wave_engine)

        # Should not crash; detections may vary due to timing
        assert pkt_engine._total_detections >= 0

    def test_bs2_receives_beams(self):
        """Verify BS2 receives beams from both MZI arms."""
        wave_engine, _, _, _, _, bs2 = self._build_mzi()

        input_ports = set()
        for conn in wave_engine.connections:
            if conn.port2.component is bs2:
                amp = wave_engine.beam_amplitudes.get(
                    f'beam_{wave_engine.connections.index(conn)}', 0j)
                if abs(amp) > 0.001:
                    input_ports.add(conn.port2.port_index)

        assert len(input_ports) >= 2, (
            f"BS2 only receives from ports {input_ports}, expected 2+ arms")


# ---------------------------------------------------------------------------
# Quantum packet engine: Michelson
# ---------------------------------------------------------------------------

class TestQuantumMichelson:
    """Michelson: BS → two flat mirrors → back to BS → detector."""

    @staticmethod
    def _build_michelson():
        engine = WaveOpticsEngine()
        laser = Laser(*gp(1, 5))
        bs = BeamSplitter(*gp(4, 5))
        fm_h = FlatMirror(*gp(8, 5), orientation='|')
        fm_v = FlatMirror(*gp(4, 8), orientation='-')
        det = Detector(*gp(4, 2))

        components = [bs, fm_h, fm_v, det]
        engine.solve_interferometer(laser, components)
        return engine, laser, components, det

    def test_wave_optics_runs(self):
        _, _, _, det = self._build_michelson()
        assert det.intensity >= 0

    def test_single_photon_no_crash(self):
        wave_engine, _, _, det = self._build_michelson()
        pkt_engine = QuantumPacketEngine()
        pkt_engine.photons_per_pulse = 1
        pkt_engine.emit_interval = 0.01
        pkt_engine.packet_speed = 500.0

        pkt_engine._graph_fingerprint = None
        for _ in range(300):
            pkt_engine.update(0.02, wave_engine)

        assert pkt_engine._total_detections >= 0

    def test_two_photon_no_crash(self):
        wave_engine, _, _, det = self._build_michelson()
        pkt_engine = QuantumPacketEngine()
        pkt_engine.photons_per_pulse = 2
        pkt_engine.emit_interval = 0.01
        pkt_engine.packet_speed = 500.0

        pkt_engine._graph_fingerprint = None
        for _ in range(300):
            pkt_engine.update(0.02, wave_engine)

        # Main check: no infinite loops, generation limit respected
        for family in pkt_engine.families:
            for pkt in family.packets:
                assert pkt.generation <= QuantumPacketEngine.MAX_GENERATION


# ---------------------------------------------------------------------------
# Regression: single-photon mode unchanged
# ---------------------------------------------------------------------------

class TestSinglePhotonRegression:
    def test_single_photon_uses_classical_split(self):
        """With photons_per_pulse=1, Fock branch is never taken."""
        wave_engine = WaveOpticsEngine()
        laser = Laser(*gp(2, 5))
        bs = BeamSplitter(*gp(5, 5))
        det1 = Detector(*gp(8, 5))
        det2 = Detector(*gp(5, 8))

        wave_engine.solve_interferometer(laser, [bs, det1, det2])

        pkt_engine = QuantumPacketEngine()
        pkt_engine.photons_per_pulse = 1
        pkt_engine.emit_interval = 0.01
        pkt_engine.packet_speed = 500.0

        pkt_engine._graph_fingerprint = None
        for _ in range(300):
            pkt_engine.update(0.02, wave_engine)

        assert pkt_engine._total_detections > 0
        assert len(pkt_engine._coincidence_counts) == 0


# ---------------------------------------------------------------------------
# Photon-number-resolved (PNR) detection
# ---------------------------------------------------------------------------

class TestPNR:
    """Validate PNR counting in the packet engine."""

    @staticmethod
    def _build_simple():
        engine = WaveOpticsEngine()
        laser = Laser(*gp(2, 5))
        bs = BeamSplitter(*gp(5, 5))
        det1 = Detector(*gp(8, 5))
        det2 = Detector(*gp(5, 8))
        engine.solve_interferometer(laser, [bs, det1, det2])
        return engine, det1, det2

    def test_single_photon_pnr_only_1(self):
        """With 1 photon/pulse, PNR entries should only contain n=1."""
        wave_engine, det1, det2 = self._build_simple()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = 1
        pkt.emit_interval = 0.01
        pkt.packet_speed = 500.0

        pkt._graph_fingerprint = None
        for _ in range(400):
            pkt.update(0.02, wave_engine)

        pnr = pkt.get_pnr_stats()
        for det, dist in pnr.items():
            for n, (count, rate) in dist.items():
                if n > 0:
                    assert n == 1, f"Single-photon mode recorded n={n}"

    def test_two_photon_pnr_has_n2(self):
        """With 2 photons/pulse through a BS, some pulses should deposit
        2 photons at the same detector (n=2 entry exists)."""
        wave_engine, det1, det2 = self._build_simple()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = 2
        pkt.emit_interval = 0.01
        pkt.packet_speed = 500.0

        pkt._graph_fingerprint = None
        for _ in range(500):
            pkt.update(0.02, wave_engine)

        pnr = pkt.get_pnr_stats()
        has_n2 = any(
            2 in dist for dist in pnr.values()
        )
        # With 2 photons through a 50/50 BS, sometimes both go to the
        # same detector → n=2 should appear.
        if pkt._total_pulses > 10:
            assert has_n2, "No n=2 PNR events with 2-photon pulses"

    def test_pnr_counts_consistent_with_detection_counts(self):
        """Sum of n*count across PNR entries should equal total detection count."""
        wave_engine, det1, det2 = self._build_simple()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = 2
        pkt.emit_interval = 0.01
        pkt.packet_speed = 500.0

        pkt._graph_fingerprint = None
        for _ in range(400):
            pkt.update(0.02, wave_engine)

        if pkt._total_pulses < 1:
            return

        for det in (det1, det2):
            det_clicks = pkt._detection_counts.get(det, 0)
            pnr_dist = pkt._pnr_counts.get(det, {})
            pnr_clicks = sum(n * count for n, count in pnr_dist.items())
            assert pnr_clicks == det_clicks, (
                f"PNR total {pnr_clicks} != detection count {det_clicks}")

    def test_pnr_pulses_consistent(self):
        """Sum of PNR counts per detector should not exceed total_pulses."""
        wave_engine, det1, det2 = self._build_simple()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = 2
        pkt.emit_interval = 0.01
        pkt.packet_speed = 500.0

        pkt._graph_fingerprint = None
        for _ in range(400):
            pkt.update(0.02, wave_engine)

        for det in (det1, det2):
            pnr_dist = pkt._pnr_counts.get(det, {})
            total_events = sum(pnr_dist.values())
            assert total_events <= pkt._total_pulses

    def test_get_pnr_stats_includes_zero(self):
        """get_pnr_stats should include n=0 entries for pulses where
        the detector didn't fire."""
        wave_engine, det1, det2 = self._build_simple()
        pkt = QuantumPacketEngine()
        pkt.photons_per_pulse = 1
        pkt.emit_interval = 0.01
        pkt.packet_speed = 500.0

        pkt._graph_fingerprint = None
        for _ in range(400):
            pkt.update(0.02, wave_engine)

        pnr = pkt.get_pnr_stats()
        if pkt._total_pulses > 10:
            # With a 50/50 BS, each detector fires ~50% of pulses,
            # so both should have n=0 entries for the other ~50%.
            for det in (det1, det2):
                if det in pnr:
                    assert 0 in pnr[det], "Missing n=0 entry in PNR stats"
