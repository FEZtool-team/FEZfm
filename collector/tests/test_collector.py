import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from fezfm import db, dedupe, export, faults, feed, pipeline
from fezfm.model import Report
from fezfm.sources import emsc, irsc, usgs

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def reports():
    return (
        irsc.parse_bulletin((FIX / "irsc_bulletin.txt").read_text())
        + usgs.parse(json.loads((FIX / "usgs_iran.geojson").read_text()))
        + emsc.parse(json.loads((FIX / "emsc_iran.json").read_text()))
    )


@pytest.fixture
def con(tmp_path):
    c = db.connect(tmp_path / "t.duckdb")
    yield c
    c.close()


def test_irsc_bulletin_parse():
    rows = irsc.parse_bulletin((FIX / "irsc_bulletin.txt").read_text())
    assert len(rows) == 21
    first = rows[0]
    assert first.source_id == "213481"
    assert first.time_utc == datetime(2026, 10, 15, 5, 7, 30)
    assert (first.lat, first.lon, first.depth_km, first.mag) == (30.120, 54.624, 8.0, 2.8)
    assert first.place == "Harat, Yazd"
    assert "eventid=213481" in first.url


def test_irsc_link_from_search_page():
    html = (FIX / "irsc_search.html").read_text(errors="replace")
    assert irsc.find_bulletin_link(html) == "http://irsc.ut.ac.ir/tm/bul54100.txt"


def test_irsc_seconds_overflow():
    line = "    1  1 2026/01/01 23:59:60.0 35.0 51.0 10.0 3.0 0.3 4 9 169  Tehran,  tehran"
    (r,) = irsc.parse_bulletin(line)
    assert r.time_utc == datetime(2026, 1, 2, 0, 0, 0)


def test_usgs_and_emsc_parse():
    u = usgs.parse(json.loads((FIX / "usgs_iran.geojson").read_text()))
    e = emsc.parse(json.loads((FIX / "emsc_iran.json").read_text()))
    assert len(u) == 3 and len(e) == 4
    assert u[0].time_utc == datetime(2026, 10, 16, 21, 30, 26)
    assert u[0].place.endswith("Iran")
    assert e[0].time_utc == datetime(2026, 10, 16, 21, 30, 26)
    assert e[0].place == "Southern Iran"


def test_same_quake_from_three_sources_is_one_event(reports):
    events = dedupe.cluster(reports)
    minab = [ev for ev in events if any(r.source_id == "213507" for r in ev.reports)]
    assert len(minab) == 1
    ev = minab[0]
    assert sorted(r.source for r in ev.reports) == ["emsc", "irsc", "usgs"]
    assert ev.preferred.source == "irsc"  # Iran region prefers IRSC
    # 3 sources x 7 cross-reported quakes collapse; IRSC-only small events stay single.
    assert len(events) == 21


def test_close_but_distinct_events_stay_apart():
    # Two IRSC events 4 minutes apart near Nodej must not merge.
    a = Report("usgs", "a", datetime(2026, 1, 1, 0, 0, 0), 27.6, 57.4, 10, 4.0, "mb", None, None)
    b = Report("emsc", "b", datetime(2026, 1, 1, 0, 4, 0), 27.6, 57.4, 10, 4.0, "mb", None, None)
    assert len(dedupe.cluster([a, b])) == 2


def test_world_prefers_usgs():
    a = Report("emsc", "a", datetime(2026, 1, 1), -20.0, -70.0, 30, 5.2, "mb", "Chile", None)
    b = Report("usgs", "b", datetime(2026, 1, 1, 0, 0, 3), -20.1, -70.1, 33, 5.3, "mww", "Chile", None)
    (ev,) = dedupe.cluster([a, b])
    assert ev.preferred.source == "usgs"


def test_fault_tagging():
    # Central Tehran, close to the North Tehran fault trace.
    assert faults.tag(35.75, 51.40)[0] == "TEHRAN"
    # Middle of the Lut desert, far from every monitored trace.
    assert faults.tag(30.5, 59.0)[0] is None
    assert len(faults.load_zones()) == 21


def test_swarm_flag():
    t0 = datetime(2026, 1, 1)
    rows = [
        {"time_utc": t0 + timedelta(minutes=30 * i), "lat": 27.6, "lon": 57.4 + 0.01 * i, "sequence": False}
        for i in range(5)
    ]
    dedupe.mark_sequences(rows)
    assert all(r["sequence"] for r in rows)
    rows = rows[:4]
    for r in rows:
        r["sequence"] = False
    dedupe.mark_sequences(rows)
    assert not any(r["sequence"] for r in rows)


def test_upsert_is_idempotent(con, reports):
    now = datetime(2026, 10, 17, 19)
    assert db.upsert_reports(con, reports, now) == len(reports)
    assert db.upsert_reports(con, reports, now) == 0
    assert con.execute("SELECT count(*) FROM raw_events").fetchone()[0] == len(reports)


def test_rebuild_and_export(con, reports, tmp_path, monkeypatch):
    db.upsert_reports(con, reports, datetime(2026, 10, 17, 19))
    assert pipeline.rebuild_events(con, None) == 21
    # Export relative to the fixture day so the 7-day window includes it.
    monkeypatch.setattr(export, "utcnow", lambda: datetime(2026, 10, 17, 19))
    db.log_run(con, "irsc", datetime(2026, 10, 17, 19), datetime(2026, 10, 17, 19), True, 21, 21, None)
    out = tmp_path / "data"
    res = export.export(con, out, "https://example.org/")
    assert res["events_7d"] == 21
    latest = json.loads((out / "latest.json").read_text())
    minab = next(e for e in latest["events"] if e["id"] == "irsc:213507")
    assert [s["name"] for s in minab["sources"]] == ["irsc", "emsc", "usgs"]
    assert minab["sig"] is True  # M4.3 in the Iran region
    assert minab["headline"].startswith("M4.3 earthquake, Nodej, Kerman")
    assert (out / "feed.xml").read_text().count("<entry>") >= 4
    assert (out / "downloads" / "events_7d.parquet").exists()
    assert con.execute(f"SELECT count(*) FROM '{out / 'downloads' / 'events_7d.csv'}'").fetchone()[0] == 21


def test_headline_zone_label():
    assert feed.zone_label("NE-LUT") == "NE Lut"
    assert feed.zone_label("VAN-TABRIZ") == "Van-Tabriz"
