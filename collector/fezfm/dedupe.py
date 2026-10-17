"""Merge reports from several sources into one event per earthquake.

Two reports describe the same earthquake when their origin times are within
MAX_DT, epicentres within MAX_KM, and magnitudes within MAX_DMAG. Agencies
locate the same event a few seconds and a few tens of km apart (IRSC vs
USGS/EMSC for the 16 Oct 2026 Minab events: 1-2 s, 5-25 km, 0.1-0.3 mag).

The preferred report supplies the event's location and magnitude. Inside the
Iran region IRSC is preferred, the same priority Faultiuo gives it in
gen_final_eq_df(); elsewhere USGS, then EMSC.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from . import faults
from .geo import haversine_km
from .model import Report, in_iran_region

MAX_DT = timedelta(seconds=45)
MAX_KM = 80.0
MAX_DMAG = 1.0

PRIORITY_REGION = ("irsc", "usgs", "emsc")
PRIORITY_WORLD = ("usgs", "emsc", "irsc")

# "Significant": M5+ anywhere, or M4+ in the Iran region.
SIG_WORLD = 5.0
SIG_REGION = 4.0

# "Sequence": at least SEQ_N events within SEQ_KM over the SEQ_WINDOW
# ending at an event (that event included). This covers aftershock sequences
# and swarms alike; the flag does not try to tell them apart.
SEQ_N = 5
SEQ_KM = 25.0
SEQ_WINDOW = timedelta(hours=6)


@dataclass
class Event:
    reports: list[Report] = field(default_factory=list)

    @property
    def anchor(self) -> Report:
        return self.reports[0]

    @property
    def preferred(self) -> Report:
        a = self.anchor
        order = PRIORITY_REGION if in_iran_region(a.lat, a.lon) else PRIORITY_WORLD
        return min(self.reports, key=lambda r: (order.index(r.source) if r.source in order else 99))

    def matches(self, r: Report) -> bool:
        if any(x.source == r.source for x in self.reports):
            return False
        for x in self.reports:
            if abs(x.time_utc - r.time_utc) > MAX_DT:
                continue
            if haversine_km(x.lat, x.lon, r.lat, r.lon) > MAX_KM:
                continue
            if x.mag is not None and r.mag is not None and abs(x.mag - r.mag) > MAX_DMAG:
                continue
            return True
        return False


def cluster(reports: list[Report]) -> list[Event]:
    """Greedy time-ordered clustering; each source contributes at most one report per event."""
    events: list[Event] = []
    active: list[Event] = []
    for r in sorted(reports, key=lambda r: r.time_utc):
        active = [e for e in active if r.time_utc - e.reports[-1].time_utc <= MAX_DT]
        candidates = [e for e in active if e.matches(r)]
        if candidates:
            best = min(
                candidates,
                key=lambda e: min(
                    haversine_km(x.lat, x.lon, r.lat, r.lon) + abs((x.time_utc - r.time_utc).total_seconds())
                    for x in e.reports
                ),
            )
            best.reports.append(r)
        else:
            e = Event([r])
            events.append(e)
            active.append(e)
    return events


def _display_place(e: Event) -> str | None:
    p = e.preferred
    if p.place:
        return p.place
    for r in e.reports:
        if r.place:
            return r.place
    return None


def to_rows(events: list[Event]) -> list[dict]:
    zones = faults.load_zones()
    rows = []
    for e in events:
        p = e.preferred
        region = in_iran_region(p.lat, p.lon)
        zone, dist = faults.tag(p.lat, p.lon, zones) if region else (None, None)
        ordered = sorted(e.reports, key=lambda r: (r is not p, r.source))
        rows.append(
            {
                "event_id": f"{p.source}:{p.source_id}",
                "time_utc": p.time_utc,
                "lat": p.lat,
                "lon": p.lon,
                "depth_km": p.depth_km,
                "mag": p.mag,
                "mag_type": p.mag_type,
                "place": _display_place(e),
                "preferred_source": p.source,
                "sources": [r.source for r in ordered],
                "urls": [r.url or "" for r in ordered],
                "in_iran_region": region,
                "fault_zone": zone,
                "fault_distance_km": dist,
                "significant": p.mag is not None and p.mag >= (SIG_REGION if region else SIG_WORLD),
                "sequence": False,
            }
        )
    mark_sequences(rows)
    return rows


def mark_sequences(rows: list[dict]) -> None:
    rows.sort(key=lambda r: r["time_utc"])
    start = 0
    for i, r in enumerate(rows):
        t: datetime = r["time_utc"]
        while rows[start]["time_utc"] < t - SEQ_WINDOW:
            start += 1
        near = [
            j
            for j in range(start, i + 1)
            if haversine_km(rows[j]["lat"], rows[j]["lon"], r["lat"], r["lon"]) <= SEQ_KM
        ]
        if len(near) >= SEQ_N:
            for j in near:
                rows[j]["sequence"] = True
