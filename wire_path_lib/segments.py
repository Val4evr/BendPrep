from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath, QPen
from PySide6.QtCore import Qt
import math

class Segment:
    """
    Base class for wire segments.

    This abstract class defines the common interface and properties
    for all types of wire segments (e.g., lines and curves).

    Attributes:
        start_point (QPointF): The starting point of the segment.
        end_point (QPointF): The ending point of the segment.
        prev (Segment): The previous segment in the wire path.
        next (Segment): The next segment in the wire path.
        color (QColor): The color of the segment.
    """
    def __init__(self, start_point, end_point):
        """
        Initialize a new Segment.

        Args:
            start_point (QPointF): The starting point of the segment.
            end_point (QPointF): The ending point of the segment.
        """
        self.start_point = start_point
        self.end_point = end_point
        self.prev = None
        self.next = None
        self.color = None

    def connect_to(self, other_segment, is_next=True):
        """
        Connect this segment to another segment.

        Args:
            other_segment (Segment): The segment to connect to.
            is_next (bool): If True, connect as the next segment. If False, connect as the previous segment.
        """
        if is_next:
            self.next = other_segment
            other_segment.prev = self
            other_segment.start_point = self.end_point
        else:
            self.prev = other_segment
            other_segment.next = self
            self.start_point = other_segment.end_point

    def disconnect(self):
        """
        Disconnect this segment from its neighboring segments.
        """
        if self.prev:
            self.prev.next = None
            self.prev = None
        if self.next:
            self.next.prev = None
            self.next = None

    def calculate_length(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def draw(self, painter, wire_diameter):
        raise NotImplementedError("Subclass must implement abstract method")

    def hit_test(self, point):
        raise NotImplementedError("Subclass must implement abstract method")

    def move_point(self, point_type, new_pos):
        raise NotImplementedError("Subclass must implement abstract method")
    
    def get_segment_midpoint(self):
        raise NotImplementedError("Subclass must implement abstract method")

class Line(Segment):
    """
    Represents a straight line segment in the wire path.

    This class inherits from Segment and implements the methods
    for drawing, hit testing, and moving points specific to a line.
    """
    def draw(self, painter, wire_diameter):
        """
        Draw the line segment on a QPainter.

        Args:
            painter (QPainter): The painter to draw on.
            wire_diameter (float): The diameter of the wire.
        """
        pen = QPen(self.color, wire_diameter)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self.start_point, self.end_point)

    def hit_test(self, point):
        """
        Test if a point is near this line segment.

        Args:
            point (QPointF): The point to test.

        Returns:
            str or None: 'start' if near the start point, 'end' if near the end point, or None if not near.
        """
        if (point - self.start_point).manhattanLength() < 10:
            return 'start'
        if (point - self.end_point).manhattanLength() < 10:
            return 'end'
        return None

    def move_point(self, point_type, new_pos):
        """
        Move a point of the line segment.

        Args:
            point_type (str): The type of point to move ('start' or 'end').
            new_pos (QPointF): The new position for the point.
        """
        if point_type == 'start':
            self.start_point = new_pos
            if self.prev:
                self.prev.end_point = new_pos
        elif point_type == 'end':
            self.end_point = new_pos
            if self.next:
                self.next.start_point = new_pos
    
    def calculate_length(self):
        """
        Returns the length of the line segment.
        """
        return math.sqrt((self.end_point.x() - self.start_point.x())**2 + 
                         (self.end_point.y() - self.start_point.y())**2)
    
    def get_segment_midpoint(self):
        """
        Calculate the midpoint of the line segment.

        Returns:
            QPointF: The midpoint of the line segment.
        """
        return (self.start_point + self.end_point) / 2

class Curve(Segment):
    """
    Represents a curved segment in the wire path.

    This class inherits from Segment and implements the methods
    for drawing, hit testing, and moving points specific to a quadratic Bezier curve.

    Attributes:
        control_point (QPointF): The control point of the quadratic Bezier curve.
    """
    def __init__(self, start_point, control_point, end_point):
        """
        Initialize a new Curve segment.

        Args:
            start_point (QPointF): The starting point of the curve.
            control_point (QPointF): The control point of the curve.
            end_point (QPointF): The ending point of the curve.
        """
        super().__init__(start_point, end_point)
        self.control_point = control_point

    def draw(self, painter, wire_diameter):
        """
        Draw the curve segment on a QPainter.

        Args:
            painter (QPainter): The painter to draw on.
            wire_diameter (float): The diameter of the wire.
        """
        pen = QPen(self.color, wire_diameter)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        path = QPainterPath()
        path.moveTo(self.start_point)
        path.quadTo(self.control_point, self.end_point)
        painter.drawPath(path)

    def calculate_length(self):
        """
        Calculate the approximate length of the curve.

        This method uses a series of line segments to approximate the curve's length.

        Returns:
            float: The approximate length of the curve.
        """
        steps = 20
        length = 0
        last_point = self.start_point
        for i in range(1, steps + 1):
            t = i / steps
            point = self.bezier_point(t)
            length += math.sqrt((point.x() - last_point.x())**2 + (point.y() - last_point.y())**2)
            last_point = point
        return length

    def hit_test(self, point):
        """
        Test if a point is near this curve segment.

        Args:
            point (QPointF): The point to test.

        Returns:
            str or None: 'start' if near the start point, 'control' if near the control point,
                         'end' if near the end point, or None if not near any point.
        """
        if (point - self.start_point).manhattanLength() < 10:
            return 'start'
        if (point - self.control_point).manhattanLength() < 10:
            return 'control'
        if (point - self.end_point).manhattanLength() < 10:
            return 'end'
        return None

    def move_point(self, point_type, new_pos):
        """
        Move a point of the curve segment.

        Args:
            point_type (str): The type of point to move ('start', 'control', or 'end').
            new_pos (QPointF): The new position for the point.
        """
        if point_type == 'start':
            self.start_point = new_pos
            if self.prev:
                self.prev.end_point = new_pos
        elif point_type == 'control':
            self.control_point = new_pos
        elif point_type == 'end':
            self.end_point = new_pos
            if self.next:
                self.next.start_point = new_pos

    def bezier_point(self, t):
        """
        Calculate a point on the quadratic Bezier curve.

        Args:
            t (float): The parameter value, between 0 and 1.

        Returns:
            QPointF: A point on the curve corresponding to the given t value.
        """
        return (1-t)**2 * self.start_point + 2*(1-t)*t * self.control_point + t**2 * self.end_point
    
    def get_segment_midpoint(self):
        """
        Calculate the approximate midpoint of the curve segment.

        Returns:
            QPointF: The approximate midpoint of the curve segment.
        """
        return (self.start_point + 2*self.control_point + self.end_point) / 4