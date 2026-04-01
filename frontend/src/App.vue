<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
</script>

<template>
  <div class="flex h-full overflow-hidden bg-dark-900">
    <!-- Sidebar -->
    <AppSidebar class="flex-shrink-0" />

    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden min-w-0">
      <AppHeader class="flex-shrink-0" />
      <main class="flex-1 overflow-auto p-6 bg-dark-900 min-h-0">
        <RouterView />
      </main>
    </div>
  </div>
</template>
