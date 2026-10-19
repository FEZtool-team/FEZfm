# FEZfm

Fault and geohazard monitoring, part of [FEZtool](https://feztool-team.github.io/FEZhome/).

FEZfm v1 is an earthquake monitor. Every 30 minutes it collects reports from USGS and EMSC, merges them, stores them in DuckDB, and publishes a feed, a map and downloadable data to GitHub Pages. It needs no server.

| Source | Coverage | How |
|---|---|---|
| USGS | Worldwide | FDSN event service |
| EMSC | Worldwide; also relays Iranian agencies | FDSN event service at seismicportal.eu |
| IRSC, Iranian Seismological Center (University of Tehran) | Iran and adjacent areas, M2.5+ | Off by default, see below |

All events in Iran and adjacent areas are kept; elsewhere M2.5 and above. Each event is tagged with its country (or the nearest one within about 150 km offshore) for the site's country filter.

## How it works

```
Monitor workflow, GitHub Actions (every 30 min)
  ├─ download fezfm.duckdb from the "data-latest" release
  ├─ fezfm collect     fetch the last 2 days from USGS and EMSC (one failing source never stops the other)
  │                    merge reports of the same quake (45 s, 80 km, 1 magnitude unit)
  │                    tag fault zones, significant events, active sequences
  ├─ upload fezfm.duckdb back to the release
  ├─ fezfm export      web/public/data: latest.json, feed.xml, CSV / GeoJSON / Parquet downloads,
  │                    monthly archive (archive/YYYY-MM.json and .csv)
  └─ nuxt generate  →  GitHub Pages
```

- **Merging.** USGS is preferred, then EMSC. Inside the Iran region an IRSC solution, where there is one, comes first, the same priority Faultiuo uses.
- **Significant.** M5+ anywhere, or M4+ in the Iran region.
- **Active sequence.** 5 or more events within 25 km in 6 hours.
- **Fault zones.** The 21 zones Faultiuo monitors, with its buffer widths of 20, 40 or 50 km.

The zone traces in `collector/fezfm/data/fault_zones.geojson` are approximate until Faultiuo's KML files are added (see below).

## Repository layout

```
collector/   Python 3.12 package "fezfm" (DuckDB, httpx), tests in collector/tests
web/         Nuxt 3 static site, FEZhome design tokens, Leaflet map with a self-hosted basemap
.github/     monitor.yml (schedule + Pages), backfill.yml (manual), ci.yml (tests + build)
```

## Run locally

Collector (needs [uv](https://docs.astral.sh/uv/)):

```bash
cd collector
uv run pytest -q
uv run fezfm backfill --days 7      # creates fezfm.duckdb
uv run fezfm collect                # what the schedule runs
uv run fezfm export                 # writes ../web/public/data
```

Site:

```bash
cd web
npm install
npm run dev                         # http://localhost:3036
```

## Publish on GitHub Pages

1. Push to `main` on GitHub. The repository must be public for free, unlimited Actions minutes.
2. Under **Settings → Pages**, set **Source** to **GitHub Actions**.
3. Under **Actions → Monitor**, choose **Run workflow**. The first run backfills 30 days, creates the `data-latest` release and deploys the site to `https://<owner>.github.io/FEZfm/`.

After that the schedule runs every 30 minutes. GitHub pauses schedules in repositories with no activity for 60 days; the workflow re-enables itself on each run to prevent that.

## IRSC

IRSC is not collected by default. irsc.ut.ac.ir cannot be reached from outside Iran, so GitHub's runners time out on it. Iranian events come from EMSC, which relays Iranian agencies, and USGS. They carry fewer small events than IRSC: in one week of October 2026, IRSC listed 44 events in the Iran region and EMSC and USGS 11.

IRSC events collected earlier stay in the database. The IRSC source (`collector/fezfm/sources/irsc.py`) still works from a machine inside Iran:

```bash
uv run fezfm --db irsc.duckdb collect --source irsc
```

`fezfm collect --snapshot irsc.duckdb` merges such a snapshot into the main database.

## Fault zones from Faultiuo

Faultiuo reads each zone from `~/GMTdata/KML/Time_Section/<Name>.kml`. With those files:

```bash
cd collector
uv run fezfm import-kml ~/GMTdata/KML/Time_Section
```

This replaces the approximate traces and clears the "approximate" note on the site.

## Data credits

- Earthquake reports: USGS and EMSC; earlier events also from IRSC (Institute of Geophysics, University of Tehran).
- Active faults: [GEM Global Active Faults Database](https://github.com/GEMScienceTools/gem-global-active-faults), CC BY-SA 4.0.
- Plate boundaries: Bird (2003), [PB2002](https://github.com/fraxen/tectonicplates), ODC-BY 1.0.
- Relief: [GEBCO Grid](https://www.gebco.net/) shaded relief, GEBCO Compilation Group; tiles built once by `collector/scripts/gebco_tiles.py`.
- Country outlines: [Natural Earth](https://www.naturalearthdata.com/), public domain.

FEZfm is a research tool, not an official earthquake warning service.

## License

Code under Apache-2.0 (see `LICENSE`). Documentation under CC BY 4.0.
