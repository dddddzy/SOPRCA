<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import type { LogEntry } from '@/types'
import { Terminal, Minus, Plus, X } from 'lucide-vue-next'

const props = defineProps<{
  logs: LogEntry[]
}>()

const isCollapsed = ref(false)
const logContainer = ref<HTMLDivElement>()

const rawLogText = computed(() => {
  return props.logs
    .map(log => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`)
    .join('\n')
})

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function copyLogs() {
  navigator.clipboard.writeText(rawLogText.value)
}

const logLevelStyles: Record<string, string> = {
  info: 'text-cyan-400',
  success: 'text-emerald-400',
  warning: 'text-amber-400',
  error: 'text-red-400',
  primary: 'text-violet-400',
}

function getLogClass(level: LogEntry['level']) {
  return logLevelStyles[level] || 'text-dark-300'
}

watch(
  () => props.logs.length,
  async () => {
    await nextTick()
    if (logContainer.value && !isCollapsed.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }
)
</script>

<template>
  <!-- VSCode-style Bottom Panel -->
  <div class="relative flex flex-col bg-dark-900 border-t border-dark-700">
    <!-- Tab Bar -->
    <div class="flex items-center bg-dark-800/80 border-b border-dark-700/50 px-1">
      <!-- Active Tab -->
      <div class="flex items-center gap-1.5 px-3 py-1.5 text-xs text-dark-100 border-b-2 border-primary-500">
        <Terminal :size="12" class="text-primary-400" />
        <span>诊断控制台</span>
        <span class="text-dark-500">({{ logs.length }})</span>
      </div>

      <!-- Spacer -->
      <div class="flex-1"></div>

      <!-- Controls -->
      <button
        @click="toggleCollapse"
        class="p-1.5 hover:bg-dark-700/50 text-dark-400 hover:text-dark-200 transition-colors"
        :title="isCollapsed ? '展开' : '折叠'"
      >
        <component :is="isCollapsed ? Plus : Minus" :size="14" />
      </button>
    </div>

    <!-- Content (hidden when collapsed) -->
    <div
      v-show="!isCollapsed"
      ref="logContainer"
      class="h-[180px] overflow-y-auto p-2 font-mono text-[11px] leading-5"
    >
      <div v-if="logs.length === 0" class="text-dark-500 italic">
        等待诊断开始...
      </div>
      <div v-else class="space-y-0.5">
        <div
          v-for="(log, index) in logs"
          :key="index"
          :class="['flex items-start gap-2 hover:bg-dark-800/20 -mx-1 px-1 rounded', getLogClass(log.level)]"
        >
          <span class="text-dark-500 text-[10px] shrink-0 w-16">{{ log.timestamp }}</span>
          <span>{{ log.message }}</span>
        </div>
      </div>
    </div>

    <!-- Collapsed indicator -->
    <div
      v-if="isCollapsed"
      class="h-6 flex items-center px-2 text-[10px] text-dark-500 cursor-pointer hover:bg-dark-800/30"
      @click="toggleCollapse"
    >
      <Terminal :size="10" class="mr-1" />
      <span>{{ logs.length }} 条日志</span>
    </div>
  </div>
</template>