"""Build the plate boundary map layer from Bird (2003), PB2002.

Source: https://github.com/fraxen/tectonicplates (GeoJSON/PB2002_boundaries.json), ODC-BY 1.0.
Bird, P. (2003), An updated digital model of plate boundaries, G3, 4(3), 1027, doi:10.1029/2001GC000252.
Usage: python scripts/plates.py PB2002_boundaries.json ../web/public/layers/plate_boundaries.geojson

Keeps the boundary name (plate pair), whether it is a subduction zone, and rounds to 0.01 degrees.
"""

import json
import sys


def main(src, dst):
    data = json.load(open(src))
    out = []
    for f in data["features"]:
        p = f["properties"]
        coords = []
        for x, y, *_ in f["geometry"]["coordinates"]:
            c = [round(x, 2), round(y, 2)]
            if not coords or coords[-1] != c:
                coords.append(c)
        if len(coords) < 2:
            continue
        out.append({
            "type": "Feature",
            "properties": {"name": p["Name"], "subduction": p["Type"] == "subduction"},
            "geometry": {"type": "LineString", "coordinates": coords},
        })
    fc = {
        "type": "FeatureCollection",
        "attribution": "Plate boundaries: Bird (2003), PB2002, via github.com/fraxen/tectonicplates, ODC-BY 1.0",
        "features": out,
    }
    json.dump(fc, open(dst, "w"), separators=(",", ":"))
    print(len(out), "boundaries")


if __name__ == "__main__":
    main(*sys.argv[1:3])
