from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                               QLabel, QFileDialog, QWidget)
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QPointF
import utils.svg_io as svg_io

class UIManager:
    def __init__(self, parent):
        self.parent = parent
        self.main_layout = QVBoxLayout()
        self.length_labels = []
        self.wire_diameter_inputs = []
        self.wire_diameter_layout = QVBoxLayout()

    def setup_layout(self):
        top_layout = QVBoxLayout()
        
        self.setup_wire_diameter_input(top_layout)
        self.setup_length_display(top_layout)
        self.setup_buttons(top_layout)
        
        self.main_layout.addLayout(top_layout)
        
        # Add a stretching widget to push everything to the top
        self.main_layout.addStretch(1)

    def setup_wire_diameter_input(self, layout):
        diameter_layout = QHBoxLayout()
        diameter_label = QLabel("Wire Diameter:")
        diameter_label.setStyleSheet("color: black;")
        diameter_layout.addWidget(diameter_label)
        
        initial_diameter = str(self.parent.path_collection.paths[0].wire_diameter) if self.parent.path_collection.paths else "2.0"
        self.diameter_input = QLineEdit(initial_diameter)
        self.diameter_input.setMaximumWidth(50)
        self.diameter_input.setStyleSheet("color: black; background-color: white;")
        self.diameter_input.textChanged.connect(self.update_wire_diameter)
        diameter_layout.addWidget(self.diameter_input)
        diameter_layout.addStretch()
        layout.addLayout(diameter_layout)

    def setup_length_display(self, layout):
        self.length_layout = QVBoxLayout()
        layout.addLayout(self.length_layout)

    def setup_buttons(self, layout):
        button_layout = QHBoxLayout()
        self.line_button = QPushButton("Line")
        self.curve_button = QPushButton("Curve")
        self.snip_button = QPushButton("Snip")
        self.save_button = QPushButton("Save SVG")
        self.import_button = QPushButton("Import SVG")
        button_layout.addWidget(self.line_button)
        button_layout.addWidget(self.curve_button)
        button_layout.addWidget(self.snip_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.import_button)
        layout.addLayout(button_layout)

    def connect_buttons(self, input_handler):
        self.line_button.clicked.connect(lambda: self.set_add_mode(input_handler, "line"))
        self.curve_button.clicked.connect(lambda: self.set_add_mode(input_handler, "curve"))
        self.snip_button.clicked.connect(self.toggle_snip_mode)
        self.save_button.clicked.connect(self.save_svg)
        self.import_button.clicked.connect(self.import_svg)
        self.diameter_input.textChanged.connect(self.update_wire_diameter)

    def set_add_mode(self, input_handler, mode):
        input_handler.set_add_mode(mode)
        self.snip_button.setStyleSheet("")
        self.parent.update_cursor()
        self.parent.update()

    def toggle_snip_mode(self):
        self.parent.input_handler.toggle_snip_mode()
        self.snip_button.setStyleSheet("background-color: red;" if self.parent.input_handler.snip_mode else "")
        self.parent.update_cursor()
        self.parent.update()

    def update_wire_diameter(self, text):
        new_diameter = float(text)
        if new_diameter > 0:
            self.parent.path_collection.set_wire_diameter(new_diameter)
            self.update_length_labels()  # Update length labels to reflect the new wire diameter
        else:
            print("Wire diameter must be a positive number.")
        
    
    def update_wire_diameter_inputs(self):
        # Clear existing inputs
        for widget in self.wire_diameter_inputs:
            self.wire_diameter_layout.removeWidget(widget)
            widget.deleteLater()
        self.wire_diameter_inputs.clear()

        # Create new inputs for each path
        for i, path in enumerate(self.parent.path_collection.paths):
            diameter_layout = QHBoxLayout()
            diameter_label = QLabel(f"Path {i+1} Wire Diameter:")
            diameter_label.setStyleSheet("color: black;")
            diameter_layout.addWidget(diameter_label)
            
            diameter_input = QLineEdit(str(path.wire_diameter))
            diameter_input.setMaximumWidth(50)
            diameter_input.setStyleSheet("color: black; background-color: white;")
            diameter_input.textChanged.connect(lambda text, p=path: self.update_wire_diameter(p, text))
            diameter_layout.addWidget(diameter_input)
            
            diameter_layout.addStretch()
            
            widget = QWidget()
            widget.setLayout(diameter_layout)
            self.wire_diameter_layout.addWidget(widget)
            self.wire_diameter_inputs.append(widget)
        # Clear existing 


    def update_length_labels(self):
        for label in self.length_labels:
            self.length_layout.removeWidget(label)
            label.deleteLater()
        self.length_labels.clear()

        for i, path in enumerate(self.parent.path_collection.paths):
            length = path.calculate_length()
            label = QLabel(f"Path {i+1} Length: {length:.2f} units")
            label.setStyleSheet("color: black;")  # Ensure text is black
            self.length_layout.addWidget(label)
            self.length_labels.append(label)

        total_length = self.parent.path_collection.calculate_total_length()
        total_label = QLabel(f"Total Length: {total_length:.2f} units")
        total_label.setStyleSheet("color: black;")  # Ensure text is black
        self.length_layout.addWidget(total_label)
        self.length_labels.append(total_label)

    def paint_paths(self, paths):
        painter = QPainter(self.parent)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.parent.rect(), Qt.white)

        for path in paths:
            path.draw(painter)

        for path in paths:
            for segment in path.segments:
                painter.setPen(QPen(segment.color, 1))
                painter.setBrush(segment.color.lighter(150))
                painter.drawEllipse(segment.start_point, 5, 5)
                painter.drawEllipse(segment.end_point, 5, 5)
                if hasattr(segment, 'control_point'):
                    painter.drawEllipse(segment.control_point, 5, 5)

        self.paint_add_points(painter)
        self.paint_snip_points(painter)

        painter.end()

    def paint_add_points(self, painter):
        if self.parent.input_handler.add_mode:
            painter.setPen(QPen(Qt.green, 2))
            painter.setBrush(QColor(0, 255, 0, 100))
            for path in self.parent.path_collection.paths:
                if path.segments:
                    self.paint_add_point(painter, path.segments[0].start_point)
                    self.paint_add_point(painter, path.segments[-1].end_point)
                else:
                    # For empty paths, you might want to add a default point
                    self.paint_add_point(painter, QPointF(0, 0))
    
    def paint_add_point(self, painter, point):
        segment_length = self.get_segment_length(point)
        size = min(10, max(5, segment_length / 10))
        painter.drawEllipse(point, size, size)
        painter.drawLine(point + QPointF(-size/2, 0), point + QPointF(size/2, 0))
        painter.drawLine(point + QPointF(0, -size/2), point + QPointF(0, size/2))


    def paint_snip_points(self, painter):
        if self.parent.input_handler.snip_mode:
            painter.setPen(QPen(Qt.red, 2))
            painter.setBrush(QColor(255, 0, 0, 100))
            for path in self.parent.path_collection.paths:
                for segment in path.segments:
                    midpoint = segment.get_segment_midpoint()
                    segment_length = segment.calculate_length()
                    size = min(10, max(5, segment_length / 10))
                    painter.drawEllipse(midpoint, size, size)
                    painter.drawLine(midpoint + QPointF(-size/2, -size/2), midpoint + QPointF(size/2, size/2))
                    painter.drawLine(midpoint + QPointF(-size/2, size/2), midpoint + QPointF(size/2, -size/2))

    def get_segment_length(self, point):
        for path in self.parent.path_collection.paths:
            for segment in path.segments:
                if segment.start_point == point or segment.end_point == point:
                    return segment.calculate_length()
        return 50

    def save_svg(self):
        file_path, _ = QFileDialog.getSaveFileName(self.parent, "Save SVG", "", "SVG Files (*.svg)")
        if file_path:
            svg_io.save_svg(file_path, self.parent.path_collection.paths)

    def import_svg(self):
        file_path, _ = QFileDialog.getOpenFileName(self.parent, "Import SVG", "", "SVG Files (*.svg)")
        if file_path:
            imported_paths = svg_io.import_svg(file_path)
            if imported_paths:
                self.parent.path_collection.import_paths(imported_paths)
                
                # Update wire diameter inputs
                self.update_wire_diameter_inputs()
                
                self.parent.update()

