from sopp.builder.configuration_builder import ConfigurationBuilder
from sopp.sopp import Sopp
from core.run_config import RunConfig
from models.beam_model import BeamModel
from config import (
    LATITUDE, LONGITUDE, ELEVATION_M,
    RA_HOURS, DEC_DEGREES,
    TIME_BEGIN, TIME_END,
    FREQUENCY_HZ,
    CONCURRENCY_LEVEL, DATA_TYPE
)
import logging
log = logging.getLogger(__name__)

class SOPPRunner:
    """
    Builds SOPP configuration and runs the interference engine.
    Uses BeamModel prefilter radius as the beamwidth passed to SOPP.
    """
    def __init__(self, beam_model: BeamModel, run_config: RunConfig, tle_file: str):
        self.beam_model = beam_model
        self.run_config = run_config
        self.tle_file = tle_file #passed in from TLELoaderThread on gui boot or initialisation on main for cli
        self.config = self._build_config()

    @staticmethod
    def select_data(group: str) -> str:
        import os
        from skyfield.api import load
        max_days = 7.0
        filename = f"data/{group}.tle"
        url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle"
        if not os.path.exists(filename) or load.days_old(filename) >= max_days:
            log.info(f"Downloading TLEs for {group}...")
            load.download(url, filename=filename)
            log.info("TLE catalogue updated.")
        else:
            log.info("TLE catalogue up to date.")
        return filename

    def _build_config(self):
        rc = self.run_config
        frequency_mhz = rc.frequency_hz / 1e6
        beamwidth = (
            rc.manual_beamwidth_deg 
            if rc.bypass_airy 
            else self.beam_model.prefilter_radius_deg
        )
        builder = (
            ConfigurationBuilder()
            .set_facility(
                latitude=rc.latitude,
                longitude=rc.longitude,
                elevation=rc.elevation_m,
                name="observer",
                beamwidth=beamwidth
            )
            .set_runtime_settings(concurrency_level=rc.concurrency_level)
            .set_time_window(begin=rc.time_begin, end=rc.time_end)
            .set_frequency_range(bandwidth=10, frequency=frequency_mhz)
            .set_satellites(tle_file=self.tle_file)
        )

        if rc.is_static():
            builder = builder.set_observation_target(
                altitude=rc.altitude_deg,
                azimuth=rc.azimuth_deg,
            )
        elif rc.is_tracking():
            builder = builder.set_observation_target(
                f"{rc.dec_degrees}d",
                right_ascension=f"{rc.ra_hours}h"
            )
        else:
            raise ValueError("RunConfig must have either RA/Dec or Az/Alt set.")

        return builder.build()

    

    def run(self):
        """
        Runs the SOPP engine and returns raw interference events.
        """
        engine = Sopp(self.config)
        log.info(f"Running SOPP for {len(self.config.satellites)} satellites...")
        return engine.get_satellites_crossing_main_beam()