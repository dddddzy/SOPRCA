<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useThemeStore } from '@/stores/theme'
import { useI18n } from 'vue-i18n'
import { setLocale } from '@/i18n'
import { useToast } from '@/composables/useToast'
import { presetModels, type PresetModel } from '@/config/presets'
import { presetClusters, type PresetCluster } from '@/config/clusterPresets'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import {
  Settings,
  Moon,
  Sun,
  Monitor,
  Save,
  RotateCcw,
  Bot,
  Folder,
  Eye,
  EyeOff,
  Zap,
  Wifi,
  Loader2,
  Trash2,
  Activity,
  Server,
  HardDrive,
  Cpu,
  Shield
} from 'lucide-vue-next'

const { t, locale } = useI18n()
const settingsStore = useSettingsStore()
const themeStore = useThemeStore()
const toast = useToast()

const showResetConfirm = ref(false)
const showClearConfirm = ref(false)

const showApiKey = ref(false)
const isSaving = ref(false)
const selectedPresetId = ref<string>('')
const selectedClusterId = ref<string>('')

const modelForm = reactive({
  apiEndpoint: settingsStore.settings.model.apiEndpoint,
  modelName: settingsStore.settings.model.modelName,
  apiKey: settingsStore.settings.model.apiKey,
  maxTokens: settingsStore.settings.model.maxTokens,
  temperature: settingsStore.settings.model.temperature
})

const clusterForm = reactive({
  server: settingsStore.settings.cluster.server,
  context: settingsStore.settings.cluster.context,
  env: settingsStore.settings.cluster.env,
  mockMode: settingsStore.settings.cluster.mockMode
})

// Monitor threshold settings
const monitorEnabled = ref(false)
const monitorForm = reactive({
  cpu_percent: 90,
  memory_percent: 85,
  disk_percent: 90,
  restart_count: 3
})
const monitorStatus = ref<any>(null)

// Anti-loop settings
const antiLoopForm = reactive({
  maxCycleLimit: 20,
  maxNoGainTimes: 3,
  maxRepeatActionTimes: 2,
  globalTimeout: 600
})
const isAntiLoopSaving = ref(false)

// 监听 store 变化，同步到 form
watch(
  () => settingsStore.settings.model,
  (newModel) => {
    modelForm.apiEndpoint = newModel.apiEndpoint
    modelForm.modelName = newModel.modelName
    modelForm.apiKey = newModel.apiKey
    modelForm.maxTokens = newModel.maxTokens
    modelForm.temperature = newModel.temperature
  },
  { deep: true }
)

function setTheme(theme: 'dark' | 'light' | 'auto') {
  themeStore.setTheme(theme)
}

function changeLanguage(lang: string) {
  setLocale(lang as 'zh-CN' | 'en-US')
}

function applyPreset(preset: PresetModel) {
  modelForm.apiEndpoint = preset.apiEndpoint
  modelForm.modelName = preset.modelName
  modelForm.apiKey = preset.apiKey
  modelForm.maxTokens = preset.maxTokens
  modelForm.temperature = preset.temperature
  selectedPresetId.value = preset.id
}

function applyClusterPreset(preset: PresetCluster) {
  clusterForm.server = preset.server
  clusterForm.context = preset.context
  clusterForm.env = preset.env
  clusterForm.mockMode = preset.mockMode
  selectedClusterId.value = preset.id
}

function saveModelConfig() {
  isSaving.value = true
  settingsStore.updateModelConfig(modelForm)
  setTimeout(() => {
    isSaving.value = false
    toast.show(t('settings.model.saveSuccess') || '保存成功')
  }, 600)
}

const isTesting = ref(false)

async function testConnection() {
  isTesting.value = true
  try {
    const response = await fetch('/api/settings/model/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(modelForm)
    })
    const data = await response.json()
    if (data.success) {
      toast.show(t('settings.model.testSuccess') || '连接成功', 'success')
    } else {
      toast.show(data.message || '连接失败', 'error')
    }
  } catch (e: any) {
    toast.show('连接失败: ' + e.message, 'error')
  } finally {
    isTesting.value = false
  }
}

async function saveClusterConfig() {
  isSaving.value = true
  settingsStore.updateClusterConfig(clusterForm)
  try {
    await fetch('/api/settings/cluster', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(clusterForm)
    })
    toast.show(t('settings.cluster.saveSuccess') || '保存成功')
  } catch (e) {
    toast.show('保存失败', 'error')
  } finally {
    isSaving.value = false
  }
}

function confirmReset() {
  settingsStore.resetSettings()
  window.location.reload()
}

function confirmClear() {
  localStorage.removeItem('soprca-settings')
  window.location.reload()
}

