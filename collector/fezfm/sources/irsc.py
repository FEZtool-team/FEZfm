"""IRSC: Iranian Seismological Center, Institute of Geophysics, University of Tehran.

Port of Faultiuo's ``update_irsc_catalog()`` / ``add2irsc()``: post the
bulletin search form, follow the "Printable Version" ``bul*.txt`` link, and
parse its fixed-width rows. Origin times in the bulletin are UTC (checked
against EMSC and USGS: the same events agree to within 1-2 s).

IRSC only accepts windows of a few days well; ``fetch`` splits longer ranges
into 10-day chunks, as Faultiuo does.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

import httpx

from ..model import Report

NAME = "irsc"
BASE = "http://irsc.ut.ac.ir/"
SEARCH_URL = BASE + "bulletin.php"
EVENT_URL = BASE + "newsview.php?&eventid={}&network=earth_ismc__"
CHUNK = timedelta(days=10)

_LINK = re.compile(r"""([\w./-]*bul\d+\.txt)""")
# NO. EventID Date Time Lat Long Depth Mag RMS N.S. N.P. GAP Comment
_ROW = re.compile(
    r"^\s*\d+\s+(?P<id>\d+)\s+(?P<date>\d{4}/\d{2}/\d{2})\s+(?P<time>\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)"
    r"\s+(?P<lat>-?\d+(?:\.\d+)?)\s+(?P<lon>-?\d+(?:\.\d+)?)\s+(?P<depth>-?\d+(?:\.\d+)?)"
    r"\s+(?P<mag>\d+(?:\.\d+)?)(?:\s+\S+\s+\d+\s+\d+\s+\d+)?\s*(?P<comment>.*?)\s*$"
)


def _parse_time(date: str, clock: str) -> datetime:
    # Seconds can read "60.0" in some catalogs; add them as a delta.
    h, m, s = clock.split(":")
    base = datetime.strptime(date, "%Y/%m/%d")
    return (base + timedelta(hours=int(h), minutes=int(m), seconds=float(s))).replace(microsecond=0)


def _place(comment: str) -> str | None:
    parts = [p.strip() for p in comment.split(",") if p.strip()]
    if not parts:
        return None
    return ", ".join(p[0].upper() + p[1:] for p in parts)


def find_bulletin_link(html: str) -> str | None:
    m = _LINK.search(html)
    return BASE + m.group(1).lstrip("./") if m else None


def parse_bulletin(text: str) -> list[Report]:
    out = []
    for line in text.splitlines():
        if "/" not in line:
            continue
        m = _ROW.match(line)
        if not m:
            continue
        out.append(
            Report(
                source=NAME,
                source_id=m["id"],
                time_utc=_parse_time(m["date"], m["time"]),
                lat=float(m["lat"]),
                lon=float(m["lon"]),
                depth_km=float(m["depth"]),
                mag=float(m["mag"]),
                mag_type=None,
                place=_place(m["comment"]),
                url=EVENT_URL.format(m["id"]),
            )
        )
    return out


def _form(start: datetime, end: datetime) -> dict:
    return {
        "start_Y": f"{start.year:04d}",
        "start_M": f"{start.month:02d}",
        "start_D": f"{start.day:02d}",
        "start_H": f"{start.hour:02d}",
        "end_Y": f"{end.year:04d}",
        "end_M": f"{end.month:02d}",
        "end_D": f"{end.day:02d}",
        "end_H": f"{end.hour:02d}",
        "action": "Search",
    }


def _fetch_chunk(client: httpx.Client, start: datetime, end: datetime) -> list[Report]:
    r = client.post(SEARCH_URL, data=_form(start, end))
    r.raise_for_status()
    html = r.content.decode("utf-8", errors="replace")
    link = find_bulletin_link(html)
    if link is None:
        # The search page renders without a link when nothing matched.
        if "Catalog Search" in html or "Origin Time" in html:
            return []
        raise RuntimeError("IRSC response had no bulletin link")
    b = client.get(link)
    b.raise_for_status()
    return parse_bulletin(b.content.decode("utf-8", errors="replace"))


def fetch(client: httpx.Client, start: datetime, end: datetime) -> list[Report]:
    reports: list[Report] = []
    t = start
    while t < end:
        t2 = min(t + CHUNK, end)
        # The form has hour resolution; widen by an hour so nothing is cut.
        reports += _fetch_chunk(client, t, t2 + timedelta(hours=1))
        t = t2
    return [r for r in reports if start <= r.time_utc <= end + timedelta(hours=1)]
