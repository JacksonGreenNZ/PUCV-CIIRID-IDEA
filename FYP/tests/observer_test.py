from core.observer import Observer
import pytest

def test_same_point_is_zero():
    assert Observer.angular_separation(45.0, 180.0, 45.0, 180.0) == pytest.approx(0.0, abs=1e-6)

def test_symmetry():
    a = Observer.angular_separation(30.0, 90.0, 60.0, 180.0)
    b = Observer.angular_separation(60.0, 180.0, 30.0, 90.0)
    assert a == pytest.approx(b, abs=1e-6)

def test_separation_positive():
    assert Observer.angular_separation(30.0, 90.0, 60.0, 180.0) > 0

def test_separation_bounded():
    result = Observer.angular_separation(10.0, 45.0, 80.0, 225.0)
    assert 0.0 <= result <= 180.0

def test_zenith_separation():
    assert Observer.angular_separation(90.0, 0.0, 90.0, 180.0) == pytest.approx(0.0, abs=1e-4)

def test_known_separation():
    result = Observer.angular_separation(0.0, 0.0, 0.0, 90.0)
    assert result == pytest.approx(90.0, abs=0.1)