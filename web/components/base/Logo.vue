<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    :viewBox="layouts[variant].viewBox"
    role="img"
    aria-label="FEZtool"
    class="text-fez-50"
  >
    <path :d="MARK_MAIN" fill="currentColor" />
    <path :d="MARK_ACCENT" fill="rgb(var(--logo-accent))" />
    <path v-if="variant !== 'mark'" :d="WORDMARK" fill="currentColor" :transform="layouts[variant].wordmark" />
  </svg>
</template>

<script setup lang="ts">
import { MARK_MAIN, MARK_ACCENT, WORDMARK } from "~/data/logo";

// Mark is 450 x 250, the FEZTOOL lettering 450 x 62 (Figma 360-838).
// The fill follows the text color, so the logo works in both themes.
withDefaults(defineProps<{ variant?: "mark" | "horizontal" | "stacked" }>(), { variant: "mark" });

const layouts = {
  mark: { viewBox: "0 0 450 250", wordmark: "" },
  // Lettering scaled to 90 units tall and centred beside the mark.
  horizontal: { viewBox: "0 0 1163.2 250", wordmark: "translate(510 80) scale(1.4516)" },
  // Lettering under the mark, as in the Figma base logo (node 360-116).
  stacked: { viewBox: "0 0 450 337", wordmark: "translate(0 275)" },
};
</script>
