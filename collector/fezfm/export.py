"""Write the static data files the FEZfm site reads (web/public/data)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

import duckdb

from . import countries, db, faults, feed
from .model import IRAN_REGION, SOURCES, WORLD_MIN_MAG, utcnow

WINDOWS = {"2h": timedelta(hours=2), "24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}
FEED_WINDOW = timedelta(days=7)
SCHEDULE_MINUTES = 30

EVENT_COLUMNS = [
    "event_id", "time_utc", "lat", "lon", "depth_km", "mag", "mag_type", "place", "preferred_source",
    "sources", "urls", "in_iran_region", "fault_zone", "fault_distance_km", "significant", "sequence",
]


def _events(con: duckdb.DuckDBPyConnection, since: datetime) -> list[dict]:
    rows = con.execute(
        f"SELECT {', '.join(EVENT_COLUMNS)} FROM events WHERE time_utc >= ? ORDER BY time_utc DESC",
        [since],
    ).fetchall()
    return [_with_country(dict(zip(EVENT_COLUMNS, r))) for r in rows]


def _with_country(e: dict) -> dict:
    e["country"] = countries.name(e["lat"], e["lon"])
    return e


def _daily(con: duckdb.DuckDBPyConnection, now: datetime) -> list[dict]:
    rows = con.execute(
        """
        SELECT CAST(time_utc AS DATE) AS day,
               count(*) FILTER (WHERE in_iran_region)            AS region,
               count(*) FILTER (WHERE NOT in_iran_region)        AS world,
               count(*) FILTER (WHERE significant)               AS significant
        FROM events WHERE time_utc >= ? GROUP BY day ORDER BY day
        """,
        [now - timedelta(days=30)],
    ).fetchall()
    return [{"day": str(d), "region": r, "world": w, "significant": s} for d, r, w, s in rows]


def _archive(con: duckdb.DuckDBPyConnection, out_dir: Path, now: datetime) -> list[dict]:
    """One JSON and one CSV file per calendar month (UTC), plus an index, for the archive page."""
    arc = out_dir / "archive"
    arc.mkdir(exist_ok=True)
    months = con.execute(
        """
        SELECT strftime(time_utc, '%Y-%m') AS month, count(*) AS events,
               count(*) FILTER (WHERE in_iran_region) AS region, count(*) FILTER (WHERE significant) AS significant
        FROM events GROUP BY month ORDER BY month DESC
        """
    ).fetchall()
    index = []
    for month, n, region, sig in months:
        start = datetime.strptime(month, "%Y-%m")
        end = (start + timedelta(days=32)).replace(day=1)
        rows = con.execute(
            f"SELECT {', '.join(EVENT_COLUMNS)} FROM events WHERE time_utc >= ? AND time_utc < ? ORDER BY time_utc DESC",
            [start, end],
        ).fetchall()
        events = [feed.item(_with_country(dict(zip(EVENT_COLUMNS, r)))) for r in rows]
        (arc / f"{month}.json").write_text(json.dumps({"month": month, "events": events}, separators=(",", ":")))
        query = f"""SELECT event_id, strftime(time_utc, '%Y-%m-%dT%H:%M:%SZ') AS time_utc, lat, lon, depth_km, mag,
                    mag_type, place, preferred_source, array_to_string(sources, ';') AS sources, in_iran_region,
                    fault_zone, fault_distance_km, significant, sequence
                    FROM events WHERE time_utc >= TIMESTAMP '{start.isoformat(sep=' ')}'
                    AND time_utc < TIMESTAMP '{end.isoformat(sep=' ')}' ORDER BY time_utc DESC"""
        con.execute(f"COPY ({query}) TO '{arc / f'{month}.csv'}' (HEADER, DELIMITER ',')")
        index.append({"month": month, "events": n, "region": region, "significant": sig})
    (arc / "index.json").write_text(json.dumps({"generated_at": feed.z(now), "months": index}, separators=(",", ":")))
    return index


def _geojson(events: list[dict]) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": e["event_id"],
                "geometry": {"type": "Point", "coordinates": [e["lon"], e["lat"], e["depth_km"]]},
                "properties": {
                    "time": feed.z(e["time_utc"]),
                    "mag": e["mag"],
                    "mag_type": e["mag_type"],
                    "depth_km": e["depth_km"],
                    "place": e["place"],
                    "country": e["country"],
                    "preferred_source": e["preferred_source"],
                    "sources": e["sources"],
                    "in_iran_region": e["in_iran_region"],
                    "fault_zone": e["fault_zone"],
                    "significant": e["significant"],
                    "sequence": e["sequence"],
                },
            }
            for e in events
        ],
    }


def _atom(events: list[dict], now: datetime, site_url: str) -> str:
    entries = []
    for e in events[:100]:
        link = next((u for u in e["urls"] if u), site_url)
        entries.append(
            f"""  <entry>
    <id>urn:fezfm:{escape(e['event_id'])}</id>
    <title>{escape(feed.headline(e))}</title>
    <updated>{feed.z(e['time_utc'])}</updated>
    <link href="{escape(link)}"/>
    <summary>{escape(feed.summary(e))}</summary>
    <georss:point xmlns:georss="http://www.georss.org/georss">{e['lat']:.3f} {e['lon']:.3f}</georss:point>
  </entry>"""
        )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>{escape(site_url)}</id>
  <title>FEZfm earthquake monitor</title>
  <subtitle>Significant earthquakes worldwide and M3.5+ in Iran and adjacent areas, from USGS and EMSC.</subtitle>
  <updated>{feed.z(now)}</updated>
  <link href="{escape(site_url)}"/>
  <author><name>FEZtool</name></author>
{chr(10).join(entries)}
</feed>
"""


