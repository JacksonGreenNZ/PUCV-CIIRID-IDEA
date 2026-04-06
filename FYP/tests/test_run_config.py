import pytest
from core.run_config import RunConfig


@pytest.fixture
def tracking_config():
    return RunConfig(
        latitude=40.8,
        longitude=-121.4,
        elevation_m=986,
        dish_diameter_m=20.0,
        frequency_hz=135e6,
        time_begin="2026-01-13T19:00:00",
        time_end="2026-01-13T19:10:00",
        ra_hours=19.983,
        dec_degrees=40.733,
    )

@pytest.fixture
def static_config():
    return RunConfig(
        latitude=40.8,
        longitude=-121.4,
        elevation_m=986,
        dish_diameter_m=20.0,
        frequency_hz=135e6,
        time_begin="2026-01-13T19:00:00",
        time_end="2026-01-13T19:10:00",
        azimuth_deg=180.0,
        altitude_deg=45.0,
    )


# --- is_static / is_tracking ---

def test_tracking_config_is_tracking(tracking_config):
    assert tracking_config.is_tracking()
    assert not tracking_config.is_static()

def test_static_config_is_static(static_config):
    assert static_config.is_static()
    assert not static_config.is_tracking()

def test_empty_config_neither():
    config = RunConfig(
        latitude=40.8,
        longitude=-121.4,
        elevation_m=986,
        dish_diameter_m=20.0,
        frequency_hz=135e6,
        time_begin="2026-01-13T19:00:00",
        time_end="2026-01-13T19:10:00",
    )
    assert not config.is_static()
    assert not config.is_tracking()

def test_bypass_defaults_false(tracking_config):
    assert tracking_config.bypass_airy == False

def test_concurrency_level_set():
    import os
    config = RunConfig(
        latitude=40.8,
        longitude=-121.4,
        elevation_m=986,
        dish_diameter_m=20.0,
        frequency_hz=135e6,
        time_begin="2026-01-13T19:00:00",
        time_end="2026-01-13T19:10:00",
    )
    assert config.concurrency_level == os.cpu_count()