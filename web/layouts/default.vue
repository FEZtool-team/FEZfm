<template>
  <div class="relative flex min-h-screen flex-col overflow-x-clip">
    <a
      href="#main"
      class="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-fez-50 focus:px-4 focus:py-2 focus:text-fez-900"
    >
      Skip to content
    </a>
    <BaseNavbar />
    <main id="main" class="flex-1 pt-16">
      <slot />
    </main>
    <BaseFooter />
  </div>
</template>
