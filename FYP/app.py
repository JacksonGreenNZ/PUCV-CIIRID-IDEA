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

def run():
    environ["QT_QPA_PLATFORM"] = "xcb"
    environ["QT_QUICK_BACKEND"] = "software"
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion') #fixes linux painting issue?
    state = AppState()
    
    splash = SplashScreen("active")
    splash.exec()  #blocks until accept()
    
    state.set_tle_file(splash.tle_file)  #grab result directly after exec
    
    window = MainWindow(state)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run()