from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from wire_path_lib.path import PathCollection
from wire_path_lib.input_handler import InputHandler
from gui.ui_manager import UIManager

class SVGPathEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SVG Path Editor")
        self.setGeometry(100, 100, 800, 600)

        self.path_collection = PathCollection()
        self.input_handler = InputHandler(self.path_collection)
        self.ui_manager = UIManager(self)
        
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        self.ui_manager.setup_layout()
        self.setLayout(self.ui_manager.main_layout)

    def setup_connections(self):
        self.ui_manager.connect_buttons(self.input_handler)
        for path in self.path_collection.paths:
            path.length_changed.connect(self.ui_manager.update_length_labels)

    def paintEvent(self, event):
        self.ui_manager.paint_paths(self.path_collection.paths)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.input_handler.snip_mode:
                if self.input_handler.handle_snip(event.position()):
                    self.update()
            elif self.input_handler.add_mode:
                if self.input_handler.handle_add(event.position()):
                    self.update()
            else:
                if self.input_handler.start_dragging(event.position()):
                    self.update()

    def mouseMoveEvent(self, event):
        if self.input_handler.handle_dragging(event.position()):
            self.update()

    def mouseReleaseEvent(self, event):
        self.input_handler.stop_dragging()

    def update_cursor(self):
        if self.input_handler.add_mode:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)