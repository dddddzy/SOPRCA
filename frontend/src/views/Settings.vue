<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useThemeStore } from '@/stores/theme'
import {
  Settings,
  Moon,
  Sun,
  Monitor,
  Save,
  RotateCcw,
  Globe,
  Bot,
  Server,
  Eye,
  EyeOff
  // Import icons if needed
} from 'lucide-vue-next'

const settingsStore = useSettingsStore()
const themeStore = useThemeStore()

const showApiKey = ref(false)
const isSaving = ref(false)

const modelForm = reactive({
  apiEndpoint: settingsStore.settings.model.apiEndpoint,
  modelName: settingsStore.settings.model.modelName,
  apiKey: settingsStore.settings.model.apiKey,
  maxTokens: settingsStore.settings.model.maxTokens,
  temperature: settingsStore.settings.model.temperature
})

const serverForm = reactive({
  host: settingsStore.settings.server.host,
  port: settingsStore.settings.server.port,
  langgraphUrl: settingsStore.settings.server.langgraphUrl
})

function setTheme(theme: 'dark' | 'light' | 'auto') {
  themeStore.setTheme(theme)
}

async function saveModelConfig() {
  isSaving.value = true
  settingsStore.updateModelConfig(modelForm)
  setTimeout(() => {
    isSaving.value = false
  }, 500)
}

async function saveServerConfig() {
  isSaving.value = true
  settingsStore.updateServerConfig(serverForm)
  setTimeout(() => {
    isSaving.value = false
  }, 500)
}

function resetAllSettings() {
  settingsStore.resetSettings()
  // Reload page to reflect changes
  window.location.reload()
}
</script>

<template>
  <div class="max-w-4xl space-y-6">
    <!-- Theme Settings -->
    <div class="card">
      <div class="flex items-center gap-3 mb-6">
        <div class="p-2 bg-dark-700 rounded-lg">
          <Settings :size="20" class="text-dark-300" />
        </div>
        <div>
          <h2 class="text-lg font-semibold text-dark-100">主题设置</h2>
          <p class="text-sm text-dark-400">自定义界面外观</p>
        </div>
      </div>

      <div class="space-y-4">
        <div>
          <label class="text-sm font-medium text-dark-300 mb-3 block">主题模式</label>
          <div class="flex gap-3">
            <button
              @click="setTheme('dark')"
              :class="[
                'flex items-center gap-2 px-4 py-3 rounded-lg border transition-all cursor-pointer',
                themeStore.theme === 'dark'
                  ? 'border-primary-500 bg-primary-500/10 text-primary-400'
                  : 'border-dark-600 bg-dark-700 text-dark-300 hover:border-dark-500'
              ]"
            >
              <Moon :size="18" />
              <span>暗色</span>
            </button>
            <button
              @click="setTheme('light')"
              :class="[
                'flex items-center gap-2 px-4 py-3 rounded-lg border transition-all cursor-pointer',
                themeStore.theme === 'light'
                  ? 'border-primary-500 bg-primary-500/10 text-primary-400'
                  : 'border-dark-600 bg-dark-700 text-dark-300 hover:border-dark-500'
              ]"
            >
              <Sun :size="18" />
              <span>亮色</span>
            </button>
            <button
              @click="setTheme('auto')"
              :class="[
                'flex items-center gap-2 px-4 py-3 rounded-lg border transition-all cursor-pointer',
                themeStore.theme === 'auto'
                  ? 'border-primary-500 bg-primary-500/10 text-primary-400'
                  : 'border-dark-600 bg-dark-700 text-dark-300 hover:border-dark-500'
              ]"
            >
              <Monitor :size="18" />
              <span>跟随系统</span>
            </button>
          </div>
        </div>

        <div>
          <label class="text-sm font-medium text-dark-300 mb-3 block">语言</label>
          <select class="input-field w-48">
            <option value="zh-CN">简体中文</option>
            <option value="en">English</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Model Settings -->
    <div class="card">
      <div class="flex items-center gap-3 mb-6">
        <div class="p-2 bg-primary-500/20 rounded-lg">
          <Bot :size="20" class="text-primary-400" />
        </div>
        <div>
          <h2 class="text-lg font-semibold text-dark-100">模型配置</h2>
          <p class="text-sm text-dark-400">配置 LLM API 连接参数</p>
        </div>
      </div>

      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">API Endpoint</label>
            <input
              v-model="modelForm.apiEndpoint"
              type="text"
              class="input-field"
              placeholder="https://api.example.com/v1"
            />
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">模型名称</label>
            <input
              v-model="modelForm.modelName"
              type="text"
              class="input-field"
              placeholder="gpt-4 / claude-3"
            />
          </div>
        </div>

        <div>
          <label class="text-sm font-medium text-dark-300 mb-2 block">API Key</label>
          <div class="relative">
            <input
              v-model="modelForm.apiKey"
              :type="showApiKey ? 'text' : 'password'"
              class="input-field pr-10"
              placeholder="sk-..."
            />
            <button
              @click="showApiKey = !showApiKey"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-200 cursor-pointer"
            >
              <component :is="showApiKey ? EyeOff : Eye" :size="18" />
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">最大 Tokens</label>
            <input
              v-model.number="modelForm.maxTokens"
              type="number"
              class="input-field"
              placeholder="8192"
            />
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">Temperature</label>
            <input
              v-model.number="modelForm.temperature"
              type="number"
              step="0.1"
              min="0"
              max="2"
              class="input-field"
              placeholder="0.7"
            />
          </div>
        </div>

        <div class="flex justify-end">
          <button
            @click="saveModelConfig"
            :disabled="isSaving"
            class="btn-primary flex items-center gap-2"
          >
            <Save :size="16" />
            {{ isSaving ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Server Settings -->
    <div class="card">
      <div class="flex items-center gap-3 mb-6">
        <div class="p-2 bg-accent-500/20 rounded-lg">
          <Server :size="20" class="text-accent-400" />
        </div>
        <div>
          <h2 class="text-lg font-semibold text-dark-100">服务器配置</h2>
          <p class="text-sm text-dark-400">配置后端服务连接</p>
        </div>
      </div>

      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">Host</label>
            <input
              v-model="serverForm.host"
              type="text"
              class="input-field"
              placeholder="0.0.0.0"
            />
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">Port</label>
            <input
              v-model.number="serverForm.port"
              type="number"
              class="input-field"
              placeholder="8000"
            />
          </div>
        </div>

        <div>
          <label class="text-sm font-medium text-dark-300 mb-2 block">LangGraph URL</label>
          <input
            v-model="serverForm.langgraphUrl"
            type="text"
            class="input-field"
            placeholder="http://localhost:8000"
          />
        </div>

        <div class="flex justify-end">
          <button
            @click="saveServerConfig"
            :disabled="isSaving"
            class="btn-primary flex items-center gap-2"
          >
            <Save :size="16" />
            {{ isSaving ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Reset -->
    <div class="card border-red-500/20">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-medium text-dark-200">重置所有设置</h3>
          <p class="text-xs text-dark-400 mt-1">将所有配置恢复为默认值</p>
        </div>
        <button
          @click="resetAllSettings"
          class="btn-danger flex items-center gap-2"
        >
          <RotateCcw :size="16" />
          重置
        </button>
      </div>
    </div>
  </div>
</template>
