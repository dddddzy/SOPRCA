<script setup lang="ts">
import type { RCAReport } from '@/types'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  MapPin,
  Lightbulb,
  Shield
} from 'lucide-vue-next'

const props = defineProps<{
  report: RCAReport | null
  isRunning: boolean
}>()

function getConfidenceColor(confidence: number) {
  if (confidence >= 0.9) return 'text-emerald-400'
  if (confidence >= 0.7) return 'text-amber-400'
  return 'text-red-400'
}

function getConfidenceBg(confidence: number) {
  if (confidence >= 0.9) return 'bg-emerald-500/20'
  if (confidence >= 0.7) return 'bg-amber-500/20'
  return 'bg-red-500/20'
}
</script>

<template>
  <div class="card h-full">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-medium text-dark-300">诊断报告</h3>
      <div
        v-if="report"
        :class="['flex items-center gap-2 px-2 py-1 rounded-lg', getConfidenceBg(report.confidence)]"
      >
        <Shield :size="14" :class="getConfidenceColor(report.confidence)" />
        <span :class="['text-sm font-medium', getConfidenceColor(report.confidence)]">
          {{ (report.confidence * 100).toFixed(0) }}%
        </span>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="!report && !isRunning"
      class="flex flex-col items-center justify-center h-full text-center py-8"
    >
      <AlertTriangle :size="36" class="text-dark-600 mb-3" />
      <p class="text-dark-400 text-sm">暂无诊断报告</p>
      <p class="text-xs text-dark-500 mt-1">请输入故障描述开始诊断</p>
    </div>

    <!-- Running State -->
    <div
      v-if="isRunning && !report"
      class="flex flex-col items-center justify-center h-full text-center py-8"
    >
      <div class="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mb-3"></div>
      <p class="text-dark-400 text-sm">正在分析中...</p>
    </div>

    <!-- Report Content -->
    <div v-if="report" class="space-y-4">
      <!-- Root Cause -->
      <div class="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
        <div class="flex items-start gap-2">
          <AlertTriangle :size="16" class="text-red-400 mt-0.5" />
          <div>
            <p class="text-xs text-red-400 mb-1">根因</p>
            <p class="text-sm font-medium text-dark-100">{{ report.rootCause }}</p>
          </div>
        </div>
      </div>

      <!-- Meta Info -->
      <div class="grid grid-cols-2 gap-3">
        <div class="flex items-center gap-2">
          <MapPin :size="14" class="text-dark-400" />
          <div>
            <p class="text-xs text-dark-500">位置</p>
            <p class="text-xs text-dark-200 truncate">{{ report.faultLocation }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <Clock :size="14" class="text-dark-400" />
          <div>
            <p class="text-xs text-dark-500">诊断时间</p>
            <p class="text-xs text-dark-200">{{ report.diagnosisTime }}</p>
          </div>
        </div>
      </div>

      <!-- Key Clues -->
      <div>
        <div class="flex items-center gap-2 mb-2">
          <Lightbulb :size="14" class="text-primary-400" />
          <span class="text-xs font-medium text-dark-300">关键线索</span>
        </div>
        <ul class="space-y-1.5">
          <li
            v-for="(clue, index) in report.keyClues"
            :key="index"
            class="flex items-start gap-2 text-xs"
          >
            <span class="text-primary-400 mt-0.5">•</span>
            <span class="text-dark-300">{{ clue }}</span>
          </li>
        </ul>
      </div>

      <!-- Suggestions -->
      <div>
        <div class="flex items-center gap-2 mb-2">
          <CheckCircle2 :size="14" class="text-emerald-400" />
          <span class="text-xs font-medium text-dark-300">建议</span>
        </div>
        <ul class="space-y-1.5">
          <li
            v-for="(suggestion, index) in report.suggestions"
            :key="index"
            class="flex items-start gap-2 text-xs"
          >
            <span class="text-emerald-400 mt-0.5">✓</span>
            <span class="text-dark-300">{{ suggestion }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
