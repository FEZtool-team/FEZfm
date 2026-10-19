<template>
  <figure class="rounded-lg border border-glass p-4">
    <figcaption class="flex items-baseline justify-between gap-2">
      <span class="text-sm text-fez-100">Events per day, Iran and adjacent areas</span>
      <span class="text-xs text-fez-500">last 30 days</span>
    </figcaption>

    <div class="relative mt-3" @mouseleave="hover = null">
      <svg :viewBox="`0 0 ${W} ${H}`" class="h-28 w-full" preserveAspectRatio="none" aria-hidden="true">
        <line v-for="g in grid" :key="g" x1="0" :x2="W" :y1="y(g)" :y2="y(g)" class="stroke-fez-700" stroke-width="1" vector-effect="non-scaling-stroke" />
        <path
          v-for="(d, i) in days"
          :key="d.day"
          :d="bar(i, d.region)"
          class="transition-opacity"
          :class="hover === null || hover === i ? 'fill-fm-500' : 'fill-fm-500/40'"
        />
        <!-- Hit targets wider than the bars. -->
        <rect v-for="(d, i) in days" :key="`hit-${d.day}`" :x="i * step" y="0" :width="step" :height="H" fill="transparent" @mouseenter="hover = i" />
      </svg>
      <div
        v-if="hover !== null && days[hover]"
        class="pointer-events-none absolute -top-2 z-10 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-md border border-glass-strong bg-fez-800 px-2.5 py-1.5 text-xs shadow-panel"
        :style="{ left: `${((hover + 0.5) / days.length) * 100}%` }"
      >
        <span class="text-fez-400">{{ days[hover].day }}</span>
        <span class="ml-2 tabular-nums text-fez-50">{{ days[hover].region }} events</span>
      </div>
    </div>
    <div class="mt-1 flex justify-between text-[11px] tabular-nums text-fez-500">
      <span>{{ days[0]?.day.slice(5) }}</span>
      <span>max {{ max }}</span>
      <span>{{ days[days.length - 1]?.day.slice(5) }}</span>
    </div>

    <!-- sr-only on the table itself does not clip its rows, which then extend the page below the footer. -->
    <div class="sr-only">
      <table>
        <caption>Events per day in Iran and adjacent areas</caption>
        <thead><tr><th>Day</th><th>Events</th></tr></thead>
        <tbody><tr v-for="d in days" :key="d.day"><td>{{ d.day }}</td><td>{{ d.region }}</td></tr></tbody>
      </table>
    </div>
  </figure>
</template>

<script setup lang="ts">
const { latest } = useQuakes();
const hover = ref<number | null>(null);

const W = 300;
const H = 100;
const GAP = 2;

const days = computed(() => latest.value?.daily ?? []);
const max = computed(() => Math.max(1, ...days.value.map((d) => d.region)));
const step = computed(() => W / Math.max(1, days.value.length));
const grid = computed(() => [max.value / 2, max.value]);
const y = (v: number) => H - (v / max.value) * (H - 4);

// Bar anchored to the baseline with a 4px-radius rounded top (radius shrinks for short bars).
const bar = (i: number, v: number) => {
  const x = i * step.value + GAP / 2;
  const w = Math.max(1, step.value - GAP);
  const top = y(v);
  const h = H - top;
  if (h <= 0) return "";
  const r = Math.min(4, w / 2, h);
  return `M${x},${H}V${top + r}Q${x},${top} ${x + r},${top}H${x + w - r}Q${x + w},${top} ${x + w},${top + r}V${H}Z`;
};
</script>
