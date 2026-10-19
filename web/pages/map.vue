<template>
  <div class="relative h-[calc(100vh-4rem)]">
    <ClientOnly>
      <QuakeMap class="h-full rounded-none border-0" :events="filtered" :selected="selected" initial-view="iran" @select="(id) => (selected = id)" />
    </ClientOnly>
    <div class="glass absolute right-3 top-14 z-[500] max-w-[calc(100%-1.5rem)] space-y-3 rounded-lg p-3 sm:right-14 sm:top-3">
      <QuakeFilters more />
      <p class="text-xs text-fez-400">
        {{ filtered.length }} events shown. Select a circle for details.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { filtered, selected } = useQuakes();
useHead({ title: "FEZfm: earthquake map" });
</script>
