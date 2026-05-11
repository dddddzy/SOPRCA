import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AppSettings, ModelConfig, ClusterConfig, AntiLoopConfig } from '@/types'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<AppSettings>({
    theme: 'dark',
    language: 'zh-CN',
    model: {
      apiEndpoint: 'https://api.deepseek.com',
      modelName: 'deepseek-chat',
      apiKey: 'sk-d22b90a04ecd4cce8fc03304d2bbfc04',
      maxTokens: 8192,
      temperature: 0.1
    },
    cluster: {
      kubeconfig: '',
      server: 'https://192.168.100.132:6443',
      context: 'default',
      env: 'dev',
      mockMode: false
    },
    antiLoop: {
      maxCycleLimit: 20,
      maxNoGainTimes: 3,
      maxRepeatActionTimes: 2,
      globalTimeout: 600
    }
  })

  function updateModelConfig(config: Partial<ModelConfig>) {
    settings.value.model = { ...settings.value.model, ...config }
    saveSettings()
  }

  function updateClusterConfig(config: Partial<ClusterConfig>) {
    settings.value.cluster = { ...settings.value.cluster, ...config }
    saveSettings()
  }

  function saveSettings() {
    localStorage.setItem('soprca-settings', JSON.stringify(settings.value))
  }

  function loadSettings() {
    const saved = localStorage.getItem('soprca-settings')
    if (saved) {
      try {
        settings.value = { ...settings.value, ...JSON.parse(saved) }
      } catch (e) {
        console.error('Failed to load settings:', e)
      }
    }
  }

  function applyPreset(preset: {
    apiEndpoint: string
    modelName: string
    apiKey: string
    temperature: number
    maxTokens: number
  }) {
    settings.value.model = {
      ...settings.value.model,
      apiEndpoint: preset.apiEndpoint,
      modelName: preset.modelName,
      apiKey: preset.apiKey,
      temperature: preset.temperature,
      maxTokens: preset.maxTokens
    }
    saveSettings()
  }

  async function saveModelConfigToBackend() {
    try {
      const response = await fetch('/api/settings/model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings.value.model)
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      return true
    } catch (e) {
      console.error('Failed to save model config:', e)
      return false
    }
  }

  function resetSettings() {
    settings.value = {
      theme: 'dark',
      language: 'zh-CN',
      model: {
        apiEndpoint: 'https://api.deepseek.com',
        modelName: 'deepseek-chat',
        apiKey: 'sk-d22b90a04ecd4cce8fc03304d2bbfc04',
        maxTokens: 8192,
        temperature: 0.1
      },
      cluster: {
        kubeconfig: '',
        server: 'https://192.168.100.132:6443',
        context: 'default',
        env: 'dev',
        mockMode: false
      },
      antiLoop: {
        maxCycleLimit: 20,
        maxNoGainTimes: 3,
        maxRepeatActionTimes: 2,
        globalTimeout: 600
      }
    }
    saveSettings()
  }

  return {
    settings,
    updateModelConfig,
    updateClusterConfig,
    saveSettings,
    loadSettings,
    applyPreset,
    saveModelConfigToBackend,
    resetSettings
  }
})