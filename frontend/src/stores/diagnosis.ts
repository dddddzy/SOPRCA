import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DiagnosisStep, RCAReport, LogEntry } from '@/types'

// History record type
export interface DiagnosisRecord {
  id: string
  faultInfo: string
  timestamp: string
  duration: string
  result: 'found' | 'not_found' | 'stopped' | 'error'
  rootCause: string
  steps: DiagnosisStep[]
  report: RCAReport | null
}

const HISTORY_KEY = 'soprca-diagnosis-history'
const MAX_HISTORY = 50

export const useDiagnosisStore = defineStore('diagnosis', () => {
  const faultInfo = ref('')
  const isRunning = ref(false)
  const steps = ref<DiagnosisStep[]>([])
  const report = ref<RCAReport | null>(null)
  const logs = ref<LogEntry[]>([])
  const error = ref<string | null>(null)
  let abortController: AbortController | null = null

  // History
  const history = ref<DiagnosisRecord[]>(loadHistory())

  const currentStep = computed(() => steps.value[steps.value.length - 1] || null)
  const isComplete = computed(() => isRunning.value === false && report.value !== null)

  function loadHistory(): DiagnosisRecord[] {
    try {
      const saved = localStorage.getItem(HISTORY_KEY)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  }

  function saveHistory() {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history.value))
    } catch (e) {
      console.error('save history failed:', e)
    }
  }

  function addToHistory(record: DiagnosisRecord) {
    history.value.unshift(record)
    if (history.value.length > MAX_HISTORY) {
      history.value = history.value.slice(0, MAX_HISTORY)
    }
    saveHistory()
  }

  function clearHistory() {
    history.value = []
    saveHistory()
  }

  function removeFromHistory(id: string) {
    history.value = history.value.filter(r => r.id !== id)
    saveHistory()
  }

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
    error.value = null
    _diagnosisStartTime = Date.now()
    addLog('primary', `开始诊断: ${info}`)
  }

  function stopDiagnosis() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isRunning.value = false
    addLog('info', '诊断已停止')
  }

  function reset() {
    stopDiagnosis()
    faultInfo.value = ''
    steps.value = []
    report.value = null
    logs.value = []
    error.value = null
  }

  async function runDiagnosis(faultInfoText: string) {
    startDiagnosis(faultInfoText)
    addLog('info', '正在连接后端服务...')

    abortController = new AbortController()

    try {
      const response = await fetch('/api/diagnose', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fault_info: faultInfoText }),
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      addLog('info', '已建立连接，开始接收诊断数据...')

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法读取响应流')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        // 检查是否被停止
        if (!isRunning.value) {
          addLog('warning', '诊断已被停止')
          break
        }

        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue

          // 再次检查是否被停止
          if (!isRunning.value) {
            addLog('warning', '诊断已被停止')
            break
          }

          try {
            const parsed = JSON.parse(line)

            if (parsed.type === 'done') {
              addLog('success', '诊断完成！')
              isRunning.value = false
              saveToHistory('found')
              break
            }

            // 处理原始日志（从后端audit透传）
            if (parsed.type === 'log') {
              // 原始日志直接显示，根据日志内容判断级别
              const msg = parsed.message || ''
              if (msg.includes('[ERROR]')) {
                addLog('error', msg)
              } else if (msg.includes('[TERMINATE]')) {
                addLog('warning', msg)
              } else if (msg.includes('[JUDGE]')) {
                addLog('primary', msg)
              } else {
                addLog('info', msg)
              }
              continue
            }

            const stepName = parsed.step
            const output = parsed.output || {}

            // 根据不同节点生成步骤
            const stepInfo = generateStepInfo(stepName, output)
            if (stepInfo) {
              addStep(stepInfo)
              // 不再在这里添加日志，因为后端会透传原始audit日志
            }

            // 如果是 generate_report，解析最终报告
            if (stepName === 'generate_report' && output.final_report) {
              console.log('[Diagnosis] generate_report, output.structured_report:', output.structured_report)
              parseAndSetReport(output.final_report, output.structured_report)
            }
          } catch (e) {
            console.warn('解析响应行失败:', line, e)
          }
        }
      }
    } catch (e: any) {
      // AbortError 是用户主动停止，不算错误
      if (e.name === 'AbortError') {
        addLog('info', '诊断已停止')
        saveToHistory('stopped')
      } else {
        error.value = e.message
        addLog('error', `诊断失败: ${e.message}`)
        saveToHistory('error')
      }
    } finally {
      isRunning.value = false
      abortController = null
    }
  }

  let _diagnosisStartTime = 0

  function saveToHistory(result: DiagnosisRecord['result']) {
    const duration = _diagnosisStartTime ? Math.round((Date.now() - _diagnosisStartTime) / 1000) : 0
    const record: DiagnosisRecord = {
      id: `diag-${Date.now()}`,
      faultInfo: faultInfo.value,
      timestamp: new Date().toLocaleString('zh-CN'),
      duration: `${duration}秒`,
      result,
      rootCause: report.value?.rootCause || '',
      steps: [...steps.value],
      report: report.value
    }
    addToHistory(record)
  }

  function generateStepInfo(stepName: string, output: any): Omit<DiagnosisStep, 'id' | 'timestamp'> | null {
    let stepData: Omit<DiagnosisStep, 'id' | 'timestamp'> | null = null

    switch (stepName) {
      case 'match_sop':
        stepData = {
          agent: 'match_sop',
          action: 'match_sop',
          status: 'done',
          content: output.matched_sop
            ? `匹配到SOP: ${output.matched_sop.sop_name || '未知'}`
            : '未匹配到SOP',
          output: output.matched_sop ? { sop_name: output.matched_sop.sop_name, fault_type: output.matched_sop.fault_type, distance: output.matched_sop.distance } : undefined,
        }
        break
      case 'generate_sop':
        stepData = {
          agent: 'generate_sop',
          action: 'generate_sop',
          status: 'done',
          content: output.matched_sop
            ? `生成SOP: ${output.matched_sop.sop_name || '未知'}`
            : 'SOP生成失败',
          output: output.matched_sop || undefined,
        }
        break
      case 'action_agent':
        stepData = {
          agent: 'action_agent',
          action: 'action_agent',
          status: 'done',
          content: `生成${(output.candidate_action_set || []).length}个候选动作`,
          output: { candidate_action_set: output.candidate_action_set || [] },
          reasoning: output.action_reasoning || output.reason || undefined,
        }
        break
      case 'main_agent':
        stepData = {
          agent: 'main_agent',
          action: 'main_agent',
          status: 'done',
          content: output.selected_action
            ? `选择动作: ${output.selected_action.action || '未知'}`
            : '等待决策...',
          output: { selected_action: output.selected_action },
          reasoning: output.selection_reasoning || output.reason || undefined,
        }
        break
      case 'code_agent':
        stepData = {
          agent: 'code_agent',
          action: 'code_agent',
          status: 'done',
          content: output.generated_code
            ? `生成代码 (${output.generated_code.length}字符)`
            : '代码生成失败',
          output: { generated_code: output.generated_code },
        }
        break
      case 'tool_executor':
        stepData = {
          agent: 'tool_executor',
          action: output.executed_steps?.slice(-1)[0]?.action || 'tool_executor',
          status: 'done',
          content: `执行 ${output.executed_steps?.slice(-1)[0]?.action || 'tool_executor'}`,
          output: {
            tool_result: output.tool_result,
            executed_steps: output.executed_steps,
            iteration_count: output.iteration_count,
          },
        }
        break
      case 'ob_agent':
        stepData = {
          agent: 'ob_agent',
          action: 'ob_agent',
          status: 'done',
          content: output.extracted_clues
            ? `提取线索: ${output.extracted_clues.fault_type || '未知'}`
            : '提取线索完成',
          output: { extracted_clues: output.extracted_clues },
          reasoning: output.ob_reasoning || output.reason || undefined,
        }
        break
      case 'judge_agent':
        stepData = {
          agent: 'judge_agent',
          action: 'judge_agent',
          status: 'done',
          content: output.is_root_cause_found
            ? '已找到根因'
            : `无增益: ${output.consecutive_no_gain || 0}`,
          output: {
            is_root_cause_found: output.is_root_cause_found,
            explanation: output.explanation,
            termination_reason: output.termination_reason,
          },
          reasoning: output.judge_reasoning || output.reason || undefined,
        }
        break
      case 'match_observation':
        stepData = {
          agent: 'match_observation',
          action: 'match_observation',
          status: 'done',
          content: `找到${(output.similar_history_faults || []).length}个相似历史故障`,
          output: { similar_history_faults: output.similar_history_faults || [] },
        }
        break
      case 'generate_report':
        stepData = {
          agent: 'generate_report',
          action: 'generate_report',
          status: 'done',
          content: '生成最终报告',
          output: output.final_report ? { report_preview: output.final_report.slice(0, 300) } : undefined,
        }
        break
      default:
        stepData = {
          agent: 'tool_executor',
          action: stepName,
          status: 'done',
          content: `执行 ${stepName}`,
          output: output,
        }
    }

    // 如果有reason字段但不在上面单独处理，从output中提取
    if (stepData && !stepData.reasoning && output.reason) {
      stepData.reasoning = output.reason
    }

    return stepData
  }

  function parseAndSetReport(reportText: string, structuredData?: any) {
    console.log('[parseAndSetReport] called', { hasStructuredData: !!structuredData, structuredDataKeys: structuredData ? Object.keys(structuredData) : [] })
    // 如果有结构化数据，优先使用
    if (structuredData) {
      const reportData: RCAReport = {
        rootCause: structuredData.final_root_cause || '',
        confidence: structuredData.is_root_cause_found ? 0.85 : 0.5,
        keyClues: structuredData.ob_agent_clues?.key_clues || [],
        diagnosisTime: new Date().toLocaleString('zh-CN'),
        faultType: structuredData.ob_agent_clues?.fault_type || '',
        faultLocation: structuredData.ob_agent_clues?.fault_location || '',
        suggestions: structuredData.suggestions || [],
        matchedSopName: structuredData.matched_sop_name || undefined,
        matchedSopSteps: structuredData.matched_sop_steps || undefined,
        diagnosisPath: structuredData.diagnosis_path || [],
        apl: structuredData.apl || 0,
        similarFaults: (structuredData.similar_faults || []).map((f: any) => ({
          id: f.id,
          similarity: f.similarity,
          rootCause: f.root_cause,
          description: '',
          hasReferenceValue: f.similarity >= 0.7
        })),
        obAgentClues: structuredData.ob_agent_clues ? {
          faultType: structuredData.ob_agent_clues.fault_type || '',
          faultLocation: structuredData.ob_agent_clues.fault_location || '',
          keyClues: structuredData.ob_agent_clues.key_clues || [],
          excludedReasons: structuredData.ob_agent_clues.excluded_reasons || []
        } : undefined,
        isRootCauseFound: structuredData.is_root_cause_found || false,
        judgeAgentReasoning: structuredData.judge_agent_reasoning || undefined,
        terminationReason: structuredData.termination_reason || undefined,
        faultId: structuredData.fault_id
      }
      setReport(reportData)
      return
    }

    // 回退到简单解析 markdown 格式的报告
    const lines = reportText.split('\n')
    const reportData: any = {
      rootCause: '',
      confidence: 0,
      faultType: '',
      faultLocation: '',
      keyClues: [],
      diagnosisTime: new Date().toLocaleString('zh-CN'),
      suggestions: [],
    }

    let currentSection = ''
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
        currentSection = trimmed.replace(/\*\*/g, '')
        continue
      }
      if (trimmed.startsWith('- ') && !trimmed.includes('：')) {
        if (currentSection.includes('建议')) {
          reportData.suggestions.push(trimmed.slice(2))
        } else if (currentSection.includes('线索')) {
          reportData.keyClues.push(trimmed.slice(2))
        }
      }
      if (trimmed.includes('：') && !trimmed.startsWith('-')) {
        const [key, ...valueParts] = trimmed.split('：')
        const value = valueParts.join('：')
        if (key.includes('根因') && !key.includes('已排除')) {
          reportData.rootCause = value
        } else if (key.includes('故障类型')) {
          reportData.faultType = value
        } else if (key.includes('位置')) {
          reportData.faultLocation = value
        }
      }
    }

    // 如果没有解析到根因，尝试从报告文本中提取
    if (!reportData.rootCause && reportText.includes('**')) {
      const match = reportText.match(/\*\*最终根因\*\*\s*\*\*([^*]+)\*\*/)
      if (match) {
        reportData.rootCause = match[1]
      }
    }

    reportData.confidence = reportData.rootCause ? 0.85 : 0.5
    setReport(reportData)
  }

  // 连接自动巡检SSE，接收后台触发的诊断更新
  let monitorEventSource: EventSource | null = null
  let pendingDiagnosisInfo: string | null = null

  function connectMonitorSSE() {
    if (monitorEventSource) {
      monitorEventSource.close()
    }
    monitorEventSource = new EventSource('/api/monitor/sse')
    monitorEventSource.onmessage = (event) => {
      try {
        let text = event.data || ''
        if (text.startsWith('data: ')) {
          text = text.slice(6)
        }
        const payload = JSON.parse(text)
        if (payload.type === 'log') {
          if (!isRunning.value && !pendingDiagnosisInfo) {
            pendingDiagnosisInfo = payload.message || '自动巡检触发的诊断'
          }
          if (!isRunning.value && pendingDiagnosisInfo) {
            startDiagnosis(pendingDiagnosisInfo)
            pendingDiagnosisInfo = null
          }
          const msg = payload.message || ''
          if (msg.includes('[ERROR]')) {
            addLog('error', msg)
          } else if (msg.includes('[TERMINATE]')) {
            addLog('warning', msg)
          } else if (msg.includes('[JUDGE]')) {
            addLog('primary', msg)
          } else {
            addLog('info', msg)
          }
        } else if (payload.step) {
          if (!isRunning.value) {
            startDiagnosis(pendingDiagnosisInfo || '自动巡检触发的诊断')
            pendingDiagnosisInfo = null
          }
          const stepInfo = generateStepInfo(payload.step, payload.output || {})
          if (stepInfo) {
            addStep(stepInfo)
          }
          if (payload.step === 'generate_report' && payload.output?.final_report) {
            console.log('[Monitor SSE] structured_report:', payload.output.structured_report)
            parseAndSetReport(payload.output.final_report, payload.output.structured_report)
          }
        } else if (payload.type === 'done') {
          addLog('success', '诊断完成！')
          isRunning.value = false
          saveToHistory('found')
        }
      } catch (e) {
        console.warn('解析SSE消息失败:', e)
      }
    }
    monitorEventSource.onerror = () => {
      console.warn('Monitor SSE 连接断开')
    }
  }

  function disconnectMonitorSSE() {
    if (monitorEventSource) {
      monitorEventSource.close()
      monitorEventSource = null
    }
  }

  return {
    faultInfo,
    isRunning,
    steps,
    report,
    logs,
    error,
    history,
    currentStep,
    isComplete,
    addStep,
    updateStep,
    addLog,
    setReport,
    startDiagnosis,
    stopDiagnosis,
    reset,
    runDiagnosis,
    clearHistory,
    removeFromHistory,
    connectMonitorSSE,
    disconnectMonitorSSE,
  }
})
