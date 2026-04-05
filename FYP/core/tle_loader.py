from PyQt6.QtCore import QThread, pyqtSignal
from core.sopp_runner import SOPPRunner
import logging

log = logging.getLogger(__name__)

class TLELoaderThread(QThread):
    status = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, group: str):
        super().__init__()
        self.group = group

    def run(self):
        self.status.emit(f"Checking TLE catalogue: {self.group}...")
        filename = SOPPRunner.select_data(self.group)
        self.status.emit("TLE catalogue ready.")
        self.finished.emit(filename)