<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import type { DiagnosisStep } from '@/types'
import { CheckCircle, Clock, XCircle, AlertCircle, Bot, Code, FileText, Search, Lightbulb, ChevronDown, ChevronRight } from 'lucide-vue-next'

const props = defineProps<{
  steps: DiagnosisStep[]
  isRunning: boolean
}>()

const emit = defineEmits<{
  (e: 'node-click', step: DiagnosisStep): void
}>()

const selectedNode = ref<string | null>(null)
const svgContainer = ref<HTMLDivElement>()

const NODE_WIDTH = 160
const NODE_HEIGHT = 70
const NODE_GAP_X = 60
const NODE_GAP_Y = 20
const PADDING = 40

// Node type to icon/color mapping
const nodeConfig: Record<string, { label: string; icon: any; color: string; bgColor: string }> = {
  match_sop: { label: '匹配SOP', icon: Search, color: '#22d3ee', bgColor: 'rgba(34,211,238,0.15)' },
  action_agent: { label: '动作生成', icon: Bot, color: '#06b6d4', bgColor: 'rgba(6,182,212,0.15)' },
  main_agent: { label: '决策选择', icon: Bot, color: '#8b5cf6', bgColor: 'rgba(139,92,246,0.15)' },
  code_agent: { label: '代码生成', icon: Code, color: '#f59e0b', bgColor: 'rgba(245,158,11,0.15)' },
  tool_executor: { label: '工具执行', icon: FileText, color: '#10b981', bgColor: 'rgba(16,185,129,0.15)' },
  match_observation: { label: '历史匹配', icon: Search, color: '#0ea5e9', bgColor: 'rgba(14,165,233,0.15)' },
  ob_agent: { label: '线索提取', icon: Lightbulb, color: '#ec4899', bgColor: 'rgba(236,72,153,0.15)' },
  judge_agent: { label: '根因判定', icon: CheckCircle, color: '#f43f5e', bgColor: 'rgba(244,63,94,0.15)' },
  generate_sop: { label: '生成SOP', icon: FileText, color: '#f97316', bgColor: 'rgba(249,115,22,0.15)' },
  generate_report: { label: '生成报告', icon: FileText, color: '#22c55e', bgColor: 'rgba(34,197,94,0.15)' },
}

const statusConfig: Record<string, { icon: any; color: string }> = {
  done: { icon: CheckCircle, color: '#10b981' },
  running: { icon: Clock, color: '#f59e0b' },
  pending: { icon: Clock, color: '#6b7280' },
  error: { icon: XCircle, color: '#ef4444' },
}

// Detect loops - find nodes that go back to previous nodes
const nodePositions = computed(() => {
  const positions: { x: number; y: number; step: DiagnosisStep; index: number }[] = []
  const loopTargets = new Set<string>()

  props.steps.forEach((step, index) => {
    // Simple linear layout for now
    // Group by "round" - nodes executed in sequence get same Y
    // If there's a back-loop, we'll handle it separately

    let x = PADDING + index * (NODE_WIDTH + NODE_GAP_X)
    let y = PADDING + NODE_HEIGHT + NODE_GAP_Y

    // Detect if this step is part of a loop back
    if (step.action === 'match_sop' && index > 0) {
      // Check if we matched the same SOP before
      loopTargets.add(step.id)
    }

    positions.push({ x, y, step, index })
  })

  return positions
})

// Calculate SVG dimensions
const svgDimensions = computed(() => {
  if (props.steps.length === 0) return { width: 400, height: 200 }

  const maxX = Math.max(...nodePositions.value.map(p => p.x)) + NODE_WIDTH + PADDING
  const maxY = Math.max(...nodePositions.value.map(p => p.y)) + NODE_HEIGHT + PADDING

  return {
    width: Math.max(400, maxX),
    height: Math.max(200, maxY + 80) // Extra space for legend
  }
})

