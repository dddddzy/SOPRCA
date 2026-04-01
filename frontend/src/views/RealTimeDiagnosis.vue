<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useDiagnosisStore } from '@/stores/diagnosis'
import StepTimeline from '@/components/diagnosis/StepTimeline.vue'
import ReportCard from '@/components/diagnosis/ReportCard.vue'
import LogConsole from '@/components/diagnosis/LogConsole.vue'
import { Play, Square, RotateCcw, Loader2 } from 'lucide-vue-next'

const diagnosisStore = useDiagnosisStore()

const inputFault = ref('')
const isAnimating = ref(false)

const placeholderExamples = [
  'cartservice 出现严重的 TCP 阻塞和未知网络延迟',
  'productcatalogservice CPU使用率超过90%',
  'paymentservice Pod频繁重启',
  'userservice 内存溢出导致服务不可用'
]

const placeholderIndex = ref(0)

onMounted(() => {
  // Animate placeholder
  setInterval(() => {
    placeholderIndex.value = (placeholderIndex.value + 1) % placeholderExamples.length
  }, 3000)
})

async function startDiagnosis() {
  if (!inputFault.value.trim()) return

  isAnimating.value = true
  await diagnosisStore.runMockDiagnosis(inputFault.value)
  isAnimating.value = false
}

function stopDiagnosis() {
  diagnosisStore.stopDiagnosis()
  isAnimating.value = false
}

function resetDiagnosis() {
  diagnosisStore.reset()
  inputFault.value = ''
}

function useExample(example: string) {
  inputFault.value = example
}
</script>

<template>
  <div class="h-full flex flex-col space-y-4">
    <!-- Input Section -->
    <div class="card">
      <div class="flex items-center gap-3 mb-4">
        <h2 class="text-lg font-semibold text-dark-100">故障描述</h2>
        <span class="badge-info">实时诊断</span>
      </div>

      <div class="flex gap-3">
        <div class="flex-1 relative">
          <input
            v-model="inputFault"
            type="text"
            class="input-field pr-24"
            :placeholder="placeholderExamples[placeholderIndex]"
            :disabled="diagnosisStore.isRunning"
            @keyup.enter="startDiagnosis"
          />
          <button
            v-if="!inputFault"
            @click="useExample(placeholderExamples[0])"
            class="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-primary-400 hover:text-primary-300 cursor-pointer"
          >
            示例
          </button>
        </div>

        <button
          v-if="!diagnosisStore.isRunning && !diagnosisStore.isComplete"
          @click="startDiagnosis"
          :disabled="!inputFault.trim()"
          class="btn-primary flex items-center gap-2"
        >
          <Play :size="18" />
          开始诊断
        </button>

        <button
          v-if="diagnosisStore.isRunning"
          @click="stopDiagnosis"
          class="btn-danger flex items-center gap-2"
        >
          <Square :size="18" />
          停止
        </button>

        <button
          v-if="diagnosisStore.isComplete"
          @click="resetDiagnosis"
          class="btn-secondary flex items-center gap-2"
        >
          <RotateCcw :size="18" />
          重置
        </button>
      </div>

      <!-- Quick Examples -->
      <div v-if="!diagnosisStore.isRunning && !diagnosisStore.isComplete" class="flex gap-2 mt-3">
        <span class="text-xs text-dark-500">快速输入:</span>
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

    <!-- Main Content -->
    <div class="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
      <!-- Left: Step Timeline -->
      <div class="card flex flex-col min-h-[400px]">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-medium text-dark-300">诊断步骤</h3>
          <div v-if="diagnosisStore.isRunning" class="flex items-center gap-2 text-primary-400">
            <Loader2 :size="14" class="animate-spin" />
            <span class="text-xs">执行中...</span>
          </div>
          <span v-else-if="diagnosisStore.isComplete" class="badge-success">
            已完成 {{ diagnosisStore.steps.length }} 步
          </span>
        </div>
        <StepTimeline
          :steps="diagnosisStore.steps"
          :is-running="diagnosisStore.isRunning"
          class="flex-1 overflow-auto"
        />
      </div>

      <!-- Right: Report & Logs -->
      <div class="space-y-4 min-h-[400px]">
        <!-- Report Card -->
        <ReportCard
          :report="diagnosisStore.report"
          :is-running="diagnosisStore.isRunning"
          class="min-h-[200px]"
        />

        <!-- Log Console -->
        <LogConsole
          :logs="diagnosisStore.logs"
          class="min-h-[200px]"
        />
      </div>
    </div>
  </div>
</template>
