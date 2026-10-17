"""The 21 monitored fault zones from Faultiuo, and event-to-zone tagging.

Faultiuo reads each zone's trace from ``~/GMTdata/KML/Time_Section/<Name>.kml``
(first <coordinates> block) and buffers it by 20, 40 or 50 km. Those KML files
are not published, so ``data/fault_zones.geojson`` ships *approximate* traces
drawn from the published locations of each fault system, with Faultiuo's
buffer widths. Every feature carries ``approximate: true`` until it is
replaced from the original KML with ``fezfm import-kml <dir>``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .geo import point_to_polyline_km

ZONES_FILE = Path(__file__).parent / "data" / "fault_zones.geojson"

# name -> (KML file name, half-width km), from Faultiuo get_base_faults().
FAULTIUO_ZONES = {
    "AVAJ": ("Avaj.kml", 20),
    "BAM-RAVAR": ("Bam-Ravar.kml", 20),
    "DAMAVAND": ("Damavand.kml", 20),
    "DEHSHIR": ("Dehshir.kml", 20),
    "IPAK": ("Ipak.kml", 20),
    "KAZEROON": ("Kazeroon.kml", 20),
    "KERMAN": ("Kerman.kml", 20),
    "KOPEDAGH": ("Kopedagh.kml", 40),
    "KUHBANAN": ("Kuhbanan.kml", 20),
    "NE-LUT": ("NE_Lut.kml", 20),
    "NEYSHABUR": ("Neyshabur.kml", 20),
    "QOM": ("Qom.kml", 20),
    "SEMNAN": ("Semnan.kml", 20),
    "SEIMARE": ("Seimare.kml", 50),
    "SHAHRUD": ("Shahrud.kml", 20),
    "SABZVAR": ("Sabzvar.kml", 20),
    "TEHRAN": ("Tehran.kml", 20),
    "TURKMANCHAY": ("Turkmanchay.kml", 20),
    "VAN-TABRIZ": ("Van_Tabriz.kml", 20),
    "WEST-LUT": ("West_Lut.kml", 20),
    "ZAGROS": ("Zagros.kml", 50),
}


@dataclass(frozen=True)
class Zone:
    name: str
    width_km: float
    line: tuple[tuple[float, float], ...]  # (lon, lat)
    approximate: bool


@lru_cache(maxsize=1)
def load_zones(path: Path = ZONES_FILE) -> tuple[Zone, ...]:
    data = json.loads(path.read_text())
    return tuple(
        Zone(
            name=f["properties"]["name"],
            width_km=float(f["properties"]["width_km"]),
            line=tuple((float(x), float(y)) for x, y, *_ in f["geometry"]["coordinates"]),
            approximate=bool(f["properties"].get("approximate", False)),
        )
        for f in data["features"]
    )


def tag(lat: float, lon: float, zones: tuple[Zone, ...] | None = None) -> tuple[str | None, float | None]:
    """Return (zone name, distance km) of the nearest zone whose buffer holds the point."""
    best: tuple[str | None, float | None] = (None, None)
    for z in zones if zones is not None else load_zones():
        d = point_to_polyline_km(lat, lon, list(z.line))
        if d <= z.width_km and (best[1] is None or d < best[1]):
            best = (z.name, round(d, 1))
    return best


_COORDS = re.compile(r"<coordinates>(.*?)</coordinates>", re.S)


def kml_first_trace(text: str) -> list[tuple[float, float]]:
    """Port of Faultiuo extract_kml_coordinates(): first <coordinates> block only."""
    m = _COORDS.search(text)
    if not m:
        raise ValueError("no <coordinates> in KML")
    pts = []
    for xyz in m.group(1).split():
        parts = xyz.split(",")
        if len(parts) > 1:
            pts.append((float(parts[0]), float(parts[1])))
    return pts


def import_kml(kml_dir: Path, path: Path = ZONES_FILE) -> list[str]:
    """Replace approximate traces with Faultiuo's KML traces where files exist."""
    data = json.loads(path.read_text())
    by_name = {f["properties"]["name"]: f for f in data["features"]}
    replaced = []
    for name, (fname, width) in FAULTIUO_ZONES.items():
        kml = kml_dir / fname
        if not kml.exists():
            continue
        line = kml_first_trace(kml.read_text())
        by_name[name] = {
            "type": "Feature",
            "properties": {"name": name, "width_km": width, "approximate": False, "source": f"Faultiuo {fname}"},
            "geometry": {"type": "LineString", "coordinates": [[round(x, 4), round(y, 4)] for x, y in line]},
        }
        replaced.append(name)
    data["features"] = [by_name[n] for n in FAULTIUO_ZONES if n in by_name]
    path.write_text(json.dumps(data, indent=1) + "\n")
    load_zones.cache_clear()
    return replaced
