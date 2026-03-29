"""Tests for optical components (base, laser, beam_splitter, mirror, detector)."""
import math
import cmath
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from utils.vector import Vector2
from components.base import Component
from components.laser import Laser
from components.beam_splitter import BeamSplitter
from components.mirror import Mirror
from components.detector import Detector


# ---------------------------------------------------------------------------
# Base Component
# ---------------------------------------------------------------------------

class TestBaseComponent:
    def test_creation(self):
        comp = Component(100, 200, "test")
        assert comp.position.x == 100
        assert comp.position.y == 200
        assert comp.component_type == "test"
        assert comp.rotation == 0

    def test_contains_point_inside(self):
        comp = Component(100, 100, "test")
        assert comp.contains_point(100, 100) is True  # center
        assert comp.contains_point(100 + comp.radius - 1, 100) is True  # near edge

    def test_contains_point_outside(self):
        comp = Component(100, 100, "test")
        far = comp.radius + 50
        assert comp.contains_point(100 + far, 100) is False

    def test_draw_not_implemented(self):
        comp = Component(0, 0, "test")
        with pytest.raises(NotImplementedError):
            comp.draw(None)

    def test_process_beam_not_implemented(self):
        comp = Component(0, 0, "test")
        with pytest.raises(NotImplementedError):
            comp.process_beam(None)


# ---------------------------------------------------------------------------
# Laser
# ---------------------------------------------------------------------------

class TestLaser:
    def test_creation(self):
        laser = Laser(50, 60)
        assert laser.component_type == "laser"
        assert laser.enabled is True
        assert laser.position.x == 50
        assert laser.position.y == 60

    def test_emit_beam_when_enabled(self):
        laser = Laser(100, 200)
        beam = laser.emit_beam()
        assert beam is not None
        assert beam["amplitude"] == 1.0
        assert beam["phase"] == 0
        assert beam["direction"].x > 0  # emits rightward
        assert beam["direction"].y == 0

    def test_emit_beam_when_disabled(self):
        laser = Laser(100, 200)
        laser.enabled = False
        assert laser.emit_beam() is None

    def test_contains_point(self):
        laser = Laser(100, 100)
        assert laser.contains_point(100, 100) is True
        assert laser.contains_point(100 + 300, 100) is False


# ---------------------------------------------------------------------------
# Beam Splitter
# ---------------------------------------------------------------------------

class TestBeamSplitter:
    def test_creation(self):
        bs = BeamSplitter(100, 200)
        assert bs.component_type == "beamsplitter"
        assert bs.orientation == "\\"

    def test_scattering_matrix_is_unitary(self):
        bs = BeamSplitter(0, 0)
        S_dag = np.conj(bs.S.T)
        identity_check = S_dag @ bs.S
        np.testing.assert_allclose(identity_check, np.eye(4), atol=1e-10)

    def test_5050_splitting(self):
        """A beam entering port A should split roughly equally to two output ports."""
        bs = BeamSplitter(0, 0)
        v_in = np.array([1, 0, 0, 0], dtype=complex)
        v_out = bs.S @ v_in
        output_powers = np.abs(v_out) ** 2
        # Total power should be conserved
        assert np.sum(output_powers) == pytest.approx(1.0, abs=1e-10)
        # Two non-zero outputs, each carrying ~0.5
        significant = output_powers[output_powers > 0.01]
        assert len(significant) == 2
        for p in significant:
            assert p == pytest.approx(0.5, abs=1e-10)

    @pytest.mark.parametrize("port_idx", [0, 1, 2, 3])
    def test_energy_conservation_each_port(self, port_idx):
        """Energy is conserved regardless of which single port receives input."""
        bs = BeamSplitter(0, 0)
        v_in = np.zeros(4, dtype=complex)
        v_in[port_idx] = 1.0
        v_out = bs.S @ v_in
        assert np.sum(np.abs(v_out) ** 2) == pytest.approx(1.0, abs=1e-10)

    def test_reset_frame(self):
        bs = BeamSplitter(0, 0)
        bs.all_beams_by_port[0].append({"dummy": True})
        bs.processed_this_frame = True
        bs.reset_frame()
        assert bs.processed_this_frame is False
        assert all(len(v) == 0 for v in bs.all_beams_by_port.values())


# ---------------------------------------------------------------------------
# Mirror
# ---------------------------------------------------------------------------

