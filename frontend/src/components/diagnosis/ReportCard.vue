<script setup lang="ts">
import type { RCAReport } from '@/types'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  MapPin,
  Lightbulb,
  Shield,
  Copy,
  Download,
  FileText,
  BookOpen,
  Route,
  History,
  BrainCircuit,
  Scale,
  Wrench
} from 'lucide-vue-next'
import { ref } from 'vue'

const props = defineProps<{
  report: RCAReport | null
  isRunning: boolean
}>()

const copied = ref(false)

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

// 生成完整的 Markdown 报告
function generateMarkdown(): string {
  if (!props.report) return ''

  const r = props.report
  let md = `# 根因分析报告（Flow-of-Action SOP 架构 v7）

`
  md += `**故障信息**\n${r.rootCause || '未知故障'}\n`
  md += `\n`

  if (r.matchedSopName) {
    md += `**匹配SOP**\n${r.matchedSopName}`
    if (r.matchedSopSteps) {
      md += `（${r.matchedSopSteps}步）`
    }
    md += `\n`
  }

  if (r.diagnosisPath && r.diagnosisPath.length > 0) {
    md += `\n**诊断路径（APL = ${r.apl || r.diagnosisPath.length}）**\n`
    md += r.diagnosisPath.join(' → ')
    md += `\n`
  }

  if (r.similarFaults && r.similarFaults.length > 0) {
    md += `\n**历史相似故障参考（match_observation）**\n`
    r.similarFaults.forEach((f, i) => {
      const level = f.similarity >= 0.9 ? '高度一致' : f.similarity >= 0.7 ? '中度相似' : '略有参考价值'
      md += `Top-${i + 1}：${f.id}（相似度 ${f.similarity.toFixed(2)}）—— 历史根因：${f.rootCause}（${level}）\n`
    })
  }

  if (r.obAgentClues) {
    md += `\n**ObAgent 提取线索**\n`
    md += `- 故障类型：${r.obAgentClues.faultType}\n`
    md += `- 故障位置：${r.obAgentClues.faultLocation}\n`
    if (r.obAgentClues.keyClues.length > 0) {
      md += `- 关键线索（${r.obAgentClues.keyClues.length}条）：\n`
      r.obAgentClues.keyClues.forEach(c => {
        md += `  - ${c}\n`
      })
    }
    if (r.obAgentClues.excludedReasons.length > 0) {
      md += `- 已排除根因（${r.obAgentClues.excludedReasons.length}条）：\n`
      r.obAgentClues.excludedReasons.forEach(e => {
        md += `  - ${e}\n`
      })
    }
  }

  md += `\n**JudgeAgent 根因判定**\n`
  if (r.isRootCauseFound) {
    md += `已找到根因`
    if (r.judgeAgentReasoning) {
      md += `\n- 判定依据：${r.judgeAgentReasoning}\n`
    }
  } else {
    md += `未找到根因\n`
    if (r.terminationReason) {
      md += `- 终止原因：${r.terminationReason}\n`
    }
  }

  md += `\n**最终根因**\n`
  md += `**${r.rootCause}**\n`

  if (r.suggestions && r.suggestions.length > 0) {
    md += `\n**修复建议**\n`
    r.suggestions.forEach((s, i) => {
      md += `- ${s}\n`
    })
  }

  if (r.faultId) {
    md += `\n**本次诊断贡献**\n`
    md += `已将完整诊断过程存入历史故障库（${r.faultId}），供后续相似故障参考。\n`
  }

  return md
}

