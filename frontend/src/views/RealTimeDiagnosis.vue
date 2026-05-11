<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDiagnosisStore } from '@/stores/diagnosis'
import FlowDiagram from '@/components/diagnosis/FlowDiagram.vue'
import ReportCard from '@/components/diagnosis/ReportCard.vue'
import LogConsole from '@/components/diagnosis/LogConsole.vue'
import type { DiagnosisStep } from '@/types'
import { Play, Square, RotateCcw, Loader2, Activity, Shield, Clock, Trash2, CheckCircle, XCircle, AlertCircle } from 'lucide-vue-next'

const { t } = useI18n()
const diagnosisStore = useDiagnosisStore()

const inputFault = ref('')
const isAnimating = ref(false)
const selectedStep = ref<DiagnosisStep | null>(null)
const monitorEnabled = ref(false)
const monitorStatus = ref<any>(null)
const showHistory = ref(false)

const placeholderExamples = [
  'cartservice 出现严重的 TCP 阻塞和未知网络延迟',
  'productcatalogservice CPU使用率超过90%',
  'paymentservice Pod频繁重启',
  'userservice 内存溢出导致服务不可用'
]

async function startDiagnosis() {
  if (!inputFault.value.trim()) return

  isAnimating.value = true
  selectedStep.value = null
  await diagnosisStore.runDiagnosis(inputFault.value)
  isAnimating.value = false
}

function stopDiagnosis() {
  diagnosisStore.stopDiagnosis()
  isAnimating.value = false
}

function resetDiagnosis() {
  diagnosisStore.reset()
  inputFault.value = ''
  selectedStep.value = null
}

function useExample(example: string) {
  inputFault.value = example
}

function onStepClick(step: DiagnosisStep) {
  selectedStep.value = selectedStep.value?.id === step.id ? null : step
}

