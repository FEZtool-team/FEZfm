"""Small spherical-geometry helpers (no GIS dependencies)."""

from __future__ import annotations

import math

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def point_to_polyline_km(lat: float, lon: float, line: list[tuple[float, float]]) -> float:
    """Distance from a point to a polyline of (lon, lat) vertices.

    Uses a local equirectangular projection centred on the point, which is
    accurate to well under 1% at the 20-50 km buffer widths used here.
    """
    kx = math.cos(math.radians(lat)) * math.pi / 180 * EARTH_RADIUS_KM
    ky = math.pi / 180 * EARTH_RADIUS_KM
    pts = [((x - lon) * kx, (y - lat) * ky) for x, y in line]
    best = math.inf
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        seg2 = dx * dx + dy * dy
        t = 0.0 if seg2 == 0 else max(0.0, min(1.0, -(x1 * dx + y1 * dy) / seg2))
        cx, cy = x1 + t * dx, y1 + t * dy
        best = min(best, math.hypot(cx, cy))
    return best
