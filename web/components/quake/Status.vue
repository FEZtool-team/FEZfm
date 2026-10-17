<template>
  <div class="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-fez-400">
    <span v-if="latest" class="flex items-center gap-2">
      <span class="relative flex h-2 w-2">
        <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-fm-400 opacity-60 motion-reduce:hidden" />
        <span class="relative inline-flex h-2 w-2 rounded-full bg-fm-400" />
      </span>
      Updated {{ ago(latest.generated_at, now) }} ({{ utc(latest.generated_at) }}). Next update in about {{ nextIn }}.
    </span>
    <span v-else-if="error">Data could not be loaded ({{ error }}).</span>
    <span v-else>Loading data…</span>

    <span v-for="s in latest?.sources ?? []" :key="s.source" class="flex items-center gap-1.5" :title="s.ok ? `Last reached ${s.last_ok}` : s.error ?? ''">
      <span class="inline-block h-1.5 w-1.5 rounded-full" :class="s.ok ? 'bg-fez-300' : 'border border-fez-400 bg-transparent'" />
      {{ SOURCE_LABELS[s.source] ?? s.source }}
      <span v-if="!s.ok" class="text-fez-300">unreachable{{ s.last_ok ? ` since ${ago(s.last_ok, now)}` : "" }}</span>
    </span>
  </div>
</template>

<script setup lang="ts">
const { latest, error, now } = useQuakes();

// GitHub's scheduler often starts runs 5-15 minutes late, so this is an estimate.
const nextIn = computed(() => {
  if (!latest.value) return "";
  const due = Date.parse(latest.value.generated_at) + latest.value.schedule_minutes * 60e3;
  const min = Math.round((due - now.value) / 60e3);
  return min > 1 ? `${min} min` : "a few minutes";
});
</script>
