"""Build the self-hosted basemap from Natural Earth (public domain).

Source: https://github.com/nvkelso/natural-earth-vector (ne_50m_admin_0_countries.geojson).
Usage: python scripts/basemap.py ne_50m_admin_0_countries.geojson ../web/public/layers/countries.geojson

Keeps only the country name and rounds coordinates to 0.02 degrees (~2 km),
which is enough at the zoom levels the monitor uses and keeps the file small.
"""

import json
import sys

STEP = 0.02


def snap(v):
    return round(round(v / STEP) * STEP, 2)


def ring(coords):
    out = []
    for x, y, *_ in coords:
        p = [snap(x), snap(y)]
        if not out or out[-1] != p:
            out.append(p)
    return out if len(out) >= 4 else None


def main(src, dst):
    data = json.load(open(src))
    feats = []
    for f in data["features"]:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        kept = []
        for poly in polys:
            rings = [r for r in (ring(r) for r in poly) if r]
            if rings:
                kept.append(rings)
        if kept:
            feats.append({
                "type": "Feature",
                "properties": {"name": f["properties"].get("NAME_EN") or f["properties"].get("NAME")},
                "geometry": {"type": "MultiPolygon", "coordinates": kept},
            })
    json.dump({"type": "FeatureCollection", "attribution": "Natural Earth (public domain)", "features": feats},
              open(dst, "w"), separators=(",", ":"))
    print(len(feats), "countries")


if __name__ == "__main__":
    main(*sys.argv[1:3])
