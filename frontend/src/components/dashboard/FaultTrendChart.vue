<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { FaultTrend } from '@/types'

const props = defineProps<{
  data: FaultTrend[]
}>()

const chartRef = ref<HTMLDivElement>()

onMounted(() => {
  if (!chartRef.value) return

  const max = Math.max(...props.data.map(d => d.count))
  const chartHeight = 120

  chartRef.value.innerHTML = `
    <div class="flex items-end justify-between h-[${chartHeight}px] gap-2">
      ${props.data.map(item => {
        const height = (item.count / max) * chartHeight
        return `
          <div class="flex-1 flex flex-col items-center gap-1">
            <span class="text-xs text-dark-400">${item.count}</span>
            <div
              class="w-full bg-primary-500/80 rounded-t transition-all hover:bg-primary-400"
              style="height: ${height}px; min-height: 4px;"
            ></div>
            <span class="text-xs text-dark-500">${item.date}</span>
          </div>
        `
      }).join('')}
    </div>
  `
})
</script>

<template>
  <div ref="chartRef" class="w-full"></div>
</template>
