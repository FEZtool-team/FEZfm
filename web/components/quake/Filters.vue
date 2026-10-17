<template>
  <div class="flex flex-wrap items-center gap-2 text-sm">
    <div class="flex rounded-full border border-glass p-1" role="group" aria-label="Time window">
      <button
        v-for="(w, key) in WINDOWS"
        :key="key"
        type="button"
        class="rounded-full px-3 py-1 transition-colors"
        :class="win === key ? 'bg-fez-50 text-fez-900' : 'text-fez-300 hover:text-fez-50'"
        :aria-pressed="win === key"
        @click="win = key"
      >
        {{ key }}
      </button>
    </div>

    <label class="sr-only" for="scope">Area</label>
    <select id="scope" v-model="scope" class="field w-auto rounded-full py-1.5 pr-8">
      <option v-for="(label, key) in SCOPES" :key="key" :value="key">{{ label }}</option>
    </select>

    <label class="sr-only" for="minmag">Minimum magnitude</label>
    <select id="minmag" v-model.number="minMag" class="field w-auto rounded-full py-1.5 pr-8">
      <option v-for="m in [0, 2.5, 3, 4, 5, 6]" :key="m" :value="m">{{ m === 0 ? "Any magnitude" : `M${m}+` }}</option>
    </select>
  </div>
</template>

<script setup lang="ts">
const { win, scope, minMag } = useQuakes();
</script>
