<template>
  <div class="mx-auto max-w-3xl px-gutter py-10">
    <div class="flex items-center gap-3">
      <ToolsToolBadge />
      <h1 class="text-3xl font-bold text-fez-50">Sources and method</h1>
    </div>
    <p class="paragraph mt-4">
      FEZfm is the fault and geohazard monitoring tool of FEZtool. This first version collects earthquake reports,
      merges them, and publishes a feed, a map and downloadable data. It builds on Faultiuo, a monitor for 21 active
      fault zones in Iran by Fariba Khosravani and Mahdi Farmahini Farahani.
    </p>

    <h2 class="mt-10 text-xl font-semibold text-fez-100">Sources</h2>
    <dl class="mt-4 space-y-4 text-sm">
      <div>
        <dt class="text-fez-100">USGS, United States Geological Survey</dt>
        <dd class="paragraph">The global FDSN event service at earthquake.usgs.gov.</dd>
      </div>
      <div>
        <dt class="text-fez-100">EMSC, European-Mediterranean Seismological Centre</dt>
        <dd class="paragraph">
          The FDSN event service at seismicportal.eu. EMSC also redistributes reports from Iranian agencies, and is the
          main source for Iran.
        </dd>
      </div>
      <div>
        <dt class="text-fez-100">IRSC, Iranian Seismological Center, Institute of Geophysics, University of Tehran</dt>
        <dd class="paragraph">
          The national network bulletin for Iran, magnitude 2.5 and above. Not collected at the moment: irsc.ut.ac.ir
          cannot be reached from outside Iran, where the collector runs. IRSC events collected earlier are kept. EMSC
          and USGS list fewer small Iranian events than IRSC does.
        </dd>
      </div>
    </dl>

    <h2 class="mt-10 text-xl font-semibold text-fez-100">How it works</h2>
    <ol class="paragraph mt-4 list-decimal space-y-2 pl-5 text-sm">
      <li>Every 30 minutes a GitHub Actions job requests the last two days from each source. Re-reading two days picks up late reports and revised magnitudes.</li>
      <li>Reports are stored in a DuckDB database, one row per source and event.</li>
      <li>
        Reports from different sources are merged into one event when they are within 45 seconds, 80 km and one
        magnitude unit of each other. USGS is preferred, then EMSC; inside the Iran region an earlier IRSC solution comes first.
      </li>
      <li>Each event is tagged with its country, or the nearest country within about 150 km for offshore events.</li>
      <li>Each event is checked against the monitored fault zones and flagged as significant or part of an active sequence.</li>
      <li>The site, the feed and the download files are rebuilt and published to GitHub Pages.</li>
    </ol>

    <h2 class="mt-10 text-xl font-semibold text-fez-100">Flags</h2>
    <dl class="mt-4 grid gap-x-6 gap-y-3 text-sm sm:grid-cols-[10rem_1fr]">
      <dt class="text-fez-100">Significant</dt>
      <dd class="paragraph">M5 or larger anywhere, or M4 or larger in Iran and adjacent areas.</dd>
      <dt class="text-fez-100">Active sequence</dt>
      <dd class="paragraph">At least 5 events within 25 km in 6 hours. This covers aftershock sequences and swarms alike.</dd>
      <dt class="text-fez-100">Fault zone</dt>
      <dd class="paragraph">The epicentre lies inside the buffer of one of the 21 zones Faultiuo monitors (20 km half-width, 40 km for Kopedagh, 50 km for Seimare and Zagros).</dd>
    </dl>

    <h2 class="mt-10 text-xl font-semibold text-fez-100">Limits</h2>
    <ul class="paragraph mt-4 list-disc space-y-2 pl-5 text-sm">
      <li>Delay: data are 30 to 45 minutes behind real time, and GitHub can delay scheduled runs further. Use official agencies for warnings.</li>
      <li v-if="meta?.zonesApproximate !== false">
        Fault zone traces are approximate. Faultiuo's original traces live in KML files that are not yet published;
        FEZfm draws each zone from published fault locations and will switch to the original traces when they are added.
      </li>
      <li>Outside the Iran region only M2.5 and above are kept, so small events elsewhere are not shown.</li>
      <li>Magnitudes of different types (ML, mb, Mw) are shown as reported and are not converted.</li>
    </ul>

    <h2 class="mt-10 text-xl font-semibold text-fez-100">Map data</h2>
    <p class="paragraph mt-4 text-sm">
      Every map layer is served by the site itself, so the map needs no tile service. Country outlines from Natural Earth
      (public domain). Active faults worldwide from the GEM Global Active Faults Database (CC BY-SA 4.0). Plate boundaries
      from Bird (2003), PB2002 (ODC-BY 1.0). The optional relief is shaded GEBCO Grid imagery from the GEBCO Compilation
      Group.
    </p>
  </div>
</template>

<script setup lang="ts">
import type { Latest } from "~/composables/useQuakes";
import { datasetBase, download, organization } from "~/data/schema";

const { data: meta } = await usePublicData("latest-meta", "latest.json", (d: Latest) => ({
  generatedAt: d.generated_at,
  zonesApproximate: d.zones_approximate,
}));

const site = useRuntimeConfig().public.siteUrl;
usePageSeo({
  path: "/about/",
  title: "Sources and method: how FEZfm merges earthquake reports | FEZfm",
  description:
    "How FEZfm merges USGS and EMSC earthquake reports every 30 minutes, tags fault zones in Iran and flags significant events and active sequences.",
});
useJsonLd(() => [
  organization,
  {
    "@type": "DataFeed",
    "@id": `${site}/about/#feed`,
    name: "FEZfm earthquake feed",
    description:
      "The last 7 days of earthquakes in Iran and worldwide, merged from USGS and EMSC reports and rebuilt every 30 minutes, with fault-zone, significant and active-sequence flags.",
    url: `${site}/`,
    ...(meta.value ? { dateModified: meta.value.generatedAt } : {}),
    ...datasetBase(),
    distribution: [
      download(`${site}/data/latest.json`, "Last 7 days, as used by this site, with source status"),
      download(`${site}/data/feed.xml`, "Atom feed: significant events, active sequences and M3.5+ in the Iran region"),
    ],
  },
]);
</script>
