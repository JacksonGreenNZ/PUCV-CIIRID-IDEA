import logging
from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from datetime import datetime


from core.run_config import RunConfig
from core.analysis_thread import AnalysisThread 


log = logging.getLogger(__name__)


@dataclass
class Observatory:
    name: str
    latitude: float
    longitude: float
    elevation_m: float
    dish_diameter_m: float
    frequency_hz: float


@dataclass
class Target:
    name: str
    ra_hours: float
    dec_degrees: float


@dataclass
class AnalysisResults:
    beam_model: object
    observer: object
    results: list
    output_dir: Path
    timestamp: str
    clean_stretches_text: str
    linked_groups_text: str


class AppState(QObject):
    state_changed = pyqtSignal()
    log_message = pyqtSignal(str)
    analysis_complete = pyqtSignal(AnalysisResults)
    analysis_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.tle_file: Optional[str] = None
        self.observatory: Optional[Observatory] = None
        self.target: Optional[Target] = None
        self.window: Optional[tuple[str, str]] = None

        self._results: Optional[AnalysisResults] = None
        self._thread: Optional[AnalysisThread] = None

    def set_tle_file(self, tle_file: str):
        self.tle_file = tle_file
        self.state_changed.emit()

    def is_ready(self) -> bool:
        return all([self.tle_file, self.observatory, self.target, self.window])



def build_run_config(self) -> RunConfig:
    return RunConfig(
        latitude=self.observatory.latitude,
        longitude=self.observatory.longitude,
        elevation_m=self.observatory.elevation_m,
        dish_diameter_m=self.observatory.dish_diameter_m,
        frequency_hz=self.observatory.frequency_hz,
        ra_hours=self.target.ra_hours,
        dec_degrees=self.target.dec_degrees,
        time_begin=self.window[0],
        time_end=self.window[1],
        gap_tolerance_seconds=60,        #could expose in UI later
        gain_cutoff_percent=3,           #same
        concurrency_level=os.cpu_count(),
        data_type="starlink",            #driven by splash group selection
    )

    def run_analysis(self):
        if not self.is_ready():
            return

        run_config = self.build_run_config()

        self._thread = AnalysisThread(run_config, self.tle_file)
        self._thread.log_message.connect(self.log_message)
        self._thread.finished.connect(self._on_analysis_done)
        self._thread.failed.connect(self.analysis_failed)
        self._thread.start()

    def _on_analysis_done(self, beam_model, observer, results, output_dir, timestamp, analyser):
        self._results = AnalysisResults(
            beam_model=beam_model,
            observer=observer,
            results=results,
            output_dir=output_dir,
            timestamp=timestamp,
            clean_stretches_text=analyser.clean_stretches_summary(),
            linked_groups_text=analyser.linked_groups_summary(),
        )
        self.analysis_complete.emit(self._results)

    def export_csv(self):
        if not self._results:
            return
        # move CSV writing logic out of main() and into here
        # or delegate to a helper in core/
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(None, "Export CSV", 
                      str(self._results.output_dir / f"sat_intersect_{self._results.timestamp}.csv"),
                      "CSV Files (*.csv)")
        if path:
            self._write_csv(Path(path))

    def export_video(self):
        if not self._results:
            return
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(None, "Export Video",
                      str(self._results.output_dir / f"sky_plot_{self._results.timestamp}.mp4"),
                      "Video Files (*.mp4)")
        if path:
            self.log_message.emit("Saving video — this may take a while...")
            from visualisation.sky_plot import SkyPlot
            plot = SkyPlot(self._results.beam_model, self._results.observer, self._results.results)
            plot.animate(save_path=path)

    def _write_csv(self, path: Path):
        import csv
        fieldnames = [
            "time_utc", "satellite", "sat_alt_deg", "sat_az_deg",
            "target_alt_deg", "target_az_deg", "angular_sep_deg", "gain_percent"
        ]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self._results.results)
        self.log_message.emit(f"Wrote {len(self._results.results)} entries to {path}")