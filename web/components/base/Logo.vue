<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    :viewBox="viewBox"
    role="img"
    :aria-label="lettering === 'fezfm' ? 'FEZfm' : 'FEZtool'"
    class="text-fez-50"
  >
    <path :d="MARK_MAIN" fill="currentColor" />
    <path :d="MARK_ACCENT" fill="rgb(var(--logo-accent))" />
    <path v-if="variant !== 'mark'" :d="words[lettering].d" fill="currentColor" :transform="layouts[variant].wordmark" />
  </svg>
</template>

<script setup lang="ts">
import { MARK_MAIN, MARK_ACCENT, WORDMARK, WORDMARK_FEZFM } from "~/data/logo";

// Mark is 450 x 250, the FEZTOOL lettering 450 x 62 (Figma 360-838) and the
// FEZFM lettering 337 x 62 on the same grid.
// The fill follows the text color, so the logo works in both themes.
const props = withDefaults(
  defineProps<{ variant?: "mark" | "horizontal" | "stacked"; lettering?: "feztool" | "fezfm" }>(),
  { variant: "mark", lettering: "feztool" }
);

const words = {
  feztool: { d: WORDMARK, width: 450 },
  fezfm: { d: WORDMARK_FEZFM, width: 337 },
};

const layouts = {
  mark: { wordmark: "" },
  // Lettering scaled to 90 units tall and centred beside the mark.
  horizontal: { wordmark: "translate(510 80) scale(1.4516)" },
  // Lettering under the mark, as in the Figma base logo (node 360-116).
  stacked: { wordmark: "translate(0 275)" },
};

// Clear space on both sides of the horizontal logo. Without it the last stem sits
// on the edge, and a width rounded down to whole pixels cuts it off at header size.
const PAD = 12;

const viewBox = computed(() => {
  const w = words[props.lettering].width;
  if (props.variant === "horizontal") return `${-PAD} 0 ${(510 + w * 1.4516 + 2 * PAD).toFixed(1)} 250`;
  if (props.variant === "stacked") return `0 0 ${Math.max(450, w)} 337`;
  return "0 0 450 250";
});
</script>
