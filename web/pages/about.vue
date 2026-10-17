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
        <dt class="text-fez-100">IRSC, Iranian Seismological Center, Institute of Geophysics, University of Tehran</dt>
        <dd class="paragraph">
          The national network bulletin for Iran and adjacent areas (lat 24-41, lon 42-64), magnitude 2.5 and above.
          Read from the bulletin search at irsc.ut.ac.ir, as Faultiuo does.
        </dd>
      </div>
      <div>
        <dt class="text-fez-100">USGS, United States Geological Survey</dt>
        <dd class="paragraph">The global FDSN event service at earthquake.usgs.gov.</dd>
      </div>
      <div>
        <dt class="text-fez-100">EMSC, European-Mediterranean Seismological Centre</dt>
        <dd class="paragraph">
          The FDSN event service at seismicportal.eu. EMSC also redistributes reports from Iranian agencies, which keeps
          Iranian coverage when IRSC cannot be reached.
        </dd>
      </div>
    </dl>

    <h2 class="mt-10 text-xl font-semibold text-fez-100">How it works</h2>
    <ol class="paragraph mt-4 list-decimal space-y-2 pl-5 text-sm">
      <li>Every 30 minutes a GitHub Actions job requests the last two days from each source. Re-reading two days picks up late reports and revised magnitudes.</li>
      <li>Reports are stored in a DuckDB database, one row per source and event.</li>
      <li>
        Reports from different sources are merged into one event when they are within 45 seconds, 80 km and one
        magnitude unit of each other. Inside the Iran region the IRSC solution is preferred, elsewhere USGS, then EMSC.
      </li>
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
      <li v-if="latest?.zones_approximate !== false">
        Fault zone traces are approximate. Faultiuo's original traces live in KML files that are not yet published;
        FEZfm draws each zone from published fault locations and will switch to the original traces when they are added.
      </li>
      <li>Outside the Iran region only M2.5 and above are kept, so small events elsewhere are not shown.</li>
      <li>Magnitudes of different types (ML, mb, Mw) are shown as reported and are not converted.</li>
    </ul>

    <h2 class="mt-10 text-xl font-semibold text-fez-100">Map data</h2>
    <p class="paragraph mt-4 text-sm">
      Country outlines from Natural Earth (public domain), drawn on the site itself so the map needs no tile service. Active faults from the GEM Global Active Faults Database
      (CC BY-SA 4.0).
    </p>
  </div>
</template>

<script setup lang="ts">
const { latest } = useQuakes();
useHead({ title: "FEZfm: sources and method" });
</script>