class TestMirror:
    @pytest.mark.parametrize("mirror_type", ["/", "\\"])
    def test_creation(self, mirror_type):
        m = Mirror(0, 0, mirror_type=mirror_type)
        assert m.component_type == "mirror"
        assert m.mirror_type == mirror_type

    def test_scattering_matrix_unitary_slash(self):
        m = Mirror(0, 0, mirror_type="/")
        S_dag = np.conj(m.S.T)
        np.testing.assert_allclose(S_dag @ m.S, np.eye(4), atol=1e-10)

    def test_scattering_matrix_unitary_backslash(self):
        m = Mirror(0, 0, mirror_type="\\")
        S_dag = np.conj(m.S.T)
        np.testing.assert_allclose(S_dag @ m.S, np.eye(4), atol=1e-10)

    def test_full_reflection_no_transmission(self):
        """All input power should be reflected -- zero transmission."""
        m = Mirror(0, 0, mirror_type="/")
        for port_idx in range(4):
            v_in = np.zeros(4, dtype=complex)
            v_in[port_idx] = 1.0
            v_out = m.S @ v_in
            # Only one output port should be non-zero
            nonzero_count = np.sum(np.abs(v_out) > 1e-10)
            assert nonzero_count == 1
            assert np.sum(np.abs(v_out) ** 2) == pytest.approx(1.0, abs=1e-10)

    def test_slash_mirror_port_mapping(self):
        """'/' mirror: RIGHT(A)→UP(D), DOWN(B)→LEFT(A), LEFT(C)→DOWN(B), UP(D)→RIGHT(C)."""
        m = Mirror(0, 0, mirror_type="/")
        # Port A input → Port D output (RIGHT → UP)
        v_in = np.array([1, 0, 0, 0], dtype=complex)
        v_out = m.S @ v_in
        assert abs(v_out[3]) == pytest.approx(1.0, abs=1e-10)

    def test_backslash_mirror_port_mapping(self):
        r"""'\\' mirror: RIGHT(A)→DOWN(B), DOWN(B)→RIGHT(C), LEFT(C)→UP(D), UP(D)→LEFT(A)."""
        m = Mirror(0, 0, mirror_type="\\")
        # Port A input → Port B output (RIGHT → DOWN)
        v_in = np.array([1, 0, 0, 0], dtype=complex)
        v_out = m.S @ v_in
        assert abs(v_out[1]) == pytest.approx(1.0, abs=1e-10)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class TestDetector:
    def test_creation(self):
        d = Detector(300, 400)
        assert d.component_type == "detector"
        assert d.intensity == 0

    def test_single_beam_intensity(self):
        d = Detector(0, 0)
        d.add_beam({
            "amplitude": 1.0,
            "accumulated_phase": 0,
            "phase": 0,
            "total_path_length": 100,
            "generation": 0,
            "beam_id": "b1",
        })
        d.finalize_frame()
        assert d.intensity == pytest.approx(1.0)

    def test_constructive_interference(self):
        """Two beams with the same phase should add constructively."""
        d = Detector(0, 0)
        for i in range(2):
            d.add_beam({
                "amplitude": 0.5,
                "accumulated_phase": 0.0,
                "phase": 0.0,
                "total_path_length": 100,
                "generation": 0,
                "beam_id": f"b{i}",
            })
        d.finalize_frame()
        # (0.5 + 0.5)^2 = 1.0
        assert d.intensity == pytest.approx(1.0)

    def test_destructive_interference(self):
        """Two beams with pi phase difference should cancel."""
        d = Detector(0, 0)
        d.add_beam({
            "amplitude": 0.5,
            "accumulated_phase": 0.0,
            "phase": 0.0,
            "total_path_length": 100,
            "generation": 0,
            "beam_id": "b1",
        })
        d.add_beam({
            "amplitude": 0.5,
            "accumulated_phase": math.pi,
            "phase": math.pi,
            "total_path_length": 200,
            "generation": 0,
            "beam_id": "b2",
        })
        d.finalize_frame()
        assert d.intensity == pytest.approx(0.0, abs=1e-10)

    def test_reset_frame(self):
        d = Detector(0, 0)
        d.add_beam({
            "amplitude": 1.0,
            "accumulated_phase": 0,
            "phase": 0,
            "total_path_length": 0,
            "generation": 0,
            "beam_id": "b1",
        })
        d.finalize_frame()
        assert d.intensity == pytest.approx(1.0)
        d.reset_frame()
        assert d.incoming_beams == []
        assert d.processed_this_frame is False

    def test_get_intensity_percentage(self):
        d = Detector(0, 0)
        d.add_beam({
            "amplitude": 1.0,
            "accumulated_phase": 0,
            "phase": 0,
            "total_path_length": 0,
            "generation": 0,
            "beam_id": "b1",
        })
        d.finalize_frame()
        assert d.get_intensity_percentage() == 100

    def test_get_energy_info(self):
        d = Detector(0, 0)
        d.add_beam({
            "amplitude": 0.7,
            "accumulated_phase": 0.5,
            "phase": 0.5,
            "total_path_length": 50,
            "generation": 0,
            "beam_id": "b1",
        })
        d.finalize_frame()
        info = d.get_energy_info()
        assert info["num_beams"] == 1
        assert info["coherent_intensity"] == pytest.approx(0.49, abs=0.01)
        assert info["input_power_sum"] == pytest.approx(0.49, abs=0.01)

    def test_no_beams_gives_zero_intensity(self):
        d = Detector(0, 0)
        d.finalize_frame()
        assert d.intensity == 0

    def test_rejects_beam_after_finalize(self):
        d = Detector(0, 0)
        d.add_beam({
            "amplitude": 1.0,
            "accumulated_phase": 0,
            "phase": 0,
            "total_path_length": 0,
            "generation": 0,
            "beam_id": "b1",
        })
        d.finalize_frame()
        # This beam should be rejected
        d.add_beam({
            "amplitude": 1.0,
            "accumulated_phase": 0,
            "phase": 0,
            "total_path_length": 0,
            "generation": 0,
            "beam_id": "b2",
        })
        assert len(d.incoming_beams) == 1  # still only the first beam
