<template>
  <div class="flex flex-wrap items-center gap-2 text-sm">
    <div v-if="!hideWindow" class="flex rounded-full border border-glass p-1" role="group" aria-label="Time window">
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

    <label class="sr-only" :for="`${uid}-scope`">Area</label>
    <select :id="`${uid}-scope`" v-model="scope" class="field w-auto rounded-full py-1.5 pr-8">
      <option v-for="(label, key) in SCOPES" :key="key" :value="key">{{ label }}</option>
    </select>

    <label class="sr-only" :for="`${uid}-minmag`">Minimum magnitude</label>
    <select :id="`${uid}-minmag`" v-model.number="minMag" class="field w-auto rounded-full py-1.5 pr-8">
      <option v-for="m in [0, 2.5, 3, 4, 5, 6]" :key="m" :value="m">{{ m === 0 ? "Any magnitude" : `M${m}+` }}</option>
    </select>

    <template v-if="more">
      <label class="sr-only" :for="`${uid}-depth`">Depth</label>
      <select :id="`${uid}-depth`" v-model="depth" class="field w-auto rounded-full py-1.5 pr-8">
        <option v-for="(d, key) in DEPTHS" :key="key" :value="key">{{ d.label }}</option>
      </select>

      <label class="sr-only" :for="`${uid}-flag`">Event type</label>
      <select :id="`${uid}-flag`" v-model="flag" class="field w-auto rounded-full py-1.5 pr-8">
        <option v-for="(label, key) in FLAGS" :key="key" :value="key">{{ label }}</option>
      </select>

      <label class="sr-only" :for="`${uid}-source`">Reported by</label>
      <select :id="`${uid}-source`" v-model="source" class="field w-auto rounded-full py-1.5 pr-8">
        <option value="all">Any source</option>
        <option v-for="(label, key) in SOURCE_LABELS" :key="key" :value="key">Reported by {{ label }}</option>
      </select>
    </template>
  </div>
</template>

<script setup lang="ts">
// `more` adds depth, event type and source; `hideWindow` is for pages with their own time range.
withDefaults(defineProps<{ more?: boolean; hideWindow?: boolean }>(), { more: false, hideWindow: false });
const { win, scope, minMag, depth, flag, source } = useQuakes();
const uid = useId();
</script>
