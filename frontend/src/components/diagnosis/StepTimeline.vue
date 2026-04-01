<script setup lang="ts">
import { computed } from 'vue'
import type { DiagnosisStep } from '@/types'
import {
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
  Bot,
  Cpu,
  Code2,
  FlaskConical,
  Scale
} from 'lucide-vue-next'

const props = defineProps<{
  steps: DiagnosisStep[]
  isRunning: boolean
}>()

const agentIcons: Record<string, any> = {
  action_agent: Bot,
  main_agent: Bot,
  tool_executor: Cpu,
  code_agent: Code2,
  judge_agent: Scale,
  ob_agent: FlaskConical
}

const agentLabels: Record<string, string> = {
  action_agent: 'Action Agent',
  main_agent: 'Main Agent',
  tool_executor: 'Tool Executor',
  code_agent: 'Code Agent',
  judge_agent: 'Judge Agent',
  ob_agent: 'Observation Agent'
}

function getStatusClass(status: DiagnosisStep['status']) {
  switch (status) {
    case 'done': return 'timeline-item-done'
    case 'running': return 'timeline-item-active'
    case 'error': return 'timeline-item-error'
    default: return ''
  }
}

function getIcon(status: DiagnosisStep['status']) {
  switch (status) {
    case 'done': return CheckCircle2
    case 'running': return Loader2
    case 'error': return XCircle
    default: return Circle
  }
}

function getIconColor(status: DiagnosisStep['status']) {
  switch (status) {
    case 'done': return 'text-emerald-400'
    case 'running': return 'text-primary-400 animate-pulse'
    case 'error': return 'text-red-400'
    default: return 'text-dark-500'
  }
}
</script>

<template>
  <div class="relative">
    <!-- Empty State -->
    <div
      v-if="steps.length === 0 && !isRunning"
      class="flex flex-col items-center justify-center h-full text-center py-12"
    >
      <Bot :size="48" class="text-dark-600 mb-4" />
      <p class="text-dark-400 mb-2">输入故障描述开始诊断</p>
      <p class="text-xs text-dark-500">系统将自动分析并生成诊断报告</p>
    </div>

    <!-- Running State -->
    <div
      v-if="isRunning && steps.length === 0"
      class="flex flex-col items-center justify-center h-full text-center py-12"
    >
      <Loader2 :size="48" class="text-primary-400 mb-4 animate-spin" />
      <p class="text-dark-400 mb-2">正在启动诊断流程...</p>
      <p class="text-xs text-dark-500">匹配SOP知识库中</p>
    </div>

    <!-- Timeline -->
    <div v-else class="space-y-0">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        :class="['timeline-item', getStatusClass(step.status)]"
      >
        <!-- Connector Line -->
        <div
          v-if="index < steps.length - 1"
          class="absolute left-[7px] top-8 w-0.5 h-6 bg-dark-700"
          :class="{ 'bg-primary-500/50': step.status === 'running' }"
        ></div>

        <div class="flex items-start gap-3">
          <!-- Icon -->
          <div
            :class="[
              'flex items-center justify-center w-8 h-8 rounded-lg bg-dark-700 border border-dark-600',
              step.status === 'running' ? 'border-primary-500/50 bg-primary-500/10' : ''
            ]"
          >
            <component
              :is="agentIcons[step.agent] || Bot"
              :size="16"
              :class="['text-dark-400', getIconColor(step.status)]"
            />
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-medium text-primary-400">
                {{ agentLabels[step.agent] || step.agent }}
              </span>
              <span class="text-xs text-dark-500">{{ step.timestamp }}</span>
              <component
                :is="getIcon(step.status)"
                :size="12"
                :class="['ml-auto', getIconColor(step.status)]"
                :class-name="step.status === 'running' ? 'animate-spin' : ''"
              />
            </div>
            <p class="text-sm text-dark-200 mb-1">{{ step.content }}</p>
            <div class="flex items-center gap-2">
              <span class="badge-default text-xs">
                {{ step.action }}
              </span>
              <span v-if="step.duration" class="text-xs text-dark-500">
                {{ (step.duration / 1000).toFixed(1) }}s
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Running Indicator -->
      <div v-if="isRunning" class="timeline-item timeline-item-active">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-dark-700 border border-primary-500/50 bg-primary-500/10 flex items-center justify-center">
            <Loader2 :size="16" class="text-primary-400 animate-spin" />
          </div>
          <div class="flex-1">
            <p class="text-sm text-primary-400">等待下一步操作...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
