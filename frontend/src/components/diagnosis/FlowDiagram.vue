<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DiagnosisStep } from '@/types'
import { ChevronDown, ChevronRight, Bot, Code, FileText, CheckCircle, Clock, XCircle, Search, Lightbulb } from 'lucide-vue-next'

const props = defineProps<{
  steps: DiagnosisStep[]
  isRunning: boolean
}>()

const expandedStep = ref<string | null>(null)

const nodeConfig: Record<string, { label: string; icon: any; color: string }> = {
  match_sop: { label: '匹配SOP', icon: Search, color: 'primary' },
  action_agent: { label: '动作生成', icon: Bot, color: 'cyan' },
  main_agent: { label: '决策选择', icon: Bot, color: 'violet' },
  code_agent: { label: '代码生成', icon: Code, color: 'amber' },
  tool_executor: { label: '工具执行', icon: FileText, color: 'emerald' },
  match_observation: { label: '历史匹配', icon: Search, color: 'sky' },
  ob_agent: { label: '线索提取', icon: Lightbulb, color: 'pink' },
  judge_agent: { label: '根因判定', icon: CheckCircle, color: 'rose' },
  generate_sop: { label: '生成SOP', icon: FileText, color: 'orange' },
  generate_report: { label: '生成报告', icon: FileText, color: 'green' },
}

const statusConfig: Record<string, { bg: string; border: string; text: string; icon: any }> = {
  done: { bg: 'bg-emerald-500/20', border: 'border-emerald-500/50', text: 'text-emerald-400', icon: CheckCircle },
  running: { bg: 'bg-amber-500/20', border: 'border-amber-500/50', text: 'text-amber-400', icon: Clock },
  pending: { bg: 'bg-dark-700/50', border: 'border-dark-600', text: 'text-dark-400', icon: Clock },
  error: { bg: 'bg-red-500/20', border: 'border-red-500/50', text: 'text-red-400', icon: XCircle },
}

function getNodeInfo(agent: string) {
  return nodeConfig[agent] || { label: agent, icon: Bot, color: 'gray' }
}

function getStatusInfo(status: string) {
  return statusConfig[status] || statusConfig.pending
}

function toggleExpand(stepId: string) {
  expandedStep.value = expandedStep.value === stepId ? null : stepId
}

