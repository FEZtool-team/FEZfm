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
export type Scope = "all" | "region" | "world";

export const WINDOWS: Record<Window, { label: string; ms: number }> = {
  "2h": { label: "Last 2 hours", ms: 2 * 3600e3 },
  "24h": { label: "Last 24 hours", ms: 24 * 3600e3 },
  "7d": { label: "Last 7 days", ms: 7 * 24 * 3600e3 },
};

export const SCOPES: Record<Scope, string> = {
  all: "All",
  region: "Iran and adjacent areas",
  world: "Rest of the world",
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
  const scope = useState<Scope>("filter-scope", () => "all");
  const minMag = useState<number>("filter-minmag", () => 0);
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

  const inScope = (q: Quake) =>
    scope.value === "all" || (scope.value === "region" ? q.region : !q.region);

  const filtered = computed(() => {
    if (!latest.value) return [];
    const since = now.value - WINDOWS[win.value].ms;
    return latest.value.events.filter(
      (q) => Date.parse(q.t) >= since && inScope(q) && (q.mag ?? 0) >= minMag.value
    );
  });

  return { latest, error, now, win, scope, minMag, selected, filtered, load };
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
