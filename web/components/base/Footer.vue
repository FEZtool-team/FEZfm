<template>
  <footer class="border-t border-glass bg-fez-950">
    <div class="mx-auto flex max-w-7xl flex-col gap-4 px-gutter py-8 text-xs text-fez-500 lg:flex-row lg:items-center lg:justify-between">
      <p>
        FEZfm is part of <a :href="cfg.homeUrl" class="text-fez-300 hover:text-fez-50">FEZtool</a>, free and easy tools for Earth sciences.
        Data from USGS and EMSC. Not an official warning service.
      </p>
      <p class="flex flex-wrap gap-x-4 gap-y-2">
        <a :href="cfg.toolUrl" class="hover:text-fez-50">FEZfm on feztool.com</a>
        <a :href="cfg.docsUrl" class="hover:text-fez-50">FEZtool docs</a>
        <a :href="cfg.repoUrl" target="_blank" rel="noopener" class="hover:text-fez-50">Source code</a>
        <NuxtLink to="/about" class="hover:text-fez-50">Sources and method</NuxtLink>
        <span>&copy; {{ year }} FEZtool</span>
      </p>
    </div>
  </footer>
</template>

<script lang="ts" setup>
const cfg = useRuntimeConfig().public;
const year = new Date().getFullYear();
</script>
