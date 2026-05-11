<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { MessageCircle, Send, Bot, BookOpen, History, Loader2, ExternalLink, Settings2, X } from 'lucide-vue-next'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  citations?: Array<{ type: string; name: string; id: string }>
}

const router = useRouter()
const settingsStore = useSettingsStore()
const showModelInfo = ref(false)
const messages = ref<Message[]>([])
const inputText = ref('')
const isLoading = ref(false)

async function sendMessage() {
  if (!inputText.value.trim() || isLoading.value) return

  const userMessage: Message = {
    id: Date.now(),
    role: 'user',
    content: inputText.value,
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false })
  }
  messages.value.push(userMessage)
  inputText.value = ''
  isLoading.value = true

  try {
    const response = await fetch('/api/knowledge/qa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: userMessage.content })
    })

    const data = await response.json()

    const assistantMessage: Message = {
      id: Date.now() + 1,
      role: 'assistant',
      content: data.success ? data.answer : data.message || '抱歉，发生了错误。',
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      citations: data.citations || []
    }
    messages.value.push(assistantMessage)
  } catch (e: any) {
    const errorMessage: Message = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '抱歉，无法连接到服务器。请确保后端服务已启动。',
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      citations: []
    }
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
  }
}

function getCitationIcon(type: string) {
  return type === 'sop' ? BookOpen : History
}

function goToCitation(citation: { type: string; name: string; id: string }) {
  if (citation.type === 'sop') {
    router.push({
      path: '/sop',
      query: { tab: 'sop', openId: citation.id }
    })
  } else {
    router.push({
      path: '/sop',
      query: { tab: 'history', openId: citation.id }
    })
  }
}

