"""Cut the GEM Global Active Faults database to the FEZfm map region.

Source: https://github.com/GEMScienceTools/gem-global-active-faults (CC BY-SA 4.0).
Usage: python scripts/gem_subset.py gem_active_faults_harmonized.geojson ../web/public/layers/gem_active_faults.geojson
"""

import json
import sys

BOX = (38.0, 68.0, 20.0, 44.0)  # lon min/max, lat min/max: Iran region plus margin


def inside(c):
    return BOX[0] <= c[0] <= BOX[1] and BOX[2] <= c[1] <= BOX[3]


def main(src, dst):
    data = json.load(open(src))
    out = []
    for f in data["features"]:
        g = f.get("geometry")
        if not g:
            continue
        lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for line in lines:
            if any(inside(c) for c in line):
                p = f["properties"]
                out.append({
                    "type": "Feature",
                    "properties": {"slip_type": p.get("slip_type"), "catalog": p.get("catalog_name")},
                    "geometry": {"type": "LineString", "coordinates": [[round(c[0], 3), round(c[1], 3)] for c in line]},
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