async function loadMonitorStatus() {
  try {
    const res = await fetch('/api/monitor/status')
    const data = await res.json()
    if (data.success) {
      monitorEnabled.value = data.data.enabled
      monitorStatus.value = data.data
      if (data.data.thresholds) {
        monitorForm.cpu_percent = data.data.thresholds.cpu_percent || 90
        monitorForm.memory_percent = data.data.thresholds.memory_percent || 85
        monitorForm.disk_percent = data.data.thresholds.disk_percent || 90
        monitorForm.restart_count = data.data.thresholds.restart_count || 3
      }
    }
  } catch (e) {
    console.error('load monitor status failed:', e)
  }
}

async function toggleMonitor() {
  try {
    const res = await fetch('/api/monitor/toggle', { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      monitorEnabled.value = data.data.enabled
      monitorStatus.value = data.data
    }
  } catch (e) {
    console.error('toggle monitor failed:', e)
  }
}

async function saveMonitorThresholds() {
  try {
    const res = await fetch('/api/monitor/thresholds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(monitorForm)
    })
    const data = await res.json()
    if (data.success) {
      toast.show('阈值保存成功', 'success')
    }
  } catch (e) {
    toast.show('保存失败', 'error')
  }
}

async function loadAntiLoopConfig() {
  try {
    const res = await fetch('/api/settings/anti-loop')
    const data = await res.json()
    if (data.success) {
      antiLoopForm.maxCycleLimit = data.data.max_cycle_limit || 20
      antiLoopForm.maxNoGainTimes = data.data.max_no_gain_times || 3
      antiLoopForm.maxRepeatActionTimes = data.data.max_repeat_action_times || 2
      antiLoopForm.globalTimeout = data.data.global_timeout || 600
    }
  } catch (e) {
    console.error('load anti-loop config failed:', e)
  }
}

async function saveAntiLoopConfig() {
  isAntiLoopSaving.value = true
  try {
    const res = await fetch('/api/settings/anti-loop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(antiLoopForm)
    })
    const data = await res.json()
    if (data.success) {
      toast.show('防死循环配置保存成功', 'success')
    }
  } catch (e) {
    toast.show('保存失败', 'error')
  } finally {
    isAntiLoopSaving.value = false
  }
}

