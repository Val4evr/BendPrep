import numpy as np
import trimesh
import svgwrite
from scipy.interpolate import splprep, splev
import argparse
from multiprocessing import Pool, cpu_count

def closest_point_between_lines(p1, v1, p2, v2):
    n = np.cross(v1, v2)
    n1 = np.cross(v1, n)
    n2 = np.cross(v2, n)
    
    c1 = p1 + (np.dot(p2 - p1, n2) / np.dot(v1, n2)) * v1
    c2 = p2 + (np.dot(p1 - p2, n1) / np.dot(v2, n1)) * v2
    
    return (c1 + c2) / 2, np.linalg.norm(c1 - c2)

def process_chunk(args):
    chunk, all_centroids, all_normals, max_distance = args
    local_center_points = []
    for i in chunk:
        p1, v1 = all_centroids[i], all_normals[i]
        for j in range(i + 1, len(all_centroids)):
            p2, v2 = all_centroids[j], all_normals[j]
            if np.linalg.norm(p1 - p2) > max_distance * 10:
                continue
            intersection_point, distance = closest_point_between_lines(p1, v1, p2, v2)
            if distance < max_distance:
                local_center_points.append(intersection_point)
    return np.array(local_center_points)

def extract_centerline(mesh, max_distance, sample_size=1000):
    facet_normals = mesh.face_normals
    facet_centroids = mesh.triangles_center

    if len(facet_centroids) > sample_size:
        indices = np.random.choice(len(facet_centroids), sample_size, replace=False)
        facet_normals = facet_normals[indices]
        facet_centroids = facet_centroids[indices]

    num_processes = cpu_count()
    chunk_size = len(facet_centroids) // num_processes
    chunks = [range(i, min(i + chunk_size, len(facet_centroids))) for i in range(0, len(facet_centroids), chunk_size)]
    
    with Pool(num_processes) as pool:
        results = pool.map(process_chunk, [(chunk, facet_centroids, facet_normals, max_distance) for chunk in chunks])

    center_points = np.vstack(results)

    center_points = np.unique(center_points.round(decimals=5), axis=0)

    pca = trimesh.transformations.principal_axes(center_points)
    projected = np.dot(center_points - np.mean(center_points, axis=0), pca[0])
    sorted_indices = np.argsort(projected)
    center_points = center_points[sorted_indices]

    diffs = np.diff(center_points, axis=0)
    distances = np.linalg.norm(diffs, axis=1)
    wire_diameter = np.median(distances)

    return center_points, wire_diameter

def fit_bezier_spline(points, max_error, wire_diameter):
    normalized_error = max_error * wire_diameter / 100
    tck, u = splprep(points.T, s=normalized_error**2, k=3)
    num_points = len(points) * 2
    smooth_points = np.column_stack(splev(np.linspace(0, 1, num_points), tck))
    return smooth_points, (num_points - 1) // 3

def create_svg(centerline, output_file, scale):
    min_x, min_y, _ = np.min(centerline, axis=0)
    max_x, max_y, _ = np.max(centerline, axis=0)
    width = (max_x - min_x) * scale
    height = (max_y - min_y) * scale
    padding = max(width, height) * 0.1
    
    dwg = svgwrite.Drawing(output_file, size=(f"{width+2*padding}mm", f"{height+2*padding}mm"))
    
    scaled_points = [(scale * (x - min_x) + padding, scale * (y - min_y) + padding) for x, y, _ in centerline]
    
    path = dwg.path(d=f"M{scaled_points[0][0]},{scaled_points[0][1]}", stroke="black", fill="none", stroke_width=0.5*scale)
    
    for i in range(1, len(scaled_points), 3):
        if i+2 < len(scaled_points):
            path.push(f"C{scaled_points[i][0]},{scaled_points[i][1]} "
                      f"{scaled_points[i+1][0]},{scaled_points[i+1][1]} "
                      f"{scaled_points[i+2][0]},{scaled_points[i+2][1]}")
    
    dwg.add(path)
    dwg.save()

def stl_to_svg_wire(stl_file, svg_file, scale, max_error, sample_size):
    mesh = trimesh.load_mesh(stl_file)
    max_distance = np.linalg.norm(mesh.bounding_box.extents) * 0.01
    
    centerline, wire_diameter = extract_centerline(mesh, max_distance, sample_size)
    smooth_centerline, num_bezier_curves = fit_bezier_spline(centerline, max_error, wire_diameter)
    create_svg(smooth_centerline, svg_file, scale)
    
    print(f"Wire diameter: {wire_diameter:.4f} units")
    print(f"Number of Bezier curves in the spline: {num_bezier_curves}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert STL wire model to SVG centerline")
    parser.add_argument("input_stl", help="Input STL file")
    parser.add_argument("output_svg", help="Output SVG file")
    parser.add_argument("--scale", type=float, default=1.0, help="Scale factor for the output SVG (default: 1.0)")
    parser.add_argument("--error", type=float, default=5.0, help="Maximum error as a percentage of wire diameter (default: 5.0)")
    parser.add_argument("--sample_size", type=int, default=1000, help="Number of facets to sample (default: 1000)")
    
    args = parser.parse_args()
    
    try:
        stl_to_svg_wire(args.input_stl, args.output_svg, args.scale, args.error, args.sample_size)
        print(f"SVG file created: {args.output_svg}")
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)