import numpy as np
import csv
from datetime import datetime
from scipy.special import j1

from sopp.config.builder import ConfigurationBuilder
from sopp.sopp import Sopp


# -----------------------------
# Antenna / gain utilities
# -----------------------------

def airy_gain(theta_rad, theta_scale_rad):
    """
    Normalized Airy power pattern.

    theta_rad        : angular separation (radians)
    theta_scale_rad  : scaling angle (e.g. first null / 3.8317)
    """
    x = 3.8317 * (theta_rad / theta_scale_rad)

    gain = np.ones_like(x)
    mask = x != 0
    gain[mask] = (2 * j1(x[mask]) / x[mask]) ** 2
    return gain


def gain_cutoff_to_linear(cutoff_percent=None, cutoff_db=None):
    if cutoff_percent is not None:
        return cutoff_percent / 100.0
    if cutoff_db is not None:
        return 10 ** (cutoff_db / 10.0)
    raise ValueError("Must specify cutoff_percent or cutoff_db")


def split_contiguous(times, mask):
    """
    Split times into contiguous segments where mask == True
    """
    segments = []
    current = []

    for t, keep in zip(times, mask):
        if keep:
            current.append(t)
        elif current:
            segments.append(current)
            current = []

    if current:
        segments.append(current)

    return segments


# -----------------------------
# Configuration
# -----------------------------

MAX_SEARCH_ANGLE_DEG = 15.0       # geometry envelope
GAIN_CUTOFF_PERCENT = 2.0        # user input
THETA_NULL_DEG = 3.0             # first null (example)

cutoff_gain = gain_cutoff_to_linear(
    cutoff_percent=GAIN_CUTOFF_PERCENT
)

theta_null_rad = np.deg2rad(THETA_NULL_DEG)

config = (
    ConfigurationBuilder()
    .set_facility(
        latitude=40.8178049,
        longitude=-121.4695413,
        elevation=986,
        name="HCRO",
        beamwidth=2 * MAX_SEARCH_ANGLE_DEG
    )
    .set_runtime_settings(concurrency_level=4, time_resolution_seconds=1.0)
    .set_time_window(
        begin="2026-01-13T12:00:00",
        end="2026-01-13T13:00:00"
    )
    .set_frequency_range(bandwidth=10, frequency=135)
    .set_observation_target(
        declination="-38d6m50.8s",
        right_ascension="4h42m"
    )
    .load_satellites(tle_file="satellites.tle")
    .build()
)


# -----------------------------
# Run SOPP
# -----------------------------

engine = Sopp(config)
events = engine.get_satellites_crossing_main_beam()


# -----------------------------
# Process events
# -----------------------------

rows = []

for event in events:
    # SOPP typically provides these arrays
    times = np.array(event.times)
    az = np.deg2rad(event.azimuth)    # degrees -> radians
    alt = np.deg2rad(event.altitude)

    # Angular separation from boresight
    # (simplified small-angle approximation)
    theta = np.sqrt(
        (az - az.mean()) ** 2 +
        (alt - alt.mean()) ** 2
    )

    gain = airy_gain(theta, theta_null_rad)
    keep = gain >= cutoff_gain

    segments = split_contiguous(times, keep)

    for segment in segments:
        for t in segment:
            idx = np.where(times == t)[0][0]
            rows.append({
                "time_utc": t.isoformat(),
                "satellite": event.satellite.name,
                "angular_sep_deg": np.rad2deg(theta[idx]),
                "gain_linear": gain[idx],
                "gain_db": 10 * np.log10(gain[idx]),
                "included": True
            })


# -----------------------------
# Write CSV
# -----------------------------

with open("interference_events.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "time_utc",
            "satellite",
            "angular_sep_deg",
            "gain_linear",
            "gain_db",
            "included",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)


print(f"Wrote {len(rows)} samples to interference_events.csv")
