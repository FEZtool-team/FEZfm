"""Command line: fezfm collect | backfill | export | import-kml."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from . import db, export, faults, pipeline

DEFAULT_DB = "fezfm.duckdb"
DEFAULT_OUT = "../web/public/data"
DEFAULT_SITE = "https://feztool-team.github.io/FEZfm/"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="fezfm", description="FEZfm earthquake collector")
    ap.add_argument("--db", default=DEFAULT_DB, help="DuckDB file (default: %(default)s)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="fetch the last 2 days from every source and rebuild events")
    c.add_argument("--source", action="append", choices=list(pipeline.SOURCE_MODULES), help="limit to a source")
    c.add_argument(
        "--snapshot",
        type=Path,
        help="first merge this database from another collector (the IRSC runner); "
        "sources it ran in the last 2 hours are not fetched again",
    )

    b = sub.add_parser("backfill", help="seed history")
    b.add_argument("--days", type=int, default=30)
    b.add_argument("--source", action="append", choices=list(pipeline.SOURCE_MODULES))

    e = sub.add_parser("export", help="write site data files")
    e.add_argument("--out", default=DEFAULT_OUT)
    e.add_argument("--site-url", default=DEFAULT_SITE)
    e.add_argument("--db-url", default=None, help="public URL of the full DuckDB file")

    k = sub.add_parser("import-kml", help="replace approximate zone traces with Faultiuo KML files")
    k.add_argument("kml_dir", type=Path, help="e.g. ~/GMTdata/KML/Time_Section")

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.cmd == "import-kml":
        print("replaced:", ", ".join(faults.import_kml(args.kml_dir.expanduser())) or "none")
        return

    con = db.connect(args.db)
    try:
        if args.cmd == "collect":
            result = pipeline.run(con, args.source, args.snapshot)
        elif args.cmd == "backfill":
            result = pipeline.backfill(con, args.days, args.source)
        else:
            result = export.export(con, Path(args.out), args.site_url, args.db_url)
    finally:
        con.close()
    print(json.dumps(result, default=str, indent=1))


if __name__ == "__main__":
    main()
