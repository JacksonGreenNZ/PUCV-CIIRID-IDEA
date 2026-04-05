import sys
from PyQt6.QtWidgets import QApplication
from GUI.splash import SplashScreen
from GUI.main_window import MainWindow
from core.app_state import AppState

def run():
    app = QApplication(sys.argv)
    
    state = AppState()
    
    splash = SplashScreen("starlink")
    splash.exec()  #blocks until accept()
    
    state.set_tle_file(splash.tle_file)  #grab result directly after exec
    
    window = MainWindow(state)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run()