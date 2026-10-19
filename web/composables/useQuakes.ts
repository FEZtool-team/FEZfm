export interface QuakeSource {
  name: "irsc" | "usgs" | "emsc" | string;
  url: string | null;
}

export interface Quake {
  id: string;
  t: string; // ISO UTC
  lat: number;
  lon: number;
  depth: number | null;
  mag: number | null;
  magType: string | null;
  place: string | null;
  country: string | null; // null: open ocean, more than ~150 km from any country
  headline: string;
  src: string;
  sources: QuakeSource[];
  region: boolean; // inside IRSC's "Iran and adjacent areas" box
  zone: string | null;
  zoneKm: number | null;
  sig: boolean;
  sequence: boolean;
}

export interface SourceStatus {
  source: string;
  ok: boolean;
  last_attempt: string | null;
  last_ok: string | null;
  error: string | null;
}

export interface Latest {
  generated_at: string;
  schedule_minutes: number;
  world_min_mag: number;
  sources: SourceStatus[];
  zones_approximate: boolean;
  db_url: string | null;
  daily: { day: string; region: number; world: number; significant: number }[];
  events: Quake[];
}

export type Window = "2h" | "24h" | "7d";

export const WINDOWS: Record<Window, { label: string; ms: number }> = {
  "2h": { label: "Last 2 hours", ms: 2 * 3600e3 },
  "24h": { label: "Last 24 hours", ms: 24 * 3600e3 },
  "7d": { label: "Last 7 days", ms: 7 * 24 * 3600e3 },
};

/** Country filter value for events far from any country. */
export const OPEN_OCEAN = "ocean";

/** Countries present in `events`, most events first, for the country filter. */
export const countryOptions = (events: Quake[]) => {
  const counts = new Map<string, number>();
  for (const q of events) counts.set(q.country ?? OPEN_OCEAN, (counts.get(q.country ?? OPEN_OCEAN) ?? 0) + 1);
  return [...counts]
    .map(([value, n]) => ({ value, n, label: value === OPEN_OCEAN ? "Open ocean" : value }))
    .sort((a, b) => b.n - a.n || a.label.localeCompare(b.label));
};

export type Depth = "all" | "shallow" | "intermediate" | "deep";
export type Flag = "all" | "sig" | "sequence" | "zone";

export const DEPTHS: Record<Depth, { label: string; min: number; max: number }> = {
  all: { label: "Any depth", min: -Infinity, max: Infinity },
  shallow: { label: "Shallow, 0-70 km", min: -Infinity, max: 70 },
  intermediate: { label: "Intermediate, 70-300 km", min: 70, max: 300 },
  deep: { label: "Deep, 300 km+", min: 300, max: Infinity },
};

export const FLAGS: Record<Flag, string> = {
  all: "All events",
  sig: "Significant only",
  sequence: "Active sequences",
  zone: "In a monitored zone",
};

export const SOURCE_LABELS: Record<string, string> = { irsc: "IRSC", usgs: "USGS", emsc: "EMSC" };

const REFRESH_MS = 5 * 60e3;
let timer: ReturnType<typeof setInterval> | undefined;
let clock: ReturnType<typeof setInterval> | undefined;

/** Feed data from data/latest.json, refreshed every 5 minutes, plus shared filters. */
export const useQuakes = () => {
  const latest = useState<Latest | null>("latest", () => null);
  const error = useState<string | null>("latest-error", () => null);
  const now = useState<number>("now", () => Date.now());
  const win = useState<Window>("filter-window", () => "24h");
  const country = useState<string>("filter-country", () => "all");
  const minMag = useState<number>("filter-minmag", () => 0);
  const depth = useState<Depth>("filter-depth", () => "all");
  const flag = useState<Flag>("filter-flag", () => "all");
  const source = useState<string>("filter-source", () => "all");
  const selected = useState<string | null>("selected-quake", () => null);
  const base = useRuntimeConfig().app.baseURL;

  const load = async () => {
    try {
      const res = await fetch(`${base}data/latest.json?t=${Math.floor(Date.now() / 60e3)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      latest.value = await res.json();
      error.value = null;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    }
  };

  onMounted(() => {
    if (!latest.value) load();
    timer ??= setInterval(load, REFRESH_MS);
    clock ??= setInterval(() => (now.value = Date.now()), 30e3);
  });

  const inCountry = (q: Quake) => country.value === "all" || (q.country ?? OPEN_OCEAN) === country.value;

  const filtered = computed(() => {
    if (!latest.value) return [];
    const since = now.value - WINDOWS[win.value].ms;
    return latest.value.events.filter((q) => Date.parse(q.t) >= since && matches(q));
  });

  /** Every filter except the time window, shared with the archive page. */
  const matches = (q: Quake) => {
    const d = DEPTHS[depth.value];
    const km = q.depth ?? 10;
    return (
      inCountry(q) &&
      (q.mag ?? 0) >= minMag.value &&
      (depth.value === "all" || (km >= d.min && km < d.max)) &&
      (flag.value === "all" || (flag.value === "sig" ? q.sig : flag.value === "sequence" ? q.sequence : !!q.zone)) &&
      (source.value === "all" || q.sources.some((s) => s.name === source.value))
    );
  };

  return { latest, error, now, win, country, minMag, depth, flag, source, selected, filtered, matches, load };
};

/** "12 min ago", "3 h ago", "2 d ago". */
export const ago = (iso: string, now: number) => {
  const s = Math.max(0, (now - Date.parse(iso)) / 1000);
  if (s < 90) return "just now";
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 48 * 3600) return `${Math.round(s / 3600)} h ago`;
  return `${Math.round(s / 86400)} d ago`;
};

/** "2026-10-17 14:33 UTC" */
export const utc = (iso: string) => iso.slice(0, 16).replace("T", " ") + " UTC";

export const zoneLabel = (name: string) =>
  name
    .split("-")
    .map((p) => (p === "NE" ? "NE" : p[0] + p.slice(1).toLowerCase()))
    .join("-")
    .replace("NE-", "NE ");
