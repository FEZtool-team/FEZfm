<template>
  <button
    type="button"
    class="grid h-9 w-9 place-items-center rounded-full border border-glass text-fez-300 transition-colors hover:border-glass-strong hover:text-fez-50"
    :aria-label="`Color theme: ${labels[preference]}. Switch to ${labels[next]}.`"
    :title="`Theme: ${labels[preference]}`"
    @click="cycle"
  >
    <SystemIcon v-if="preference === 'system'" class="text-lg" aria-hidden="true" />
    <SunIcon v-else-if="preference === 'light'" class="text-lg" aria-hidden="true" />
    <MoonIcon v-else class="text-lg" aria-hidden="true" />
  </button>
</template>

<script setup lang="ts">
import SystemIcon from "~icons/material-symbols-light/contrast";
import SunIcon from "~icons/material-symbols-light/light-mode-outline";
import MoonIcon from "~icons/material-symbols-light/dark-mode-outline";

const { preference, cycle } = useTheme();
const labels = { system: "system", light: "light", dark: "dark" } as const;
const next = computed(() =>
  preference.value === "system" ? "light" : preference.value === "light" ? "dark" : "system"
);
</script>
