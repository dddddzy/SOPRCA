// RCA Diagnosis Types
export interface DiagnosisStep {
  id: string
  timestamp: string
  agent: 'action_agent' | 'main_agent' | 'tool_executor' | 'code_agent' | 'judge_agent' | 'ob_agent'
  action: string
  status: 'running' | 'done' | 'error' | 'pending'
  content: string
  duration?: number
}

export interface RCAReport {
  rootCause: string
  confidence: number
  keyClues: string[]
  diagnosisTime: string
  faultType: string
  faultLocation: string
  suggestions: string[]
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

export interface ServerConfig {
  host: string
  port: number
  langgraphUrl: string
}

export interface AppSettings {
  theme: 'dark' | 'light' | 'auto'
  language: string
  model: ModelConfig
  server: ServerConfig
}
