import pytest
from core.app_state import AppState, Observatory, Target


@pytest.fixture
def state(qapp):
    return AppState()

@pytest.fixture
def observatory():
    return Observatory(
        name="Test Obs",
        latitude=40.8,
        longitude=-121.4,
        elevation_m=986,
        dish_diameter_m=20.0,
        frequency_hz=135e6,
    )

@pytest.fixture
def tracking_target():
    return Target(name="Vela", ra_hours=8.56, dec_degrees=-45.8)

@pytest.fixture
def static_target():
    return Target(name="Fixed", azimuth_deg=180.0, altitude_deg=45.0, is_static=True)


# --- is_ready ---

def test_not_ready_by_default(state):
    assert not state.is_ready()

def test_not_ready_missing_window(state, observatory, tracking_target):
    state.tle_file = "data/starlink.tle"
    state.observatory = observatory
    state.target = tracking_target
    assert not state.is_ready()

def test_not_ready_missing_target(state, observatory):
    state.tle_file = "data/starlink.tle"
    state.observatory = observatory
    state.window = ("2026-01-01T10:00:00", "2026-01-01T10:10:00", 30)
    assert not state.is_ready()

def test_ready_when_all_set(state, observatory, tracking_target):
    state.tle_file = "data/starlink.tle"
    state.observatory = observatory
    state.target = tracking_target
    state.window = ("2026-01-01T10:00:00", "2026-01-01T10:10:00", 30)
    assert state.is_ready()


# --- build_run_config ---

def test_build_run_config_tracking(state, observatory, tracking_target):
    state.tle_file = "data/starlink.tle"
    state.observatory = observatory
    state.target = tracking_target
    state.window = ("2026-01-01T10:00:00", "2026-01-01T10:10:00", 30)
    config = state.build_run_config()
    assert config.ra_hours == tracking_target.ra_hours
    assert config.dec_degrees == tracking_target.dec_degrees
    assert config.azimuth_deg is None
    assert config.altitude_deg is None

def test_build_run_config_static(state, observatory, static_target):
    state.tle_file = "data/starlink.tle"
    state.observatory = observatory
    state.target = static_target
    state.window = ("2026-01-01T10:00:00", "2026-01-01T10:10:00", 30)
    config = state.build_run_config()
    assert config.azimuth_deg == 180.0
    assert config.altitude_deg == 45.0
    assert config.ra_hours is None

def test_build_run_config_gap_tolerance(state, observatory, tracking_target):
    state.tle_file = "data/starlink.tle"
    state.observatory = observatory
    state.target = tracking_target
    state.window = ("2026-01-01T10:00:00", "2026-01-01T10:10:00", 60)
    config = state.build_run_config()
    assert config.gap_tolerance_seconds == 60

def test_build_run_config_bypass(state, tracking_target):
    obs = Observatory(
        name="Bypass Obs",
        latitude=40.8,
        longitude=-121.4,
        elevation_m=986,
        dish_diameter_m=20.0,
        frequency_hz=135e6,
        bypass_airy=True,
        manual_beamwidth_deg=5.0,
    )
    state.tle_file = "data/starlink.tle"
    state.observatory = obs
    state.target = tracking_target
    state.window = ("2026-01-01T10:00:00", "2026-01-01T10:10:00", 30)
    config = state.build_run_config()
    assert config.bypass_airy == True
    assert config.manual_beamwidth_deg == 5.0