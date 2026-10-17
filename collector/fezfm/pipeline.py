"""Collect from every source, then rebuild merged events."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

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
# A snapshot from another collector (the IRSC runner in Iran) counts as current
# for this long. While it is current, its sources are not fetched again here.
SNAPSHOT_FRESH = timedelta(hours=2)


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


def merge_snapshot(con: duckdb.DuckDBPyConnection, path: Path) -> dict:
    """Merge raw reports and the run log from another collector's database.

    GitHub's hosted runners cannot reach IRSC, so a self-hosted runner in Iran
    collects IRSC into a small database of its own. Merging the same snapshot
    twice changes nothing. Returns each source's latest run in the snapshot and
    the earliest report time that was added or updated.
    """
    quoted = str(path).replace("'", "''")
    con.execute(f"ATTACH '{quoted}' AS snap (READ_ONLY)")
    try:
        con.execute(
            """
            CREATE OR REPLACE TEMP TABLE incoming AS
            SELECT s.* FROM snap.raw_events s LEFT JOIN raw_events r USING (source, source_id)
            WHERE r.fetched_at IS NULL OR s.fetched_at > r.fetched_at
            """
        )
        earliest = con.execute("SELECT min(time_utc) FROM incoming").fetchone()[0]
        con.execute("INSERT OR REPLACE INTO raw_events BY NAME SELECT * FROM incoming")
        con.execute("DROP TABLE incoming")
        con.execute(
            """
            INSERT INTO source_runs SELECT * FROM snap.source_runs s
            WHERE NOT EXISTS (
                SELECT 1 FROM source_runs r WHERE r.source = s.source AND r.started_at = s.started_at
            )
            """
        )
        latest = dict(con.execute("SELECT source, max(finished_at) FROM snap.source_runs GROUP BY source").fetchall())
    finally:
        con.execute("DETACH snap")
    return {"latest_run": latest, "earliest": earliest}


def run(
    con: duckdb.DuckDBPyConnection,
    sources: list[str] | None = None,
    snapshot: Path | None = None,
) -> dict:
    now = utcnow()
    todo = list(sources or SOURCE_MODULES)
    rebuild_from = now - REBUILD_WINDOW
    result: dict = {}
    if snapshot is not None:
        merged = merge_snapshot(con, snapshot)
        fresh = [s for s, t in merged["latest_run"].items() if now - t <= SNAPSHOT_FRESH]
        if fresh:
            log.info("snapshot is current for %s, not fetching it here", ", ".join(fresh))
        todo = [s for s in todo if s not in fresh]
        if merged["earliest"] is not None:
            rebuild_from = min(rebuild_from, merged["earliest"])
        result["snapshot"] = {s: str(t) for s, t in merged["latest_run"].items()}
    result["sources"] = collect(con, now - LOOKBACK, now, todo) if todo else {}
    result["events_rebuilt"] = rebuild_events(con, rebuild_from)
    return result


def backfill(con: duckdb.DuckDBPyConnection, days: int, sources: list[str] | None = None) -> dict:
    """Seed history in 7-day windows (keeps each request well under source limits).

    A source that fails in one window is skipped in the later ones, so an
    unreachable server (IRSC from GitHub's runners, for example) costs one
    timeout instead of one per window.
    """
    end = utcnow()
    start = end - timedelta(days=days)
    active = list(sources or SOURCE_MODULES)
    out = []
    t = start
    while t < end and active:
        t2 = min(t + timedelta(days=7), end)
        summary = collect(con, t, t2, active)
        out.append(summary)
        failed = [name for name, s in summary.items() if not s["ok"]]
        if failed:
            log.warning("skipping %s for the rest of the backfill", ", ".join(failed))
            active = [name for name in active if name not in failed]
        t = t2
    n = rebuild_events(con, None)
    return {"windows": out, "events_rebuilt": n}
