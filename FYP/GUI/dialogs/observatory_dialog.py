import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QListWidget, QLabel,
    QDoubleSpinBox, QWidget, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt
from core.app_state import Observatory

SAVED_OBSERVATORIES_FILE = Path("data/observatories.json")


class ObservatoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Observatory")
        self.setMinimumSize(600, 400)
        self._selected: Observatory | None = None
        self._saved: list[Observatory] = self._load_saved()

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(16, 16, 16, 16)

        # --- Left: saved list ---
        left = QVBoxLayout()
        left.addWidget(QLabel("Saved Locations"))

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_list_select)
        left.addWidget(self._list)

        # placeholder for future web search
        self._search_btn = QPushButton("Search Database...")
        self._search_btn.setEnabled(False)  # not yet implemented
        self._search_btn.setToolTip("Online observatory database — coming soon")
        left.addWidget(self._search_btn)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setFixedWidth(200)

        # --- Right: entry form ---
        right = QVBoxLayout()
        right.addWidget(QLabel("Observatory Details"))

        form = QFormLayout()
        form.setSpacing(8)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Warkworth 30m")

        self._lat_spin = self._coord_spin(-90, 90)
        self._lon_spin = self._coord_spin(-180, 180)
        self._elev_spin = self._coord_spin(-500, 9000, decimals=1, suffix=" m")
        self._dish_spin = self._coord_spin(0, 999, decimals=2, suffix=" m")
        self._freq_spin = self._coord_spin(0, 1e6, decimals=3, suffix=" MHz", step=1.0)

        form.addRow("Name", self._name_edit)
        form.addRow("Latitude (°)", self._lat_spin)
        form.addRow("Longitude (°)", self._lon_spin)
        form.addRow("Elevation (m, set 0 if unknown)", self._elev_spin)
        form.addRow("Dish Diameter (m)", self._dish_spin)
        form.addRow("Frequency (MHz)", self._freq_spin)

        right.addLayout(form)
        right.addStretch()

        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("Save Location")
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

    def _coord_spin(self, min_val, max_val, decimals=6, suffix="", step=None) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(decimals)
        spin.setSuffix(suffix)
        if step:
            spin.setSingleStep(step)
        return spin

    def _refresh_list(self):
        self._list.clear()
        for obs in self._saved:
            self._list.addItem(obs.name)

    def _on_list_select(self, row: int):
        if row < 0:
            self._delete_btn.setEnabled(False)
            return
        obs = self._saved[row]
        self._name_edit.setText(obs.name)
        self._lat_spin.setValue(obs.latitude)
        self._lon_spin.setValue(obs.longitude)
        self._elev_spin.setValue(obs.elevation_m)
        self._dish_spin.setValue(obs.dish_diameter_m)
        self._freq_spin.setValue(obs.frequency_hz)
        self._delete_btn.setEnabled(True)

    def _current_observatory(self) -> Observatory | None:
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for this observatory.")
            return None
        return Observatory(
            name=name,
            latitude=self._lat_spin.value(),
            longitude=self._lon_spin.value(),
            elevation_m=self._elev_spin.value(),
            dish_diameter_m=self._dish_spin.value(),
            frequency_hz=self._freq_spin.value() * 1e6,
        )

    def _save_current(self):
        obs = self._current_observatory()
        if not obs:
            return
        # overwrite if name already exists
        self._saved = [o for o in self._saved if o.name != obs.name]
        self._saved.append(obs)
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
        obs = self._current_observatory()
        if not obs:
            return
        self._selected = obs
        self.accept()

    def result(self) -> Observatory | None:
        return self._selected

    # --- Persistence ---

    def _persist(self):
        SAVED_OBSERVATORIES_FILE.parent.mkdir(exist_ok=True)
        with open(SAVED_OBSERVATORIES_FILE, "w") as f:
            json.dump([self._obs_to_dict(o) for o in self._saved], f, indent=2)

    def _load_saved(self) -> list[Observatory]:
        if not SAVED_OBSERVATORIES_FILE.exists():
            return []
        try:
            with open(SAVED_OBSERVATORIES_FILE) as f:
                return [self._obs_from_dict(d) for d in json.load(f)]
        except Exception:
            return []

    @staticmethod
    def _obs_to_dict(obs: Observatory) -> dict:
        return {
            "name": obs.name,
            "latitude": obs.latitude,
            "longitude": obs.longitude,
            "elevation_m": obs.elevation_m,
            "dish_diameter_m": obs.dish_diameter_m,
            "frequency_hz": obs.frequency_hz,
        }

    @staticmethod
    def _obs_from_dict(d: dict) -> Observatory:
        return Observatory(**d)