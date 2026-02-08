import math

def calculate_distance(point1, point2):
    """Return Euclidean distance between two points.

    Accepts 2D points (x, y) or 3D points (x, y, z). If a point has only
    two coordinates, `z` is assumed to be 0.
    """
    def as_xyz(p):
        try:
            ln = len(p)
        except TypeError:
            raise TypeError("point must be a sequence of length 2 or 3")

        if ln == 2:
            x, y = p
            z = 0
        elif ln >= 3:
            x, y, z = p[0], p[1], p[2]
        else:
            raise ValueError("point must have at least 2 coordinates")
        return x, y, z

    x1, y1, z1 = as_xyz(point1)
    x2, y2, z2 = as_xyz(point2)
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)