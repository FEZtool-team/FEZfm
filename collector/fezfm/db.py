"""DuckDB storage: raw reports per source, merged events, and source run log."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import duckdb

from .model import Report

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_events (
    source      VARCHAR NOT NULL,
    source_id   VARCHAR NOT NULL,
    time_utc    TIMESTAMP NOT NULL,
    lat         DOUBLE NOT NULL,
    lon         DOUBLE NOT NULL,
    depth_km    DOUBLE,
    mag         DOUBLE,
    mag_type    VARCHAR,
    place       VARCHAR,
    url         VARCHAR,
    fetched_at  TIMESTAMP NOT NULL,
    PRIMARY KEY (source, source_id)
);
CREATE TABLE IF NOT EXISTS events (
    event_id          VARCHAR PRIMARY KEY,
    time_utc          TIMESTAMP NOT NULL,
    lat               DOUBLE NOT NULL,
    lon               DOUBLE NOT NULL,
    depth_km          DOUBLE,
    mag               DOUBLE,
    mag_type          VARCHAR,
    place             VARCHAR,
    preferred_source  VARCHAR NOT NULL,
    sources           VARCHAR[] NOT NULL,
    urls              VARCHAR[] NOT NULL,
    in_iran_region    BOOLEAN NOT NULL,
    fault_zone        VARCHAR,
    fault_distance_km DOUBLE,
    significant       BOOLEAN NOT NULL,
    sequence          BOOLEAN NOT NULL
);
CREATE TABLE IF NOT EXISTS source_runs (
    source       VARCHAR NOT NULL,
    started_at   TIMESTAMP NOT NULL,
    finished_at  TIMESTAMP NOT NULL,
    ok           BOOLEAN NOT NULL,
    n_fetched    INTEGER NOT NULL,
    n_new        INTEGER NOT NULL,
    error        VARCHAR
);
"""

RAW_COLUMNS = ("source", "source_id", "time_utc", "lat", "lon", "depth_km", "mag", "mag_type", "place", "url")


def connect(path: str | Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(path))
    con.execute(SCHEMA)
    return con


def upsert_reports(con: duckdb.DuckDBPyConnection, reports: list[Report], fetched_at: datetime) -> int:
    """Insert or update reports; returns how many (source, source_id) keys are new."""
    if not reports:
        return 0
    # Last write wins for duplicate keys within one batch (e.g. overlapping queries).
    rows = {(r.source, r.source_id): r for r in reports}
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        for r in rows.values():
            rec = {c: getattr(r, c) for c in RAW_COLUMNS}
            rec["time_utc"] = r.time_utc.isoformat(sep=" ")
            rec["fetched_at"] = fetched_at.isoformat(sep=" ")
            fh.write(json.dumps(rec) + "\n")
        tmp = fh.name
    try:
        con.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE incoming AS
            SELECT * FROM read_json(?, format='newline_delimited', columns={{
                source: 'VARCHAR', source_id: 'VARCHAR', time_utc: 'TIMESTAMP',
                lat: 'DOUBLE', lon: 'DOUBLE', depth_km: 'DOUBLE', mag: 'DOUBLE',
                mag_type: 'VARCHAR', place: 'VARCHAR', url: 'VARCHAR', fetched_at: 'TIMESTAMP'
            }})
            """,
            [tmp],
        )
        n_new = con.execute(
            """
            SELECT count(*) FROM incoming i
            ANTI JOIN raw_events r USING (source, source_id)
            """
        ).fetchone()[0]
        con.execute("INSERT OR REPLACE INTO raw_events BY NAME SELECT * FROM incoming")
        con.execute("DROP TABLE incoming")
    finally:
        Path(tmp).unlink(missing_ok=True)
    return int(n_new)


EVENT_TYPES = {
    "event_id": "VARCHAR", "time_utc": "TIMESTAMP", "lat": "DOUBLE", "lon": "DOUBLE", "depth_km": "DOUBLE",
    "mag": "DOUBLE", "mag_type": "VARCHAR", "place": "VARCHAR", "preferred_source": "VARCHAR",
    "sources": "VARCHAR[]", "urls": "VARCHAR[]", "in_iran_region": "BOOLEAN", "fault_zone": "VARCHAR",
    "fault_distance_km": "DOUBLE", "significant": "BOOLEAN", "sequence": "BOOLEAN",
}


def insert_events(con: duckdb.DuckDBPyConnection, rows: list[dict]) -> None:
    """Bulk insert merged events (a JSON load is ~100x faster than executemany)."""
    if not rows:
        return
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        for r in rows:
            fh.write(json.dumps({**r, "time_utc": r["time_utc"].isoformat(sep=" ")}) + "\n")
        tmp = fh.name
    cols = ", ".join(f"{k}: '{v}'" for k, v in EVENT_TYPES.items())
    try:
        con.execute(
            f"INSERT OR REPLACE INTO events BY NAME "
            f"SELECT * FROM read_json(?, format='newline_delimited', columns={{{cols}}})",
            [tmp],
        )
    finally:
        Path(tmp).unlink(missing_ok=True)


def log_run(
    con: duckdb.DuckDBPyConnection,
    source: str,
    started_at: datetime,
    finished_at: datetime,
    ok: bool,
    n_fetched: int,
    n_new: int,
    error: str | None,
) -> None:
    con.execute(
        "INSERT INTO source_runs VALUES (?, ?, ?, ?, ?, ?, ?)",
        [source, started_at, finished_at, ok, n_fetched, n_new, error],
    )


def raw_since(con: duckdb.DuckDBPyConnection, since: datetime | None) -> list[Report]:
    sql = f"SELECT {', '.join(RAW_COLUMNS)} FROM raw_events"
    params: list = []
    if since is not None:
        sql += " WHERE time_utc >= ?"
        params.append(since)
    sql += " ORDER BY time_utc"
    return [Report(*row) for row in con.execute(sql, params).fetchall()]


def source_status(con: duckdb.DuckDBPyConnection) -> list[dict]:
    """Latest attempt and latest success per source."""
    rows = con.execute(
        """
        SELECT source,
               max(finished_at)                          AS last_attempt,
               max(finished_at) FILTER (WHERE ok)        AS last_ok,
               arg_max(ok, finished_at)                  AS ok,
               arg_max(error, finished_at)               AS error
        FROM source_runs GROUP BY source ORDER BY source
        """
    ).fetchall()
    return [
        {"source": s, "last_attempt": la, "last_ok": lo, "ok": ok, "error": err}
        for s, la, lo, ok, err in rows
    ]