// Generate edge paths between nodes
const edges = computed(() => {
  const edgeList: { x1: number; y1: number; x2: number; y2: number; isLoop?: boolean; targetIndex?: number }[] = []

  for (let i = 0; i < nodePositions.value.length - 1; i++) {
    const curr = nodePositions.value[i]
    const next = nodePositions.value[i + 1]

    edgeList.push({
      x1: curr.x + NODE_WIDTH,
      y1: curr.y + NODE_HEIGHT / 2,
      x2: next.x,
      y2: next.y + NODE_HEIGHT / 2
    })
  }

  return edgeList
})

function getNodeInfo(agent: string) {
  return nodeConfig[agent] || { label: agent, icon: Bot, color: '#9ca3af', bgColor: 'rgba(156,163,175,0.15)' }
}

function getStatusInfo(status: string) {
  return statusConfig[status] || statusConfig.pending
}

function onNodeClick(step: DiagnosisStep) {
  selectedNode.value = selectedNode.value === step.id ? null : step.id
  emit('node-click', step)
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
</script>

<template>
  <div class="trace-graph">
    <!-- Graph SVG -->
    <div
      ref="svgContainer"
      class="relative overflow-auto bg-dark-900 rounded-lg"
      :style="{ height: '400px' }"
    >
      <svg
        :width="svgDimensions.width"
        :height="svgDimensions.height"
        class="min-w-full"
      >
        <!-- Gradient definitions -->
        <defs>
          <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#22d3ee;stop-opacity:0.8" />
            <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:0.8" />
          </linearGradient>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill="#4b5563"
            />
          </marker>
          <marker
            id="arrowhead-active"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill="#22d3ee"
            />
          </marker>
        </defs>

        <!-- Edges (connection lines) -->
        <g class="edges">
          <template v-for="(edge, i) in edges" :key="'edge-' + i">
            <line
              :x1="edge.x1"
              :y1="edge.y1"
              :x2="edge.x2"
              :y2="edge.y2"
              stroke="url(#edgeGradient)"
              stroke-width="2"
              marker-end="url(#arrowhead)"
              :class="['transition-all', isRunning && i === edges.length - 1 ? 'animate-pulse' : '']"
            />
          </template>
        </g>

        <!-- Nodes -->
        <g class="nodes">
          <template v-for="pos in nodePositions" :key="pos.step.id">
            <g
              :transform="`translate(${pos.x}, ${pos.y})`"
              @click="onNodeClick(pos.step)"
              class="cursor-pointer"
            >
              <!-- Node background -->
              <rect
                :width="NODE_WIDTH"
                :height="NODE_HEIGHT"
                :rx="8"
                :fill="getNodeInfo(pos.step.agent).bgColor"
                :stroke="selectedNode === pos.step.id ? getNodeInfo(pos.step.agent).color : 'rgba(75,85,99,0.5)'"
                stroke-width="2"
                class="transition-all hover:brightness-110"
              />

              <!-- Status indicator -->
              <circle
                :cx="NODE_WIDTH - 12"
                cy="12"
                r="6"
                :fill="getStatusInfo(pos.step.status).color"
              >
                <animate
                  v-if="pos.step.status === 'running'"
                  attributeName="opacity"
                  values="1;0.5;1"
                  dur="1s"
                  repeatCount="indefinite"
                />
              </circle>

              <!-- Agent icon -->
              <foreignObject :x="8" :y="8" width="24" height="24">
                <div class="flex items-center justify-center w-full h-full">
                  <component
                    :is="getNodeInfo(pos.step.agent).icon"
                    :size="18"
                    :style="{ color: getNodeInfo(pos.step.agent).color }"
                  />
                </div>
              </foreignObject>

              <!-- Agent label -->
              <text
                :x="38"
                :y="20"
                class="text-xs font-medium"
                :fill="getNodeInfo(pos.step.agent).color"
              >
                {{ getNodeInfo(pos.step.agent).label }}
              </text>

              <!-- Step number -->
              <text
                :x="8"
                :y="55"
                class="text-xs"
                fill="#6b7280"
              >
                #{{ pos.index + 1 }}
              </text>

              <!-- Content preview -->
              <text
                :x="24"
                :y="55"
                class="text-xs"
                fill="#9ca3af"
              >
                <tspan v-if="pos.step.content.length > 18">
                  {{ pos.step.content.slice(0, 18) }}...
                </tspan>
                <tspan v-else>
                  {{ pos.step.content }}
                </tspan>
              </text>
            </g>
          </template>
        </g>
      </svg>

      <!-- Empty state -->
      <div
        v-if="steps.length === 0 && !isRunning"
        class="absolute inset-0 flex flex-col items-center justify-center"
      >
        <Search :size="48" class="text-dark-600 mb-4" />
        <p class="text-dark-400 text-sm">开始诊断后将显示追踪图</p>
      </div>

      <!-- Running indicator -->
      <div
        v-if="isRunning"
        class="absolute bottom-4 left-4 flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-500/20 border border-amber-500/50"
      >
        <Clock :size="14" class="text-amber-400 animate-spin" />
        <span class="text-amber-400 text-sm">诊断进行中...</span>
      </div>
    </div>

    <!-- Selected Node Detail Panel -->
    <div
      v-if="selectedNode"
      class="mt-4 p-4 rounded-lg border border-dark-700 bg-dark-800/50"
    >
      <div class="flex items-center justify-between mb-3">
        <h4 class="text-sm font-medium text-dark-100 flex items-center gap-2">
          <component
            :is="getNodeInfo(steps.find(s => s.id === selectedNode)?.agent || '').icon"
            :size="16"
            :style="{ color: getNodeInfo(steps.find(s => s.id === selectedNode)?.agent || '').color }"
          />
          节点详情
        </h4>
        <button
          @click="selectedNode = null"
          class="text-dark-400 hover:text-dark-200"
        >
          ×
        </button>
      </div>

      <div class="space-y-3 text-xs">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <span class="text-dark-500">Agent:</span>
            <span class="text-dark-200 ml-2">{{ steps.find(s => s.id === selectedNode)?.agent }}</span>
          </div>
          <div>
            <span class="text-dark-500">Action:</span>
            <span class="text-dark-200 ml-2">{{ steps.find(s => s.id === selectedNode)?.action }}</span>
          </div>
          <div>
            <span class="text-dark-500">Status:</span>
            <span class="ml-2" :style="{ color: getStatusInfo(steps.find(s => s.id === selectedNode)?.status || '').color }">
              {{ steps.find(s => s.id === selectedNode)?.status }}
            </span>
          </div>
          <div>
            <span class="text-dark-500">Time:</span>
            <span class="text-dark-200 ml-2">{{ steps.find(s => s.id === selectedNode)?.timestamp }}</span>
          </div>
        </div>

        <!-- Content -->
        <div>
          <span class="text-dark-500">Content:</span>
          <p class="text-dark-200 mt-1 p-2 bg-dark-900 rounded">{{ steps.find(s => s.id === selectedNode)?.content }}</p>
        </div>

        <!-- Reasoning -->
        <div v-if="steps.find(s => s.id === selectedNode)?.reasoning">
          <span class="text-dark-500">Reasoning:</span>
          <pre class="mt-1 p-2 bg-dark-900 rounded text-dark-300 max-h-32 overflow-auto whitespace-pre-wrap">{{ steps.find(s => s.id === selectedNode)?.reasoning }}</pre>
        </div>

        <!-- Output -->
        <div v-if="steps.find(s => s.id === selectedNode)?.output">
          <span class="text-dark-500">Output:</span>
          <pre class="mt-1 p-2 bg-dark-900 rounded text-dark-300 max-h-48 overflow-auto whitespace-pre-wrap">{{ formatJson(steps.find(s => s.id === selectedNode)?.output) }}</pre>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="mt-4 flex flex-wrap items-center gap-4 text-xs text-dark-500">
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
        <span>Done</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-amber-500 animate-pulse"></span>
        <span>Running</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-gray-500"></span>
        <span>Pending</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-red-500"></span>
        <span>Error</span>
      </div>
      <div class="flex items-center gap-1">
        <svg width="24" height="8">
          <line x1="0" y1="4" x2="24" y2="4" stroke="url(#edgeGradient)" stroke-width="2" />
        </svg>
        <span>Flow</span>
      </div>
    </div>
  </div>
</template>
