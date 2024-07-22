from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from gui.svg_editor import SVGPathEditor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wire Bender")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        
        self.svg_editor = SVGPathEditor()
        layout.addWidget(self.svg_editor)

        # TODO: Add other widgets and menus as needed