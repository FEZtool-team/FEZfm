<template>
  <article
    class="group flex cursor-pointer gap-4 border-b border-glass px-4 py-4 transition-colors hover:bg-fez-800/50 sm:px-5"
    :class="selected ? 'bg-fez-800/70' : ''"
    :aria-current="selected ? 'true' : undefined"
    tabindex="0"
    @click="$emit('select', q.id)"
    @keydown.enter="$emit('select', q.id)"
  >
    <div
      class="grid h-12 w-12 shrink-0 place-items-center rounded-md border text-lg font-medium tabular-nums"
      :class="magClass"
      :aria-label="q.mag != null ? `Magnitude ${q.mag.toFixed(1)}` : 'Magnitude unknown'"
      :title="q.magType ? `Magnitude type: ${q.magType}` : undefined"
    >
      {{ q.mag != null ? q.mag.toFixed(1) : "–" }}
    </div>

    <div class="min-w-0 flex-1">
      <h3 class="text-[15px] leading-snug text-fez-50">{{ q.place || "Unnamed location" }}</h3>
      <p class="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-fez-400">
        <time :datetime="q.t" :title="utc(q.t)">{{ ago(q.t, now) }}</time>
        <span>{{ utc(q.t) }}</span>
        <span v-if="q.depth != null">Depth {{ q.depth.toFixed(0) }} km</span>
      </p>

      <div class="mt-2 flex flex-wrap items-center gap-1.5 text-[11px]">
        <span v-if="q.sig" class="rounded-full bg-fm-500 px-2 py-0.5 font-medium text-on-tool">Significant</span>
        <span v-if="q.sequence" class="rounded-full border border-fm-500/50 px-2 py-0.5 text-fm-300" title="5 or more events within 25 km in 6 hours">
          Active sequence
        </span>
        <span v-if="q.zone" class="rounded-full border border-fm-500/50 bg-fm-500/10 px-2 py-0.5 text-fm-300" :title="`${q.zoneKm} km from the zone trace`">
          {{ zoneLabel(q.zone) }} fault zone
        </span>
        <span class="ml-auto flex gap-1.5 text-fez-500">
          <template v-for="s in q.sources" :key="s.name">
            <a
              v-if="s.url"
              :href="s.url"
              target="_blank"
              rel="noopener"
              class="rounded border border-glass px-1.5 py-0.5 transition-colors hover:border-glass-strong hover:text-fez-100"
              :title="`Open on ${SOURCE_LABELS[s.name] ?? s.name}`"
              @click.stop
            >{{ SOURCE_LABELS[s.name] ?? s.name }}</a>
            <span v-else class="rounded border border-glass px-1.5 py-0.5">{{ SOURCE_LABELS[s.name] ?? s.name }}</span>
          </template>
        </span>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { Quake } from "~/composables/useQuakes";

const props = defineProps<{ q: Quake; now: number; selected?: boolean }>();
defineEmits<{ select: [id: string] }>();

// Stronger fill for larger magnitudes; text stays in text tokens except on the solid fill.
const magClass = computed(() => {
  const m = props.q.mag ?? 0;
  if (m >= 6) return "border-fm-400 bg-fm-500 text-on-tool shadow-glow-fm";
  if (m >= 5) return "border-fm-400 bg-fm-500 text-on-tool";
  if (m >= 4) return "border-fm-500/60 bg-fm-500/25 text-fez-50";
  if (m >= 3) return "border-fm-500/40 bg-fm-500/10 text-fez-100";
  return "border-glass text-fez-300";
});
</script>