async function copyReport() {
  const md = generateMarkdown()
  if (!md) return

  try {
    await navigator.clipboard.writeText(md)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (e) {
    console.error('复制失败:', e)
  }
}

function downloadReport() {
  const md = generateMarkdown()
  if (!md) return

  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const timestamp = new Date().toISOString().slice(0, 10)
  a.href = url
  a.download = `RCA报告_${timestamp}.md`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="card h-full flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4 flex-shrink-0">
      <div class="flex items-center gap-2">
        <FileText :size="16" class="text-primary-400" />
        <h3 class="text-sm font-medium text-dark-300">诊断报告</h3>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-if="report"
          @click="copyReport"
          class="flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs transition-colors"
          :class="copied ? 'bg-emerald-500/20 text-emerald-400' : 'bg-dark-700 hover:bg-dark-600 text-dark-300'"
        >
          <Copy :size="12" />
          {{ copied ? '已复制' : '复制' }}
        </button>
        <button
          v-if="report"
          @click="downloadReport"
          class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-dark-700 hover:bg-dark-600 text-dark-300 text-xs transition-colors"
        >
          <Download :size="12" />
          下载
        </button>
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
    </div>

    <!-- Empty State -->
    <div
      v-if="!report && !isRunning"
      class="flex flex-col items-center justify-center flex-1 text-center py-8"
    >
      <AlertTriangle :size="36" class="text-dark-600 mb-3" />
      <p class="text-dark-400 text-sm">暂无诊断报告</p>
      <p class="text-xs text-dark-500 mt-1">请输入故障描述开始诊断</p>
    </div>

    <!-- Running State -->
    <div
      v-if="isRunning && !report"
      class="flex flex-col items-center justify-center flex-1 text-center py-8"
    >
      <div class="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mb-3"></div>
      <p class="text-dark-400 text-sm">正在分析中...</p>
    </div>

    <!-- Report Content - Scrollable -->
    <div v-if="report" class="flex-1 overflow-auto space-y-4 min-h-0">
      <!-- Root Cause Card -->
      <div class="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
        <div class="flex items-start gap-2">
          <AlertTriangle :size="18" class="text-red-400 mt-0.5 shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="text-xs text-red-400 mb-2 font-medium">最终根因</p>
            <p class="text-sm font-medium text-dark-100 leading-relaxed">{{ report.rootCause }}</p>
          </div>
        </div>
      </div>

      <!-- Meta Grid -->
      <div class="grid grid-cols-2 gap-3">
        <div class="flex items-center gap-2 p-2 rounded-lg bg-dark-800/50">
          <BookOpen :size="14" class="text-dark-400 shrink-0" />
          <div class="min-w-0">
            <p class="text-[10px] text-dark-500">匹配SOP</p>
            <p class="text-xs text-dark-200 truncate">{{ report.matchedSopName || '未匹配' }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2 p-2 rounded-lg bg-dark-800/50">
          <Route :size="14" class="text-dark-400 shrink-0" />
          <div class="min-w-0">
            <p class="text-[10px] text-dark-500">诊断路径</p>
            <p class="text-xs text-dark-200">
              <span v-if="report.diagnosisPath">{{ report.diagnosisPath.join(' → ') }}</span>
              <span v-else-if="report.apl">APL = {{ report.apl }}</span>
              <span v-else>无</span>
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2 p-2 rounded-lg bg-dark-800/50">
          <MapPin :size="14" class="text-dark-400 shrink-0" />
          <div class="min-w-0">
            <p class="text-[10px] text-dark-500">故障位置</p>
            <p class="text-xs text-dark-200 truncate">{{ report.faultLocation || '未知' }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2 p-2 rounded-lg bg-dark-800/50">
          <Clock :size="14" class="text-dark-400 shrink-0" />
          <div class="min-w-0">
            <p class="text-[10px] text-dark-500">诊断时间</p>
            <p class="text-xs text-dark-200">{{ report.diagnosisTime }}</p>
          </div>
        </div>
      </div>

      <!-- Similar Faults Reference -->
      <div v-if="report.similarFaults && report.similarFaults.length > 0" class="p-3 rounded-lg bg-dark-800/30 border border-dark-700">
        <div class="flex items-center gap-2 mb-2">
          <History :size="14" class="text-amber-400" />
          <span class="text-xs font-medium text-dark-300">历史相似故障参考</span>
        </div>
        <div class="space-y-1.5">
          <div
            v-for="(fault, idx) in report.similarFaults.slice(0, 3)"
            :key="fault.id"
            class="flex items-start gap-2 text-xs"
          >
            <span class="text-amber-400 shrink-0">Top-{{ idx + 1 }}</span>
            <div class="min-w-0 flex-1">
              <span class="text-dark-300">{{ fault.id }}（相似度 {{ (fault.similarity * 100).toFixed(0) }}%）</span>
              <span class="text-dark-500 ml-1">—— {{ fault.rootCause }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ObAgent Clues -->
      <div v-if="report.obAgentClues" class="p-3 rounded-lg bg-dark-800/30 border border-dark-700">
        <div class="flex items-center gap-2 mb-3">
          <BrainCircuit :size="14" class="text-primary-400" />
          <span class="text-xs font-medium text-dark-300">ObAgent 提取线索</span>
        </div>

        <div class="space-y-2">
          <div class="flex items-center gap-2 text-xs">
            <span class="text-dark-500 w-16 shrink-0">故障类型：</span>
            <span class="text-dark-200">{{ report.obAgentClues.faultType }}</span>
          </div>
          <div class="flex items-center gap-2 text-xs">
            <span class="text-dark-500 w-16 shrink-0">故障位置：</span>
            <span class="text-dark-200">{{ report.obAgentClues.faultLocation }}</span>
          </div>

          <div v-if="report.obAgentClues.keyClues.length > 0">
            <p class="text-xs text-dark-500 mb-1.5">关键线索（{{ report.obAgentClues.keyClues.length }}条）：</p>
            <ul class="space-y-1">
              <li
                v-for="(clue, idx) in report.obAgentClues.keyClues"
                :key="idx"
                class="flex items-start gap-2 text-xs"
              >
                <span class="text-primary-400 shrink-0">•</span>
                <span class="text-dark-300">{{ clue }}</span>
              </li>
            </ul>
          </div>

          <div v-if="report.obAgentClues.excludedReasons.length > 0">
            <p class="text-xs text-dark-500 mb-1.5">已排除根因（{{ report.obAgentClues.excludedReasons.length }}条）：</p>
            <ul class="space-y-1">
              <li
                v-for="(reason, idx) in report.obAgentClues.excludedReasons"
                :key="idx"
                class="flex items-start gap-2 text-xs"
              >
                <span class="text-dark-500 shrink-0">✗</span>
                <span class="text-dark-400">{{ reason }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- JudgeAgent Reasoning -->
      <div v-if="report.judgeAgentReasoning" class="p-3 rounded-lg bg-dark-800/30 border border-dark-700">
        <div class="flex items-center gap-2 mb-2">
          <Scale :size="14" class="text-emerald-400" />
          <span class="text-xs font-medium text-dark-300">JudgeAgent 根因判定</span>
        </div>
        <div class="flex items-center gap-2 mb-2">
          <span :class="report.isRootCauseFound ? 'text-emerald-400' : 'text-amber-400'" class="text-xs font-medium">
            {{ report.isRootCauseFound ? '已找到根因（三要素均满足）' : '未找到根因' }}
          </span>
        </div>
        <p class="text-xs text-dark-400 leading-relaxed">{{ report.judgeAgentReasoning }}</p>
      </div>

      <!-- Suggestions -->
      <div v-if="report.suggestions && report.suggestions.length > 0" class="p-3 rounded-lg bg-dark-800/30 border border-dark-700">
        <div class="flex items-center gap-2 mb-2">
          <Wrench :size="14" class="text-emerald-400" />
          <span class="text-xs font-medium text-dark-300">修复建议</span>
        </div>
        <ul class="space-y-1.5">
          <li
            v-for="(suggestion, idx) in report.suggestions"
            :key="idx"
            class="flex items-start gap-2 text-xs"
          >
            <CheckCircle2 :size="12" class="text-emerald-400 mt-0.5 shrink-0" />
            <span class="text-dark-300">{{ suggestion }}</span>
          </li>
        </ul>
      </div>

      <!-- Contribution Note -->
      <div v-if="report.faultId" class="text-xs text-dark-500 text-center py-2 border-t border-dark-800">
        已存入历史故障库（{{ report.faultId }}）
      </div>
    </div>
  </div>
</template>
