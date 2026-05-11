<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LayoutDashboard,
  MessageCircle,
  Activity,
  BookOpen,
  Settings,
  ChevronLeft,
  ChevronRight,
  Brain
} from 'lucide-vue-next'

const { t } = useI18n()
const router = useRouter()

const navItems = [
  { path: '/', name: 'dashboard', label: 'nav.dashboard', icon: LayoutDashboard },
  { path: '/knowledge', name: 'knowledge', label: 'nav.knowledge', icon: MessageCircle },
  { path: '/diagnosis', name: 'diagnosis', label: 'nav.diagnosis', icon: Activity },
  { path: '/sop', name: 'sop', label: 'nav.sop', icon: BookOpen },
  { path: '/settings', name: 'settings', label: 'nav.settings', icon: Settings }
]

const isCollapsed = computed(() => false)

function isActive(path: string) {
  return router.currentRoute.value.path === path
}

function navigate(path: string) {
  if (router.currentRoute.value.path !== path) {
    router.push(path)
  }
}
</script>

<template>
  <aside
    :class="[
      'flex flex-col bg-dark-800 border-r border-dark-700 transition-all duration-300',
      isCollapsed ? 'w-16' : 'w-64'
    ]"
  >
    <!-- Logo -->
    <div class="flex items-center gap-3 px-4 py-5 border-b border-dark-700">
      <div class="flex items-center justify-center w-10 h-10 rounded-xl bg-primary-500/20 text-primary-400">
        <Brain :size="22" />
      </div>
      <div v-if="!isCollapsed" class="flex flex-col">
        <span class="text-lg font-bold text-dark-100">SOPRCA</span>
        <span class="text-xs text-dark-400">{{ t('nav.diagnosis') }}</span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 py-4 px-3 space-y-1">
      <button
        v-for="item in navItems"
        :key="item.path"
        @click="navigate(item.path)"
        :class="[
          'flex items-center gap-3 w-full px-3 py-2.5 rounded-lg transition-all duration-200',
          'hover:bg-dark-700 group cursor-pointer',
          isActive(item.path)
            ? 'bg-primary-500/15 text-primary-400 border-l-2 border-primary-500'
            : 'text-dark-300 hover:text-dark-100'
        ]"
      >
        <component
          :is="item.icon"
          :size="20"
          :class="[
            'transition-colors',
            isActive(item.path) ? 'text-primary-400' : 'text-dark-400 group-hover:text-dark-200'
          ]"
        />
        <span
          v-if="!isCollapsed"
          :class="[
            'font-medium transition-colors',
            isActive(item.path) ? 'text-primary-400' : ''
          ]"
        >
          {{ t(item.label) }}
        </span>
      </button>
    </nav>

    <!-- Collapse Toggle -->
    <div class="p-3 border-t border-dark-700">
      <button
        class="flex items-center justify-center w-full py-2 rounded-lg text-dark-400 hover:text-dark-200 hover:bg-dark-700 transition-all cursor-pointer"
      >
        <ChevronLeft v-if="!isCollapsed" :size="18" />
        <ChevronRight v-else :size="18" />
      </button>
    </div>
  </aside>
</template>
