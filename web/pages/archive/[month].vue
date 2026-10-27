<template>
  <div class="mx-auto max-w-5xl px-gutter py-10">
    <nav aria-label="Breadcrumb" class="text-xs text-fez-400">
      <NuxtLink to="/archive" class="hover:text-fez-50">Archive</NuxtLink>
      <span class="mx-1.5" aria-hidden="true">/</span>
      <span aria-current="page">{{ label }}</span>
    </nav>
    <h1 class="mt-3 text-3xl font-bold text-fez-50 sm:text-4xl">Earthquakes in Iran and worldwide, {{ label }}</h1>

    <template v-if="summary">
      <p class="paragraph mt-4 max-w-3xl">{{ lead }}</p>

      <dl class="mt-6 grid grid-cols-2 border-l border-t border-glass sm:grid-cols-4">
        <div v-for="s in stats" :key="s.label" class="border-b border-r border-glass px-4 py-3.5">
          <dt class="text-xs text-fez-400">{{ s.label }}</dt>
          <dd class="mt-1 text-2xl font-light tabular-nums text-fez-50">{{ s.value }}</dd>
          <dd v-if="s.note" class="mt-0.5 truncate text-xs text-fez-500" :title="s.note">{{ s.note }}</dd>
        </div>
      </dl>

      <div class="mt-5 flex flex-wrap items-center gap-2 text-sm">
        <a
          v-for="f in ['csv', 'json']"
          :key="f"
          :href="`${base}data/archive/${month}.${f}`"
          download
          class="rounded-full border border-glass-strong px-3 py-1.5 text-xs text-fez-100 transition-colors hover:border-fez-400 hover:text-fez-50"
        >Download {{ f.toUpperCase() }}</a>
        <NuxtLink
          :to="{ path: '/archive', query: { month } }"
          class="rounded-full border border-glass-strong px-3 py-1.5 text-xs text-fez-100 transition-colors hover:border-fez-400 hover:text-fez-50"
        >Map and filters</NuxtLink>
      </div>

      <section class="mt-10" aria-labelledby="month-events">
        <h2 id="month-events" class="text-lg font-semibold text-fez-100">Significant events and events in the Iran region</h2>
        <p class="paragraph mt-1 text-sm">
          Significant means M5 or larger anywhere, or M4 or larger in Iran and adjacent areas. Newest first<template
            v-if="summary.rowsTotal > summary.rows.length"
          >; the first {{ summary.rows.length }} of {{ fmt(summary.rowsTotal) }} are listed, and the CSV has them all</template>.
        </p>
        <div class="mt-3 overflow-x-auto rounded-lg border border-glass">
          <table class="w-full text-left text-sm">
            <thead class="border-b border-glass text-xs text-fez-400">
              <tr>
                <th class="px-4 py-2.5 font-normal">Time (UTC)</th>
                <th class="px-4 py-2.5 text-right font-normal">Mag</th>
                <th class="px-4 py-2.5 text-right font-normal">Depth</th>
                <th class="px-4 py-2.5 font-normal">Place</th>
                <th class="hidden px-4 py-2.5 font-normal md:table-cell">Sources</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in summary.rows" :key="q.id" class="border-b border-glass last:border-0">
                <td class="whitespace-nowrap px-4 py-2.5 tabular-nums text-fez-300">
                  <time :datetime="q.t">{{ q.t.slice(0, 16).replace("T", " ") }}</time>
                </td>
                <td class="px-4 py-2.5 text-right tabular-nums" :class="q.sig ? 'font-medium text-fm-300' : 'text-fez-100'">
                  {{ q.mag != null ? q.mag.toFixed(1) : "–" }}
                </td>
                <td class="whitespace-nowrap px-4 py-2.5 text-right tabular-nums text-fez-300">
                  {{ q.depth != null ? `${q.depth.toFixed(0)} km` : "–" }}
                </td>
                <td class="min-w-[12rem] px-4 py-2.5 text-fez-100">
                  {{ q.place || "Unnamed location" }}
                  <span v-if="q.zone" class="ml-1 text-xs text-fm-300">{{ zoneLabel(q.zone) }} zone</span>
                  <span v-if="q.sequence" class="ml-1 text-xs text-fez-400">active sequence</span>
                </td>
                <td class="hidden px-4 py-2.5 text-xs text-fez-400 md:table-cell">
                  {{ q.sources.map((s) => SOURCE_LABELS[s] ?? s).join(", ") }}
                </td>
              </tr>
            </tbody>
          </table>
          <p v-if="!summary.rows.length" class="px-5 py-10 text-center text-sm text-fez-400">
            No significant events and no events in the Iran region in {{ label }}.
          </p>
        </div>
      </section>
    </template>
    <p v-else class="paragraph mt-4">The data for {{ label }} could not be loaded.</p>

    <nav class="mt-10 flex flex-wrap justify-between gap-4 border-t border-glass pt-5 text-sm" aria-label="Other months">
      <NuxtLink v-if="older" :to="`/archive/${older}/`" class="text-fez-300 hover:text-fez-50">&larr; {{ monthLabel(older) }}</NuxtLink>
      <span v-else />
      <NuxtLink v-if="newer" :to="`/archive/${newer}/`" class="text-fez-300 hover:text-fez-50">{{ monthLabel(newer) }} &rarr;</NuxtLink>
    </nav>

    <p class="mt-8 text-xs text-fez-500">
      Times are UTC. Events are merged from USGS and EMSC reports<template v-if="summary?.sources.includes('irsc')">, and IRSC
      for events collected earlier</template>. All events in Iran and adjacent areas are kept; elsewhere M2.5 and above.
      See <NuxtLink to="/about" class="underline decoration-fez-600 underline-offset-4 hover:text-fez-50">sources and method</NuxtLink>.
    </p>
  </div>
