# FEZfm

Fault and geohazard monitoring, part of [FEZtool](https://feztool-team.github.io/FEZhome/).

FEZfm v1 is an earthquake monitor. Every 30 minutes it collects reports from three agencies, merges them, stores them in DuckDB, and publishes a feed, a map and downloadable data to GitHub Pages. It needs no server.

| Source | Coverage | How |
|---|---|---|
| IRSC, Iranian Seismological Center (University of Tehran) | Iran and adjacent areas, M2.5+ | Bulletin search at irsc.ut.ac.ir, ported from [Faultiuo](https://github.com/mhdned/Faultiuo) |
| USGS | Worldwide | FDSN event service |
| EMSC | Worldwide; also relays Iranian agencies | FDSN event service at seismicportal.eu |

All events in Iran and adjacent areas are kept; elsewhere M2.5 and above.

## How it works

```
IRSC workflow, self-hosted runner in Iran (every 30 min, optional)
  ├─ fezfm collect --source irsc   into a fresh irsc.duckdb
  ├─ upload irsc.duckdb to the "data-latest" release
  └─ start the Monitor workflow

Monitor workflow, GitHub Actions (every 30 min)
  ├─ download fezfm.duckdb and irsc.duckdb from the "data-latest" release
  ├─ fezfm collect     merge irsc.duckdb; skip IRSC if that snapshot is under 2 hours old
  │                    fetch the last 2 days from IRSC, USGS, EMSC (one failing source never stops the others)
  │                    merge reports of the same quake (45 s, 80 km, 1 magnitude unit)
  │                    tag fault zones, significant events, active sequences
  ├─ upload fezfm.duckdb back to the release
  ├─ fezfm export      web/public/data: latest.json, feed.xml, CSV / GeoJSON / Parquet downloads
  └─ nuxt generate  →  GitHub Pages
```

- **Merging.** Inside the Iran region the IRSC solution is preferred, the same priority Faultiuo uses. Elsewhere USGS is preferred, then EMSC.
- **Significant.** M5+ anywhere, or M4+ in the Iran region.
- **Active sequence.** 5 or more events within 25 km in 6 hours.
- **Fault zones.** The 21 zones Faultiuo monitors, with its buffer widths of 20, 40 or 50 km.

The zone traces in `collector/fezfm/data/fault_zones.geojson` are approximate until Faultiuo's KML files are added (see below).

## Repository layout

```
collector/   Python 3.12 package "fezfm" (DuckDB, httpx), tests in collector/tests
web/         Nuxt 3 static site, FEZhome design tokens, Leaflet map with a self-hosted basemap
.github/     monitor.yml (schedule + Pages), irsc.yml (runner in Iran), backfill.yml (manual), ci.yml (tests + build)
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

## IRSC from a runner in Iran

GitHub's hosted runners cannot connect to irsc.ut.ac.ir. Without help, the site shows IRSC as unreachable and Iranian events arrive only through EMSC and USGS, which relay mostly the larger ones. A Linux machine inside Iran restores IRSC by running the IRSC workflow as a [self-hosted runner](https://docs.github.com/actions/hosting-your-own-runners).

The runner only fetches IRSC and uploads a small snapshot (`irsc.duckdb`). The database, the site build and GitHub Pages stay on GitHub. Any always-on Linux machine works: a small VPS in Iran, a home server or a Raspberry Pi.

### What the machine needs

- Linux x64 or ARM64 with systemd, `git`, `curl` and the [GitHub CLI](https://cli.github.com/) (`gh`).
- Outbound HTTPS to irsc.ut.ac.ir, to GitHub (github.com, `*.githubusercontent.com`, `*.actions.githubusercontent.com`, `*.blob.core.windows.net`) and to pypi.org and files.pythonhosted.org. If GitHub needs a proxy, see step 4.
- A synchronised clock (`timedatectl` should show `System clock synchronized: yes`). Snapshot ages are compared with GitHub's clock.

### Set it up

1. **Allow the runner safely.** The repository is public, so under **Settings → Actions → General → Approval for running fork pull request workflows from contributors**, choose **Require approval for all external contributors**. Otherwise a pull request could change a workflow to run its own code on your machine. Use a machine with nothing else sensitive on it.

2. **Create a user and install the tools.**

   ```bash
   sudo useradd -m -s /bin/bash fezfm
   sudo apt install -y git curl gh
   ```

3. **Register the runner.** On GitHub open **Settings → Actions → Runners → New self-hosted runner**, choose **Linux** and your architecture, and follow the *Download* commands as the `fezfm` user (`sudo -iu fezfm`). Then configure it with the token that page shows (it expires after an hour) and the `iran` label:

   ```bash
   ./config.sh --url https://github.com/FEZtool-team/FEZfm --token <TOKEN> \
     --name iran-1 --labels iran --unattended
   ```

4. **Proxy (only if GitHub needs one).** Add the proxy to `.env` in the runner folder, and keep IRSC direct:

   ```
   https_proxy=http://127.0.0.1:8080
   no_proxy=irsc.ut.ac.ir,localhost
   ```

5. **Run it as a systemd service**, so it starts on boot and restarts after a crash. From the runner folder, as a user with sudo:

   ```bash
   sudo ./svc.sh install fezfm
   sudo ./svc.sh start
   sudo ./svc.sh status
   ```

   The runner should now show as **Idle** under **Settings → Actions → Runners**. Logs: `journalctl -u 'actions.runner.*' -f`.

6. **Turn the workflow on.** Under **Settings → Secrets and variables → Actions → Variables**, add the repository variable `IRSC_RUNNER` with the value `true`. Until then the IRSC workflow skips its job, so it never waits for a runner that does not exist.

7. **Test it.** Under **Actions → IRSC**, choose **Run workflow**. It should finish in about a minute and start a Monitor run. When that Monitor run is done, the site shows IRSC as reachable, and Iranian events list IRSC as their preferred source.

### When the machine is offline

- **The site keeps working.** Monitor still runs on GitHub every 30 minutes with EMSC and USGS.
- **IRSC shows as unreachable.** Once the last snapshot is more than 2 hours old, Monitor tries IRSC itself. That fails from GitHub, so the site shows "IRSC unreachable since …" and Iranian events come only from EMSC and USGS.
- **IRSC runs wait.** Each IRSC run waits for the runner in the queue. A waiting run never blocks Monitor, because the IRSC workflow does not write `fezfm.duckdb`. After 24 hours GitHub fails the waiting run and emails a failure notice.
- **Recovery is automatic.** When the machine is back, the runner reconnects and the next run fetches the last 2 days. For a longer outage, run **Actions → IRSC → Run workflow** with **days** set to the length of the gap.

To retire the machine, set `IRSC_RUNNER` to `false` and remove the runner under **Settings → Actions → Runners**.

## Fault zones from Faultiuo

Faultiuo reads each zone from `~/GMTdata/KML/Time_Section/<Name>.kml`. With those files:

```bash
cd collector
uv run fezfm import-kml ~/GMTdata/KML/Time_Section
```

This replaces the approximate traces and clears the "approximate" note on the site.

## Data credits

- Earthquake reports: IRSC (Institute of Geophysics, University of Tehran), USGS and EMSC.
- Active faults: [GEM Global Active Faults Database](https://github.com/GEMScienceTools/gem-global-active-faults), CC BY-SA 4.0.
- Country outlines: [Natural Earth](https://www.naturalearthdata.com/), public domain.

FEZfm is a research tool, not an official earthquake warning service.

## License

Code under Apache-2.0 (see `LICENSE`). Documentation under CC BY 4.0.
