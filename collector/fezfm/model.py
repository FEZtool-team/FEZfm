"""Shared record types and region constants."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

# IRSC's own search box, "Iran and adjacent areas" (lat 24-41, lon 42-64).
# Faultiuo uses the same box for its IRSC catalog.
IRAN_REGION = {"min_lat": 24.0, "max_lat": 41.0, "min_lon": 42.0, "max_lon": 64.0}

# Outside the Iran region only events at or above this magnitude are kept,
# so the world feed stays readable.
WORLD_MIN_MAG = 2.5

SOURCES = ("irsc", "usgs", "emsc")


def in_iran_region(lat: float, lon: float) -> bool:
    r = IRAN_REGION
    return r["min_lat"] <= lat <= r["max_lat"] and r["min_lon"] <= lon <= r["max_lon"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


@dataclass(frozen=True)
class Report:
    """One earthquake as reported by one source. Times are naive UTC."""

    source: str
    source_id: str
    time_utc: datetime
    lat: float
    lon: float
    depth_km: float | None
    mag: float | None
    mag_type: str | None
    place: str | None
    url: str | None

    def keep(self) -> bool:
        """Region events are always kept; elsewhere only M >= WORLD_MIN_MAG."""
        if in_iran_region(self.lat, self.lon):
            return True
        return self.mag is not None and self.mag >= WORLD_MIN_MAG