def export(con: duckdb.DuckDBPyConnection, out_dir: Path, site_url: str, db_url: str | None = None) -> dict:
    now = utcnow()
    out_dir.mkdir(parents=True, exist_ok=True)
    dl = out_dir / "downloads"
    dl.mkdir(exist_ok=True)

    recent = _events(con, now - FEED_WINDOW)
    latest = {
        "generated_at": feed.z(now),
        "schedule_minutes": SCHEDULE_MINUTES,
        "region": IRAN_REGION,
        "world_min_mag": WORLD_MIN_MAG,
        "sources": [
            {
                "source": s["source"],
                "ok": s["ok"],
                "last_attempt": feed.z(s["last_attempt"]) if s["last_attempt"] else None,
                "last_ok": feed.z(s["last_ok"]) if s["last_ok"] else None,
                "error": s["error"],
            }
            for s in db.source_status(con)
            if s["source"] in SOURCES
        ],
        "zones_approximate": any(zn.approximate for zn in faults.load_zones()),
        "db_url": db_url,
        "daily": _daily(con, now),
        "events": [feed.item(e) for e in recent],
    }
    (out_dir / "latest.json").write_text(json.dumps(latest, separators=(",", ":")))

    (out_dir / "feed.xml").write_text(_atom([e for e in recent if feed.notable(e)], now, site_url))
    shutil.copyfile(faults.ZONES_FILE, out_dir / "fault_zones.geojson")

    counts = {}
    for name, span in WINDOWS.items():
        since = now - span
        evs = _events(con, since)
        counts[name] = len(evs)
        (dl / f"events_{name}.geojson").write_text(json.dumps(_geojson(evs), separators=(",", ":")))
        query = f"""SELECT event_id, strftime(time_utc, '%Y-%m-%dT%H:%M:%SZ') AS time_utc, lat, lon, depth_km, mag,
                    mag_type, place, preferred_source, array_to_string(sources, ';') AS sources, in_iran_region,
                    fault_zone, fault_distance_km, significant, sequence
                    FROM events WHERE time_utc >= TIMESTAMP '{since.isoformat(sep=' ')}' ORDER BY time_utc DESC"""
        con.execute(f"COPY ({query}) TO '{dl / f'events_{name}.csv'}' (HEADER, DELIMITER ',')")
        con.execute(f"COPY ({query}) TO '{dl / f'events_{name}.parquet'}' (FORMAT PARQUET)")
    (out_dir / "downloads.json").write_text(json.dumps({"generated_at": feed.z(now), "counts": counts, "db_url": db_url}))
    months = _archive(con, out_dir, now)
    return {"events_7d": len(recent), "counts": counts, "archive_months": len(months)}
