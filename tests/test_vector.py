"""Tests for utils.vector.Vector2."""
import math
import pytest
from utils.vector import Vector2


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestVector2Creation:
    def test_basic_creation(self):
        v = Vector2(3, 4)
        assert v.x == 3
        assert v.y == 4

    def test_float_creation(self):
        v = Vector2(1.5, -2.7)
        assert v.x == pytest.approx(1.5)
        assert v.y == pytest.approx(-2.7)

    def test_zero_vector(self):
        v = Vector2(0, 0)
        assert v.x == 0
        assert v.y == 0


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------

class TestVector2Arithmetic:
    def test_addition(self):
        result = Vector2(1, 2) + Vector2(3, 4)
        assert result.x == 4
        assert result.y == 6

    def test_subtraction(self):
        result = Vector2(5, 7) - Vector2(2, 3)
        assert result.x == 3
        assert result.y == 4

    def test_scalar_multiplication(self):
        result = Vector2(2, -3) * 4
        assert result.x == 8
        assert result.y == -12

    def test_scalar_multiplication_float(self):
        result = Vector2(1, 1) * 0.5
        assert result.x == pytest.approx(0.5)
        assert result.y == pytest.approx(0.5)

    def test_scalar_multiplication_zero(self):
        result = Vector2(5, 5) * 0
        assert result.x == 0
        assert result.y == 0


# ---------------------------------------------------------------------------
# Magnitude / normalization
# ---------------------------------------------------------------------------

class TestVector2Geometry:
    @pytest.mark.parametrize("x, y, expected_mag", [
        (3, 4, 5.0),
        (0, 0, 0.0),
        (1, 0, 1.0),
        (0, -1, 1.0),
        (1, 1, math.sqrt(2)),
    ])
    def test_magnitude(self, x, y, expected_mag):
        assert Vector2(x, y).magnitude() == pytest.approx(expected_mag)

    def test_normalize_unit_vector(self):
        n = Vector2(3, 4).normalize()
        assert n.magnitude() == pytest.approx(1.0)
        assert n.x == pytest.approx(3 / 5)
        assert n.y == pytest.approx(4 / 5)

    def test_normalize_already_unit(self):
        n = Vector2(1, 0).normalize()
        assert n.x == pytest.approx(1.0)
        assert n.y == pytest.approx(0.0)

    def test_normalize_zero_vector(self):
        """Normalizing the zero vector should return the zero vector (no crash)."""
        n = Vector2(0, 0).normalize()
        assert n.x == 0
        assert n.y == 0

    @pytest.mark.parametrize("v1, v2, expected_dist", [
        (Vector2(0, 0), Vector2(3, 4), 5.0),
        (Vector2(1, 1), Vector2(1, 1), 0.0),
        (Vector2(-1, -1), Vector2(2, 3), 5.0),
    ])
    def test_distance_to(self, v1, v2, expected_dist):
        assert v1.distance_to(v2) == pytest.approx(expected_dist)


# ---------------------------------------------------------------------------
# Conversion / display
# ---------------------------------------------------------------------------

class TestVector2Conversion:
    def test_tuple_returns_ints(self):
        t = Vector2(3.7, 4.2).tuple()
        assert t == (4, 4)  # round(), not truncate
        assert all(isinstance(c, int) for c in t)

    def test_str(self):
        s = str(Vector2(1.23, -4.56))
        assert "1.2" in s
        assert "-4.6" in s

    def test_repr(self):
        r = repr(Vector2(1, 2))
        assert "Vector2" in r
