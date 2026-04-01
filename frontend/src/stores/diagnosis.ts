import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DiagnosisStep, RCAReport, LogEntry } from '@/types'

export const useDiagnosisStore = defineStore('diagnosis', () => {
  const faultInfo = ref('')
  const isRunning = ref(false)
  const steps = ref<DiagnosisStep[]>([])
  const report = ref<RCAReport | null>(null)
  const logs = ref<LogEntry[]>([])

  const currentStep = computed(() => steps.value[steps.value.length - 1] || null)

  const isComplete = computed(() => isRunning.value === false && report.value !== null)

  function addStep(step: Omit<DiagnosisStep, 'id' | 'timestamp'>) {
    const newStep: DiagnosisStep = {
      ...step,
      id: `step-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false })
    }
    steps.value.push(newStep)
    return newStep
  }

  function updateStep(stepId: string, updates: Partial<DiagnosisStep>) {
    const index = steps.value.findIndex(s => s.id === stepId)
    if (index !== -1) {
      steps.value[index] = { ...steps.value[index], ...updates }
    }
  }

  function addLog(level: LogEntry['level'], message: string) {
    logs.value.push({
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      level,
      message
    })
  }

  function setReport(newReport: RCAReport) {
    report.value = newReport
  }

  function startDiagnosis(info: string) {
    faultInfo.value = info
    isRunning.value = true
    steps.value = []
    report.value = null
    logs.value = []
    addLog('primary', `开始诊断: ${info}`)
  }

  function stopDiagnosis() {
    isRunning.value = false
    addLog('info', '诊断已停止')
  }

  function reset() {
    faultInfo.value = ''
    isRunning.value = false
    steps.value = []
    report.value = null
    logs.value = []
  }

  // Simulate streaming diagnosis for demo
  async function runMockDiagnosis(faultInfoText: string) {
    startDiagnosis(faultInfoText)

    const mockSteps: Omit<DiagnosisStep, 'id' | 'timestamp'>[] = [
      { agent: 'action_agent', action: 'match_sop', status: 'done', content: '正在匹配SOP知识库...', duration: 1200 },
      { agent: 'main_agent', action: 'analyze', status: 'done', content: '分析故障描述: cpuservice CPU过高', duration: 800 },
      { agent: 'action_agent', action: 'generate_sop', status: 'done', content: '未找到匹配SOP，生成动态诊断流程', duration: 1500 },
      { agent: 'tool_executor', action: 'get_relevant_metric', status: 'done', content: '获取CPU指标数据: p95=95.2%', duration: 2000 },
      { agent: 'tool_executor', action: 'pod_analyze', status: 'done', content: '分析Pod状态: RestartCount=15', duration: 1800 },
      { agent: 'tool_executor', action: 'check_events', status: 'done', content: '检查Events: CPUThrottling', duration: 900 },
      { agent: 'code_agent', action: 'generate_code', status: 'done', content: '生成诊断代码', duration: 600 },
      { agent: 'judge_agent', action: 'evaluate', status: 'done', content: '评估根因: CPU资源不足', duration: 1100 },
      { agent: 'action_agent', action: 'final_decision', status: 'done', content: '确认最终诊断结果', duration: 500 }
    ]

    for (const step of mockSteps) {
      await new Promise(resolve => setTimeout(resolve, step.duration || 1000))
      addStep(step)
      addLog('info', `[${step.agent}] ${step.action}: ${step.content}`)
    }

    report.value = {
      rootCause: 'CPU资源不足 - 容器CPU限制过低导致节流',
      confidence: 0.92,
      faultType: '资源不足',
      faultLocation: 'cpuservice-pod-7d8b9c-xyz',
      keyClues: [
        'CPU使用率p95达95.2%',
        'Pod重启次数15次',
        'CPUThrottling事件频繁',
        '内存使用正常，排除OOM'
      ],
      diagnosisTime: new Date().toLocaleString('zh-CN'),
      suggestions: [
        '建议增加容器CPU limits',
        '考虑水平扩展cpuservice副本数',
        '检查是否存在CPU密集型业务逻辑'
      ]
    }

    isRunning.value = false
    addLog('success', '诊断完成！')
  }

  return {
    faultInfo,
    isRunning,
    steps,
    report,
    logs,
    currentStep,
    isComplete,
    addStep,
    updateStep,
    addLog,
    setReport,
    startDiagnosis,
    stopDiagnosis,
    reset,
    runMockDiagnosis
  }
})
