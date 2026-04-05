import logging
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from datetime import datetime

from core.run_config import RunConfig
from models.beam_model import BeamModel
from core.observer import Observer
from core.checker import InterferenceChecker
from core.sopp_runner import SOPPRunner
from core.window_analyser import WindowAnalyser


class QtLogHandler(logging.Handler):
    """Forwards log records to a Qt signal."""
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    def emit(self, record):
        self.signal.emit(self.format(record))


class AnalysisThread(QThread):
    log_message = pyqtSignal(str)
    finished = pyqtSignal(object, object, list, object, str, object)  # beam, observer, results, output_dir, timestamp, analyser
    failed = pyqtSignal(str)

    def __init__(self, run_config: RunConfig, tle_file: str):
        super().__init__()
        self._run_config = run_config
        self._tle_file = tle_file

    def run(self):
        handler = QtLogHandler(self.log_message)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        
        
        try:
            log = logging.getLogger(__name__)
            log.info(f"dish={self._run_config.dish_diameter_m}")
            log.info(f"freq={self._run_config.frequency_hz}")
            log.info(f"Bypass Airy={self._run_config.bypass_airy}")
            observer = Observer(
                latitude=self._run_config.latitude,
                longitude=self._run_config.longitude,
                elevation_m=self._run_config.elevation_m,
                time_begin=self._run_config.time_begin,
                time_end=self._run_config.time_end,
                ra_hours=self._run_config.ra_hours,
                dec_degrees=self._run_config.dec_degrees,
                azimuth_deg=self._run_config.azimuth_deg,
                altitude_deg=self._run_config.altitude_deg,
            )
            beam_model = BeamModel(
                dish_diameter_m=self._run_config.dish_diameter_m,
                frequency_hz=self._run_config.frequency_hz,
                gain_cutoff_percent=self._run_config.gain_cutoff_percent,
                bypass=self._run_config.bypass_airy
            )
            if self._run_config.bypass_airy:
                beam_model.prefilter_radius_deg = self._run_config.manual_beamwidth_deg

            runner = SOPPRunner(beam_model, self._run_config, self._tle_file)
            interference_events = runner.run()
            log.info(f"SOPP returned {len(interference_events)} events")

            checker = InterferenceChecker(beam_model, observer)
            results = checker.check(interference_events)
            log.info(f"Check flagged {len(results)} position points")

            analyser = WindowAnalyser(
                results,
                self._run_config.time_begin,
                self._run_config.time_end
            )
            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log.info("Analysis complete.")
            self.finished.emit(beam_model, observer, results, output_dir, timestamp, analyser)

        except Exception as e:
            self.failed.emit(str(e))
        finally:
            root_logger.removeHandler(handler)