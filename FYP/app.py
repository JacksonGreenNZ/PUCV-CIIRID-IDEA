import sys
from PyQt6.QtWidgets import QApplication
from GUI.splash import SplashScreen
from GUI.main_window import MainWindow
from core.app_state import AppState
from os import environ
from pathlib import Path
Path("outputs").mkdir(exist_ok=True)
environ["QT_LOGGING_RULES"] = "qt.svg.draw=false"
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("outputs/rfi.log"),
    ]
)
import platform
import subprocess

def run():
    
    system = platform.system()
    release = platform.uname().release.lower()

    if system == "Linux" and "microsoft" in release:
        # WSL
        windows_host = subprocess.check_output("ip route show default | awk '{print $3}'", shell=True).decode().strip()
        environ["DISPLAY"] = f"{windows_host}:0"
    elif system == "Linux":
        # native Linux - display already set
        pass
    elif system == "Darwin":
        # macOS - nothing needed, Qt works natively
        pass
    elif system == "Windows":
        # native Windows - nothing needed
        pass
    
    environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    environ["QT_QPA_PLATFORM"] = "xcb"
    app = QApplication(sys.argv)
    state = AppState()
    
    splash = SplashScreen("active")
    splash.exec()  #blocks until accept()
    
    state.set_tle_file(splash.tle_file)  #grab result directly after exec
    
    window = MainWindow(state)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run()