// Load monitor status on mount
loadMonitorStatus()
loadAntiLoopConfig()
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
          <h2 class="text-lg font-semibold text-dark-100">{{ t('settings.theme.title') }}</h2>
          <p class="text-sm text-dark-400">{{ t('settings.theme.description') }}</p>
        </div>
      </div>

      <div class="space-y-4">
        <div>
          <label class="text-sm font-medium text-dark-300 mb-3 block">{{ t('settings.theme.title') }}</label>
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
              <span>{{ t('settings.theme.dark') }}</span>
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
              <span>{{ t('settings.theme.light') }}</span>
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
              <span>{{ t('settings.theme.auto') }}</span>
            </button>
          </div>
        </div>

        <div>
          <label class="text-sm font-medium text-dark-300 mb-3 block">{{ t('settings.language.title') }}</label>
          <select
            :value="locale"
            @change="changeLanguage(($event.target as HTMLSelectElement).value)"
            class="input-field w-48"
          >
            <option value="zh-CN">简体中文</option>
            <option value="en-US">English</option>
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
          <h2 class="text-lg font-semibold text-dark-100">{{ t('settings.model.title') }}</h2>
          <p class="text-sm text-dark-400">{{ t('settings.model.description') }}</p>
        </div>
      </div>

      <!-- 预设模型选择 -->
      <div class="mb-4 p-3 bg-dark-700/50 rounded-lg">
        <div class="flex items-center gap-2 mb-3">
          <Zap :size="16" class="text-primary-400" />
          <span class="text-sm font-medium text-dark-200">{{ t('settings.model.presets') || '预设模型' }}</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="preset in presetModels"
            :key="preset.id"
            @click="applyPreset(preset)"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer border',
              selectedPresetId === preset.id
                ? 'border-primary-500 bg-primary-500/20 text-primary-400'
                : 'border-dark-600 bg-dark-700 text-dark-300 hover:border-dark-500'
            ]"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>

      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">{{ t('settings.model.apiEndpoint') }}</label>
            <input
              v-model="modelForm.apiEndpoint"
              type="text"
              class="input-field"
              placeholder="https://api.example.com/v1"
            />
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">{{ t('settings.model.modelName') }}</label>
            <input
              v-model="modelForm.modelName"
              type="text"
              class="input-field"
              placeholder="gpt-4 / claude-3"
            />
          </div>
        </div>

        <div>
          <label class="text-sm font-medium text-dark-300 mb-2 block">{{ t('settings.model.apiKey') }}</label>
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
            <label class="text-sm font-medium text-dark-300 mb-2 block">{{ t('settings.model.maxTokens') }}</label>
            <input
              v-model.number="modelForm.maxTokens"
              type="number"
              class="input-field"
              placeholder="8192"
            />
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">{{ t('settings.model.temperature') }}</label>
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

        <div class="flex gap-3">
          <button
            @click="testConnection"
            :disabled="isTesting || isSaving"
            class="btn-secondary flex items-center gap-2"
          >
            <component :is="isTesting ? 'Loader2' : 'Wifi'" :size="16" :class="isTesting ? 'animate-spin' : ''" />
            {{ isTesting ? (t('common.loading') || '测试中...') : (t('settings.model.testConnection') || '测试连接') }}
          </button>
          <button
            @click="saveModelConfig"
            :disabled="isSaving"
            class="btn-primary flex items-center gap-2"
          >
            <Save :size="16" />
            {{ t('common.save') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Cluster Settings -->
    <div class="card">
      <div class="flex items-center gap-3 mb-6">
        <div class="p-2 bg-accent-500/20 rounded-lg">
          <Folder :size="20" class="text-accent-400" />
        </div>
        <div>
          <h2 class="text-lg font-semibold text-dark-100">{{ t('settings.cluster.title') }}</h2>
          <p class="text-sm text-dark-400">{{ t('settings.cluster.description') }}</p>
        </div>
      </div>

      <!-- 预设集群选择 -->
      <div class="mb-4 p-3 bg-dark-700/50 rounded-lg">
        <div class="flex items-center gap-2 mb-3">
          <Zap :size="16" class="text-primary-400" />
          <span class="text-sm font-medium text-dark-200">{{ t('settings.cluster.presets') || '预设集群' }}</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="preset in presetClusters"
            :key="preset.id"
            @click="applyClusterPreset(preset)"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer border',
              selectedClusterId === preset.id
                ? 'border-primary-500 bg-primary-500/20 text-primary-400'
                : 'border-dark-600 bg-dark-700 text-dark-300 hover:border-dark-500'
            ]"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>

      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">{{ t('settings.cluster.server') }}</label>
            <input
              v-model="clusterForm.server"
              type="text"
              class="input-field"
              placeholder="https://192.168.100.132:6443"
            />
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">{{ t('settings.cluster.context') }}</label>
            <input
              v-model="clusterForm.context"
              type="text"
              class="input-field"
              placeholder="default"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">{{ t('settings.cluster.env') }}</label>
            <select v-model="clusterForm.env" class="input-field">
              <option value="dev">开发环境 (dev)</option>
              <option value="prod">生产环境 (prod)</option>
            </select>
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 block">{{ t('settings.cluster.mockMode') }}</label>
            <select v-model="clusterForm.mockMode" class="input-field">
              <option :value="false">真实模式 (Mock OFF)</option>
              <option :value="true">模拟模式 (Mock ON)</option>
            </select>
          </div>
        </div>

        <div class="flex justify-end">
          <button
            @click="saveClusterConfig"
            :disabled="isSaving"
            class="btn-primary flex items-center gap-2"
          >
            <Save :size="16" />
            {{ t('common.save') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Monitor Settings -->
    <div class="card">
      <div class="flex items-center gap-3 mb-6">
        <div class="p-2 bg-emerald-500/20 rounded-lg">
          <Activity :size="20" class="text-emerald-400" />
        </div>
        <div>
          <h2 class="text-lg font-semibold text-dark-100">自动巡检设置</h2>
          <p class="text-sm text-dark-400">配置自动诊断触发条件</p>
        </div>
        <div class="ml-auto flex items-center gap-2">
          <span class="text-xs text-dark-500">{{ monitorEnabled ? '运行中' : '已停止' }}</span>
          <button
            @click="toggleMonitor"
            :class="[
              'w-10 h-5 rounded-full transition-colors relative',
              monitorEnabled ? 'bg-emerald-500' : 'bg-dark-600'
            ]"
          >
            <span
              :class="[
                'absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all',
                monitorEnabled ? 'left-5.5' : 'left-0.5'
              ]"
            ></span>
          </button>
        </div>
      </div>

      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 flex items-center gap-2">
              <Cpu :size="14" class="text-cyan-400" />
              CPU 阈值 (%)
            </label>
            <input
              v-model.number="monitorForm.cpu_percent"
              type="number"
              min="0"
              max="100"
              class="input-field"
              placeholder="90"
            />
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 flex items-center gap-2">
              <Server :size="14" class="text-violet-400" />
              内存阈值 (%)
            </label>
            <input
              v-model.number="monitorForm.memory_percent"
              type="number"
              min="0"
              max="100"
              class="input-field"
              placeholder="85"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 flex items-center gap-2">
              <HardDrive :size="14" class="text-amber-400" />
              磁盘阈值 (%)
            </label>
            <input
              v-model.number="monitorForm.disk_percent"
              type="number"
              min="0"
              max="100"
              class="input-field"
              placeholder="90"
            />
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 flex items-center gap-2">
              <Activity :size="14" class="text-rose-400" />
              Pod 重启次数阈值
            </label>
            <input
              v-model.number="monitorForm.restart_count"
              type="number"
              min="0"
              class="input-field"
              placeholder="3"
            />
          </div>
        </div>

        <div class="flex justify-end">
          <button
            @click="saveMonitorThresholds"
            class="btn-primary flex items-center gap-2"
          >
            <Save :size="16" />
            保存阈值
          </button>
        </div>
      </div>
    </div>

    <!-- Anti-Loop Settings -->
    <div class="card">
      <div class="flex items-center gap-3 mb-6">
        <div class="p-2 bg-rose-500/20 rounded-lg">
          <Shield :size="20" class="text-rose-400" />
        </div>
        <div>
          <h2 class="text-lg font-semibold text-dark-100">防死循环设置</h2>
          <p class="text-sm text-dark-400">配置诊断循环的限制参数，防止无限循环</p>
        </div>
      </div>

      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 flex items-center gap-2">
              <Activity :size="14" class="text-rose-400" />
              最大循环次数
            </label>
            <input
              v-model.number="antiLoopForm.maxCycleLimit"
              type="number"
              min="5"
              max="100"
              class="input-field"
              placeholder="20"
            />
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 flex items-center gap-2">
              <Zap :size="14" class="text-amber-400" />
              最大无增益次数
            </label>
            <input
              v-model.number="antiLoopForm.maxNoGainTimes"
              type="number"
              min="1"
              max="10"
              class="input-field"
              placeholder="3"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 flex items-center gap-2">
              <RotateCcw :size="14" class="text-violet-400" />
              最大重复动作次数
            </label>
            <input
              v-model.number="antiLoopForm.maxRepeatActionTimes"
              type="number"
              min="1"
              max="10"
              class="input-field"
              placeholder="2"
            />
          </div>
          <div>
            <label class="text-sm font-medium text-dark-300 mb-2 flex items-center gap-2">
              <Loader2 :size="14" class="text-cyan-400" />
              全局超时时间 (秒)
            </label>
            <input
              v-model.number="antiLoopForm.globalTimeout"
              type="number"
              min="60"
              max="3600"
              class="input-field"
              placeholder="600"
            />
          </div>
        </div>

        <div class="flex justify-end">
          <button
            @click="saveAntiLoopConfig"
            :disabled="isAntiLoopSaving"
            class="btn-primary flex items-center gap-2"
          >
            <Save :size="16" />
            {{ isAntiLoopSaving ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Reset -->
    <div class="card border-red-500/20">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-medium text-dark-200">{{ t('settings.reset.title') }}</h3>
          <p class="text-xs text-dark-400 mt-1">{{ t('settings.reset.description') }}</p>
        </div>
        <button
          @click="showResetConfirm = true"
          class="btn-danger flex items-center gap-2"
        >
          <RotateCcw :size="16" />
          {{ t('common.reset') }}
        </button>
      </div>
    </div>

    <!-- Clear Settings -->
    <div class="card border-dark-600">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-medium text-dark-200">{{ t('settings.clear.title') }}</h3>
          <p class="text-xs text-dark-400 mt-1">{{ t('settings.clear.description') }}</p>
        </div>
        <button
          @click="showClearConfirm = true"
          class="px-4 py-2 bg-dark-700 text-dark-300 rounded-lg hover:bg-dark-600 transition-colors flex items-center gap-2"
        >
          <Trash2 :size="16" />
          {{ t('settings.clear.button') }}
        </button>
      </div>
    </div>

    <!-- Reset Confirmation Dialog -->
    <ConfirmDialog
      :visible="showResetConfirm"
      :title="t('settings.reset.confirmTitle') || '确认重置'"
      :message="t('settings.reset.confirmMessage') || '确定要重置所有设置吗？此操作不可撤销。'"
      @confirm="confirmReset"
      @cancel="showResetConfirm = false"
    />

    <!-- Clear Confirmation Dialog -->
    <ConfirmDialog
      :visible="showClearConfirm"
      :title="t('settings.clear.confirmTitle') || '确认清空'"
      :message="t('settings.clear.confirmMessage') || '确定要清空所有设置吗？此操作不可撤销。'"
      @confirm="confirmClear"
      @cancel="showClearConfirm = false"
    />
  </div>
</template>