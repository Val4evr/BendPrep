from PySide6.QtCore import QPointF
from wire_path_lib.segments import Line, Curve
import math
from wire_path_lib.path import Path

class InputHandler:
    """
    Manages user input for manipulating wire paths.
    This class handles various user interactions such as adding segments,
    snipping paths, and dragging points. It works in conjunction with
    a PathCollection to modify the wire paths based on user input.
    Attributes:
    path_collection (PathCollection): The collection of paths being manipulated.
    add_mode (str): The current add mode ('line', 'curve', or None).
    snip_mode (bool): Whether snip mode is active.
    add_points (list): Points where new segments can be added.
    dragging_segment (Segment): The segment currently being dragged.
    dragging_point_type (str): The type of point being dragged.
    """

    def __init__(self, path_collection):
        self.path_collection = path_collection
        self.add_mode = None
        self.snip_mode = False
        self.add_points = []
        self.dragging_segment = None
        self.dragging_point_type = None

    def set_add_mode(self, mode):
        self.add_mode = mode
        self.snip_mode = False

    def toggle_snip_mode(self):
        self.snip_mode = not self.snip_mode
        self.add_mode = None

    def handle_snip(self, position):
        for path_index, path in enumerate(self.path_collection.paths):
            for segment_index, segment in enumerate(path.segments):
                midpoint = segment.get_segment_midpoint()
                if (position - midpoint).manhattanLength() < 10:
                    # Remove the segment
                    path.remove_segment(segment)
                    
                    # Split the path
                    self.path_collection.split_path(path_index, segment_index - 1)
                    return True
        return False

    def handle_add(self, position):
        if self.add_mode:
            for path in self.path_collection.paths:
                if not path.segments:
                    self.add_segment(position, path)
                    return True
                if (position - path.segments[0].start_point).manhattanLength() < 10:
                    self.add_segment(path.segments[0].start_point, path, at_beginning=True)
                    return True
                if (position - path.segments[-1].end_point).manhattanLength() < 10:
                    self.add_segment(path.segments[-1].end_point, path)
                    return True
            # If no existing path end points are clicked, create a new path
            new_path = Path()
            self.path_collection.paths.append(new_path)
            self.add_segment(position, new_path)
            return True
        return False

    def add_segment(self, start_point, path, at_beginning=False):
        if at_beginning:
            direction = -1
            end_point = start_point - QPointF(100, 0)
        else:
            direction = 1
            if path.segments:
                last_segment = path.segments[-1]
                dir_vector = last_segment.end_point - last_segment.start_point
                angle = math.atan2(dir_vector.y(), dir_vector.x())
                end_point = start_point + QPointF(100 * math.cos(angle), 100 * math.sin(angle))
            else:
                end_point = start_point + QPointF(100, 0)
        
        if self.add_mode == "line":
            new_segment = Line(start_point, end_point)
        else:  # Curve
            control_point = QPointF(
                (start_point.x() + end_point.x()) / 2,
                (start_point.y() + end_point.y()) / 2 + direction * 50
            )
            new_segment = Curve(start_point, control_point, end_point)
        
        path.add_segment(new_segment, at_beginning)
        self.add_mode = None

    def start_dragging(self, position):
        for path in self.path_collection.paths:
            for segment in path.segments:
                drag_type = segment.hit_test(position)
                if drag_type:
                    self.dragging_segment = segment
                    self.dragging_point_type = drag_type
                    return True
        return False

    def handle_dragging(self, position):
        if self.dragging_segment:
            # Find the path that contains the dragging segment
            for path in self.path_collection.paths:
                if self.dragging_segment in path.segments:
                    path.move_segment(self.dragging_segment, self.dragging_point_type, position)
                    return True
        return False

    def stop_dragging(self):
        """
        Stop the current dragging action.
        """
        self.dragging_segment = None
        self.dragging_point_type = None