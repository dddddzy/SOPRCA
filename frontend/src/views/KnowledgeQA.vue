<script setup lang="ts">
import { ref } from 'vue'
import { MessageCircle, Construction, Send, Bot } from 'lucide-vue-next'

const messages = ref<Array<{
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}>>([])

const inputText = ref('')
const isLoading = ref(false)

async function sendMessage() {
  if (!inputText.value.trim()) return

  const userMessage = {
    id: Date.now(),
    role: 'user' as const,
    content: inputText.value,
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false })
  }
  messages.value.push(userMessage)
  inputText.value = ''
  isLoading.value = true

  // Simulate response
  setTimeout(() => {
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: '知识问答功能正在开发中...该模块将集成知识库检索和RCA历史案例分析。',
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false })
    })
    isLoading.value = false
  }, 1000)
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="card mb-4">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-amber-500/20 rounded-lg">
          <Construction :size="20" class="text-amber-400" />
        </div>
        <div>
          <h2 class="text-lg font-semibold text-dark-100">知识库问答</h2>
          <p class="text-sm text-dark-400">基于历史诊断案例和SOP知识的智能问答</p>
        </div>
        <div class="ml-auto">
          <span class="badge-warning">功能开发中</span>
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
          即将上线：基于历史诊断案例和SOP知识库的智能问答系统。您可以询问关于故障诊断、SOP流程、以及运维最佳实践等问题。
        </p>
        <div class="flex flex-wrap gap-2 justify-center">
          <span class="badge-default">历史案例分析</span>
          <span class="badge-default">SOP流程咨询</span>
          <span class="badge-default">故障根因问答</span>
          <span class="badge-default">运维知识库</span>
        </div>
      </div>

      <!-- Messages -->
      <div v-else class="flex-1 overflow-auto space-y-4 mb-4">
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="[
            'flex gap-3',
            msg.role === 'user' ? 'flex-row-reverse' : ''
          ]"
        >
          <div
            :class="[
              'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
              msg.role === 'user' ? 'bg-primary-500/20' : 'bg-dark-700'
            ]"
          >
            <Bot
              v-if="msg.role === 'assistant'"
              :size="16"
              class="text-dark-300"
            />
            <MessageCircle
              v-else
              :size="16"
              class="text-primary-400"
            />
          </div>
          <div
            :class="[
              'max-w-[70%] rounded-xl p-3',
              msg.role === 'user'
                ? 'bg-primary-500/20 text-dark-100'
                : 'bg-dark-700 text-dark-200'
            ]"
          >
            <p class="text-sm">{{ msg.content }}</p>
            <p class="text-xs text-dark-500 mt-1">{{ msg.timestamp }}</p>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="flex gap-3 pt-4 border-t border-dark-700">
        <input
          v-model="inputText"
          type="text"
          class="input-field"
          placeholder="输入您的问题..."
          :disabled="isLoading"
          @keyup.enter="sendMessage"
        />
        <button
          @click="sendMessage"
          :disabled="!inputText.trim() || isLoading"
          class="btn-primary"
        >
          <Send :size="18" />
        </button>
      </div>
    </div>
  </div>
</template>
