<template>
  <dl class="grid grid-cols-2 border-l border-t border-glass sm:grid-cols-4">
    <div v-for="s in stats" :key="s.label" class="border-b border-r border-glass px-4 py-3.5">
      <dt class="text-xs text-fez-400">{{ s.label }}</dt>
      <dd class="mt-1 text-2xl font-light tabular-nums text-fez-50">{{ s.value }}</dd>
      <dd v-if="s.note" class="mt-0.5 truncate text-xs text-fez-500" :title="s.note">{{ s.note }}</dd>
    </div>
  </dl>
</template>

<script setup lang="ts">
const { filtered, win } = useQuakes();

const stats = computed(() => {
  const list = filtered.value;
  const largest = list.reduce<(typeof list)[number] | null>((a, q) => ((q.mag ?? -9) > (a?.mag ?? -9) ? q : a), null);
  return [
    { label: `Events, ${WINDOWS[win.value].label.toLowerCase()}`, value: list.length, note: "" },
    { label: "Iran and adjacent areas", value: list.filter((q) => q.region).length, note: "" },
    { label: "Significant", value: list.filter((q) => q.sig).length, note: "M5+ worldwide, M4+ in the Iran region" },
    {
      label: "Largest",
      value: largest?.mag != null ? `M${largest.mag.toFixed(1)}` : "–",
      note: largest?.place ?? "",
    },
  ];
});
</script>
