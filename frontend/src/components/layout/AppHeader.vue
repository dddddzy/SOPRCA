<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { Sun, Moon, Monitor, Bell, User } from 'lucide-vue-next'

const route = useRoute()
const themeStore = useThemeStore()

const pageTitle = computed(() => {
  return (route.meta.title as string) || 'SOPRCA'
})

const pageIcon = computed(() => {
  return route.meta.icon as string
})

function toggleTheme() {
  const themes: Array<'dark' | 'light' | 'auto'> = ['dark', 'light', 'auto']
  const currentIndex = themes.indexOf(themeStore.theme)
  const nextIndex = (currentIndex + 1) % themes.length
  themeStore.setTheme(themes[nextIndex])
}

const themeIcon = computed(() => {
  switch (themeStore.theme) {
    case 'dark': return Moon
    case 'light': return Sun
    default: return Monitor
  }
})

const themeLabel = computed(() => {
  switch (themeStore.theme) {
    case 'dark': return '暗色'
    case 'light': return '亮色'
    default: return '自动'
  }
})
</script>

<template>
  <header class="flex items-center justify-between h-16 px-6 bg-dark-800 border-b border-dark-700">
    <!-- Page Title -->
    <div class="flex items-center gap-3">
      <h1 class="text-xl font-semibold text-dark-100">{{ pageTitle }}</h1>
    </div>

    <!-- Right Actions -->
    <div class="flex items-center gap-3">
      <!-- Theme Toggle -->
      <button
        @click="toggleTheme"
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-dark-300 hover:text-dark-100 hover:bg-dark-700 transition-all cursor-pointer"
        :title="`当前: ${themeLabel}`"
      >
        <component :is="themeIcon" :size="18" />
        <span class="text-sm">{{ themeLabel }}</span>
      </button>

      <!-- Notifications -->
      <button class="relative p-2 rounded-lg text-dark-300 hover:text-dark-100 hover:bg-dark-700 transition-all cursor-pointer">
        <Bell :size="20" />
        <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
      </button>

      <!-- User -->
      <button class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-dark-300 hover:text-dark-100 hover:bg-dark-700 transition-all cursor-pointer">
        <div class="w-7 h-7 rounded-full bg-primary-500/20 text-primary-400 flex items-center justify-center">
          <User :size="16" />
        </div>
        <span class="text-sm">Admin</span>
      </button>
    </div>
  </header>
</template>
