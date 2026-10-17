<template>
  <nav class="glass fixed inset-x-0 top-0 z-40 border-x-0 border-t-0" aria-label="Main">
    <div class="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-gutter">
      <div class="flex items-center gap-3">
        <a :href="homeUrl" class="shrink-0" aria-label="FEZtool home">
          <BaseLogo variant="mark" class="h-7 w-auto" />
        </a>
        <NuxtLink to="/" class="flex items-center gap-2">
          <ToolsToolBadge size="sm" />
          <span class="text-sm text-fez-100">Earthquake monitor</span>
        </NuxtLink>
      </div>

      <ul class="hidden items-center gap-7 text-sm text-fez-400 md:flex">
        <li v-for="link in links" :key="link.to">
          <NuxtLink :to="link.to" class="transition-colors hover:text-fez-50" active-class="text-fez-50">{{ link.label }}</NuxtLink>
        </li>
      </ul>

      <div class="flex items-center gap-2">
        <BaseThemeToggle />
        <button
          type="button"
          class="-mr-2 rounded-md p-2 text-fez-100 md:hidden"
          :aria-expanded="open"
          aria-controls="mobile-menu"
          @click="open = !open"
        >
          <span class="sr-only">{{ open ? "Close menu" : "Open menu" }}</span>
          <CloseIcon v-if="open" class="text-2xl" />
          <MenuIcon v-else class="text-2xl" />
        </button>
      </div>
    </div>

    <div v-show="open" id="mobile-menu" class="border-t border-glass px-gutter pb-4 pt-2 md:hidden">
      <ul class="flex flex-col text-base text-fez-200">
        <li v-for="link in links" :key="link.to">
          <NuxtLink :to="link.to" class="block py-2.5" @click="open = false">{{ link.label }}</NuxtLink>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script lang="ts" setup>
import MenuIcon from "~icons/material-symbols-light/menu-rounded";
import CloseIcon from "~icons/material-symbols-light/close-rounded";

const homeUrl = useRuntimeConfig().public.homeUrl;
const links = [
  { label: "Feed", to: "/" },
  { label: "Map", to: "/map" },
  { label: "Data", to: "/downloads" },
  { label: "About", to: "/about" },
];
const open = ref(false);
</script>
