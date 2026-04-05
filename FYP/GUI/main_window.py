import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QTextEdit, QSplitter
)
from PyQt6.QtGui import QFont


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Satellite RFI Predictor")
        self.setMinimumSize(900, 600)
        self.tle_file = None
        self.observatory = None
        self.target = None
        self.window = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # --- Left panel: config buttons ---
        left = QVBoxLayout()
        left.setSpacing(10)

        self.obs_btn = self._config_button("Observatory Selection\nNone Selected")
        self.targ_btn = self._config_button("Target Selection\nNone Selected")
        self.win_btn = self._config_button("Window Selection\nNone Selected")

        self.obs_btn.clicked.connect(self._select_observatory)
        self.targ_btn.clicked.connect(self._select_target)
        self.win_btn.clicked.connect(self._select_window)

        self.compute_btn = QPushButton("Compute Interference")
        self.compute_btn.setEnabled(False)
        self.compute_btn.setFixedHeight(44)
        self.compute_btn.clicked.connect(self._run_analysis)

        left.addWidget(self.obs_btn)
        left.addWidget(self.targ_btn)
        left.addWidget(self.win_btn)
        left.addStretch()
        left.addWidget(self.compute_btn)

        # --- Right panel: results tabs ---
        right = QVBoxLayout()

        self.tabs = QTabWidget()
        self.clean_stretches_view = QTextEdit()
        self.clean_stretches_view.setReadOnly(True)
        self.linked_groups_view = QTextEdit()
        self.linked_groups_view.setReadOnly(True)

        self.tabs.addTab(self.clean_stretches_view, "Clean Stretches")
        self.tabs.addTab(self.linked_groups_view, "Linked Groups")

        #log output at the bottom of the right panel
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(120)
        self.log_view.setPlaceholderText("Log output will appear here...")
        font = QFont("Arial", 9)
        self.log_view.setFont(font)

        right.addWidget(self.tabs)
        right.addWidget(QLabel("Log"))
        right.addWidget(self.log_view)

        #export buttons
        export_row = QHBoxLayout()
        export_row.addStretch()
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_video_btn = QPushButton("Export Video")
        self.export_csv_btn.setEnabled(False)
        self.export_video_btn.setEnabled(False)
        self.export_csv_btn.clicked.connect(self._export_csv)
        self.export_video_btn.clicked.connect(self._export_video)
        export_row.addWidget(self.export_csv_btn)
        export_row.addWidget(self.export_video_btn)
        right.addLayout(export_row)

        #root layout
        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setFixedWidth(220)

        right_widget = QWidget()
        right_widget.setLayout(right)

        root.addWidget(left_widget)
        root.addWidget(right_widget)

    def _config_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(64)
        btn.setCheckable(False)
        return btn

    def _update_compute_button(self):
        ready = all([self.observatory, self.target, self.window])
        self.compute_btn.setEnabled(ready)

    def _update_button_label(self, btn: QPushButton, title: str, value: str):
        btn.setText(f"{title}\n{value}")
        
    def set_tle_file(self, tle_file: str): 
        self.tle_file = tle_file

    # --- Slots ---

    def _select_observatory(self):
        # TODO: open ObservatoryDialog, set self.observatory
        self.observatory = "Warkworth 30m"  # placeholder
        self._update_button_label(self.obs_btn, "Observatory Selection:", self.observatory)
        self._update_compute_button()

    def _select_target(self):
        # TODO: open TargetDialog, set self.target
        self.target = "Vela"  # placeholder
        self._update_button_label(self.targ_btn, "Target Selection:", self.target)
        self._update_compute_button()

    def _select_window(self):
        # TODO: open WindowDialog, set self.window
        self.window = ("2026-10-16 16:20", "2026-10-16 16:40")  # placeholder
        label = f"{self.window[0]} → {self.window[1]}"
        self._update_button_label(self.win_btn, "Window Selection:", label)
        self._update_compute_button()

    def _run_analysis(self):
        # TODO: call main() from engine, route log output to self.log_view
        self.log_view.append("Analysis started...")
        self.export_csv_btn.setEnabled(True)
        self.export_video_btn.setEnabled(True)

    def _export_csv(self):
        # TODO: open save dialog, write CSV
        pass

    def _export_video(self):
        # TODO: call save_animation()
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())