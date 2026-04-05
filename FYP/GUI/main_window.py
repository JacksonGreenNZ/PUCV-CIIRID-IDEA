import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QTextEdit
)
from PyQt6.QtGui import QFont

from core.app_state import AppState
from GUI.dialogs.observatory_dialog import ObservatoryDialog
from GUI.dialogs.target_dialog import TargetDialog
from GUI.dialogs.window_dialog import WindowDialog


class MainWindow(QMainWindow):
    def __init__(self, state: AppState):
        super().__init__()
        self._state = state
        self.setWindowTitle("Satellite RFI Predictor")
        self.setMinimumSize(900, 600)

        self._build_ui()
        self._connect_state()

    def _connect_state(self):
        """Wire AppState signals to UI refresh methods."""
        self._state.state_changed.connect(self._refresh_ui)
        self._state.log_message.connect(self.log_view.append)
        self._state.analysis_complete.connect(self._on_analysis_done)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # --- Left panel ---
        left = QVBoxLayout()
        left.setSpacing(10)

        self.obs_btn = self._config_button("Observatory Selection\nNone Selected")
        self.targ_btn = self._config_button("Target Selection\nNone Selected")
        self.win_btn = self._config_button("Window Selection\nNone Selected")

        self.obs_btn.clicked.connect(self._select_observatory)
        self.targ_btn.clicked.connect(self._select_target)
        self.win_btn.clicked.connect(self._select_window)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset_state)
        left.addWidget(self.reset_btn) 

        self.compute_btn = QPushButton("Compute Interference")
        self.compute_btn.setEnabled(False)
        self.compute_btn.setFixedHeight(44)
        self.compute_btn.clicked.connect(self._run_analysis)

        left.addWidget(self.obs_btn)
        left.addWidget(self.targ_btn)
        left.addWidget(self.win_btn)
        left.addStretch()
        left.addWidget(self.compute_btn)

        # --- Right panel ---
        right = QVBoxLayout()

        self.tabs = QTabWidget()
        self.clean_stretches_view = QTextEdit()
        self.clean_stretches_view.setReadOnly(True)
        self.linked_groups_view = QTextEdit()
        self.linked_groups_view.setReadOnly(True)
        self.tabs.addTab(self.clean_stretches_view, "Clean Stretches")
        self.tabs.addTab(self.linked_groups_view, "Linked Groups")

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(120)
        self.log_view.setPlaceholderText("Log output will appear here...")
        self.log_view.setFont(QFont("Arial", 9))

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

        right.addWidget(self.tabs)
        right.addWidget(QLabel("Log"))
        right.addWidget(self.log_view)
        right.addLayout(export_row)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setFixedWidth(220)

        right_widget = QWidget()
        right_widget.setLayout(right)

        root.addWidget(left_widget)
        root.addWidget(right_widget)

    # --- UI helpers ---

    def _config_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(64)
        return btn

    def _refresh_ui(self):
        """Called whenever AppState changes — sync all UI to current state."""
        self.compute_btn.setEnabled(self._state.is_ready())

        if self._state.observatory:
            self.obs_btn.setText(f"Observatory Selection\n{self._state.observatory.name}")
        if self._state.target:
            self.targ_btn.setText(f"Target Selection\n{self._state.target.name}")
        else:
            self.targ_btn.setText("Target Selection\nNone")
        if self._state.window:
            start, end, gap = self._state.window
            from datetime import datetime
            delta = int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())
            h, m = delta // 3600, (delta % 3600) // 60
            s = delta % 60
            self.win_btn.setText(f"Window Selection\n{start}\n{h:02d}h{m:02d}m{s:02d}s")
        self.update()
        self.repaint()

    def _on_analysis_done(self, results):
        self.export_csv_btn.setEnabled(True)
        self.export_video_btn.setEnabled(True)
        gap = self._state.window[2]
        self.clean_stretches_view.setPlainText(results.analyser.clean_stretches_summary(gap))
        self.linked_groups_view.setPlainText(results.analyser.linked_groups_summary(gap))

    # --- Slots ---

    def _select_observatory(self):
        dlg = ObservatoryDialog(self)
        if dlg.exec():
            self._state.observatory = dlg.result()
            self._state.state_changed.emit()

    def _select_target(self):
        dlg = TargetDialog(self)
        if dlg.exec():
            self._state.target = dlg.result()
            self._state.state_changed.emit()

    def _select_window(self):
        dlg = WindowDialog(self)
        if dlg.exec():
            self._state.window = dlg.result()
            self._state.state_changed.emit()

    def _run_analysis(self):
        self._state.run_analysis()  #AppState owns this, not MainWindow

    def _export_csv(self):
        self._state.export_csv()

    def _export_video(self):
        self._state.export_video()
        
    def _reset_state(self):
        self._state.observatory = None
        self._state.target = None
        self._state.window = None
        self._state.window = None
        self._results = None
        self.obs_btn.setText("Observatory Selection\nNone Selected")
        self.targ_btn.setText("Target Selection\nNone Selected")
        self.win_btn.setText("Window Selection\nNone Selected")
        self.export_csv_btn.setEnabled(False)
        self.export_video_btn.setEnabled(False)
        self.clean_stretches_view.clear()
        self.linked_groups_view.clear()
        self.log_view.clear()
        self._state.state_changed.emit()