</template>

<script setup lang="ts">
import type { MonthRow } from "~/composables/useArchive";
import type { Quake } from "~/composables/useQuakes";
import { breadcrumbs, datasetBase, download, organization, SOURCES } from "~/data/schema";

const route = useRoute();
const month = String(route.params.month);
if (!isMonth(month)) throw createError({ statusCode: 404, statusMessage: "Page not found", fatal: true });

const base = useRuntimeConfig().app.baseURL;
const site = useRuntimeConfig().public.siteUrl;

const { data: index } = await useArchiveIndex();
const at = index.value?.months.findIndex((m) => m.month === month) ?? -1;
if (index.value && at < 0) throw createError({ statusCode: 404, statusMessage: "Month not found", fatal: true });

// Only the summary and the listed rows go into the payload, not the whole month.
const { data: summary } = await usePublicData(`archive-${month}`, `archive/${month}.json`, (d: { events: Quake[] }) =>
  summarizeMonth(month, d.events)
);

const label = monthLabel(month);
const older = index.value?.months[at + 1]?.month;
const newer = at > 0 ? index.value?.months[at - 1]?.month : undefined;
// The current month is still being collected.
const ongoing = index.value?.generated_at.slice(0, 7) === month;

const fmt = (n: number) => n.toLocaleString("en-GB");
const mag = (q: { mag: number | null }) => (q.mag != null ? `M${q.mag.toFixed(1)}` : "unknown magnitude");
const describe = (q: MonthRow) =>
  `${mag(q)}, ${q.place || "unnamed location"}, at ${utc(q.t)}`;

const lead = computed(() => {
  const s = summary.value;
  if (!s) return "";
  const when = ongoing ? `So far in ${label} (up to ${utc(index.value!.generated_at)})` : `In ${label} (UTC)`;
  const parts = [
    `${when}, FEZfm recorded ${fmt(s.events)} earthquakes: ${fmt(s.region)} in Iran and adjacent areas and ${fmt(s.significant)} significant events.`,
  ];
  if (s.largest) parts.push(`The largest was ${describe(s.largest)}.`);
  if (s.largestRegion && s.largestRegion.id !== s.largest?.id) parts.push(`In the Iran region the largest was ${describe(s.largestRegion)}.`);
  return parts.join(" ");
});

const stats = computed(() => {
  const s = summary.value;
  if (!s) return [];
  return [
    { label: "Events", value: fmt(s.events), note: ongoing ? "so far" : "" },
    { label: "Iran and adjacent areas", value: fmt(s.region), note: "" },
    { label: "Significant", value: fmt(s.significant), note: "M5+ worldwide, M4+ in the Iran region" },
    { label: "Largest", value: s.largest ? mag(s.largest) : "–", note: s.largest?.place ?? "" },
  ];
});

const description = computed(() => {
  const s = summary.value;
  if (!s) return `Earthquakes in Iran and worldwide in ${label}, from USGS and EMSC.`;
  const largest = s.largest ? ` Largest: ${mag(s.largest)}, ${s.largest.place || "unnamed location"}.` : "";
  return `${fmt(s.events)} earthquakes in ${label}${ongoing ? " so far" : ""}: ${fmt(s.region)} in Iran and adjacent areas, ${fmt(s.significant)} significant.${largest}`;
});

const path = `/archive/${month}/`;
const title = `Earthquakes in Iran and worldwide, ${label} | FEZfm`;
usePageSeo(() => ({
  path,
  title,
  description: description.value,
  noindex: (summary.value?.events ?? 0) < MIN_INDEXED_EVENTS,
}));

useJsonLd(() => [
  organization,
  {
    "@type": "Dataset",
    "@id": `${site}${path}#dataset`,
    name: `Earthquakes in Iran and worldwide, ${label}`,
    description: lead.value || description.value,
    url: `${site}${path}`,
    temporalCoverage: monthInterval(month),
    ...(index.value ? { dateModified: index.value.generated_at } : {}),
    ...datasetBase((summary.value?.sources ?? ["usgs", "emsc"]).filter((s): s is keyof typeof SOURCES => s in SOURCES)),
    distribution: [
      download(`${site}/data/archive/${month}.csv`, `${label}, CSV`),
      download(`${site}/data/archive/${month}.json`, `${label}, JSON`),
    ],
  },
  breadcrumbs(site, [
    { name: "FEZfm", path: "/" },
    { name: "Archive", path: "/archive/" },
    { name: label, path },
  ]),
]);
</script>
