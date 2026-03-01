from sopp.builder.configuration_builder import ConfigurationBuilder
from sopp.sopp import Sopp
from models.beam_model import BeamModel
from config import (
    LATITUDE, LONGITUDE, ELEVATION_M,
    RA_HOURS, DEC_DEGREES,
    TIME_BEGIN, TIME_END,
    FREQUENCY_HZ, TLE_FILE,
    CONCURRENCY_LEVEL
)

class SOPPRunner:
    """
    Builds SOPP configuration and runs the interference engine.
    Uses BeamModel prefilter radius as the beamwidth passed to SOPP.
    """
    def __init__(self, beam_model: BeamModel):
        self.beam_model = beam_model
        self.config = self._build_config()

    def _build_config(self):
        """
        Builds SOPP configuration using hardcoded parameters for testing and
        prefilter radius from BeamModel as the beamwidth.
        """
        frequency_mhz = FREQUENCY_HZ / 1e6

        return (
            ConfigurationBuilder()
            .set_facility(
                latitude=LATITUDE,
                longitude=LONGITUDE,
                elevation=ELEVATION_M,
                name="observer",
                beamwidth=self.beam_model.prefilter_radius_deg
            )
            .set_runtime_settings(concurrency_level=CONCURRENCY_LEVEL)
            .set_time_window(begin=TIME_BEGIN, end=TIME_END)
            .set_frequency_range(bandwidth=10, frequency=frequency_mhz)
            .set_observation_target(f"{DEC_DEGREES}d", right_ascension=f"{RA_HOURS}h")
            .set_satellites(tle_file=TLE_FILE)
            .build()
        )

    def run(self):
        """
        Runs the SOPP engine and returns raw interference events.
        """
        engine = Sopp(self.config)
        print(f"Running SOPP for {len(self.config.satellites)} satellites...")
        return engine.get_satellites_crossing_main_beam()