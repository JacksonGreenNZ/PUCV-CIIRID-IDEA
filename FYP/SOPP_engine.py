from sopp.builder.configuration_builder import ConfigurationBuilder
from sopp.sopp import Sopp

from skyfield.api import load, wgs84, Star

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

for event in interference_events:
    # first and last satellite positions
    start = event.positions[0].time
    end   = event.positions[-1].time
    duration = (end - start).total_seconds()

    print(f"--- {event.satellite.name} ---")
    print(f"  Window:   {start} -> {end}")
    print(f"  Duration: {duration:.1f} seconds")

    # max altitude
    altitudes = [p.position.altitude for p in event.positions]
    print(f"  Max Elev: {max(altitudes):.1f} deg")

    # --- Add target position at first satellite time ---
    sat_time = event.positions[0].time
    t = ts.utc(sat_time.year, sat_time.month, sat_time.day,
               sat_time.hour, sat_time.minute, sat_time.second + sat_time.microsecond*1e-6)
    target_apparent = observer.at(t).observe(target).apparent()
    target_alt, target_az, _ = target_apparent.altaz()
    print(f"  Target Pos at first satellite time: Alt={target_alt.degrees:.2f}°, Az={target_az.degrees:.2f}°")
