"""Country of an epicentre, for the site's country filter.

Uses the site's own Natural Earth basemap (web/public/layers/countries.geojson),
so the filter and the map agree. Offshore events get the nearest country within
NEAR_DEG (most are on its coast or trench); the rest return None (open ocean).
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from shapely import Point, STRtree
from shapely.geometry import shape

COUNTRIES_FILE = Path(__file__).resolve().parents[2] / "web" / "public" / "layers" / "countries.geojson"
NEAR_DEG = 1.5  # about 150 km


@cache
def _index() -> tuple[STRtree, list[str]]:
    data = json.loads(COUNTRIES_FILE.read_text())
    geoms, names = [], []
    for f in data["features"]:
        geoms.append(shape(f["geometry"]))
        names.append(f["properties"]["name"])
    return STRtree(geoms), names


def name(lat: float, lon: float) -> str | None:
    tree, names = _index()
    pt = Point(lon, lat)
    hits = tree.query(pt, predicate="intersects")
    if len(hits):
        return names[int(hits[0])]
    near = tree.query_nearest(pt, max_distance=NEAR_DEG)
    return names[int(near[0])] if len(near) else None
