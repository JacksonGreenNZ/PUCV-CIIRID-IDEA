from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QSpinBox, QWidget, QButtonGroup, QRadioButton, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QDateTime


class WindowDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Observation Window")
        self.setMinimumWidth(400)
        self._selected = None
        self._updating = False  # guard against recursive signal loops

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(10)

        # --- Start time ---
        self._start_edit = QDateTimeEdit()
        self._start_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._start_edit.setDateTime(QDateTime.currentDateTimeUtc())
        self._start_edit.setCalendarPopup(True)
        self._start_edit.dateTimeChanged.connect(self._on_start_changed)
        form.addRow("Start (UTC)", self._start_edit)

        # --- End mode toggle ---
        mode_row = QHBoxLayout()
        self._mode_end = QRadioButton("End Time")
        self._mode_dur = QRadioButton("Duration")
        self._mode_end.setChecked(True)
        mode_group = QButtonGroup(self)
        mode_group.addButton(self._mode_end)
        mode_group.addButton(self._mode_dur)
        self._mode_end.toggled.connect(self._on_mode_changed)
        mode_row.addWidget(self._mode_end)
        mode_row.addWidget(self._mode_dur)
        mode_row.addStretch()
        form.addRow("Mode", mode_row)

        # --- End time ---
        self._end_edit = QDateTimeEdit()
        self._end_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._end_edit.setDateTime(QDateTime.currentDateTimeUtc().addSecs(600))
        self._end_edit.setCalendarPopup(True)
        self._end_edit.dateTimeChanged.connect(self._on_end_changed)
        form.addRow("End (UTC)", self._end_edit)

        # --- Duration ---
        dur_row = QHBoxLayout()
        self._dur_h = self._int_spin(0, 23, suffix="h")
        self._dur_m = self._int_spin(0, 59, suffix="m")
        self._dur_s = self._int_spin(0, 59, suffix="s")
        self._dur_h.valueChanged.connect(self._on_duration_changed)
        self._dur_m.valueChanged.connect(self._on_duration_changed)
        self._dur_s.valueChanged.connect(self._on_duration_changed)
        dur_row.addWidget(self._dur_h)
        dur_row.addWidget(self._dur_m)
        dur_row.addWidget(self._dur_s)
        dur_row.addStretch()
        form.addRow("Duration", dur_row)

        # --- Gap tolerance ---
        self._gap_spin = self._int_spin(0, 3600, suffix=" s")
        self._gap_spin.setValue(30)
        self._gap_spin.setToolTip("Maximum gap between clean stretches before they are treated as separate windows")
        form.addRow("Gap Tolerance", self._gap_spin)

        root.addLayout(form)

        # --- Duration display (read-only hint when in end time mode) ---
        self._summary_label = QLabel()
        self._summary_label.setStyleSheet("color: grey; font-size: 10px;")
        root.addWidget(self._summary_label)

        root.addStretch()

        # --- Buttons ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setDefault(True)
        confirm_btn.clicked.connect(self._confirm)
        btn_row.addWidget(confirm_btn)
        root.addLayout(btn_row)

        self._on_mode_changed()
        self._update_summary()

    def _int_spin(self, min_val, max_val, suffix="") -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSuffix(suffix)
        spin.setFixedWidth(72)
        return spin

    def _on_mode_changed(self):
        end_mode = self._mode_end.isChecked()
        self._end_edit.setEnabled(end_mode)
        self._dur_h.setEnabled(not end_mode)
        self._dur_m.setEnabled(not end_mode)
        self._dur_s.setEnabled(not end_mode)
        # sync whichever field just became active
        if end_mode:
            self._sync_end_from_duration()
        else:
            self._sync_duration_from_end()
        self._update_summary()

    def _on_start_changed(self):
        if self._updating:
            return
        if self._mode_end.isChecked():
            self._update_summary()
        else:
            self._sync_end_from_duration()

    def _on_end_changed(self):
        if self._updating:
            return
        if self._mode_end.isChecked():
            self._sync_duration_from_end()
            self._update_summary()

    def _on_duration_changed(self):
        if self._updating:
            return
        if self._mode_dur.isChecked():
            self._sync_end_from_duration()

    def _sync_end_from_duration(self):
        self._updating = True
        total_secs = (
            self._dur_h.value() * 3600 +
            self._dur_m.value() * 60 +
            self._dur_s.value()
        )
        end = self._start_edit.dateTime().addSecs(total_secs)
        self._end_edit.setDateTime(end)
        self._update_summary()
        self._updating = False

    def _sync_duration_from_end(self):
        self._updating = True
        start = self._start_edit.dateTime()
        end = self._end_edit.dateTime()
        delta = start.secsTo(end)
        if delta < 0:
            delta = 0
        h = delta // 3600
        m = (delta % 3600) // 60
        s = delta % 60
        self._dur_h.setValue(h)
        self._dur_m.setValue(m)
        self._dur_s.setValue(s)
        self._updating = False

    def _update_summary(self):
        start = self._start_edit.dateTime()
        end = self._end_edit.dateTime()
        delta = start.secsTo(end)
        if delta <= 0:
            self._summary_label.setText("⚠ End time is not after start time")
            return
        h = delta // 3600
        m = (delta % 3600) // 60
        s = delta % 60
        self._summary_label.setText(f"Window duration: {h:02d}h {m:02d}m {s:02d}s")

    def _confirm(self):
        start = self._start_edit.dateTime()
        end = self._end_edit.dateTime()
        if start.secsTo(end) <= 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Window", "End time must be after start time.")
            return
        self._selected = (
            start.toString("yyyy-MM-ddTHH:mm:ss"),
            end.toString("yyyy-MM-ddTHH:mm:ss"),
            self._gap_spin.value(),
        )
        self.accept()

    def result(self):
        return self._selected