function formatJson(obj: any): string {
  if (!obj) return '无数据'
  if (typeof obj === 'string') return obj
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

async function toggleMonitor() {
  try {
    const res = await fetch('/api/monitor/toggle', { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      monitorEnabled.value = data.data.enabled
      monitorStatus.value = data.data
    }
  } catch (e) {
    console.error('toggle monitor failed:', e)
  }
}

async function fetchMonitorStatus() {
  try {
    const res = await fetch('/api/monitor/status')
    const data = await res.json()
    if (data.success) {
      monitorEnabled.value = data.data.enabled
      monitorStatus.value = data.data
    }
  } catch (e) {
    console.error('fetch monitor status failed:', e)
  }
}

onMounted(() => {
  fetchMonitorStatus()
  // 连接自动巡检SSE
  diagnosisStore.connectMonitorSSE()
})

function loadHistoryRecord(record: any) {
  diagnosisStore.reset()
  diagnosisStore.faultInfo = record.faultInfo
  diagnosisStore.steps = [...record.steps]
  diagnosisStore.report = record.report
  diagnosisStore.isRunning = false
  showHistory.value = false
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Top Section: Input + Main Content -->
    <div class="flex-1 flex flex-col space-y-4 overflow-hidden">
      <!-- Input Section -->
      <div class="card flex-shrink-0">
        <div class="flex items-center gap-3 mb-4">
          <h2 class="text-lg font-semibold text-dark-100">{{ t('diagnosis.faultDescription') }}</h2>
          <span class="badge-info">{{ t('nav.diagnosis') }}</span>

          <!-- Auto Monitor Toggle -->
          <div class="ml-auto flex items-center gap-3 px-3 py-1.5 rounded-lg bg-dark-800 border border-dark-700">
            <Activity :size="14" :class="monitorEnabled ? 'text-emerald-400' : 'text-dark-500'" />
            <span class="text-xs text-dark-300">自动巡检</span>
            <button
              @click="toggleMonitor"
              :class="[
                'w-10 h-5 rounded-full transition-colors relative',
                monitorEnabled ? 'bg-emerald-500' : 'bg-dark-600'
              ]"
            >
              <span
                :class="[
                  'absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all',
                  monitorEnabled ? 'left-5.5' : 'left-0.5'
                ]"
              ></span>
            </button>
            <!-- Thresholds Display -->
            <div v-if="monitorStatus?.thresholds" class="flex items-center gap-2 text-[10px] text-dark-500 border-l border-dark-700 pl-3">
              <span>CPU≥{{ monitorStatus.thresholds.cpu_percent }}%</span>
              <span>重启≥{{ monitorStatus.thresholds.restart_count }}</span>
            </div>
          </div>
        </div>

        <div class="flex gap-3">
          <div class="flex-1 relative">
            <input
              v-model="inputFault"
              type="text"
              class="input-field pr-24"
              :placeholder="t('diagnosis.placeholder')"
              :disabled="diagnosisStore.isRunning"
              @keyup.enter="startDiagnosis"
            />
          </div>

          <button
            v-if="!diagnosisStore.isRunning && !diagnosisStore.isComplete"
            @click="startDiagnosis"
            :disabled="!inputFault.trim()"
            class="btn-primary flex items-center gap-2"
          >
            <Play :size="18" />
            {{ t('diagnosis.startDiagnosis') }}
          </button>

          <button
            v-if="diagnosisStore.isRunning"
            @click="stopDiagnosis"
            class="btn-danger flex items-center gap-2"
          >
            <Square :size="18" />
            {{ t('diagnosis.stop') }}
          </button>

          <button
            v-if="diagnosisStore.isComplete"
            @click="resetDiagnosis"
            class="btn-secondary flex items-center gap-2"
          >
            <RotateCcw :size="18" />
            {{ t('diagnosis.reset') }}
          </button>

          <button
            v-if="diagnosisStore.history.length > 0"
            @click="showHistory = !showHistory"
            :class="[
              'btn-secondary flex items-center gap-2',
              showHistory ? 'bg-primary-500/20 border-primary-500/50' : ''
            ]"
          >
            <Clock :size="18" />
            历史 ({{ diagnosisStore.history.length }})
          </button>
        </div>

        <!-- Quick Examples -->
        <div v-if="!diagnosisStore.isRunning && !diagnosisStore.isComplete" class="flex gap-2 mt-3">
          <span class="text-xs text-dark-500">{{ t('diagnosis.quickInput') }}</span>
          <button
            v-for="example in placeholderExamples"
            :key="example"
            @click="useExample(example)"
            class="text-xs text-dark-400 hover:text-primary-400 transition-colors cursor-pointer"
          >
            {{ example.slice(0, 15) }}...
          </button>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 min-h-0 overflow-hidden">
        <!-- Left: Step Timeline -->
        <div class="card flex flex-col lg:col-span-2 min-h-[300px] overflow-hidden">
          <div class="flex items-center justify-between mb-4 flex-shrink-0">
            <h3 class="text-sm font-medium text-dark-300">{{ t('diagnosis.diagnosisSteps') }}</h3>
            <div v-if="diagnosisStore.isRunning" class="flex items-center gap-2 text-primary-400">
              <Loader2 :size="14" class="animate-spin" />
              <span class="text-xs">{{ t('diagnosis.running') }}</span>
            </div>
            <span v-else-if="diagnosisStore.isComplete" class="badge-success">
              {{ t('diagnosis.completed', { count: diagnosisStore.steps.length }) }}
            </span>
          </div>

          <FlowDiagram
            :steps="diagnosisStore.steps"
            :is-running="diagnosisStore.isRunning"
            class="flex-1 overflow-auto min-h-0"
            @node-click="onStepClick"
          />

          <!-- Selected Step Detail Panel -->
          <div
            v-if="selectedStep"
            class="mt-4 p-3 rounded-lg border border-primary-500/30 bg-primary-500/5 flex-shrink-0"
          >
            <h4 class="text-sm font-medium text-primary-400 mb-2">节点详情</h4>
            <div class="space-y-2 text-xs max-h-40 overflow-auto">
              <div class="flex items-start gap-2">
                <span class="text-dark-400 shrink-0">时间:</span>
                <span class="text-dark-200">{{ selectedStep.timestamp }}</span>
              </div>
              <div class="flex items-start gap-2">
                <span class="text-dark-400 shrink-0">动作:</span>
                <span class="text-dark-200">{{ selectedStep.action }}</span>
              </div>
              <div v-if="selectedStep.reasoning">
                <span class="text-dark-400">思考过程:</span>
                <pre class="mt-1 p-2 bg-dark-800 rounded text-dark-300 max-h-24 overflow-auto whitespace-pre-wrap">{{ selectedStep.reasoning }}</pre>
              </div>
              <div v-if="selectedStep.output">
                <span class="text-dark-400">输出:</span>
                <pre class="mt-1 p-2 bg-dark-800 rounded text-dark-300 max-h-32 overflow-auto whitespace-pre-wrap">{{ formatJson(selectedStep.output) }}</pre>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Report -->
        <div class="min-h-[200px]">
          <ReportCard
            :report="diagnosisStore.report"
            :is-running="diagnosisStore.isRunning"
            class="h-full"
          />
        </div>
      </div>
    </div>

    <!-- History Panel -->
    <div v-if="showHistory" class="card max-h-[300px] overflow-hidden flex-shrink-0">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-medium text-dark-300">诊断历史</h3>
        <button
          @click="diagnosisStore.clearHistory()"
          class="text-xs text-dark-500 hover:text-red-400 transition-colors flex items-center gap-1"
        >
          <Trash2 :size="12" />
          清空
        </button>
      </div>
      <div class="overflow-auto max-h-[220px] space-y-2">
        <div
          v-for="record in diagnosisStore.history"
          :key="record.id"
          class="flex items-center gap-3 p-2 rounded-lg bg-dark-700/30 hover:bg-dark-700/50 transition-colors cursor-pointer"
          @click="loadHistoryRecord(record)"
        >
          <!-- Status Icon -->
          <div :class="[
            'w-8 h-8 rounded-lg flex items-center justify-center',
            record.result === 'found' ? 'bg-emerald-500/20 text-emerald-400' :
            record.result === 'not_found' ? 'bg-amber-500/20 text-amber-400' :
            record.result === 'stopped' ? 'bg-dark-600 text-dark-400' :
            'bg-red-500/20 text-red-400'
          ]">
            <CheckCircle v-if="record.result === 'found'" :size="16" />
            <AlertCircle v-else-if="record.result === 'not_found'" :size="16" />
            <XCircle v-else-if="record.result === 'stopped'" :size="16" />
            <XCircle v-else :size="16" />
          </div>
          <!-- Info -->
          <div class="flex-1 min-w-0">
            <p class="text-sm text-dark-200 truncate">{{ record.faultInfo }}</p>
            <p class="text-xs text-dark-500">{{ record.timestamp }} · {{ record.duration }}</p>
          </div>
          <!-- Root Cause -->
          <div v-if="record.rootCause" class="text-xs text-emerald-400 truncate max-w-[150px]">
            {{ record.rootCause }}
          </div>
          <!-- Remove -->
          <button
            @click.stop="diagnosisStore.removeFromHistory(record.id)"
            class="p-1 hover:bg-dark-600 rounded text-dark-500 hover:text-red-400"
          >
            <XCircle :size="14" />
          </button>
        </div>
        <div v-if="diagnosisStore.history.length === 0" class="text-center text-dark-500 py-4 text-sm">
          暂无历史记录
        </div>
      </div>
    </div>

    <!-- Bottom: Log Panel (VSCode-style) -->
    <div class="flex-shrink-0">
      <LogConsole :logs="diagnosisStore.logs" />
    </div>
  </div>
</template>