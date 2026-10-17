"""Turn merged events into feed items (headline plus flags) for the site and Atom feed."""

from __future__ import annotations

from datetime import datetime

SOURCE_LABELS = {"irsc": "IRSC", "usgs": "USGS", "emsc": "EMSC"}


def z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def headline(ev: dict) -> str:
    mag = f"M{ev['mag']:.1f} earthquake" if ev.get("mag") is not None else "Earthquake"
    place = ev.get("place")
    text = f"{mag}, {place}" if place else mag
    if ev.get("fault_zone"):
        text += f", {zone_label(ev['fault_zone'])} fault zone"
    return text


def zone_label(name: str) -> str:
    return "-".join(p.capitalize() for p in name.split("-")).replace("Ne-", "NE ")


def summary(ev: dict) -> str:
    parts = []
    if ev.get("depth_km") is not None:
        parts.append(f"Depth {ev['depth_km']:.0f} km")
    parts.append(ev["time_utc"].strftime("%Y-%m-%d %H:%M UTC"))
    parts.append("Reported by " + ", ".join(SOURCE_LABELS.get(s, s) for s in ev["sources"]))
    return ". ".join(parts) + "."


def item(ev: dict) -> dict:
    """Compact JSON record consumed by the web app."""
    return {
        "id": ev["event_id"],
        "t": z(ev["time_utc"]),
        "lat": round(ev["lat"], 3),
        "lon": round(ev["lon"], 3),
        "depth": None if ev["depth_km"] is None else round(ev["depth_km"], 1),
        "mag": None if ev["mag"] is None else round(ev["mag"], 1),
        "magType": ev["mag_type"],
        "place": ev["place"],
        "headline": headline(ev),
        "src": ev["preferred_source"],
        "sources": [{"name": s, "url": u or None} for s, u in zip(ev["sources"], ev["urls"])],
        "region": ev["in_iran_region"],
        "zone": ev["fault_zone"],
        "zoneKm": ev["fault_distance_km"],
        "sig": ev["significant"],
        "sequence": ev["sequence"],
    }


def notable(ev: dict) -> bool:
    """Events that go into the Atom feed."""
    if ev["significant"] or ev["sequence"]:
        return True
    return ev["in_iran_region"] and ev["mag"] is not None and ev["mag"] >= 3.5
