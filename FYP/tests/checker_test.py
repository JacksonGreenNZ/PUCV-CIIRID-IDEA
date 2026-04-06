import pytest
from unittest.mock import MagicMock
from core.checker import InterferenceChecker
from models.beam_model import BeamModel


# --- Helpers ---

def make_event(sat_name, positions):
    event = MagicMock()
    event.satellite.name = sat_name
    event.positions = positions
    return event

def make_position(alt, az, time_iso="2026-01-01T10:00:00+00:00"):
    pt = MagicMock()
    pt.position.altitude = alt
    pt.position.azimuth = az
    # mock time to return isoformat
    pt.time.isoformat.return_value = time_iso
    pt.time.year = 2026
    pt.time.month = 1
    pt.time.day = 1
    pt.time.hour = 10
    pt.time.minute = 0
    pt.time.second = 0
    pt.time.microsecond = 0
    return pt

def make_observer(target_alt=45.0, target_az=180.0):
    observer = MagicMock()
    observer.get_target_position.return_value = (target_alt, target_az)
    from core.observer import Observer
    observer.angular_separation = lambda alt1, az1, alt2, az2: Observer.angular_separation(alt1, az1, alt2, az2)
    return observer


# --- Tests ---

def test_empty_events_returns_empty():
    beam = BeamModel(dish_diameter_m=20.0, frequency_hz=135e6)
    observer = make_observer()
    checker = InterferenceChecker(beam, observer)
    assert checker.check([]) == []

def test_event_within_beam_is_flagged():
    beam = BeamModel(dish_diameter_m=20.0, frequency_hz=135e6, gain_cutoff_percent=3.0)
    # place satellite at same position as target — 0 separation, max gain
    observer = make_observer(target_alt=45.0, target_az=180.0)
    pt = make_position(alt=45.0, az=180.0)
    event = make_event("SAT-1", [pt])
    checker = InterferenceChecker(beam, observer)
    results = checker.check([event])
    assert len(results) == 1

def test_event_outside_beam_not_flagged():
    beam = BeamModel(dish_diameter_m=20.0, frequency_hz=135e6, gain_cutoff_percent=3.0)
    # place satellite far from target
    observer = make_observer(target_alt=45.0, target_az=180.0)
    pt = make_position(alt=45.0, az=0.0)  # 180 degrees away in az
    event = make_event("SAT-1", [pt])
    checker = InterferenceChecker(beam, observer)
    results = checker.check([event])
    assert len(results) == 0

def test_result_dict_has_required_keys():
    beam = BeamModel(dish_diameter_m=20.0, frequency_hz=135e6)
    observer = make_observer(target_alt=45.0, target_az=180.0)
    pt = make_position(alt=45.0, az=180.0)
    event = make_event("SAT-1", [pt])
    checker = InterferenceChecker(beam, observer)
    results = checker.check([event])
    assert len(results) == 1
    expected_keys = {
        "time_utc", "satellite", "sat_alt_deg", "sat_az_deg",
        "target_alt_deg", "target_az_deg", "angular_sep_deg", "gain_percent"
    }
    assert expected_keys == set(results[0].keys())

def test_multiple_events_multiple_results():
    beam = BeamModel(dish_diameter_m=20.0, frequency_hz=135e6)
    observer = make_observer(target_alt=45.0, target_az=180.0)
    events = [
        make_event("SAT-1", [make_position(45.0, 180.0)]),
        make_event("SAT-2", [make_position(45.0, 180.0)]),
    ]
    checker = InterferenceChecker(beam, observer)
    results = checker.check(events)
    assert len(results) == 2
    assert results[0]["satellite"] == "SAT-1"
    assert results[1]["satellite"] == "SAT-2"

def test_bypass_mode_flags_everything():
    beam = BeamModel(dish_diameter_m=20.0, frequency_hz=135e6, bypass=True)
    beam.prefilter_radius_deg = 3.0
    observer = make_observer(target_alt=45.0, target_az=180.0)
    # satellite outside normal beam
    pt = make_position(alt=45.0, az=0.0)
    event = make_event("SAT-1", [pt])
    checker = InterferenceChecker(beam, observer)
    results = checker.check([event])
    # bypass should return gain regardless of separation
    assert len(results) == 1

def test_satellite_name_in_result():
    beam = BeamModel(dish_diameter_m=20.0, frequency_hz=135e6)
    observer = make_observer(target_alt=45.0, target_az=180.0)
    pt = make_position(alt=45.0, az=180.0)
    event = make_event("STARLINK-123", [pt])
    checker = InterferenceChecker(beam, observer)
    results = checker.check([event])
    assert results[0]["satellite"] == "STARLINK-123"