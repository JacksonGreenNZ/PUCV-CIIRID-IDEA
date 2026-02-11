from sopp.builder.configuration_builder import ConfigurationBuilder
from sopp.sopp import Sopp

from skyfield.api import load, wgs84, Star

import csv
from datetime import datetime
import numpy as np

# Load timescale and Earth
ts = load.timescale()
planets = load('de421.bsp')
earth = planets['earth']

# Build Configuration
lat = 40.8
long = -121.4
elevation = 986

observer = wgs84.latlon(lat, long, elevation_m=elevation)+earth

ra_hours = 19 + 59/60
dec_degrees = 40 + 44/60

target = Star(ra_hours=ra_hours, dec_degrees=dec_degrees)  # Cygnus A

config = (
    ConfigurationBuilder()
    .set_facility(
        latitude=lat, longitude=long, elevation=elevation, name="HCRO", beamwidth=3
    )
    .set_runtime_settings(concurrency_level=4)
    .set_time_window(begin="2026-01-13T19:00:00", end="2026-01-13T19:01:00")
    .set_frequency_range(bandwidth=10, frequency=135)
    # Cygnus A
    .set_observation_target(f"{dec_degrees}d", right_ascension=f"{ra_hours}h")
    .set_satellites(tle_file="active.tle")
    .build()
)

print(f"Running interference simulation for {len(config.satellites)} satellites:")

# Run Engine
engine = Sopp(config)
interference_events = engine.get_satellites_crossing_main_beam()

# Analyze Results
print(f"Found {len(interference_events)} interference events:")

local_time = datetime.now()
timestamp = local_time.strftime("%Y-%m-%d_%H-%M-%S")
filename = f"sat_intersect_{timestamp}.csv"

rows = []

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

        # Angular separation (approx)
        ang_sep = np.sqrt((np.deg2rad(sat_az) - np.deg2rad(target_az.degrees))**2 +
                  (np.deg2rad(sat_alt) - np.deg2rad(target_alt.degrees))**2)

        ang_sep_deg = np.rad2deg(ang_sep)

        rows.append({
            "time_utc": sat_time.isoformat(),
            "satellite": event.satellite.name,
            "sat_alt_deg": sat_alt,
            "sat_az_deg": sat_az,
            "target_alt_deg": target_alt.degrees,
            "target_az_deg": target_az.degrees,
            "angular_sep_deg": ang_sep_deg
        })
        
        #print to console
        start = event.positions[0].time 
        end = event.positions[-1].time 
        duration = (end - start).total_seconds() 
        print(f"--- {event.satellite.name} ---") 
        print(f" Window: {start} -> {end}") 
        print(f" Duration: {duration:.1f} seconds") 
        altitudes = [p.position.altitude for p in event.positions] 
        print(f" Max Elev: {max(altitudes):.1f} deg")
        print(f" Target Pos at first satellite time: Alt={target_alt.degrees:.2f}°, Az={target_az.degrees:.2f}°")
        

# Write CSV
with open(filename, "w", newline="") as f:
    fieldnames = ["time_utc", "satellite", "sat_alt_deg", "sat_az_deg",
                  "target_alt_deg", "target_az_deg", "angular_sep_deg"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} entries to {filename}")
