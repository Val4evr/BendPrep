from svgpathtools import svg2paths, Path as SvgPath, Line as SvgLine, QuadraticBezier, wsvg
from wire_path_lib.path import Path
from wire_path_lib.segments import Line, Curve
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

def import_svg(file_path):
    paths, attributes = svg2paths(file_path)
    
    imported_paths = []
    for svg_path, attr in zip(paths, attributes):
        path = Path()
        path.wire_diameter = float(attr.get('stroke-width', 2.0))
        color = attr.get('stroke', '#000000')
        
        current_point = None
        prev_segment = None
        for segment in svg_path:
            start = segment.start
            end = segment.end
            
            if current_point is None:
                current_point = QPointF(start.real, start.imag)
            
            end_point = QPointF(end.real, end.imag)
            
            if segment.__class__.__name__ == 'Line':
                new_segment = Line(current_point, end_point)
            elif segment.__class__.__name__ in ['CubicBezier', 'QuadraticBezier']:
                control = segment.control1 if hasattr(segment, 'control1') else segment.control
                control_point = QPointF(control.real, control.imag)
                new_segment = Curve(current_point, control_point, end_point)
            else:
                continue
            
            new_segment.color = QColor(color)
            
            # Connect the new segment to the previous one
            if prev_segment:
                prev_segment.connect_to(new_segment, is_next=True)
            
            path.segments.append(new_segment)
            current_point = end_point
            prev_segment = new_segment
        
        imported_paths.append(path)
    
    return imported_paths

def save_svg(file_path, paths):
    svg_paths = []
    attributes = []
    
    for path in paths:
        svg_segments = []
        for segment in path.segments:
            start = complex(segment.start_point.x(), segment.start_point.y())
            end = complex(segment.end_point.x(), segment.end_point.y())
            
            if isinstance(segment, Line):
                svg_segments.append(SvgLine(start, end))
            elif isinstance(segment, Curve):
                control = complex(segment.control_point.x(), segment.control_point.y())
                svg_segments.append(QuadraticBezier(start, control, end))
        
        svg_paths.append(SvgPath(*svg_segments))
        
        attributes.append({
            'stroke': segment.color.name(),  # Use the color of the last segment
            'stroke-width': str(path.wire_diameter),
            'fill': 'none'
        })
    
    wsvg(svg_paths, attributes=attributes, filename=file_path)