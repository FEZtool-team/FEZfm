import type { Quake } from "~/composables/useQuakes";

export interface MonthInfo {
  month: string; // YYYY-MM, UTC
  events: number;
  region: number;
  significant: number;
}

export interface ArchiveIndex {
  generated_at: string;
  months: MonthInfo[]; // newest first
}

/** Month pages with fewer events (a partly collected first month) get noindex and stay out of the sitemap. */
export const MIN_INDEXED_EVENTS = 100;

/** The most rows the month page lists; the CSV has every event. */
export const MONTH_ROW_LIMIT = 500;

export const isMonth = (m: string) => /^\d{4}-(0[1-9]|1[0-2])$/.test(m);

/** data/archive/index.json, from the prerender payload where there is one. */
export const useArchiveIndex = () => usePublicData<ArchiveIndex>("archive-index", "archive/index.json");

/** "October 2026" */
export const monthLabel = (m: string) =>
  m ? new Date(`${m}-01T00:00:00Z`).toLocaleDateString("en-GB", { month: "long", year: "numeric", timeZone: "UTC" }) : "";

/** "2026-10-01/2026-10-31" */
export const monthInterval = (m: string) => {
  const [y, mo] = m.split("-").map(Number);
  const last = new Date(Date.UTC(y, mo, 0)).getUTCDate();
  return `${m}-01/${m}-${String(last).padStart(2, "0")}`;
};

export type MonthRow = Pick<Quake, "id" | "t" | "mag" | "magType" | "depth" | "place" | "region" | "sig" | "sequence" | "zone"> & {
  sources: string[];
};

export interface MonthSummary {
  month: string;
  events: number;
  region: number;
  significant: number;
  /** Source names that reported at least one event this month. */
  sources: string[];
  largest: MonthRow | null;
  largestRegion: MonthRow | null;
  /** Significant events and events in the Iran region, newest first. */
  rows: MonthRow[];
  rowsTotal: number;
}

const row = (q: Quake): MonthRow => ({
  id: q.id,
  t: q.t,
  mag: q.mag,
  magType: q.magType,
  depth: q.depth,
  place: q.place,
  region: q.region,
  sig: q.sig,
  sequence: q.sequence,
  zone: q.zone,
  sources: q.sources.map((s) => s.name),
});

const largestOf = (list: Quake[]) =>
  list.reduce<Quake | null>((a, q) => (q.mag != null && q.mag > (a?.mag ?? -Infinity) ? q : a), null);

/** What the month page shows, computed from data/archive/YYYY-MM.json (events newest first). */
export const summarizeMonth = (month: string, events: Quake[]): MonthSummary => {
  const regional = events.filter((q) => q.region);
  const listed = events.filter((q) => q.sig || q.region);
  const largest = largestOf(events);
  const largestRegion = largestOf(regional);
  return {
    month,
    events: events.length,
    region: regional.length,
    significant: events.filter((q) => q.sig).length,
    sources: [...new Set(events.flatMap((q) => q.sources.map((s) => s.name)))],
    largest: largest && row(largest),
    largestRegion: largestRegion && row(largestRegion),
    rows: listed.slice(0, MONTH_ROW_LIMIT).map(row),
    rowsTotal: listed.length,
  };
};
