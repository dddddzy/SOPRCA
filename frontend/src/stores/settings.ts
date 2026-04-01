import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AppSettings, ModelConfig, ServerConfig } from '@/types'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<AppSettings>({
    theme: 'dark',
    language: 'zh-CN',
    model: {
      apiEndpoint: 'https://api.minimax.chat/v1',
      modelName: 'MiniMax-Text-01',
      apiKey: '',
      maxTokens: 8192,
      temperature: 0.7
    },
    server: {
      host: '0.0.0.0',
      port: 8000,
      langgraphUrl: 'http://localhost:8000'
    }
  })

  function updateModelConfig(config: Partial<ModelConfig>) {
    settings.value.model = { ...settings.value.model, ...config }
    saveSettings()
  }

  function updateServerConfig(config: Partial<ServerConfig>) {
    settings.value.server = { ...settings.value.server, ...config }
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

  function resetSettings() {
    settings.value = {
      theme: 'dark',
      language: 'zh-CN',
      model: {
        apiEndpoint: 'https://api.minimax.chat/v1',
        modelName: 'MiniMax-Text-01',
        apiKey: '',
        maxTokens: 8192,
        temperature: 0.7
      },
      server: {
        host: '0.0.0.0',
        port: 8000,
        langgraphUrl: 'http://localhost:8000'
      }
    }
    saveSettings()
  }

  return {
    settings,
    updateModelConfig,
    updateServerConfig,
    saveSettings,
    loadSettings,
    resetSettings
  }
})
