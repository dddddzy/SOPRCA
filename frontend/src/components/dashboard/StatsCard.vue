<script setup lang="ts">
import { computed } from 'vue'
import { Activity, Clock, CheckCircle, Zap, TrendingUp, TrendingDown } from 'lucide-vue-next'

const props = defineProps<{
  title: string
  value: number | string
  icon: string
  color: 'primary' | 'accent' | 'emerald' | 'amber'
  trend?: string
  trendUp?: boolean
}>()

const iconComponent = computed(() => {
  const icons: Record<string, any> = {
    Activity, Clock, CheckCircle, Zap
  }
  return icons[props.icon] || Activity
})

const colorClasses = computed(() => {
  const colors = {
    primary: 'bg-primary-500/20 text-primary-400',
    accent: 'bg-accent-500/20 text-accent-400',
    emerald: 'bg-emerald-500/20 text-emerald-400',
    amber: 'bg-amber-500/20 text-amber-400'
  }
  return colors[props.color]
})
</script>

<template>
  <div class="card group hover:border-dark-500 transition-all duration-200">
    <div class="flex items-start justify-between">
      <div>
        <p class="text-sm text-dark-400 mb-1">{{ title }}</p>
        <p class="text-2xl font-bold text-dark-100">{{ value }}</p>
        <div v-if="trend" class="flex items-center gap-1 mt-2">
          <component
            :is="trendUp ? TrendingUp : TrendingDown"
            :size="14"
            :class="trendUp ? 'text-emerald-400' : 'text-red-400'"
          />
          <span
            :class="[
              'text-xs font-medium',
              trendUp ? 'text-emerald-400' : 'text-red-400'
            ]"
          >
            {{ trend }}
          </span>
        </div>
      </div>
      <div :class="['p-3 rounded-xl transition-colors group-hover:scale-110', colorClasses]">
        <component :is="iconComponent" :size="24" />
      </div>
    </div>
  </div>
</template>
