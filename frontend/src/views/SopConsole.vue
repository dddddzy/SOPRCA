<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSopStore } from '@/stores/sop'
import { useToast } from '@/composables/useToast'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import {
  Search,
  Plus,
  Edit2,
  Trash2,
  Eye,
  BookOpen,
  X,
  Save,
  History,
  ChevronRight,
  AlertCircle,
  Clock
} from 'lucide-vue-next'
import type { SOP } from '@/types'

const router = useRouter()
const route = useRoute()
const activeTab = ref<'sop' | 'history'>('sop')
const sopStore = useSopStore()
const toast = useToast()

// History cases
const historyCases = ref<any[]>([])
const historyLoading = ref(false)
const historySearchQuery = ref('')
const historyTypeFilter = ref('all')

// SOP modals
const showSopDetailModal = ref(false)
const showSopEditModal = ref(false)
const showSopDeleteConfirm = ref(false)
const selectedSopId = ref<string | null>(null)
const editingSop = ref<Partial<SOP>>({})

// History modals
const showHistoryDetailModal = ref(false)
const showHistoryEditModal = ref(false)
const showHistoryDeleteConfirm = ref(false)
const selectedHistoryId = ref<string | null>(null)
const editingHistory = ref<any>({})

const isSaving = ref(false)

const selectedSop = computed(() => {
  if (!selectedSopId.value) return null
  return sopStore.getSopById(selectedSopId.value)
})

const selectedHistory = computed(() => {
  if (!selectedHistoryId.value) return null
  return historyCases.value.find(c => c.id === selectedHistoryId.value)
})

const filteredHistoryCases = computed(() => {
  return historyCases.value.filter(c => {
    const matchSearch = historySearchQuery.value === '' ||
      c.faultInfo.toLowerCase().includes(historySearchQuery.value.toLowerCase()) ||
      c.faultType.toLowerCase().includes(historySearchQuery.value.toLowerCase()) ||
      (c.rootCause && c.rootCause.toLowerCase().includes(historySearchQuery.value.toLowerCase()))

    const matchType = historyTypeFilter.value === 'all' || c.faultType === historyTypeFilter.value

    return matchSearch && matchType
  })
})

const historyFaultTypes = computed(() => {
  return [...new Set(historyCases.value.map(c => c.faultType))]
})

onMounted(() => {
  sopStore.fetchSops()
  fetchHistoryCases()
  handleRouteQuery()
})

function handleRouteQuery() {
  const tab = route.query.tab as 'sop' | 'history' | undefined
  const openId = route.query.openId as string | undefined

  if (tab) {
    activeTab.value = tab
  }

  if (openId) {
    if (tab === 'history') {
      selectedHistoryId.value = openId
      showHistoryDetailModal.value = true
    } else {
      selectedSopId.value = openId
      showSopDetailModal.value = true
    }
  }
}

watch(() => route.query, handleRouteQuery)

async function fetchHistoryCases() {
  historyLoading.value = true
  try {
    const response = await fetch('/api/history')
    const data = await response.json()
    if (data.success) {
      historyCases.value = data.data
    }
  } catch (e) {
    console.error('Failed to fetch history cases:', e)
  } finally {
    historyLoading.value = false
  }
}

// ============== SOP Functions ==============

function openSopDetail(sopId: string) {
  selectedSopId.value = sopId
  showSopDetailModal.value = true
}

function closeSopDetail() {
  showSopDetailModal.value = false
  selectedSopId.value = null
}

function openSopEdit(sop: SOP, event: Event) {
  event.stopPropagation()
  selectedSopId.value = sop.id
  editingSop.value = JSON.parse(JSON.stringify(sop))
  showSopEditModal.value = true
  showSopDetailModal.value = false
}

function closeSopEdit() {
  showSopEditModal.value = false
  selectedSopId.value = null
  editingSop.value = {}
}

async function saveSopEdit() {
  if (!editingSop.value.id) return

  isSaving.value = true
  const success = await sopStore.updateSop(editingSop.value.id, editingSop.value)
  isSaving.value = false

  if (success) {
    toast.show('SOP已保存', 'success')
    closeSopEdit()
    await sopStore.fetchSops()
  } else {
    toast.show('保存失败', 'error')
  }
}