function formatJson(obj: any): string {
  if (!obj) return ''
  if (typeof obj === 'string') return obj
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

const emit = defineEmits<{
  (e: 'node-click', step: DiagnosisStep): void
}>()

function onNodeClick(step: DiagnosisStep) {
  emit('node-click', step)
}
</script>

<template>
  <div class="flow-diagram">
    <!-- 节点列表 -->
    <div class="space-y-2">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="relative"
      >
        <!-- 连接线 -->
        <div
          v-if="index > 0"
          class="absolute left-4 -top-2 w-0.5 h-2 bg-dark-600"
        ></div>

        <!-- 节点卡片 -->
        <div
          @click="onNodeClick(step)"
          :class="[
            'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all',
            'hover:border-primary-500/50 hover:bg-dark-700/30',
            expandedStep === step.id ? 'border-primary-500/50 bg-dark-700/50' : 'border-dark-700 bg-dark-800/50'
          ]"
        >
          <!-- 状态图标 -->
          <div
            :class="[
              'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
              getStatusInfo(step.status).bg
            ]"
          >
            <component
              :is="getStatusInfo(step.status).icon"
              :size="16"
              :class="getStatusInfo(step.status).text"
            />
          </div>

          <!-- 节点信息 -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-xs font-medium px-1.5 py-0.5 rounded bg-dark-700 text-dark-300">
                {{ index + 1 }}
              </span>
              <component
                :is="getNodeInfo(step.agent).icon"
                :size="14"
                :class="`text-${getNodeInfo(step.agent).color}-400`"
              />
              <span class="text-sm font-medium text-dark-100">
                {{ getNodeInfo(step.agent).label }}
              </span>
              <span
                v-if="step.status === 'running'"
                class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"
              ></span>
            </div>
            <p class="text-xs text-dark-400 mt-0.5 truncate">
              {{ step.content }}
            </p>
          </div>

          <!-- 展开按钮 -->
          <button
            @click.stop="toggleExpand(step.id)"
            class="p-1 hover:bg-dark-700 rounded transition-colors"
          >
            <ChevronDown
              v-if="expandedStep === step.id"
              :size="16"
              class="text-dark-400"
            />
            <ChevronRight
              v-else
              :size="16"
              class="text-dark-400"
            />
          </button>
        </div>

        <!-- 展开详情 -->
        <div
          v-if="expandedStep === step.id"
          class="mt-2 ml-4 p-3 rounded-lg border border-dark-700 bg-dark-900/50 space-y-3"
        >
          <!-- 时间戳 -->
          <div class="text-xs text-dark-500">
            {{ step.timestamp }}
          </div>

          <!-- Reasoning (思考过程) -->
          <div v-if="step.reasoning" class="space-y-1">
            <h4 class="text-xs font-medium text-dark-300 flex items-center gap-1">
              <Bot :size="12" /> 思考过程
            </h4>
            <pre class="text-xs text-dark-400 bg-dark-800 p-2 rounded overflow-auto max-h-32 whitespace-pre-wrap">{{ step.reasoning }}</pre>
          </div>

          <!-- 节点类型专属详情 -->
          <div v-if="step.agent === 'match_sop' && step.output?.matched_sop" class="space-y-2">
            <h4 class="text-xs font-medium text-cyan-400">匹配的SOP</h4>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="bg-dark-800 p-2 rounded">
                <span class="text-dark-500">名称:</span>
                <span class="text-dark-200 ml-1">{{ step.output.matched_sop.sop_name || '未知' }}</span>
              </div>
              <div class="bg-dark-800 p-2 rounded">
                <span class="text-dark-500">类型:</span>
                <span class="text-dark-200 ml-1">{{ step.output.matched_sop.fault_type || '未知' }}</span>
              </div>
              <div class="bg-dark-800 p-2 rounded">
                <span class="text-dark-500">SOP ID:</span>
                <span class="text-dark-200 ml-1">{{ step.output.matched_sop.sop_id || '未知' }}</span>
              </div>
              <div class="bg-dark-800 p-2 rounded">
                <span class="text-dark-500">匹配度:</span>
                <span class="text-dark-200 ml-1">{{ step.output.matched_sop.distance ? (1 / step.output.matched_sop.distance).toFixed(2) : 'N/A' }}</span>
              </div>
            </div>
          </div>

          <div v-else-if="step.agent === 'action_agent' && step.output?.candidate_action_set" class="space-y-2">
            <h4 class="text-xs font-medium text-cyan-400">候选动作 ({{ step.output.candidate_action_set.length }})</h4>
            <div class="space-y-1">
              <div
                v-for="(action, idx) in step.output.candidate_action_set"
                :key="idx"
                class="bg-dark-800 p-2 rounded text-xs"
              >
                <span class="text-amber-400">{{ idx + 1 }}. {{ action.action || '未知动作' }}</span>
                <p class="text-dark-400 mt-1">{{ action.reason || action.explanation || '' }}</p>
              </div>
            </div>
          </div>

          <div v-else-if="step.agent === 'main_agent' && step.output?.selected_action" class="space-y-2">
            <h4 class="text-xs font-medium text-green-400">选中的动作</h4>
            <div class="bg-dark-800 p-2 rounded">
              <span class="text-lg font-medium text-emerald-400">{{ step.output.selected_action.action || '未知' }}</span>
            </div>
            <div v-if="step.output.selected_action.reason" class="bg-dark-800 p-2 rounded text-xs">
              <span class="text-dark-500">选择原因:</span>
              <p class="text-dark-300 mt-1">{{ step.output.selected_action.reason }}</p>
            </div>
          </div>

          <div v-else-if="step.agent === 'code_agent' && step.output?.generated_code" class="space-y-2">
            <h4 class="text-xs font-medium text-amber-400">生成的代码</h4>
            <pre class="bg-dark-800 p-3 rounded text-xs text-emerald-300 overflow-auto max-h-64 whitespace-pre-wrap font-mono">{{ step.output.generated_code }}</pre>
          </div>

          <div v-else-if="step.agent === 'tool_executor' && step.output" class="space-y-2">
            <h4 class="text-xs font-medium text-emerald-400">执行结果</h4>
            <div v-if="step.output.tool_result" class="bg-dark-800 p-2 rounded text-xs text-dark-300 max-h-32 overflow-auto">
              {{ typeof step.output.tool_result === 'string' ? step.output.tool_result : formatJson(step.output.tool_result) }}
            </div>
            <div v-else-if="step.output.executed_steps" class="space-y-1">
              <div
                v-for="(exec, idx) in step.output.executed_steps"
                :key="idx"
                class="bg-dark-800 p-2 rounded text-xs"
              >
                <span class="text-cyan-400">{{ idx + 1 }}. {{ exec.action }}</span>
                <span class="text-dark-500 ml-2">第{{ step.output.iteration_count || 0 }}轮</span>
              </div>
            </div>
          </div>

          <div v-else-if="step.agent === 'ob_agent' && step.output?.extracted_clues" class="space-y-2">
            <h4 class="text-xs font-medium text-pink-400">提取的线索</h4>
            <div class="grid grid-cols-2 gap-2 text-xs mb-2">
              <div class="bg-dark-800 p-2 rounded">
                <span class="text-dark-500">故障类型:</span>
                <span class="text-dark-200 ml-1">{{ step.output.extracted_clues.fault_type || '未知' }}</span>
              </div>
              <div class="bg-dark-800 p-2 rounded">
                <span class="text-dark-500">故障位置:</span>
                <span class="text-dark-200 ml-1">{{ step.output.extracted_clues.fault_location || '未知' }}</span>
              </div>
            </div>
            <div v-if="step.output.extracted_clues.key_clues?.length" class="space-y-1">
              <span class="text-xs text-dark-500">关键线索:</span>
              <div
                v-for="(clue, idx) in step.output.extracted_clues.key_clues"
                :key="idx"
                class="bg-dark-800 p-2 rounded text-xs text-dark-300"
              >
                {{ clue }}
              </div>
            </div>
            <div v-if="step.output.extracted_clues.possible_root_causes?.length" class="space-y-1 mt-2">
              <span class="text-xs text-dark-500">可能根因:</span>
              <div
                v-for="(cause, idx) in step.output.extracted_clues.possible_root_causes"
                :key="idx"
                class="bg-dark-800 p-2 rounded text-xs text-amber-300"
              >
                {{ cause }}
              </div>
            </div>
          </div>

          <div v-else-if="step.agent === 'judge_agent' && step.output" class="space-y-2">
            <h4 class="text-xs font-medium text-rose-400">根因判定</h4>
            <div class="bg-dark-800 p-2 rounded">
              <span class="text-xs text-dark-500">判定结果:</span>
              <span :class="['ml-1', step.output.is_root_cause_found ? 'text-emerald-400' : 'text-amber-400']">
                {{ step.output.is_root_cause_found ? '已找到根因' : '未找到根因' }}
              </span>
            </div>
            <div v-if="step.output.explanation" class="bg-dark-800 p-2 rounded text-xs text-dark-300">
              {{ step.output.explanation }}
            </div>
            <div v-if="step.output.termination_reason" class="bg-dark-800 p-2 rounded text-xs">
              <span class="text-dark-500">终止原因:</span>
              <span class="text-rose-400 ml-1">{{ step.output.termination_reason }}</span>
            </div>
          </div>

          <div v-else-if="step.agent === 'generate_sop' && step.output?.matched_sop" class="space-y-2">
            <h4 class="text-xs font-medium text-orange-400">生成的SOP</h4>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="bg-dark-800 p-2 rounded">
                <span class="text-dark-500">名称:</span>
                <span class="text-dark-200 ml-1">{{ step.output.matched_sop.sop_name || '未知' }}</span>
              </div>
              <div class="bg-dark-800 p-2 rounded">
                <span class="text-dark-500">类型:</span>
                <span class="text-dark-200 ml-1">{{ step.output.matched_sop.fault_type || '未知' }}</span>
              </div>
            </div>
          </div>

          <div v-else-if="step.agent === 'match_observation' && step.output?.similar_history_faults" class="space-y-2">
            <h4 class="text-xs font-medium text-sky-400">相似历史故障 ({{ step.output.similar_history_faults.length }})</h4>
            <div
              v-for="(hist, idx) in step.output.similar_history_faults"
              :key="idx"
              class="bg-dark-800 p-2 rounded text-xs"
            >
              <div class="text-dark-300">{{ hist.fault_info || hist.faultInfo || '未知' }}</div>
              <div v-if="hist.similarity_score" class="text-dark-500 mt-1">相似度: {{ (hist.similarity_score * 100).toFixed(1) }}%</div>
              <div v-if="hist.root_cause || hist.rootCause" class="text-emerald-400 mt-1">根因: {{ hist.root_cause || hist.rootCause }}</div>
            </div>
          </div>

          <!-- Fallback: 原始输出 -->
          <div v-else-if="step.output && !['match_sop', 'action_agent', 'main_agent', 'code_agent', 'tool_executor', 'ob_agent', 'judge_agent', 'generate_sop', 'match_observation'].includes(step.agent)" class="space-y-1">
            <h4 class="text-xs font-medium text-dark-300">原始输出</h4>
            <pre class="text-xs text-dark-400 bg-dark-800 p-2 rounded overflow-auto max-h-48 whitespace-pre-wrap">{{ formatJson(step.output) }}</pre>
          </div>

          <!-- Input (输入) -->
          <div v-if="step.input" class="space-y-1">
            <h4 class="text-xs font-medium text-dark-300 flex items-center gap-1">
              <FileText :size="12" /> 输入
            </h4>
            <pre class="text-xs text-dark-400 bg-dark-800 p-2 rounded overflow-auto max-h-32 whitespace-pre-wrap">{{ formatJson(step.input) }}</pre>
          </div>
        </div>
      </div>

      <!-- Running indicator -->
      <div
        v-if="isRunning"
        class="flex items-center gap-2 p-3 rounded-lg border border-amber-500/30 bg-amber-500/10"
      >
        <Clock :size="16" class="text-amber-400 animate-spin" />
        <span class="text-sm text-amber-400">诊断进行中...</span>
      </div>
    </div>
  </div>
</template>
