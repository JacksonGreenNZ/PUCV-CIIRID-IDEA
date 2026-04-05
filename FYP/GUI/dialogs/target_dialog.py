import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QListWidget, QLabel,
    QSpinBox, QDoubleSpinBox, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from core.app_state import Target

SAVED_TARGETS_FILE = Path("data/targets.json")


class TargetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Target")
        self.setMinimumSize(600, 400)
        self._selected: Target | None = None
        self._saved: list[Target] = self._load_saved()

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(16, 16, 16, 16)

        # --- Left: saved list ---
        left = QVBoxLayout()
        left.addWidget(QLabel("Saved Targets"))

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_list_select)
        left.addWidget(self._list)

        self._search_btn = QPushButton("Search Catalogue...")
        self._search_btn.setEnabled(False)
        self._search_btn.setToolTip("Online target catalogue — coming soon")
        left.addWidget(self._search_btn)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setFixedWidth(200)

        # --- Right: entry form ---
        right = QVBoxLayout()
        right.addWidget(QLabel("Target Details"))

        form = QFormLayout()
        form.setSpacing(8)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Vela Pulsar")

        # RA: HH MM SS.ss
        ra_row = QHBoxLayout()
        self._ra_h = self._int_spin(0, 23, suffix="h")
        self._ra_m = self._int_spin(0, 59, suffix="m")
        self._ra_s = self._float_spin(0, 59.999, suffix="s")
        ra_row.addWidget(self._ra_h)
        ra_row.addWidget(self._ra_m)
        ra_row.addWidget(self._ra_s)
        ra_row.addStretch()

        # Dec: +/- DD MM SS.ss
        dec_row = QHBoxLayout()
        self._dec_sign = QPushButton("+")
        self._dec_sign.setFixedWidth(32)
        self._dec_sign.setCheckable(True)
        self._dec_sign.clicked.connect(self._toggle_dec_sign)
        self._dec_d = self._int_spin(0, 90, suffix="°")
        self._dec_m = self._int_spin(0, 59, suffix="'")
        self._dec_s = self._float_spin(0, 59.999, suffix="\"")
        dec_row.addWidget(self._dec_sign)
        dec_row.addWidget(self._dec_d)
        dec_row.addWidget(self._dec_m)
        dec_row.addWidget(self._dec_s)
        dec_row.addStretch()

        form.addRow("Name", self._name_edit)
        form.addRow("Right Ascension", ra_row)
        form.addRow("Declination", dec_row)

        right.addLayout(form)
        right.addStretch()

        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("Save Target")
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setEnabled(False)
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setDefault(True)

        self._save_btn.clicked.connect(self._save_current)
        self._delete_btn.clicked.connect(self._delete_selected)
        confirm_btn.clicked.connect(self._confirm)

        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(confirm_btn)
        right.addLayout(btn_row)

        root.addWidget(left_widget)
        root.addLayout(right)

    def _int_spin(self, min_val, max_val, suffix="") -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSuffix(suffix)
        spin.setFixedWidth(72)
        return spin

    def _float_spin(self, min_val, max_val, suffix="") -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(2)
        spin.setSuffix(suffix)
        spin.setFixedWidth(88)
        return spin

    def _toggle_dec_sign(self):
        self._dec_sign.setText("-" if self._dec_sign.isChecked() else "+")

    # --- Conversion helpers ---

    def _get_ra_hours(self) -> float:
        return self._ra_h.value() + self._ra_m.value() / 60 + self._ra_s.value() / 3600

    def _get_dec_degrees(self) -> float:
        val = self._dec_d.value() + self._dec_m.value() / 60 + self._dec_s.value() / 3600
        return -val if self._dec_sign.isChecked() else val

    def _set_ra_hours(self, ra: float):
        h = int(ra)
        m = int((ra - h) * 60)
        s = ((ra - h) * 60 - m) * 60
        self._ra_h.setValue(h)
        self._ra_m.setValue(m)
        self._ra_s.setValue(round(s, 2))

    def _set_dec_degrees(self, dec: float):
        negative = dec < 0
        dec = abs(dec)
        d = int(dec)
        m = int((dec - d) * 60)
        s = ((dec - d) * 60 - m) * 60
        self._dec_sign.setChecked(negative)
        self._dec_sign.setText("-" if negative else "+")
        self._dec_d.setValue(d)
        self._dec_m.setValue(m)
        self._dec_s.setValue(round(s, 2))

    # --- List ---

    def _refresh_list(self):
        self._list.clear()
        for t in self._saved:
            self._list.addItem(t.name)

    def _on_list_select(self, row: int):
        if row < 0:
            self._delete_btn.setEnabled(False)
            return
        t = self._saved[row]
        self._name_edit.setText(t.name)
        self._set_ra_hours(t.ra_hours)
        self._set_dec_degrees(t.dec_degrees)
        self._delete_btn.setEnabled(True)

    def _current_target(self) -> Target | None:
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for this target.")
            return None
        return Target(
            name=name,
            ra_hours=self._get_ra_hours(),
            dec_degrees=self._get_dec_degrees(),
        )

    def _save_current(self):
        target = self._current_target()
        if not target:
            return
        self._saved = [t for t in self._saved if t.name != target.name]
        self._saved.append(target)
        self._persist()
        self._refresh_list()

    def _delete_selected(self):
        row = self._list.currentRow()
        if row < 0:
            return
        self._saved.pop(row)
        self._persist()
        self._refresh_list()
        self._delete_btn.setEnabled(False)

    def _confirm(self):
        target = self._current_target()
        if not target:
            return
        self._selected = target
        self.accept()

    def result(self) -> Target | None:
        return self._selected

    # --- Persistence ---

    def _persist(self):
        SAVED_TARGETS_FILE.parent.mkdir(exist_ok=True)
        with open(SAVED_TARGETS_FILE, "w") as f:
            json.dump([self._target_to_dict(t) for t in self._saved], f, indent=2)

    def _load_saved(self) -> list[Target]:
        if not SAVED_TARGETS_FILE.exists():
            return []
        try:
            with open(SAVED_TARGETS_FILE) as f:
                return [self._target_from_dict(d) for d in json.load(f)]
        except Exception:
            return []

    @staticmethod
    def _target_to_dict(t: Target) -> dict:
        return {"name": t.name, "ra_hours": t.ra_hours, "dec_degrees": t.dec_degrees}

    @staticmethod
    def _target_from_dict(d: dict) -> Target:
        return Target(**d)