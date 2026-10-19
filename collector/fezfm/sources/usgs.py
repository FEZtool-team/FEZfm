"""USGS FDSN event service (global).

https://earthquake.usgs.gov/fdsnws/event/1/
Two queries per window: the Iran region at any magnitude, and the world at
M >= WORLD_MIN_MAG. Overlap is harmless because rows are keyed by event id.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..model import IRAN_REGION, WORLD_MIN_MAG, Report
from . import get, iso

NAME = "usgs"
URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def parse(payload: dict) -> list[Report]:
    out = []
    for f in payload.get("features", []):
        p = f.get("properties") or {}
        if p.get("type") not in (None, "earthquake"):
            continue
        coords = (f.get("geometry") or {}).get("coordinates") or []
        if len(coords) < 2 or p.get("time") is None:
            continue
        t = datetime.fromtimestamp(p["time"] // 1000, tz=timezone.utc).replace(tzinfo=None)
        out.append(
            Report(
                source=NAME,
                source_id=str(f["id"]),
                time_utc=t,
                lat=float(coords[1]),
                lon=float(coords[0]),
                depth_km=float(coords[2]) if len(coords) > 2 and coords[2] is not None else None,
                mag=float(p["mag"]) if p.get("mag") is not None else None,
                mag_type=p.get("magType"),
                place=p.get("place"),
                url=p.get("url"),
            )
        )
    return out


def _query(client: httpx.Client, params: dict) -> list[Report]:
    r = get(client, URL, {"format": "geojson", "orderby": "time-asc", "limit": 20000, **params})
    if r.status_code == 204:
        return []
    r.raise_for_status()
    return parse(r.json())


def fetch(client: httpx.Client, start: datetime, end: datetime) -> list[Report]:
    window = {"starttime": iso(start), "endtime": iso(end)}
    region = {
        "minlatitude": IRAN_REGION["min_lat"],
        "maxlatitude": IRAN_REGION["max_lat"],
        "minlongitude": IRAN_REGION["min_lon"],
        "maxlongitude": IRAN_REGION["max_lon"],
    }
    reports = _query(client, {**window, **region})
    reports += _query(client, {**window, "minmagnitude": WORLD_MIN_MAG})
    return reports
