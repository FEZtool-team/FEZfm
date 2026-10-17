<template>
  <span
    class="inline-grid shrink-0 place-items-center rounded-md border border-fm-500/50 bg-fm-500/10 font-medium tracking-wide text-fm-300"
    :class="size === 'lg' ? 'h-14 w-14 text-xl' : size === 'sm' ? 'h-7 w-7 text-xs' : 'h-10 w-10 text-sm'"
    aria-label="FEZfm badge"
  >
    FM
  </span>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ size?: "sm" | "md" | "lg" }>(), { size: "md" });
</script>
