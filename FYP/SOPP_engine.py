from sopp.builder.configuration_builder import ConfigurationBuilder
from sopp.sopp import Sopp

from skyfield.api import load, wgs84, Star
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import j1
import csv
from datetime import datetime
from pathlib import Path
import os

# ---- PARAMETERS ----
lat = 40.8
long = -121.4
elevation = 986
beamwidth_deg = 10.0      # maximum search radius (SOPP beamwidth)
gain_cutoff_percent = 50   # user-defined gain threshold (linear, 0-100)

ra_hours = 19 + 59/60
dec_degrees = 40 + 44/60

target = Star(ra_hours=ra_hours, dec_degrees=dec_degrees)  # Cygnus A

# ---- Load timescale and Earth ----
ts = load.timescale()
planets = load('de421.bsp')
earth = planets['earth']
observer = wgs84.latlon(lat, long, elevation_m=elevation) + earth

# ---- Airy pattern function ----
def airy_gain(theta_deg, beamwidth_deg):
    """
    Returns normalized linear gain (0-1) at angular separation theta_deg
    theta_deg: angular separation in degrees
    beamwidth_deg: radius to first null (approx)
    """
    theta_rad = np.deg2rad(theta_deg)
    k = 3.8317 / np.deg2rad(beamwidth_deg)  # scale factor so first null at beamwidth
    x = k * np.sin(theta_rad)
    g = np.ones_like(x)
    mask = x != 0
    g[mask] = (2 * j1(x[mask]) / x[mask])**2
    return g

# ---- Build SOPP Configuration ----
config = (
    ConfigurationBuilder()
    .set_facility(
        latitude=lat, longitude=long, elevation=elevation,
        name="HCRO", beamwidth=beamwidth_deg
    )
    .set_runtime_settings(concurrency_level=4)
    .set_time_window(begin="2026-01-13T19:00:00", end="2026-01-13T19:10:00")
    .set_frequency_range(bandwidth=10, frequency=135)
    .set_observation_target(f"{dec_degrees}d", right_ascension=f"{ra_hours}h")
    .set_satellites(tle_file="active.tle")
    .build()
)

print(f"Running interference simulation for {len(config.satellites)} satellites:")

# ---- Run SOPP ----
engine = Sopp(config)
interference_events = engine.get_satellites_crossing_main_beam()

# ---- Prepare outputs folder ----
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

local_time = datetime.now()
timestamp = local_time.strftime("%Y-%m-%d_%H-%M-%S")
csv_filename = output_dir / f"sat_intersect_{timestamp}.csv"

rows = []
polar_data = []  # list of (theta_rad, r_deg) tuples for plotting

# ---- Process events ----
for event in interference_events:
    for pt in event.positions:
        sat_time = pt.time
        t = ts.utc(
            sat_time.year, sat_time.month, sat_time.day,
            sat_time.hour, sat_time.minute, sat_time.second + sat_time.microsecond*1e-6
        )

        # Satellite position
        sat_alt = pt.position.altitude
        sat_az  = pt.position.azimuth

        # Target apparent position
        target_apparent = observer.at(t).observe(target).apparent()
        target_alt, target_az, _ = target_apparent.altaz()

        # Angular separation
        ang_sep_deg = np.sqrt((sat_alt - target_alt.degrees)**2 +
                              (sat_az - target_az.degrees)**2)

        # Compute gain
        gain_linear = airy_gain(ang_sep_deg, beamwidth_deg)
        gain_percent = gain_linear * 100

        if gain_percent >= gain_cutoff_percent:
            # Include only if above threshold
            rows.append({
                "time_utc": sat_time.isoformat(),
                "satellite": event.satellite.name,
                "sat_alt_deg": sat_alt,
                "sat_az_deg": sat_az,
                "target_alt_deg": target_alt.degrees,
                "target_az_deg": target_az.degrees,
                "angular_sep_deg": ang_sep_deg,
                "gain_percent": gain_percent
            })

            # Polar coordinates for plotting
            theta_rad = np.deg2rad(sat_az - target_az.degrees)  # relative azimuth
            r_deg = 90 - sat_alt  # zenith=0, horizon=90
            polar_data.append((theta_rad, r_deg))

# ---- Write CSV ----
with open(csv_filename, "w", newline="") as f:
    fieldnames = ["time_utc", "satellite", "sat_alt_deg", "sat_az_deg",
                  "target_alt_deg", "target_az_deg", "angular_sep_deg", "gain_percent"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} entries to {csv_filename}")

# ---- Polar plot ----
if polar_data:
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_rlim(0, 90)
    ax.set_rlabel_position(135)
    ax.set_title("Satellite Positions Relative to Target")

    theta_vals, r_vals = zip(*polar_data)
    ax.scatter(theta_vals, r_vals, c='r', s=20, label='Satellites')

    # Optional: plot a circle for 50% gain cutoff
    cutoff_theta = np.linspace(0, 2*np.pi, 360)
    cutoff_radius = 90 - (beamwidth_deg * gain_cutoff_percent/100)  # rough visual
    ax.plot(cutoff_theta, np.full_like(cutoff_theta, cutoff_radius),
            color='b', linestyle='--', label=f'{gain_cutoff_percent}% gain cutoff')

    ax.legend()
    plot_filename = output_dir / f"sat_positions_{timestamp}.png"
    fig.savefig(plot_filename, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Polar plot saved to {plot_filename}")
