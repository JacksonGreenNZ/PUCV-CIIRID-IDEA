from sopp.builder.configuration_builder import ConfigurationBuilder
from sopp.sopp import Sopp
from core.run_config import RunConfig
from models.beam_model import BeamModel
import logging
import os
from enums.tle_group import TLEGroup

log = logging.getLogger(__name__)
from core.paths import get_base_dir
data_dir = get_base_dir() / "data"
data_dir.mkdir(exist_ok=True)

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
    def select_data(group: TLEGroup | str) -> str:
        from skyfield.api import load
        max_days = 7.0
        data_dir.mkdir(exist_ok=True)
        filename = str(data_dir / f"{group}.tle")
        url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle"
        if not os.path.exists(filename) or load.days_old(filename) >= max_days:
            log.info(f"Downloading TLEs for {group}...")
            try:
                load.download(url, filename=filename)
                log.info("TLE catalogue updated.")
            except Exception as e:
                if os.path.exists(filename):
                    log.warning(f"TLE download failed ({e}) — using cached file.")
                else:
                    raise RuntimeError(
                        f"TLE download failed and no cached file exists for '{group}'.\n"
                        f"Please check your internet connection or manually place a TLE file at:\n{filename}"
                    ) from e
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