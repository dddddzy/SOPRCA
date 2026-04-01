<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { FaultTypeDistribution } from '@/types'

const props = defineProps<{
  data: FaultTypeDistribution[]
}>()

const chartRef = ref<HTMLDivElement>()

const colors = [
  'bg-primary-500',
  'bg-accent-500',
  'bg-amber-500',
  'bg-emerald-500',
  'bg-dark-500'
]

onMounted(() => {
  if (!chartRef.value) return

  chartRef.value.innerHTML = `
    <div class="space-y-3">
      ${props.data.map((item, index) => `
        <div class="flex items-center gap-3">
          <div class="w-16 text-xs text-dark-300">${item.type}</div>
          <div class="flex-1">
            <div class="h-2 bg-dark-700 rounded-full overflow-hidden">
              <div
                class="h-full ${colors[index % colors.length]} rounded-full transition-all"
                style="width: ${item.percentage}%"
              ></div>
            </div>
          </div>
          <div class="w-20 text-right">
            <span class="text-xs text-dark-300">${item.count}次</span>
            <span class="text-xs text-dark-500 ml-1">(${item.percentage}%)</span>
          </div>
        </div>
      `).join('')}
    </div>
  `
})
</script>

<template>
  <div ref="chartRef" class="w-full"></div>
</template>
