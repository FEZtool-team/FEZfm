<template>
  <div ref="root" class="max-w-[calc(100%-1.5rem)] rounded-md border border-glass bg-fez-900/85 text-[11px] text-fez-300 backdrop-blur">
    <button
      type="button"
      class="flex w-full items-center justify-between gap-3 px-3 py-2 text-fez-100"
      :aria-expanded="open"
      @click="open = !open"
    >
      <span class="font-medium">Legend and layers</span>
      <ChevronIcon class="text-base text-fez-400 transition-transform" :class="open ? '' : 'rotate-180'" />
    </button>

    <div v-show="open" class="border-t border-glass px-3 pb-2.5 pt-2">
      <p class="mb-1.5 text-fez-400">Depth</p>
      <div class="flex items-end gap-2">
        <div v-for="([km, t], i) in DEPTH_STOPS" :key="km" class="flex flex-col items-center gap-1">
          <span class="h-3 w-3 rounded-full ring-1 ring-map-ink/80" :class="swatch[t]" />
          <span>{{ i === DEPTH_STOPS.length - 1 ? `${km}+` : km }}</span>
        </div>
        <span class="pb-0.5 text-fez-500">km</span>
      </div>

      <p class="mb-1.5 mt-2.5 text-fez-400">Magnitude <span class="text-fez-500">at this zoom</span></p>
      <div class="flex items-center gap-2.5">
        <span v-for="m in [3, 5, 7]" :key="m" class="flex items-center gap-1">
          <span
            class="inline-block rounded-full bg-fez-400/60 ring-1 ring-fez-50/80 transition-all"
            :style="{ width: `${size(m)}px`, height: `${size(m)}px` }"
          />
          {{ m }}
        </span>
      </div>

      <fieldset class="mt-2.5 space-y-1">
        <legend class="mb-1 text-fez-400">Layers</legend>
        <label v-for="row in rows" :key="row.key" class="flex cursor-pointer items-center gap-2 text-fez-300 hover:text-fez-50">
          <input v-model="layers[row.key]" type="checkbox" class="h-3 w-3 accent-fm-500" />
          <span class="w-4" :class="row.swatch" />
          {{ row.label }}
        </label>
      </fieldset>
    </div>
  </div>
</template>

<script setup lang="ts">
import ChevronIcon from "~icons/material-symbols-light/keyboard-arrow-down-rounded";
import type { MapLayers } from "~/composables/useTokens";

const props = defineProps<{ scale: number }>();
const layers = defineModel<MapLayers>("layers", { required: true });

// Literal class names so Tailwind's content scan keeps them.
const swatch: Record<string, string> = {
  "fm-100": "bg-fm-100",
  "fm-300": "bg-fm-300",
  "fm-500": "bg-fm-500",
  "fm-700": "bg-fm-700",
};
const rows: { key: keyof MapLayers; label: string; swatch: string }[] = [
  { key: "zones", label: "Monitored zones", swatch: "h-0 border-t-2 border-dashed border-fm-400" },
  { key: "plates", label: "Plate boundaries", swatch: "h-0 border-t-2 border-map-plate" },
  { key: "faults", label: "Active faults (GEM)", swatch: "h-0 border-t border-fez-400" },
  { key: "relief", label: "GEBCO relief", swatch: "h-2.5 rounded-sm bg-gradient-to-r from-fm-700 via-fm-300 to-fez-500" },
];
const size = (m: number) => 2 * magRadius(m) * props.scale;

// Open on tall maps, folded on short ones (phones, the feed page) where it would cover the map.
const root = ref<HTMLDivElement>();
const open = ref(true);
onMounted(() => (open.value = (root.value?.parentElement?.clientHeight ?? 0) >= 520));
</script>
