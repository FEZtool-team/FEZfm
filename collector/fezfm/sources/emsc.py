"""EMSC (European-Mediterranean Seismological Centre) FDSN event service.

https://www.seismicportal.eu/fdsn-wsevent.html
EMSC also redistributes reports from Iranian agencies (IIEES, IRSC), so it
keeps Iranian coverage alive when IRSC itself cannot be reached.
"""

from __future__ import annotations

from datetime import datetime

import httpx

from ..model import IRAN_REGION, WORLD_MIN_MAG, Report
from . import get, iso

NAME = "emsc"
URL = "https://www.seismicportal.eu/fdsnws/event/1/query"
EVENT_URL = "https://www.seismicportal.eu/eventdetails.html?unid={}"

# ke = known earthquake, se = suspected earthquake; others are blasts etc.
EARTHQUAKE_TYPES = {None, "", "ke", "se"}


def _time(s: str) -> datetime:
    s = s.rstrip("Z")
    if "." in s:
        head, frac = s.split(".", 1)
        s = f"{head}.{frac[:6]}"
    return datetime.fromisoformat(s).replace(microsecond=0)


def parse(payload: dict) -> list[Report]:
    out = []
    for f in payload.get("features", []):
        p = f.get("properties") or {}
        if p.get("evtype") not in EARTHQUAKE_TYPES:
            continue
        if p.get("time") is None or p.get("lat") is None or p.get("lon") is None:
            continue
        unid = p.get("unid") or f.get("id")
        region = p.get("flynn_region")
        out.append(
            Report(
                source=NAME,
                source_id=str(unid),
                time_utc=_time(p["time"]),
                lat=float(p["lat"]),
                lon=float(p["lon"]),
                depth_km=float(p["depth"]) if p.get("depth") is not None else None,
                mag=float(p["mag"]) if p.get("mag") is not None else None,
                mag_type=p.get("magtype"),
                place=region.title() if region else None,
                url=EVENT_URL.format(unid),
            )
        )
    return out


def _query(client: httpx.Client, params: dict) -> list[Report]:
    r = get(client, URL, {"format": "json", "orderby": "time-asc", "limit": 20000, **params})
    if r.status_code == 204:  # FDSN "no data"
        return []
    r.raise_for_status()
    return parse(r.json())


def fetch(client: httpx.Client, start: datetime, end: datetime) -> list[Report]:
    window = {"starttime": iso(start), "endtime": iso(end)}
    region = {
        "minlat": IRAN_REGION["min_lat"],
        "maxlat": IRAN_REGION["max_lat"],
        "minlon": IRAN_REGION["min_lon"],
        "maxlon": IRAN_REGION["max_lon"],
    }
    reports = _query(client, {**window, **region})
    reports += _query(client, {**window, "minmag": WORLD_MIN_MAG})
    return reports