function confirmDeleteSop(sop: SOP, event: Event) {
  event.stopPropagation()
  selectedSopId.value = sop.id
  showSopDeleteConfirm.value = true
  showSopDetailModal.value = false
}

async function executeDeleteSop() {
  if (!selectedSopId.value) return

  const success = await sopStore.deleteSop(selectedSopId.value)
  showSopDeleteConfirm.value = false

  if (success) {
    toast.show('SOP已删除', 'success')
    selectedSopId.value = null
  } else {
    toast.show('删除失败', 'error')
  }
}

// ============== History Functions ==============

function openHistoryDetail(historyId: string) {
  selectedHistoryId.value = historyId
  showHistoryDetailModal.value = true
}

function closeHistoryDetail() {
  showHistoryDetailModal.value = false
  selectedHistoryId.value = null
}

function openHistoryEdit(history: any, event: Event) {
  event.stopPropagation()
  selectedHistoryId.value = history.id
  editingHistory.value = JSON.parse(JSON.stringify(history))
  showHistoryEditModal.value = true
  showHistoryDetailModal.value = false
}

function closeHistoryEdit() {
  showHistoryEditModal.value = false
  selectedHistoryId.value = null
  editingHistory.value = {}
}

async function saveHistoryEdit() {
  if (!editingHistory.value.id) return

  try {
    const response = await fetch(`/api/history/${editingHistory.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editingHistory.value)
    })
    const data = await response.json()
    if (data.success) {
      toast.show('案例已保存', 'success')
      closeHistoryEdit()
      await fetchHistoryCases()
    } else {
      toast.show('保存失败', 'error')
    }
  } catch (e) {
    toast.show('保存失败', 'error')
  }
}

function openNewHistory(event: Event) {
  event.stopPropagation()
  editingHistory.value = {
    id: '',
    faultInfo: '',
    faultType: '',
    rootCause: '',
    observation: ''
  }
  showHistoryEditModal.value = true
}

function openNewSop(event: Event) {
  event.stopPropagation()
  editingSop.value = {
    name: '',
    faultType: '',
    description: '',
    steps: [],
    status: 'active'
  }
  showSopEditModal.value = true
}

async function saveNewHistory() {
  if (!editingHistory.value.faultInfo || !editingHistory.value.faultType) {
    toast.show('请填写必填项', 'error')
    return
  }

  try {
    const response = await fetch('/api/history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editingHistory.value)
    })
    const data = await response.json()
    if (data.success) {
      toast.show('案例已添加', 'success')
      closeHistoryEdit()
      await fetchHistoryCases()
    } else {
      toast.show('添加失败', 'error')
    }
  } catch (e) {
    toast.show('添加失败', 'error')
  }
}

async function saveNewSop() {
  if (!editingSop.value.name || !editingSop.value.faultType) {
    toast.show('请填写必填项', 'error')
    return
  }

  try {
    const response = await fetch('/api/sops', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editingSop.value)
    })
    const data = await response.json()
    if (data.success) {
      toast.show('SOP已添加', 'success')
      closeSopEdit()
      await sopStore.fetchSops()
    } else {
      toast.show('添加失败', 'error')
    }
  } catch (e) {
    toast.show('添加失败', 'error')
  }
}

function confirmDeleteHistory(history: any, event: Event) {
  event.stopPropagation()
  selectedHistoryId.value = history.id
  showHistoryDeleteConfirm.value = true
  showHistoryDetailModal.value = false
}

async function executeDeleteHistory() {
  if (!selectedHistoryId.value) return

  try {
    const response = await fetch(`/api/history/${selectedHistoryId.value}`, { method: 'DELETE' })
    const data = await response.json()
    if (data.success) {
      toast.show('案例已删除', 'success')
      selectedHistoryId.value = null
      await fetchHistoryCases()
    } else {
      toast.show(data.message || '删除失败', 'error')
    }
  } catch (e) {
    toast.show('删除失败', 'error')
  }
}

function getFaultTypeColor(type: string) {
  const colors: Record<string, string> = {
    'CPU过高': 'text-amber-400',
    '内存过高': 'text-red-400',
    '网络故障': 'text-primary-400',
    'Pod异常': 'text-orange-400',
    '磁盘IO过高': 'text-emerald-400',
    '服务500错误': 'text-purple-400',
    '网关502错误': 'text-blue-400',
    '服务响应延迟': 'text-cyan-400',
    'Pod频繁重启': 'text-pink-400'
  }
  return colors[type] || 'text-dark-300'
}

function getStatusBadgeClass(status: string) {
  switch (status) {
    case 'active': return 'badge-success'
    case 'draft': return 'badge-warning'
    case 'archived': return 'badge-default'
    default: return 'badge-default'
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'active': return '启用'
    case 'draft': return '草稿'
    case 'archived': return '归档'
    default: return status
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-dark-100">{{ $t('sop.title') }}</h2>
        <p class="text-sm text-dark-400">{{ $t('sop.description') }}</p>
      </div>
      <button
        v-if="activeTab === 'sop'"
        @click="openNewSop"
        class="btn-primary flex items-center gap-2"
      >
        <Plus :size="18" />
        新建 SOP
      </button>
      <button
        v-else
        @click="openNewHistory"
        class="btn-primary flex items-center gap-2"
      >
        <Plus :size="18" />
        新建案例
      </button>
    </div>

    <!-- Tabs -->
    <div class="card">
      <div class="flex border-b border-dark-700">
        <button
          @click="activeTab = 'sop'"
          :class="[
            'flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'sop'
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-dark-400 hover:text-dark-200'
          ]"
        >
          <BookOpen :size="16" />
          SOP 知识库
          <span class="px-1.5 py-0.5 text-xs rounded-full bg-dark-700">{{ sopStore.sops.length }}</span>
        </button>
        <button
          @click="activeTab = 'history'"
          :class="[
            'flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'history'
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-dark-400 hover:text-dark-200'
          ]"
        >
          <History :size="16" />
          历史案例
          <span class="px-1.5 py-0.5 text-xs rounded-full bg-dark-700">{{ historyCases.length }}</span>
        </button>
      </div>

      <!-- SOP Content -->
      <div v-if="activeTab === 'sop'" class="p-4 space-y-4">
        <!-- Filters -->
        <div class="flex flex-wrap gap-4">
          <div class="flex-1 min-w-[200px] relative">
            <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
            <input
              type="text"
              class="input-field pl-10"
              :placeholder="$t('sop.search')"
              :value="sopStore.searchQuery"
              @input="sopStore.setSearchQuery(($event.target as HTMLInputElement).value)"
            />
          </div>

          <select
            :value="sopStore.typeFilter"
            @change="sopStore.setTypeFilter(($event.target as HTMLSelectElement).value)"
            class="input-field w-40"
          >
            <option value="all">{{ $t('sop.typeFilter') }}</option>
            <option v-for="type in sopStore.faultTypes" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>

        <!-- SOP Table -->
        <div v-if="sopStore.loading" class="flex items-center justify-center py-12">
          <div class="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full"></div>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-dark-700">
                <th class="text-left text-xs font-medium text-dark-400 px-4 py-3">{{ $t('sop.table.name') }}</th>
                <th class="text-left text-xs font-medium text-dark-400 px-4 py-3">{{ $t('sop.table.faultType') }}</th>
                <th class="text-left text-xs font-medium text-dark-400 px-4 py-3">{{ $t('sop.table.status') }}</th>
                <th class="text-left text-xs font-medium text-dark-400 px-4 py-3">{{ $t('sop.table.matchCount') }}</th>
                <th class="text-right text-xs font-medium text-dark-400 px-4 py-3">{{ $t('sop.table.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="sop in sopStore.filteredSops"
                :key="sop.id"
                class="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors cursor-pointer"
                @click="openSopDetail(sop.id)"
              >
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <BookOpen :size="16" class="text-dark-400" />
                    <div>
                      <p class="text-sm font-medium text-dark-200">{{ sop.name }}</p>
                      <p class="text-xs text-dark-500 truncate max-w-[200px]">{{ sop.description }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span :class="['text-sm font-medium', getFaultTypeColor(sop.faultType)]">
                    {{ sop.faultType }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <span :class="getStatusBadgeClass(sop.status)">
                    {{ getStatusLabel(sop.status) }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <span class="text-sm text-dark-300">{{ sop.matchCount }}</span>
                </td>
                <td class="px-4 py-3">
                  <div class="flex items-center justify-end gap-1" @click.stop>
                    <button
                      @click="openSopDetail(sop.id)"
                      class="p-1.5 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-600 transition-all cursor-pointer"
                      title="查看"
                    >
                      <Eye :size="16" />
                    </button>
                    <button
                      @click="openSopEdit(sop, $event)"
                      class="p-1.5 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-600 transition-all cursor-pointer"
                      title="编辑"
                    >
                      <Edit2 :size="16" />
                    </button>
                    <button
                      @click="confirmDeleteSop(sop, $event)"
                      class="p-1.5 rounded-lg text-dark-400 hover:text-red-400 hover:bg-red-500/10 transition-all cursor-pointer"
                      title="删除"
                    >
                      <Trash2 :size="16" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div
          v-if="!sopStore.loading && sopStore.filteredSops.length === 0"
          class="flex flex-col items-center justify-center py-12"
        >
          <BookOpen :size="48" class="text-dark-600 mb-4" />
          <p class="text-dark-400">{{ $t('common.noData') }}</p>
        </div>
      </div>

      <!-- History Content -->
      <div v-if="activeTab === 'history'" class="p-4 space-y-4">
        <!-- Filters -->
        <div class="flex flex-wrap gap-4">
          <div class="flex-1 min-w-[200px] relative">
            <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
            <input
              type="text"
              class="input-field pl-10"
              placeholder="搜索历史案例..."
              v-model="historySearchQuery"
            />
          </div>

          <select
            v-model="historyTypeFilter"
            class="input-field w-40"
          >
            <option value="all">全部类型</option>
            <option v-for="type in historyFaultTypes" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>

        <!-- History Table -->
        <div v-if="historyLoading" class="flex items-center justify-center py-12">
          <div class="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full"></div>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="history in filteredHistoryCases"
            :key="history.id"
            class="p-4 bg-dark-700/30 rounded-lg hover:bg-dark-700/50 transition-colors cursor-pointer"
            @click="openHistoryDetail(history.id)"
          >
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-2">
                  <span :class="['text-sm font-medium', getFaultTypeColor(history.faultType)]">
                    {{ history.faultType }}
                  </span>
                  <span class="flex items-center gap-1 text-xs text-dark-500">
                    <Clock :size="12" />
                    {{ new Date(history.createdAt).toLocaleDateString('zh-CN') }}
                  </span>
                </div>
                <p class="text-sm text-dark-200 mb-1">{{ history.faultInfo }}</p>
                <p class="text-xs text-dark-400 line-clamp-2">{{ history.observation }}</p>
                <div v-if="history.rootCause" class="mt-2 flex items-start gap-2">
                  <AlertCircle :size="14" class="text-green-400 mt-0.5 flex-shrink-0" />
                  <p class="text-xs text-green-400">根因: {{ history.rootCause }}</p>
                </div>
                <div v-if="history.matchedSopName" class="mt-1 flex items-center gap-2">
                  <ChevronRight :size="14" class="text-dark-500" />
                  <span class="text-xs text-dark-400">匹配SOP: {{ history.matchedSopName }}</span>
                </div>
              </div>
              <div class="flex items-center gap-1 flex-shrink-0" @click.stop>
                <button
                  @click="openHistoryDetail(history.id)"
                  class="p-1.5 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-600 transition-all cursor-pointer"
                  title="查看"
                >
                  <Eye :size="16" />
                </button>
                <button
                  @click="openHistoryEdit(history, $event)"
                  class="p-1.5 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-600 transition-all cursor-pointer"
                  title="编辑"
                >
                  <Edit2 :size="16" />
                </button>
                <button
                  @click="confirmDeleteHistory(history, $event)"
                  class="p-1.5 rounded-lg text-dark-400 hover:text-red-400 hover:bg-red-500/10 transition-all cursor-pointer"
                  title="删除"
                >
                  <Trash2 :size="16" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="!historyLoading && filteredHistoryCases.length === 0"
          class="flex flex-col items-center justify-center py-12"
        >
          <History :size="48" class="text-dark-600 mb-4" />
          <p class="text-dark-400">{{ $t('common.noData') }}</p>
        </div>
      </div>
    </div>

    <!-- SOP Detail Modal -->
    <Teleport to="body">
      <div
        v-if="showSopDetailModal && selectedSop"
        class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
        @click.self="closeSopDetail"
      >
        <div class="bg-dark-800 border border-dark-700 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-auto">
          <div class="flex items-center justify-between p-4 border-b border-dark-700">
            <div class="flex items-center gap-3">
              <BookOpen :size="20" class="text-primary-400" />
              <h3 class="text-lg font-semibold text-dark-100">{{ selectedSop.name }}</h3>
              <span :class="getStatusBadgeClass(selectedSop.status)">
                {{ getStatusLabel(selectedSop.status) }}
              </span>
            </div>
            <button @click="closeSopDetail" class="p-1 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700 cursor-pointer">
              <X :size="18" />
            </button>
          </div>

          <div class="p-4 space-y-4">
            <div>
              <p class="text-sm text-dark-400 mb-1">描述</p>
              <p class="text-sm text-dark-200">{{ selectedSop.description || '无' }}</p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-sm text-dark-400 mb-1">故障类型</p>
                <p :class="['font-medium', getFaultTypeColor(selectedSop.faultType)]">
                  {{ selectedSop.faultType }}
                </p>
              </div>
              <div>
                <p class="text-sm text-dark-400 mb-1">匹配次数</p>
                <p class="text-dark-200">{{ selectedSop.matchCount }} 次</p>
              </div>
            </div>

            <div>
              <p class="text-sm font-medium text-dark-300 mb-3">诊断步骤</p>
              <div class="space-y-2">
                <div
                  v-for="step in selectedSop.steps"
                  :key="step.order"
                  class="flex items-start gap-3 p-3 bg-dark-700/50 rounded-lg"
                >
                  <span class="flex items-center justify-center w-6 h-6 rounded-full bg-primary-500/20 text-primary-400 text-xs font-medium">
                    {{ step.order }}
                  </span>
                  <div class="flex-1">
                    <p class="text-sm font-medium text-dark-200">{{ step.tool }}</p>
                    <p class="text-xs text-dark-400">{{ step.description }}</p>
                  </div>
                </div>
                <div v-if="!selectedSop.steps || selectedSop.steps.length === 0" class="text-sm text-dark-400">
                  暂无步骤
                </div>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 p-4 border-t border-dark-700">
            <button @click="closeSopDetail" class="btn-secondary">关闭</button>
            <button @click="openSopEdit(selectedSop, $event)" class="btn-primary flex items-center gap-2">
              <Edit2 :size="16" />
              编辑
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- History Detail Modal -->
    <Teleport to="body">
      <div
        v-if="showHistoryDetailModal && selectedHistory"
        class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
        @click.self="closeHistoryDetail"
      >
        <div class="bg-dark-800 border border-dark-700 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-auto">
          <div class="flex items-center justify-between p-4 border-b border-dark-700">
            <div class="flex items-center gap-3">
              <History :size="20" class="text-primary-400" />
              <h3 class="text-lg font-semibold text-dark-100">历史案例详情</h3>
              <span :class="['text-sm', getFaultTypeColor(selectedHistory.faultType)]">
                {{ selectedHistory.faultType }}
              </span>
            </div>
            <button @click="closeHistoryDetail" class="p-1 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700 cursor-pointer">
              <X :size="18" />
            </button>
          </div>

          <div class="p-4 space-y-4">
            <div>
              <p class="text-sm text-dark-400 mb-1">故障描述</p>
              <p class="text-sm text-dark-200">{{ selectedHistory.faultInfo }}</p>
            </div>

            <div>
              <p class="text-sm text-dark-400 mb-1">故障类型</p>
              <p :class="['text-sm font-medium', getFaultTypeColor(selectedHistory.faultType)]">
                {{ selectedHistory.faultType }}
              </p>
            </div>

            <div>
              <p class="text-sm text-dark-400 mb-1">观测现象</p>
              <p class="text-sm text-dark-200 whitespace-pre-wrap">{{ selectedHistory.observation || '无' }}</p>
            </div>

            <div v-if="selectedHistory.rootCause">
              <p class="text-sm text-dark-400 mb-1">根因分析</p>
              <div class="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                <p class="text-sm text-green-400">{{ selectedHistory.rootCause }}</p>
              </div>
            </div>

            <div v-if="selectedHistory.matchedSopName">
              <p class="text-sm text-dark-400 mb-1">匹配SOP</p>
              <p class="text-sm text-dark-200">{{ selectedHistory.matchedSopName }}</p>
            </div>

            <div>
              <p class="text-sm text-dark-400 mb-1">创建时间</p>
              <p class="text-sm text-dark-300">{{ new Date(selectedHistory.createdAt).toLocaleString('zh-CN') }}</p>
            </div>
          </div>

          <div class="flex justify-end gap-3 p-4 border-t border-dark-700">
            <button @click="closeHistoryDetail" class="btn-secondary">关闭</button>
            <button @click="openHistoryEdit(selectedHistory, $event)" class="btn-primary flex items-center gap-2">
              <Edit2 :size="16" />
              编辑
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- SOP Edit Modal -->
    <Teleport to="body">
      <div
        v-if="showSopEditModal"
        class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
        @click.self="closeSopEdit"
      >
        <div class="bg-dark-800 border border-dark-700 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-auto">
          <div class="flex items-center justify-between p-4 border-b border-dark-700">
            <h3 class="text-lg font-semibold text-dark-100">
              {{ editingSop.id ? '编辑 SOP' : '新建 SOP' }}
            </h3>
            <button @click="closeSopEdit" class="p-1 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700 cursor-pointer">
              <X :size="18" />
            </button>
          </div>

          <div class="p-4 space-y-4">
            <div>
              <label class="text-sm font-medium text-dark-300 mb-2 block">名称 <span class="text-red-400">*</span></label>
              <input v-model="editingSop.name" type="text" class="input-field w-full" placeholder="输入 SOP 名称" />
            </div>

            <div>
              <label class="text-sm font-medium text-dark-300 mb-2 block">故障类型 <span class="text-red-400">*</span></label>
              <input v-model="editingSop.faultType" type="text" class="input-field w-full" placeholder="如：CPU过高、内存过高" />
            </div>

            <div>
              <label class="text-sm font-medium text-dark-300 mb-2 block">描述</label>
              <textarea v-model="editingSop.description" class="input-field w-full h-20 resize-none" placeholder="输入描述"></textarea>
            </div>

            <div>
              <label class="text-sm font-medium text-dark-300 mb-2 block">状态</label>
              <select v-model="editingSop.status" class="input-field w-full">
                <option value="active">启用</option>
                <option value="draft">草稿</option>
                <option value="archived">归档</option>
              </select>
            </div>

            <div>
              <label class="text-sm font-medium text-dark-300 mb-2 block">诊断步骤</label>
              <div class="space-y-3">
                <div
                  v-for="(step, index) in editingSop.steps"
                  :key="index"
                  class="flex gap-3 items-start p-3 bg-dark-700/50 rounded-lg"
                >
                  <span class="flex items-center justify-center w-6 h-6 rounded-full bg-primary-500/20 text-primary-400 text-xs font-medium">
                    {{ index + 1 }}
                  </span>
                  <div class="flex-1 grid grid-cols-2 gap-3">
                    <input v-model="step.tool" type="text" class="input-field" placeholder="工具名称" />
                    <input v-model="step.description" type="text" class="input-field" placeholder="步骤描述" />
                  </div>
                  <button @click="editingSop.steps?.splice(index, 1)" class="p-1.5 text-dark-400 hover:text-red-400 cursor-pointer">
                    <X :size="16" />
                  </button>
                </div>
                <button
                  @click="editingSop.steps?.push({ order: (editingSop.steps?.length || 0) + 1, tool: '', description: '', expectedResult: '' })"
                  class="w-full py-2 border border-dashed border-dark-600 rounded-lg text-dark-400 hover:text-dark-200 hover:border-dark-500 transition-colors cursor-pointer"
                >
                  + 添加步骤
                </button>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 p-4 border-t border-dark-700">
            <button @click="closeSopEdit" class="btn-secondary">取消</button>
            <button @click="editingSop.id ? saveSopEdit() : saveNewSop()" :disabled="isSaving" class="btn-primary flex items-center gap-2">
              <Save :size="16" />
              {{ isSaving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- History Edit Modal -->
    <Teleport to="body">
      <div
        v-if="showHistoryEditModal"
        class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
        @click.self="closeHistoryEdit"
      >
        <div class="bg-dark-800 border border-dark-700 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-auto">
          <div class="flex items-center justify-between p-4 border-b border-dark-700">
            <h3 class="text-lg font-semibold text-dark-100">
              {{ editingHistory.id ? '编辑案例' : '新建案例' }}
            </h3>
            <button @click="closeHistoryEdit" class="p-1 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700 cursor-pointer">
              <X :size="18" />
            </button>
          </div>

          <div class="p-4 space-y-4">
            <div>
              <label class="text-sm font-medium text-dark-300 mb-2 block">故障描述 <span class="text-red-400">*</span></label>
              <textarea v-model="editingHistory.faultInfo" class="input-field w-full h-20 resize-none" placeholder="输入故障描述"></textarea>
            </div>

            <div>
              <label class="text-sm font-medium text-dark-300 mb-2 block">故障类型 <span class="text-red-400">*</span></label>
              <input v-model="editingHistory.faultType" type="text" class="input-field w-full" placeholder="如：CPU过高、内存过高" />
            </div>

            <div>
              <label class="text-sm font-medium text-dark-300 mb-2 block">观测现象</label>
              <textarea v-model="editingHistory.observation" class="input-field w-full h-24 resize-none" placeholder="输入观测到的现象"></textarea>
            </div>

            <div>
              <label class="text-sm font-medium text-dark-300 mb-2 block">根因分析</label>
              <textarea v-model="editingHistory.rootCause" class="input-field w-full h-20 resize-none" placeholder="输入根因分析"></textarea>
            </div>

            <div>
              <label class="text-sm font-medium text-dark-300 mb-2 block">匹配SOP</label>
              <input v-model="editingHistory.matchedSopName" type="text" class="input-field w-full" placeholder="如：CPU过高诊断SOP" />
            </div>
          </div>

          <div class="flex justify-end gap-3 p-4 border-t border-dark-700">
            <button @click="closeHistoryEdit" class="btn-secondary">取消</button>
            <button @click="editingHistory.id ? saveHistoryEdit() : saveNewHistory()" :disabled="isSaving" class="btn-primary flex items-center gap-2">
              <Save :size="16" />
              {{ isSaving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirmations -->
    <ConfirmDialog
      :visible="showSopDeleteConfirm"
      :title="'确认删除'"
      :message="'确定要删除这个SOP吗？此操作不可撤销。'"
      @confirm="executeDeleteSop"
      @cancel="showSopDeleteConfirm = false"
    />

    <ConfirmDialog
      :visible="showHistoryDeleteConfirm"
      :title="'确认删除'"
      :message="'确定要删除这个历史案例吗？此操作不可撤销。'"
      @confirm="executeDeleteHistory"
      @cancel="showHistoryDeleteConfirm = false"
    />
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>