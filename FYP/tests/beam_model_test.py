import pytest
import numpy as np
from models.beam_model import BeamModel


# --- Fixtures ---

@pytest.fixture
def standard_beam():
    return BeamModel(dish_diameter_m=20.0, frequency_hz=135e6, gain_cutoff_percent=3.0)

@pytest.fixture
def bypass_beam():
    return BeamModel(dish_diameter_m=20.0, frequency_hz=135e6, gain_cutoff_percent=3.0, bypass=True)


# --- airy_gain ---

def test_airy_gain_boresight(standard_beam):
    assert standard_beam.airy_gain(0) == 1.0

def test_airy_gain_decreases_with_separation(standard_beam):
    assert standard_beam.airy_gain(1.0) < standard_beam.airy_gain(0.1)

def test_airy_gain_always_positive(standard_beam):
    for theta in [0, 0.1, 0.5, 1.0, 2.0, 5.0]:
        assert standard_beam.airy_gain(theta) >= 0

def test_airy_gain_max_one(standard_beam):
    for theta in [0, 0.1, 0.5, 1.0]:
        assert standard_beam.airy_gain(theta) <= 1.0


# --- compute_prefilter_radius ---

def test_prefilter_radius_positive(standard_beam):
    assert standard_beam.prefilter_radius_deg > 0

def test_prefilter_radius_gain_at_boundary(standard_beam):
    # gain at prefilter radius should be approximately at threshold
    gain = standard_beam.airy_gain(standard_beam.prefilter_radius_deg)
    assert abs(gain - standard_beam.threshold) < 0.001

def test_prefilter_radius_zero_in_bypass(bypass_beam):
    assert bypass_beam.prefilter_radius_deg == 0.0

def test_prefilter_radius_larger_dish_smaller_beam():
    small_dish = BeamModel(dish_diameter_m=10.0, frequency_hz=135e6)
    large_dish = BeamModel(dish_diameter_m=30.0, frequency_hz=135e6)
    assert large_dish.prefilter_radius_deg < small_dish.prefilter_radius_deg

def test_prefilter_radius_higher_freq_smaller_beam():
    low_freq = BeamModel(dish_diameter_m=20.0, frequency_hz=100e6)
    high_freq = BeamModel(dish_diameter_m=20.0, frequency_hz=500e6)
    assert high_freq.prefilter_radius_deg < low_freq.prefilter_radius_deg

def test_prefilter_radius_tighter_threshold_larger_radius():
    tight = BeamModel(dish_diameter_m=20.0, frequency_hz=135e6, gain_cutoff_percent=1.0)
    loose = BeamModel(dish_diameter_m=20.0, frequency_hz=135e6, gain_cutoff_percent=10.0)
    assert tight.prefilter_radius_deg > loose.prefilter_radius_deg


# --- interference_gain ---

def test_interference_gain_boresight_is_100(standard_beam):
    assert standard_beam.interference_gain(0) == pytest.approx(100.0)

def test_interference_gain_returns_none_below_threshold(standard_beam):
    # well outside the beam should be below threshold
    assert standard_beam.interference_gain(standard_beam.prefilter_radius_deg + 1.0) is None

def test_interference_gain_returns_value_at_boresight(standard_beam):
    assert standard_beam.interference_gain(0) is not None

def test_interference_gain_bypass_never_none(bypass_beam):
    for theta in [0, 1.0, 5.0, 10.0, 20.0]:
        assert bypass_beam.interference_gain(theta) is not None

def test_interference_gain_bypass_returns_100_at_boresight(bypass_beam):
    assert bypass_beam.interference_gain(0) == pytest.approx(100.0)

def test_interference_gain_within_prefilter_not_none(standard_beam):
    # just inside the prefilter radius should return a value
    assert standard_beam.interference_gain(standard_beam.prefilter_radius_deg * 0.5) is not None