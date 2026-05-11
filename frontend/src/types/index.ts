// RCA Diagnosis Types
export interface DiagnosisStep {
  id: string
  timestamp: string
  agent: 'action_agent' | 'main_agent' | 'tool_executor' | 'code_agent' | 'judge_agent' | 'ob_agent' | 'match_sop' | 'match_observation' | 'generate_sop' | 'generate_report'
  action: string
  status: 'running' | 'done' | 'error' | 'pending'
  content: string
  duration?: number
  // 详细输入输出
  input?: Record<string, any>
  output?: Record<string, any>
  reasoning?: string  // LLM思考过程
}

export interface RCAReport {
  rootCause: string
  confidence: number
  keyClues: string[]
  diagnosisTime: string
  faultType: string
  faultLocation: string
  suggestions: string[]
  // 扩展字段
  matchedSopName?: string
  matchedSopSteps?: number
  diagnosisPath?: string[]
  apl?: number
  similarFaults?: Array<{
    id: string
    similarity: number
    rootCause: string
    description: string
    hasReferenceValue: boolean
  }>
  obAgentClues?: {
    faultType: string
    faultLocation: string
    keyClues: string[]
    excludedReasons: string[]
  }
  judgeAgentReasoning?: string
  isRootCauseFound?: boolean
  terminationReason?: string
  faultId?: string
}

export interface DiagnosisState {
  faultInfo: string
  isRunning: boolean
  steps: DiagnosisStep[]
  report: RCAReport | null
  logs: LogEntry[]
}

export interface LogEntry {
  timestamp: string
  level: 'info' | 'success' | 'warning' | 'error' | 'primary'
  message: string
}

// SOP Types
export interface SOP {
  id: string
  name: string
  description: string
  faultType: string
  status: 'active' | 'draft' | 'archived'
  createdAt: string
  updatedAt: string
  matchCount: number
  steps: SOPStep[]
}

export interface SOPStep {
  order: number
  tool: string
  description: string
  expectedResult: string
}

// Dashboard Types
export interface ClusterStats {
  name: string
  status: 'healthy' | 'warning' | 'critical'
  podCount: number
  cpuUsage: number
  memoryUsage: number
  serviceCount: number
}

export interface FaultTrend {
  date: string
  count: number
}

export interface FaultTypeDistribution {
  type: string
  count: number
  percentage: number
}

// Settings Types
export interface ModelConfig {
  apiEndpoint: string
  modelName: string
  apiKey: string
  maxTokens: number
  temperature: number
}

export interface ClusterConfig {
  kubeconfig: string
  context: string
  server: string
  env: 'dev' | 'prod'
  mockMode: boolean
}

export interface AntiLoopConfig {
  maxCycleLimit: number
  maxNoGainTimes: number
  maxRepeatActionTimes: number
  globalTimeout: number
}

export interface AppSettings {
  theme: 'dark' | 'light' | 'auto'
  language: string
  model: ModelConfig
  cluster: ClusterConfig
  antiLoop: AntiLoopConfig
}
