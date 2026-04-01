<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { LogEntry } from '@/types'
import { Terminal, Trash2 } from 'lucide-vue-next'

const props = defineProps<{
  logs: LogEntry[]
}>()

const logContainer = ref<HTMLDivElement>()

// Auto scroll to bottom when new logs arrive
watch(
  () => props.logs.length,
  async () => {
    await nextTick()
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }
)

function getLogClass(level: LogEntry['level']) {
  return `log-${level}`
}

function clearLogs() {
  // This would be handled by the store in real app
}
</script>

<template>
  <div class="card flex flex-col h-full">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <Terminal :size="14" class="text-dark-400" />
        <h3 class="text-sm font-medium text-dark-300">控制台输出</h3>
        <span class="badge-default text-xs">{{ logs.length }}</span>
      </div>
    </div>

    <!-- Log Content -->
    <div
      ref="logContainer"
      class="log-console flex-1 min-h-[120px] max-h-[200px]"
    >
      <!-- Empty State -->
      <div
        v-if="logs.length === 0"
        class="flex flex-col items-center justify-center h-full text-center"
      >
        <Terminal :size="24" class="text-dark-600 mb-2" />
        <p class="text-xs text-dark-500">暂无日志输出</p>
      </div>

      <!-- Log Lines -->
      <div v-else>
        <div
          v-for="(log, index) in logs"
          :key="index"
          :class="['log-line', getLogClass(log.level)]"
        >
          <span class="text-dark-500 mr-2">[{{ log.timestamp }}]</span>
          <span>{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
