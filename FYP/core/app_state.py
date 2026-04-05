import os
import csv
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from typing import Optional
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
    gain_cutoff_percent: float = 3.0
    bypass_airy: bool = False
    manual_beamwidth_deg: float = 3.0

@dataclass
class Target:
    name: str
    ra_hours: Optional[float] = None
    dec_degrees: Optional[float] = None
    azimuth_deg: Optional[float] = None
    altitude_deg: Optional[float] = None
    is_static: bool = False


@dataclass
class AnalysisResults:
    beam_model: object
    observer: object
    results: list
    output_dir: Path
    timestamp: str
    analyser: object


class AppState(QObject):
    state_changed = pyqtSignal()
    log_message = pyqtSignal(str)
    analysis_complete = pyqtSignal(object)
    analysis_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.tle_file: Optional[str] = None
        self.observatory: Optional[Observatory] = None
        self.target: Optional[Target] = None
        self.window: Optional[tuple[str, str, int]] = None
        self._results: Optional[AnalysisResults] = None
        self._thread: Optional[AnalysisThread] = None

    def set_tle_file(self, tle_file: str):
        self.tle_file = tle_file
        self.state_changed.emit()

    def is_ready(self) -> bool:
        return all([self.tle_file, self.observatory, self.target, self.window])

    def build_run_config(self) -> RunConfig:
        assert self.observatory and self.target and self.window
        return RunConfig(
            latitude=self.observatory.latitude,
            longitude=self.observatory.longitude,
            elevation_m=self.observatory.elevation_m,
            dish_diameter_m=self.observatory.dish_diameter_m,
            frequency_hz=self.observatory.frequency_hz,
            ra_hours=self.target.ra_hours,
            dec_degrees=self.target.dec_degrees,
            azimuth_deg=self.target.azimuth_deg,
            altitude_deg=self.target.altitude_deg,
            time_begin=self.window[0],
            time_end=self.window[1],
            gap_tolerance_seconds=self.window[2],
            gain_cutoff_percent=self.observatory.gain_cutoff_percent,
            bypass_airy=self.observatory.bypass_airy,
            manual_beamwidth_deg=self.observatory.manual_beamwidth_deg,
            concurrency_level=os.cpu_count(),
            data_type="starlink",
        )

    def run_analysis(self):
        if not self.is_ready():
            return
        run_config = self.build_run_config()
        self._thread = AnalysisThread(run_config, self.tle_file)
        self._thread.log_message.connect(self.log_message)
        self._thread.finished.connect(self._on_analysis_done)
        self._thread.failed.connect(self._on_analysis_failed)
        self._thread.start()

    def _on_analysis_done(self, beam_model, observer, results, output_dir, timestamp, analyser):
        self._results = AnalysisResults(
            beam_model=beam_model,
            observer=observer,
            results=results,
            output_dir=output_dir,
            timestamp=timestamp,
            analyser=analyser,
        )
        self.analysis_complete.emit(self._results)

    def _on_analysis_failed(self, error: str):
        self.log_message.emit(f"ERROR: {error}")
        self.analysis_failed.emit(error)

    def export_csv(self):
        if not self._results:
            return
        from PyQt6.QtWidgets import QFileDialog
        default = str(self._results.output_dir / f"sat_intersect_{self._results.timestamp}.csv")
        path, _ = QFileDialog.getSaveFileName(None, "Export CSV", default, "CSV Files (*.csv)")
        if not path:
            return
        fieldnames = [
            "time_utc", "satellite", "sat_alt_deg", "sat_az_deg",
            "target_alt_deg", "target_az_deg", "angular_sep_deg", "gain_percent"
        ]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self._results.results)
        self.log_message.emit(f"Wrote {len(self._results.results)} entries to {path}")

    def export_video(self):
        if not self._results:
            return
        from PyQt6.QtWidgets import QFileDialog
        default = str(self._results.output_dir / f"sky_plot_{self._results.timestamp}.mp4")
        path, _ = QFileDialog.getSaveFileName(None, "Export Video", default, "Video Files (*.mp4)")
        if not path:
            return
        self.log_message.emit("Saving video — this may take a while...")
        from visualisation.sky_plot import SkyPlot
        plot = SkyPlot(self._results.beam_model, self._results.observer, self._results.results)
        plot.animate(save_path=path)
        self.log_message.emit(f"Video saved to {path}")