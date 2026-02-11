from sopp.builder.configuration_builder import ConfigurationBuilder
from sopp.sopp import Sopp

# Build Configuration
config = (
    ConfigurationBuilder()
    .set_facility(
        latitude=40.8, longitude=-121.4, elevation=986, name="HCRO", beamwidth=3
    )
    .set_runtime_settings(concurrency_level=4)
    .set_time_window(begin="2026-01-13T19:00:00", end="2026-01-13T19:01:00")
    .set_frequency_range(bandwidth=10, frequency=135)
    # Cygnus A
    .set_observation_target(declination="40d44m", right_ascension="19h59m")
    .set_satellites(tle_file="satellites.tle")
    .build()
)

print(f"Running interference simulation for {len(config.satellites)} satellites:")

# Run Engine
engine = Sopp(config)
interference_events = engine.get_satellites_crossing_main_beam()

# Analyze Results
print(f"Found {len(interference_events)} interference events:")

for event in interference_events:
    start = event.times[0]
    end = event.times[-1]
    duration = (end - start).total_seconds()

    print(f"--- {event.satellite.name} ---")
    print(f"  Window:   {start} -> {end}")
    print(f"  Duration: {duration:.1f} seconds")
    print(f"  Max Elev: {event.altitude.max():.1f} deg")