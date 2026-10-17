# FEZfm agent notes

FEZfm is the FEZtool fault and geohazard monitor. v1 is an earthquake feed plus map, published to GitHub Pages by a scheduled workflow. See README.md for the overview.

## Layout

- `collector/`: Python package `fezfm` (uv, Python 3.12).
  - `sources/{irsc,usgs,emsc}.py`: each exposes `fetch(client, start, end) -> list[Report]`.
  - `db.py`: DuckDB schema (`raw_events`, `events`, `source_runs`) and bulk loaders. Use the JSON-load helpers, not `executemany`, which is about 100 times slower.
  - `dedupe.py`: merging rules and the significant and sequence flags.
  - `faults.py`: fault zone tagging; zone geometry is in `data/fault_zones.geojson`.
  - `export.py`: writes `web/public/data/`, which is generated and gitignored.
  - `scripts/gem_subset.py` and `scripts/basemap.py`: rebuild the static map layers in `web/public/layers/`.
- `web/`: Nuxt 3 static site.
  - Design tokens are copied from FEZhome (`assets/css/main.css`).
  - The data composable is `composables/useQuakes.ts`.
  - The map is `components/quake/Map.vue`: Leaflet canvas with a self-hosted Natural Earth basemap. It deliberately uses no WebGL and no third-party tiles; CARTO and Esri tiles fail from Iran.

## Rules

- **Times.** UTC everywhere. IRSC bulletin times are UTC (verified against EMSC and USGS).
- **Colors.** Use `fez-*` for site chrome and `fm-*` (FEZfm blue) for monitor data. No raw hex in components; map colors are read from CSS variables (`composables/useTokens.ts`).
- **Copy.** Follow FEZhome's fez-brand tone: plain, sentence case, no hype.
- **Type.** Poppins, as in FEZhome. Use `font-bold` for page titles (h1), `font-semibold` for section headings (h2), and `font-medium` for card titles.
- **Routes.** `public/data/` is reserved for generated files, so do not add a page route named `/data`.
- **Before committing:**
  - run `uv run pytest -q` in `collector/`;
  - run `npm run generate` in `web/`.
- **Commit messages** use the FEZtool style: `FEAT ...` or `FIX ...`.
