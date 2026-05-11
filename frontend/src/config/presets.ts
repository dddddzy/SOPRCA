// 预设模型配置
export interface PresetModel {
  id: string
  name: string
  apiEndpoint: string
  modelName: string
  apiKey: string
  temperature: number
  maxTokens: number
  description: string
}

export const presetModels: PresetModel[] = [
  {
    id: 'deepseek-chat',
    name: 'DeepSeek Chat',
    apiEndpoint: 'https://api.deepseek.com',
    modelName: 'deepseek-chat',
    apiKey: 'sk-d22b90a04ecd4cce8fc03304d2bbfc04',
    temperature: 0.1,
    maxTokens: 8192,
    description: 'DeepSeek V3 模型，适合通用对话'
  },
  {
    id: 'qwen3-32b',
    name: 'Qwen3 32B (Ollama)',
    apiEndpoint: 'http://82.157.52.68:11434',
    modelName: 'qwen3:32b',
    apiKey: 'Dummy',
    temperature: 0.7,
    maxTokens: 8192,
    description: 'Qwen3 32B 本地模型 (Ollama)'
  },
  {
    id: 'minimax',
    name: 'MiniMax Text-01',
    apiEndpoint: 'http://82.157.52.68:30001/v1',
    modelName: 'MiniMax-Text-01',
    apiKey: 'Dummy',
    temperature: 0.7,
    maxTokens: 8192,
    description: 'MiniMax Text-01 模型'
  }
]