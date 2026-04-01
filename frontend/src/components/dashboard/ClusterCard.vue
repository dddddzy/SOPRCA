<script setup lang="ts">
import { computed } from 'vue'
import type { ClusterStats } from '@/types'
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-vue-next'

const props = defineProps<{
  cluster: ClusterStats
}>()

const statusConfig = computed(() => {
  const configs = {
    healthy: {
      icon: CheckCircle,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/20',
      label: '健康'
    },
    warning: {
      icon: AlertTriangle,
      color: 'text-amber-400',
      bg: 'bg-amber-500/20',
      label: '警告'
    },
    critical: {
      icon: XCircle,
      color: 'text-red-400',
      bg: 'bg-red-500/20',
      label: '危急'
    }
  }
  return configs[props.cluster.status]
})

function getUsageColor(usage: number) {
  if (usage >= 85) return 'text-red-400'
  if (usage >= 70) return 'text-amber-400'
  return 'text-emerald-400'
}

function getBarColor(usage: number) {
  if (usage >= 85) return 'bg-red-500'
  if (usage >= 70) return 'bg-amber-500'
  return 'bg-primary-500'
}
</script>

<template>
  <div class="card">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <div :class="['p-1.5 rounded-lg', statusConfig.bg]">
          <component :is="statusConfig.icon" :size="16" :class="statusConfig.color" />
        </div>
        <span class="font-medium text-dark-100">{{ cluster.name }}</span>
      </div>
      <span :class="['badge', `badge-${cluster.status === 'healthy' ? 'success' : cluster.status === 'warning' ? 'warning' : 'error'}`]">
        {{ statusConfig.label }}
      </span>
    </div>

    <!-- Metrics -->
    <div class="space-y-3">
      <div>
        <div class="flex justify-between text-xs mb-1">
          <span class="text-dark-400">CPU</span>
          <span :class="['font-medium', getUsageColor(cluster.cpuUsage)]">{{ cluster.cpuUsage }}%</span>
        </div>
        <div class="h-1.5 bg-dark-700 rounded-full overflow-hidden">
          <div
            :class="['h-full rounded-full transition-all', getBarColor(cluster.cpuUsage)]"
            :style="{ width: `${cluster.cpuUsage}%` }"
          ></div>
        </div>
      </div>
      <div>
        <div class="flex justify-between text-xs mb-1">
          <span class="text-dark-400">内存</span>
          <span :class="['font-medium', getUsageColor(cluster.memoryUsage)]">{{ cluster.memoryUsage }}%</span>
        </div>
        <div class="h-1.5 bg-dark-700 rounded-full overflow-hidden">
          <div
            :class="['h-full rounded-full transition-all', getBarColor(cluster.memoryUsage)]"
            :style="{ width: `${cluster.memoryUsage}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Footer Stats -->
    <div class="flex justify-between mt-4 pt-3 border-t border-dark-700">
      <span class="text-xs text-dark-400">Pods: <span class="text-dark-200">{{ cluster.podCount }}</span></span>
      <span class="text-xs text-dark-400">Services: <span class="text-dark-200">{{ cluster.serviceCount }}</span></span>
    </div>
  </div>
</template>
