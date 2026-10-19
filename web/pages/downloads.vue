<template>
  <div class="mx-auto max-w-5xl px-gutter py-10">
    <h1 class="text-3xl font-bold text-fez-50">Data</h1>
    <p class="paragraph mt-3 max-w-2xl text-sm">
      Every file below is rebuilt each time the collector runs (every 30 minutes). Times are UTC. One row is one
      earthquake after merging reports from IRSC, USGS and EMSC.
    </p>

    <section class="mt-8" aria-labelledby="files">
      <h2 id="files" class="text-lg font-semibold text-fez-100">Event files</h2>
      <div class="mt-3 overflow-x-auto rounded-lg border border-glass">
        <table class="w-full text-left text-sm">
          <thead class="border-b border-glass text-xs text-fez-400">
            <tr>
              <th class="px-4 py-2.5 font-normal">Window</th>
              <th class="px-4 py-2.5 text-right font-normal">Events</th>
              <th class="px-4 py-2.5 font-normal">Download</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="w in windows" :key="w.key" class="border-b border-glass last:border-0">
              <td class="px-4 py-3 text-fez-100">{{ w.label }}</td>
              <td class="px-4 py-3 text-right tabular-nums text-fez-300">{{ counts?.[w.key] ?? "–" }}</td>
              <td class="px-4 py-3">
                <span class="flex flex-wrap gap-2">
                  <a
                    v-for="f in formats"
                    :key="f"
                    :href="`${base}data/downloads/events_${w.key}.${f}`"
                    download
                    class="rounded-full border border-glass-strong px-3 py-1 text-xs text-fez-100 transition-colors hover:border-fez-400 hover:text-fez-50"
                  >{{ f.toUpperCase() }}</a>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="mt-10 grid gap-6 md:grid-cols-2">
      <div class="rounded-lg border border-glass p-5">
        <div class="flex items-center gap-3">
          <ToolsToolBadge size="sm" />
          <h2 class="text-lg font-semibold text-fez-100">Full database</h2>
        </div>
        <p class="paragraph mt-2 text-sm">
          The complete DuckDB file: raw reports from each source (<code class="text-fez-200">raw_events</code>), merged
          events (<code class="text-fez-200">events</code>) and the collector log (<code class="text-fez-200">source_runs</code>).
        </p>
        <BaseButton v-if="dbUrl" variant="fm" :href="dbUrl" class="mt-4">Download fezfm.duckdb</BaseButton>
        <p v-else class="mt-4 text-xs text-fez-500">Available once the scheduled collector has published it.</p>
        <pre class="mt-4 overflow-x-auto rounded-md bg-fez-950 p-3 text-xs text-fez-300">duckdb fezfm.duckdb
SELECT time_utc, mag, place, sources
FROM events WHERE in_iran_region
ORDER BY time_utc DESC LIMIT 20;</pre>
      </div>

      <div class="rounded-lg border border-glass p-5">
        <h2 class="text-lg font-semibold text-fez-100">Feeds and layers</h2>
        <ul class="mt-3 space-y-2.5 text-sm">
          <li>
            <a :href="`${base}data/feed.xml`" class="text-fez-100 underline decoration-fez-600 underline-offset-4 hover:text-fez-50">Atom feed</a>
            <span class="text-fez-400">: significant events, active sequences, and M3.5+ in the Iran region.</span>
          </li>
          <li>
            <a :href="`${base}data/latest.json`" class="text-fez-100 underline decoration-fez-600 underline-offset-4 hover:text-fez-50">latest.json</a>
            <span class="text-fez-400">: the last 7 days as used by this site, with source status.</span>
          </li>
          <li>
            <a :href="`${base}data/fault_zones.geojson`" class="text-fez-100 underline decoration-fez-600 underline-offset-4 hover:text-fez-50">fault_zones.geojson</a>
            <span class="text-fez-400">: the 21 monitored zones and their buffer widths.</span>
          </li>
          <li>
            <NuxtLink to="/archive" class="text-fez-100 underline decoration-fez-600 underline-offset-4 hover:text-fez-50">Monthly archive</NuxtLink>
            <span class="text-fez-400">: every stored event, one CSV file per calendar month.</span>
          </li>
          <li>
            <a :href="`${base}layers/gem_active_faults.geojson`" class="text-fez-100 underline decoration-fez-600 underline-offset-4 hover:text-fez-50">gem_active_faults.geojson</a>
            <span class="text-fez-400">: GEM active faults worldwide, simplified (CC BY-SA 4.0).</span>
          </li>
          <li>
            <a :href="`${base}layers/plate_boundaries.geojson`" class="text-fez-100 underline decoration-fez-600 underline-offset-4 hover:text-fez-50">plate_boundaries.geojson</a>
            <span class="text-fez-400">: plate boundaries from Bird (2003), PB2002 (ODC-BY 1.0).</span>
          </li>
        </ul>
      </div>
    </section>

    <section class="mt-10" aria-labelledby="columns">
      <h2 id="columns" class="text-lg font-semibold text-fez-100">Columns</h2>
      <dl class="mt-3 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-[12rem_1fr]">
        <template v-for="c in columns" :key="c[0]">
          <dt class="font-mono text-xs leading-6 text-fez-200">{{ c[0] }}</dt>
          <dd class="text-fez-400">{{ c[1] }}</dd>
        </template>
      </dl>
    </section>

    <p class="mt-10 text-xs text-fez-500">
      Use of the data: credit the original agencies (IRSC, University of Tehran; USGS; EMSC) and FEZfm. FEZfm is a
      research tool, not an official earthquake warning service.
    </p>
  </div>
</template>

<script setup lang="ts">
const base = useRuntimeConfig().app.baseURL;
const counts = ref<Record<string, number> | null>(null);
const dbUrl = ref<string | null>(null);

const windows = [
  { key: "2h", label: "Last 2 hours" },
  { key: "24h", label: "Last 24 hours" },
  { key: "7d", label: "Last 7 days" },
  { key: "30d", label: "Last 30 days" },
];
const formats = ["csv", "geojson", "parquet"];
const columns = [
  ["event_id", "Preferred source and its event id, e.g. irsc:213507."],
  ["time_utc", "Origin time, UTC."],
  ["lat, lon", "Epicentre, degrees."],
  ["depth_km", "Hypocentre depth, km."],
  ["mag, mag_type", "Magnitude and its type as reported by the preferred source."],
  ["place", "Location description from the preferred source."],
  ["preferred_source", "IRSC inside the Iran region, otherwise USGS, then EMSC."],
  ["sources", "Every source that reported the event."],
  ["in_iran_region", "Inside IRSC's box for Iran and adjacent areas (lat 24-41, lon 42-64)."],
  ["fault_zone", "Monitored fault zone whose buffer contains the epicentre, if any."],
  ["fault_distance_km", "Distance from the zone trace."],
  ["significant", "M5+ worldwide, or M4+ in the Iran region."],
  ["sequence", "5 or more events within 25 km in the 6 hours up to this event."],
];

onMounted(async () => {
  try {
    const r = await fetch(`${base}data/downloads.json?t=${Math.floor(Date.now() / 60e3)}`);
    const d = await r.json();
    counts.value = d.counts;
    dbUrl.value = d.db_url;
  } catch {}
});

useHead({ title: "FEZfm: data downloads" });
</script>
