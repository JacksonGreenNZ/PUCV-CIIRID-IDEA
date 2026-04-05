from PyQt6.QtCore import QThread, pyqtSignal
from core.run_config import RunConfig
from core.sopp_runner import SOPPRunner
from models.beam_model import BeamModel
from core.observer import Observer
from core.checker import InterferenceChecker
from core.window_analyser import WindowAnalyser
from pathlib import Path
from datetime import datetime


class AnalysisThread(QThread):
    log_message = pyqtSignal(str)
    finished = pyqtSignal(object, object, list, object, str, object)  # beam, observer, results, dir, ts, analyser
    failed = pyqtSignal(str)

    def __init__(self, run_config: RunConfig, tle_file: str):
        super().__init__()
        self._run_config = run_config
        self._tle_file = tle_file

    def run(self):
        try:
            beam_model = BeamModel()
            observer = Observer()

            runner = SOPPRunner(beam_model, self._run_config, self._tle_file)
            interference_events = runner.run()
            self.log_message.emit(f"SOPP returned {len(interference_events)} events")

            checker = InterferenceChecker(beam_model, observer)
            results = checker.check(interference_events)
            self.log_message.emit(f"Airy check flagged {len(results)} position points")

            analyser = WindowAnalyser(results, self._run_config.time_begin, self._run_config.time_end)

            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            self.finished.emit(beam_model, observer, results, output_dir, timestamp, analyser)

        except Exception as e:
            self.failed.emit(str(e))