from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtGui import QColor
from wire_path_lib.segments import Curve
import random

class Path(QObject):
    """
    Represents a single continuous wire path.
    This class manages a collection of connected segments that form a wire path.
    It provides methods for adding, removing, and manipulating segments, as well as
    calculating the path's total length and drawing the path.
    Attributes:
    segments (list): A list of Segment objects that make up the path.
    wire_diameter (float): The diameter of the wire used in this path.
    color_pool (list): A list of QColor objects used for coloring segments.
    """
    length_changed = Signal()

    def __init__(self):
        super().__init__()
        self.segments = []
        self.wire_diameter = 2.0  # Default wire diameter
        self.color_pool = [
            QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255),
            QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255),
            QColor(128, 0, 0), QColor(0, 128, 0), QColor(0, 0, 128),
            QColor(128, 128, 0), QColor(128, 0, 128), QColor(0, 128, 128)
        ]

    def calculate_length(self):
        """
        Calculate the total length of the path.
        Returns:
        float: The sum of the lengths of all segments in the path.
        """
        return sum(segment.calculate_length() for segment in self.segments)

    def draw(self, painter):
        """
        Draw the entire path using the provided painter.
        Args:
        painter (QPainter): The painter object to use for drawing.
        """
        for segment in self.segments:
            segment.draw(painter, self.wire_diameter)

    def add_segment(self, new_segment, at_beginning=False):
        """
        Add a new segment to the path.
        Args:
        new_segment (Segment): The segment to be added.
        at_beginning (bool): If True, add the segment at the start of the path.
        If False, add it at the end.
        """
        new_segment.color = self.get_unique_color()
        
        if at_beginning:
            if self.segments:
                new_segment.connect_to(self.segments[0], is_next=True)
            self.segments.insert(0, new_segment)
        else:
            if self.segments:
                self.segments[-1].connect_to(new_segment, is_next=True)
            self.segments.append(new_segment)
        
        self.length_changed.emit()

    def get_unique_color(self):
        """
        Get a unique color for a new segment.
        Returns:
        QColor: A color that is not currently used by adjacent segments.
        """
        used_colors = [segment.color for segment in self.segments]
        available_colors = [c for c in self.color_pool if c not in used_colors]
        return random.choice(available_colors) if available_colors else random.choice(self.color_pool)

    def move_segment(self, segment, point_type, new_pos):
        """
        Move a point in the specified segment.
        Args:
        segment (Segment): The segment containing the point to move.
        point_type (str): The type of point to move ('start', 'end', or 'control').
        new_pos (QPointF): The new position for the point.
        """
        segment.move_point(point_type, new_pos)
        self.length_changed.emit()

    def remove_segment(self, segment):
        """
        Remove a segment from the path.
        Args:
        segment (Segment): The segment to be removed.
        """
        if segment in self.segments:
            self.segments.remove(segment)
            segment.disconnect()
        self.length_changed.emit()

    def split(self, segment_index):
        new_path = Path()
        new_path.wire_diameter = self.wire_diameter

        # Split the segments
        new_path.segments = self.segments[segment_index + 1:]
        self.segments = self.segments[:segment_index + 1]

        # Disconnect the segments at the split point
        if self.segments and new_path.segments:
            last_segment = self.segments[-1]
            first_segment = new_path.segments[0]
            
            # Ensure all points are properly set for both paths
            if isinstance(last_segment, Curve):
                last_segment.end_point = last_segment.control_point
            if isinstance(first_segment, Curve):
                first_segment.start_point = first_segment.control_point
                first_segment.control_point = QPointF(
                    (first_segment.start_point.x() + first_segment.end_point.x()) / 2,
                    (first_segment.start_point.y() + first_segment.end_point.y()) / 2
                )
            
            last_segment.next = None
            first_segment.prev = None

        # Ensure all segments in the new path have their points set correctly
        for i, segment in enumerate(new_path.segments):
            if i > 0:
                segment.start_point = new_path.segments[i-1].end_point
            if isinstance(segment, Curve):
                if i == 0:  # First segment
                    segment.control_point = QPointF(
                        (segment.start_point.x() + segment.end_point.x()) / 2,
                        (segment.start_point.y() + segment.end_point.y()) / 2
                    )

        return new_path

    def set_wire_diameter(self, diameter):
        """
        Set the wire diameter for the path.
        Args:
        diameter (float): The new wire diameter.
        """
        self.wire_diameter = diameter
        self.length_changed.emit()

class PathCollection(QObject):
    """
    Manages a collection of Path objects.
    This class provides methods for manipulating multiple paths, including
    splitting paths, calculating total length, and importing paths.
    Attributes:
    paths (list): A list of Path objects.
    active_path_index (int): The index of the currently active path.
    """
    def __init__(self):
        super().__init__()
        self.paths = [Path()]

    def split_path(self, path_index, segment_index):
        """
        Split a path at the specified index.
        Args:
        path_index (int): The index of the path to split.
        segment_index (int): The index of the segment at which to split the path.
        """
        path = self.paths[path_index]
        new_path = path.split(segment_index)
        
        # Insert the new path after the current one
        self.paths.insert(path_index + 1, new_path)

        # If the split results in an empty path, remove it
        if not path.segments:
            self.paths.pop(path_index)
        if not new_path.segments:
            self.paths.pop(path_index + 1)

    def calculate_total_length(self):
        """
        Calculate the total length of all paths.
        Returns:
        float: The sum of the lengths of all paths.
        """
        return sum(path.calculate_length() for path in self.paths)

    def import_paths(self, imported_paths):
        """
        Import a list of paths, replacing the current paths.
        Args:
        imported_paths (list): A list of Path objects to import.
        """
        self.paths = imported_paths

    def get_add_points(self):
        add_points = []
        for path in self.paths:
            if path.segments:
                add_points.append(path.segments[0].start_point)
                add_points.append(path.segments[-1].end_point)
        return add_points
    
    def set_wire_diameter(self, diameter, path_index=None):
        """
        Set the wire diameter for all paths or a specific path.
        
        Args:
        diameter (float): The new wire diameter.
        path_index (int, optional): If provided, only update the specified path.
        """
        if path_index is not None and 0 <= path_index < len(self.paths):
            self.paths[path_index].set_wire_diameter(diameter)
        else:
            for path in self.paths:
                path.set_wire_diameter(diameter)