<template>
  <div class="rounded-md border border-glass bg-fez-900/85 px-3 py-2.5 text-[11px] text-fez-300 backdrop-blur">
    <p class="mb-1.5 text-fez-400">Depth</p>
    <div class="flex items-end gap-2">
      <div v-for="([km, t], i) in DEPTH_STOPS" :key="km" class="flex flex-col items-center gap-1">
        <span class="h-3 w-3 rounded-full ring-1 ring-fez-50/80" :class="swatch[t]" />
        <span>{{ i === DEPTH_STOPS.length - 1 ? `${km}+` : km }}</span>
      </div>
      <span class="pb-0.5 text-fez-500">km</span>
    </div>
    <p class="mb-1.5 mt-2.5 text-fez-400">Magnitude</p>
    <div class="flex items-center gap-2.5">
      <span v-for="m in [3, 5, 7]" :key="m" class="flex items-center gap-1">
        <span class="inline-block rounded-full bg-fez-400/60 ring-1 ring-fez-50/80" :style="{ width: `${size(m)}px`, height: `${size(m)}px` }" />
        {{ m }}
      </span>
    </div>
    <div class="mt-2.5 flex items-center gap-3 text-fez-400">
      <span class="flex items-center gap-1.5"><span class="h-0 w-4 border-t-2 border-dashed border-fm-400" />Monitored zone</span>
      <span class="flex items-center gap-1.5"><span class="h-0 w-4 border-t border-fez-400/60" />Active fault</span>
    </div>
  </div>
</template>

<script setup lang="ts">
// Literal class names so Tailwind's content scan keeps them.
const swatch: Record<string, string> = {
  "fm-100": "bg-fm-100",
  "fm-300": "bg-fm-300",
  "fm-500": "bg-fm-500",
  "fm-700": "bg-fm-700",
};
const size = (m: number) => 2 * magRadius(m);
</script>
