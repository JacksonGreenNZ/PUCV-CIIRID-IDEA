import sys
from PyQt6.QtWidgets import QApplication
from GUI.splash import SplashScreen
from GUI.main_window import MainWindow


def run():
    app = QApplication(sys.argv)

    main_window = MainWindow()

    splash = SplashScreen("starlink")
    splash.ready.connect(main_window.set_tle_file)
    splash.ready.connect(lambda: main_window.show())
    splash.exec() #blocks until accept() is called

    sys.exit(app.exec()) #then starts main event loop


if __name__ == "__main__":
    run()