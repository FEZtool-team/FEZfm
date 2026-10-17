"""Collect from every source, then rebuild merged events."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import duckdb
import httpx

from . import db, dedupe
from .model import utcnow
from .sources import emsc, irsc, make_client, usgs

log = logging.getLogger("fezfm")

SOURCE_MODULES = {"irsc": irsc, "usgs": usgs, "emsc": emsc}

# Each scheduled run re-reads this much history so late and revised reports
# (agencies update magnitudes and locations for hours) are picked up.
LOOKBACK = timedelta(days=2)
# Events are rebuilt over this window each run; older events are frozen.
REBUILD_WINDOW = timedelta(days=14)


def collect(
    con: duckdb.DuckDBPyConnection,
    start: datetime,
    end: datetime,
    sources: list[str] | None = None,
    client: httpx.Client | None = None,
) -> dict[str, dict]:
    """Fetch every source independently. One failing source never stops the others."""
    client = client or make_client()
    summary = {}
    for name in sources or list(SOURCE_MODULES):
        mod = SOURCE_MODULES[name]
        started = utcnow()
        try:
            reports = [r for r in mod.fetch(client, start, end) if r.keep()]
            n_new = db.upsert_reports(con, reports, started)
            db.log_run(con, name, started, utcnow(), True, len(reports), n_new, None)
            summary[name] = {"ok": True, "fetched": len(reports), "new": n_new}
            log.info("%s: %d reports, %d new", name, len(reports), n_new)
        except Exception as exc:  # noqa: BLE001 - any failure is logged per source
            msg = f"{type(exc).__name__}: {exc}"[:500]
            db.log_run(con, name, started, utcnow(), False, 0, 0, msg)
            summary[name] = {"ok": False, "error": msg}
            log.warning("%s failed: %s", name, msg)
    return summary


def rebuild_events(con: duckdb.DuckDBPyConnection, since: datetime | None) -> int:
    """Re-merge raw reports from ``since`` (None = everything) into ``events``."""
    context = since - dedupe.SEQ_WINDOW if since else None
    reports = db.raw_since(con, context)
    rows = dedupe.to_rows(dedupe.cluster(reports))
    if since is not None:
        rows = [r for r in rows if r["time_utc"] >= since]
        con.execute("DELETE FROM events WHERE time_utc >= ?", [since])
    else:
        con.execute("DELETE FROM events")
    db.insert_events(con, rows)
    return len(rows)


def run(con: duckdb.DuckDBPyConnection, sources: list[str] | None = None) -> dict:
    now = utcnow()
    summary = collect(con, now - LOOKBACK, now, sources)
    n = rebuild_events(con, now - REBUILD_WINDOW)
    return {"sources": summary, "events_rebuilt": n}


def backfill(con: duckdb.DuckDBPyConnection, days: int, sources: list[str] | None = None) -> dict:
    """Seed history in 7-day windows (keeps each request well under source limits)."""
    end = utcnow()
    start = end - timedelta(days=days)
    out = []
    t = start
    while t < end:
        t2 = min(t + timedelta(days=7), end)
        out.append(collect(con, t, t2, sources))
        t = t2
    n = rebuild_events(con, None)
    return {"windows": out, "events_rebuilt": n}