function clearChat() {
  messages.value = []
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="card mb-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-primary-500/20 rounded-lg">
            <Bot :size="20" class="text-primary-400" />
          </div>
          <div>
            <h2 class="text-lg font-semibold text-dark-100">知识库问答</h2>
            <p class="text-sm text-dark-400">基于SOP知识库和历史案例的智能问答</p>
          </div>
        </div>
        <button
          v-if="messages.length > 0"
          @click="clearChat"
          class="text-sm text-dark-400 hover:text-dark-200 transition-colors"
        >
          清空对话
        </button>
        <button
          @click="showModelInfo = !showModelInfo"
          class="text-sm text-dark-400 hover:text-dark-200 transition-colors flex items-center gap-1"
        >
          <Settings2 :size="14" />
          模型信息
        </button>
      </div>
    </div>

    <!-- Model Info Panel -->
    <div v-if="showModelInfo" class="card mb-4 bg-dark-800/50">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-medium text-dark-200">当前模型配置</h3>
        <button @click="showModelInfo = false" class="text-dark-400 hover:text-dark-200">
          <X :size="16" />
        </button>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <span class="text-dark-400">模型</span>
          <p class="text-dark-100 font-medium">{{ settingsStore.settings.model.modelName }}</p>
        </div>
        <div>
          <span class="text-dark-400">API</span>
          <p class="text-dark-100 font-medium truncate">{{ settingsStore.settings.model.apiEndpoint }}</p>
        </div>
        <div>
          <span class="text-dark-400">Temperature</span>
          <p class="text-dark-100 font-medium">{{ settingsStore.settings.model.temperature }}</p>
        </div>
        <div>
          <span class="text-dark-400">Max Tokens</span>
          <p class="text-dark-100 font-medium">{{ settingsStore.settings.model.maxTokens }}</p>
        </div>
      </div>
    </div>

    <!-- Chat Area -->
    <div class="card flex-1 flex flex-col min-h-0">
      <!-- Empty State -->
      <div
        v-if="messages.length === 0"
        class="flex-1 flex flex-col items-center justify-center text-center py-12"
      >
        <div class="p-4 bg-primary-500/10 rounded-full mb-4">
          <Bot :size="48" class="text-primary-400" />
        </div>
        <h3 class="text-lg font-medium text-dark-200 mb-2">RCA 智能问答助手</h3>
        <p class="text-dark-400 text-sm max-w-md mb-6">
          基于SOP知识库和历史诊断案例的智能问答系统。您可以询问关于故障诊断、SOP流程、以及运维最佳实践等问题。
        </p>
        <div class="flex flex-wrap gap-2 justify-center mb-6">
          <button
            @click="inputText = 'CPU过高怎么诊断？'; sendMessage()"
            class="px-3 py-1.5 bg-dark-700 text-dark-300 rounded-lg text-xs hover:bg-dark-600 transition-colors cursor-pointer"
          >
            CPU过高怎么诊断
          </button>
          <button
            @click="inputText = '内存泄漏怎么处理？'; sendMessage()"
            class="px-3 py-1.5 bg-dark-700 text-dark-300 rounded-lg text-xs hover:bg-dark-600 transition-colors cursor-pointer"
          >
            内存泄漏怎么处理
          </button>
          <button
            @click="inputText = 'Pod重启的原因有哪些？'; sendMessage()"
            class="px-3 py-1.5 bg-dark-700 text-dark-300 rounded-lg text-xs hover:bg-dark-600 transition-colors cursor-pointer"
          >
            Pod重启的原因
          </button>
          <button
            @click="inputText = '网络延迟排查步骤是什么？'; sendMessage()"
            class="px-3 py-1.5 bg-dark-700 text-dark-300 rounded-lg text-xs hover:bg-dark-600 transition-colors cursor-pointer"
          >
            网络延迟排查步骤
          </button>
        </div>
        <div class="flex gap-4 text-xs text-dark-500">
          <span class="flex items-center gap-1"><BookOpen :size="12" /> SOP知识库</span>
          <span class="flex items-center gap-1"><History :size="12" /> 历史案例库</span>
        </div>
      </div>

      <!-- Messages -->
      <div v-else class="flex-1 overflow-auto space-y-4 mb-4">
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['flex gap-3', msg.role === 'user' ? 'flex-row-reverse' : '']"
        >
          <div
            :class="[
              'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
              msg.role === 'user' ? 'bg-primary-500/20' : 'bg-dark-700'
            ]"
          >
            <Bot v-if="msg.role === 'assistant'" :size="16" class="text-dark-300" />
            <MessageCircle v-else :size="16" class="text-primary-400" />
          </div>

          <div class="flex flex-col gap-2 max-w-[75%]">
            <div
              :class="[
                'rounded-xl p-3',
                msg.role === 'user'
                  ? 'bg-primary-500/20 text-dark-100'
                  : 'bg-dark-700 text-dark-200'
              ]"
            >
              <p class="text-sm whitespace-pre-wrap">{{ msg.content }}</p>
              <p class="text-xs text-dark-500 mt-1">{{ msg.timestamp }}</p>
            </div>

            <!-- Citations -->
            <div
              v-if="msg.citations && msg.citations.length > 0"
              class="flex flex-col gap-2"
            >
              <p class="text-xs text-dark-500">引用来源：</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="citation in msg.citations"
                  :key="citation.id"
                  @click="goToCitation(citation)"
                  class="flex items-center gap-1.5 px-2.5 py-1.5 bg-dark-700/50 hover:bg-dark-700 border border-dark-600 hover:border-primary-500/50 rounded-lg text-xs text-dark-300 hover:text-primary-400 transition-all cursor-pointer group"
                >
                  <component :is="getCitationIcon(citation.type)" :size="12" class="text-primary-400" />
                  <span class="max-w-[150px] truncate">{{ citation.name }}</span>
                  <ExternalLink :size="10" class="opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="isLoading" class="flex gap-3">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 bg-dark-700">
            <Bot :size="16" class="text-dark-300" />
          </div>
          <div class="bg-dark-700 rounded-xl p-3">
            <div class="flex items-center gap-2 text-dark-400">
              <Loader2 :size="16" class="animate-spin" />
              <span class="text-sm">正在思考...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="flex gap-3 pt-4 border-t border-dark-700">
        <input
          v-model="inputText"
          type="text"
          class="input-field flex-1"
          placeholder="输入您的问题..."
          :disabled="isLoading"
          @keyup.enter="sendMessage"
        />
        <button
          @click="sendMessage"
          :disabled="!inputText.trim() || isLoading"
          class="btn-primary px-4"
        >
          <Send :size="18" />
        </button>
      </div>
    </div>
  </div>
</template>