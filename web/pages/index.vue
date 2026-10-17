<template>
  <div class="mx-auto max-w-7xl px-gutter py-8">
    <header class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 class="text-3xl font-light text-fez-50 sm:text-4xl">Recent earthquakes</h1>
        <p class="paragraph mt-2 max-w-2xl text-sm">
          Reports from the Iranian Seismological Center (IRSC), USGS and EMSC, merged into one feed and refreshed every
          30 minutes. All events in Iran and adjacent areas; elsewhere M{{ latest?.world_min_mag ?? 2.5 }} and above.
        </p>
      </div>
      <QuakeFilters />
    </header>

    <QuakeStatus class="mt-5" />
    <QuakeStats class="mt-5" />

    <div class="mt-6 grid gap-6 lg:grid-cols-12">
      <section class="lg:col-span-6 xl:col-span-5" aria-labelledby="feed-title">
        <h2 id="feed-title" class="sr-only">Event feed</h2>
        <div class="overflow-hidden rounded-lg border border-glass">
          <template v-if="latest">
            <QuakeCard
              v-for="q in shown"
              :key="q.id"
              :q="q"
              :now="now"
              :selected="selected === q.id"
              @select="select"
            />
            <p v-if="!filtered.length" class="px-5 py-10 text-center text-sm text-fez-400">
              No events match these filters in the {{ WINDOWS[win].label.toLowerCase() }}.
            </p>
            <div v-if="filtered.length > limit" class="p-4 text-center">
              <BaseButton variant="ghost" @click="limit += 100">Show more ({{ filtered.length - limit }} left)</BaseButton>
            </div>
          </template>
          <div v-else class="space-y-px" aria-hidden="true">
            <div v-for="i in 6" :key="i" class="h-[92px] animate-pulse bg-fez-800/40" />
          </div>
        </div>
      </section>

      <aside class="space-y-6 lg:col-span-6 xl:col-span-7">
        <ClientOnly>
          <QuakeMap class="h-[420px] lg:sticky lg:top-20 lg:h-[calc(100vh-14rem)]" :events="filtered" :selected="selected" @select="select" />
          <template #fallback>
            <div class="h-[420px] rounded-lg border border-glass bg-fez-950 lg:h-[calc(100vh-14rem)]" />
          </template>
        </ClientOnly>
      </aside>
    </div>

    <div class="mt-6 grid gap-6 lg:grid-cols-12">
      <QuakeDaily v-if="latest" class="lg:col-span-6 xl:col-span-5" />
    </div>
  </div>
</template>

<script setup lang="ts">
const { latest, filtered, now, win, selected } = useQuakes();
const limit = ref(100);
const shown = computed(() => filtered.value.slice(0, limit.value));
watch([filtered], () => (limit.value = 100));

const select = (id: string) => {
  selected.value = id;
  // Bring the card into view when the selection comes from the map.
  nextTick(() => document.querySelector('[aria-current="true"]')?.scrollIntoView({ block: "nearest", behavior: "smooth" }));
};

useHead({ title: "FEZfm: recent earthquakes" });
</script>
