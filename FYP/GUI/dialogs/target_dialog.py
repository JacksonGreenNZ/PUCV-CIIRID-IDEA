from PyQt6.QtWidgets import QDialog

class TargetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

    def result(self):
        return None