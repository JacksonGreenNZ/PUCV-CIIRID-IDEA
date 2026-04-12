import multiprocessing
multiprocessing.freeze_support()

import sys
import logging
import platform
import subprocess
from os import environ
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from core.app_state import AppState
from core.paths import get_base_dir, get_asset_path
from enums.tle_group import TLEGroup
from GUI.splash import SplashScreen
from GUI.main_window import MainWindow

# --- Environment setup (must happen before QApplication) ---
environ["QT_LOGGING_RULES"] = "qt.svg.draw=false"
environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"

system = platform.system()
release = platform.uname().release.lower()
if system == "Linux" and "microsoft" in release:
    route_output = subprocess.check_output(["ip", "route", "show", "default"])
    windows_host = route_output.decode().split()[2]
    environ["DISPLAY"] = f"{windows_host}:0"
    environ["QT_QPA_PLATFORM"] = "xcb"
elif system == "Linux":
    environ["QT_QPA_PLATFORM"] = "xcb"

# --- Directory and logging setup ---
base = get_base_dir()
Path(base / "outputs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(base / "outputs" / "rfi.log"),
    ]
)


def run():
    app = QApplication(sys.argv)

    if system == "Windows":
        icon_path = get_asset_path("GUI/icons/icon.ico")
    elif system == "Darwin":
        icon_path = get_asset_path("GUI/icons/MyIcon.icns")
    else:
        icon_path = get_asset_path("GUI/icons/linux_icon/hicolor/256x256/apps/ClearSkyRFI.png")
    app.setWindowIcon(QIcon(icon_path))

    state = AppState()

    splash = SplashScreen(TLEGroup.ACTIVE)
    splash.exec()

    state.set_tle_file(splash.tle_file)

    window = MainWindow(state)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()