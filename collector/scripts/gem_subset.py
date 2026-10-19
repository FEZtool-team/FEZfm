"""Cut the GEM Global Active Faults database down to a small worldwide map layer.

Source: https://github.com/GEMScienceTools/gem-global-active-faults (CC BY-SA 4.0).
Usage: python scripts/gem_subset.py gem_active_faults_harmonized.geojson ../web/public/layers/gem_active_faults.geojson

Keeps every fault worldwide (folds are dropped), with only the slip type and catalog.
Traces are simplified to about 1 km outside the Iran region and 300 m inside it.
"""

import json
import sys

REGION = (38.0, 68.0, 20.0, 44.0)  # lon min/max, lat min/max: Iran region plus margin
TOLERANCE = 0.01  # degrees, about 1 km
REGION_TOLERANCE = 0.003
FOLDS = {"Anticline", "Syncline"}


def inside(c):
    return REGION[0] <= c[0] <= REGION[1] and REGION[2] <= c[1] <= REGION[3]


def simplify(pts, tol):
    """Douglas-Peucker on lon/lat pairs."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x0, y0), (x1, y1) = pts[a], pts[b]
        dx, dy = x1 - x0, y1 - y0
        norm = (dx * dx + dy * dy) ** 0.5
        far, idx = 0.0, -1
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * (x - x0) - dx * (y - y0)) / norm if norm else ((x - x0) ** 2 + (y - y0) ** 2) ** 0.5
            if d > far:
                far, idx = d, i
        if far > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def main(src, dst):
    data = json.load(open(src))
    out = []
    for f in data["features"]:
        g = f.get("geometry")
        p = f["properties"]
        if not g or p.get("slip_type") in FOLDS:
            continue
        lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for line in lines:
            pts = [(c[0], c[1]) for c in line]
            tol = REGION_TOLERANCE if any(inside(c) for c in pts) else TOLERANCE
            coords = []
            for x, y in simplify(pts, tol):
                c = [round(x, 3), round(y, 3)]
                if not coords or coords[-1] != c:
                    coords.append(c)
            if len(coords) < 2:
                continue
            out.append({
                "type": "Feature",
                "properties": {"slip_type": p.get("slip_type"), "catalog": p.get("catalog_name")},
                "geometry": {"type": "LineString", "coordinates": coords},
            })
    fc = {
        "type": "FeatureCollection",
        "attribution": "GEM Global Active Faults Database, CC BY-SA 4.0, github.com/GEMScienceTools/gem-global-active-faults",
        "features": out,
    }
    json.dump(fc, open(dst, "w"), separators=(",", ":"))
    print(len(out), "lines")


if __name__ == "__main__":
    main(*sys.argv[1:3])
