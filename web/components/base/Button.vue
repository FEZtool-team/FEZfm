<template>
  <component
    :is="to ? NuxtLink : href ? 'a' : 'button'"
    :to="to"
    :href="href"
    :target="external ? '_blank' : undefined"
    :rel="external ? 'noopener' : undefined"
    :type="href || to ? undefined : type"
    class="inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-40"
    :class="variants[variant]"
  >
    <slot />
  </component>
</template>

<script setup lang="ts">
import { NuxtLink } from "#components";

type Variant = "primary" | "ghost" | "fm";

withDefaults(
  defineProps<{
    href?: string;
    /** In-app route, e.g. "/#request-demo"; works from every page. */
    to?: string;
    external?: boolean;
    variant?: Variant;
    type?: "button" | "submit";
  }>(),
  { variant: "primary", type: "button" }
);

// Tool variants are only for CTAs inside that tool's own panel.
const variants: Record<Variant, string> = {
  primary: "bg-fez-50 text-fez-900 hover:bg-fez-200",
  ghost: "border border-glass-strong text-fez-100 hover:border-fez-400 hover:text-fez-50",
  fm: "bg-fm-500 text-on-tool hover:bg-fm-400",
};
</script>
