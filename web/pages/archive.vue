<template>
  <div class="mx-auto max-w-7xl px-gutter py-8">
    <header>
      <h1 class="text-3xl font-bold text-fez-50 sm:text-4xl">Archive</h1>
      <p class="paragraph mt-2 max-w-2xl text-sm">
        Every merged event the monitor has stored, one calendar month (UTC) at a time. Each month is also available as
        CSV.
      </p>
    </header>

    <div class="mt-5 flex flex-wrap items-center gap-2 text-sm">
      <label class="sr-only" for="month">Month</label>
      <select id="month" v-model="month" class="field w-auto rounded-full py-1.5 pr-8" :disabled="!months.length">
        <option v-for="m in months" :key="m.month" :value="m.month">{{ monthLabel(m.month) }} ({{ m.events }})</option>
      </select>
      <QuakeFilters more hide-window class="contents" />
      <a
        v-if="month"
        :href="`${base}data/archive/${month}.csv`"
        download
        class="rounded-full border border-glass-strong px-3 py-1.5 text-xs text-fez-100 transition-colors hover:border-fez-400 hover:text-fez-50"
      >Download CSV</a>
    </div>

    <p class="mt-3 text-xs text-fez-400">
      <template v-if="error">The archive could not be loaded ({{ error }}).</template>
      <template v-else-if="loading">Loading {{ monthLabel(month) }}…</template>
      <template v-else-if="month">{{ shownEvents.length }} of {{ events.length }} events in {{ monthLabel(month) }} match these filters.</template>
      <template v-else>No archived months yet.</template>
    </p>

    <ClientOnly>
      <QuakeMap class="mt-4 h-[420px] lg:h-[520px]" :events="shownEvents" :selected="selected" @select="select" />
      <template #fallback>
        <div class="mt-4 h-[420px] rounded-lg border border-glass bg-fez-950 lg:h-[520px]" />
      </template>
    </ClientOnly>

    <section class="mt-6" aria-labelledby="archive-list">
      <h2 id="archive-list" class="text-lg font-semibold text-fez-100">Events</h2>
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
            <tr
              v-for="q in rows"
              :key="q.id"
              class="cursor-pointer border-b border-glass transition-colors last:border-0 hover:bg-fez-800/50"
              :class="selected === q.id ? 'bg-fez-800/70' : ''"
              :aria-current="selected === q.id ? 'true' : undefined"
              tabindex="0"
              @click="select(q.id, true)"
              @keydown.enter="select(q.id, true)"
            >
              <td class="whitespace-nowrap px-4 py-2.5 tabular-nums text-fez-300">{{ q.t.slice(0, 16).replace("T", " ") }}</td>
              <td class="px-4 py-2.5 text-right tabular-nums" :class="q.sig ? 'font-medium text-fm-300' : 'text-fez-100'">
                {{ q.mag != null ? q.mag.toFixed(1) : "–" }}
              </td>
              <td class="whitespace-nowrap px-4 py-2.5 text-right tabular-nums text-fez-300">{{ q.depth != null ? `${q.depth.toFixed(0)} km` : "–" }}</td>
              <td class="px-4 py-2.5 text-fez-100">
                {{ q.place || "Unnamed location" }}
                <span v-if="q.zone" class="ml-1 text-xs text-fm-300">{{ zoneLabel(q.zone) }} zone</span>
              </td>
              <td class="hidden px-4 py-2.5 text-xs text-fez-400 md:table-cell">
                {{ q.sources.map((s) => SOURCE_LABELS[s.name] ?? s.name).join(", ") }}
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!loading && month && !shownEvents.length" class="px-5 py-10 text-center text-sm text-fez-400">
          No events match these filters in {{ monthLabel(month) }}.
        </p>
        <div v-if="shownEvents.length > limit" class="border-t border-glass p-4 text-center">
          <BaseButton variant="ghost" @click="limit += STEP">Show more ({{ shownEvents.length - limit }} left)</BaseButton>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { Quake } from "~/composables/useQuakes";

interface MonthInfo {
  month: string;
  events: number;
  region: number;
  significant: number;
}

const STEP = 100;
const base = useRuntimeConfig().app.baseURL;
const { matches } = useQuakes();

const months = ref<MonthInfo[]>([]);
const month = ref("");
const events = ref<Quake[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const selected = ref<string | null>(null);
const limit = ref(STEP);

const shownEvents = computed(() => events.value.filter(matches));
const rows = computed(() => shownEvents.value.slice(0, limit.value));
watch(shownEvents, () => (limit.value = STEP));

const monthLabel = (m: string) =>
  m ? new Date(`${m}-01T00:00:00Z`).toLocaleDateString("en-GB", { month: "long", year: "numeric", timeZone: "UTC" }) : "";

const getJson = async (path: string) => {
  const r = await fetch(`${base}data/archive/${path}?t=${Math.floor(Date.now() / 60e3)}`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
};

watch(month, async (m) => {
  if (!m) return;
  loading.value = true;
  selected.value = null;
  try {
    events.value = (await getJson(`${m}.json`)).events;
    error.value = null;
  } catch (e) {
    events.value = [];
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
});

onMounted(async () => {
  try {
    months.value = (await getJson("index.json")).months;
    month.value = months.value[0]?.month ?? "";
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
});

const select = (id: string, fromList = false) => {
  selected.value = id;
  if (fromList) return;
  // A quake picked on the map may be past the end of the list.
  const i = shownEvents.value.findIndex((q) => q.id === id);
  if (i >= limit.value) limit.value = Math.ceil((i + 1) / STEP) * STEP;
  nextTick(() => document.querySelector('tr[aria-current="true"]')?.scrollIntoView({ block: "nearest", behavior: "smooth" }));
};

useHead({ title: "FEZfm: earthquake archive" });
</script>
