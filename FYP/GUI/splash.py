from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import QSize
from core.tle_loader import TLELoaderThread
from core.paths import get_asset_path


class SplashScreen(QDialog):
    ready = pyqtSignal(str)
    
    @property
    def tle_file(self) -> str | None:
        return self._tle_file
    
    def __init__(self, group: str = "active"):
        super().__init__()
        self.setWindowTitle("RFI Window Analyser")
        self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self._tle_file = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._status_label = QLabel("Starting...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._close_btn = QPushButton("Continue")
        self._close_btn.setEnabled(False)
        self._close_btn.clicked.connect(self._on_close)

        layout.addStretch()
        layout.addWidget(self._status_label)
        layout.addStretch()
        layout.addWidget(self._close_btn)

        self._thread = TLELoaderThread(group)
        self._thread.status.connect(self._status_label.setText)
        self._thread.finished.connect(self._on_thread_done)
        self._thread.start()
        self._spinner = QLabel()
        self._movie = QMovie(get_asset_path("visualisation/spinner.gif"))        
        self._spinner.setMovie(self._movie)
        self._movie.setScaledSize(QSize(32, 32))
        layout.addWidget(self._spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        self._movie.start()

    def _on_thread_done(self, tle_file: str):
        self._tle_file = tle_file
        self._status_label.setText("TLE catalogue ready.")
        self._close_btn.setEnabled(True)
        self._movie.stop()
        self._spinner.hide()

    def _on_close(self):
        self.ready.emit(self._tle_file)
        self.accept()