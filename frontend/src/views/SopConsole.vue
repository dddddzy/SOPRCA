<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSopStore } from '@/stores/sop'
import {
  Search,
  Filter,
  Plus,
  Edit2,
  Trash2,
  Eye,
  BookOpen,
  ChevronDown
} from 'lucide-vue-next'

const sopStore = useSopStore()

const showDetailModal = ref(false)
const selectedSopId = ref<string | null>(null)

const selectedSop = computed(() => {
  if (!selectedSopId.value) return null
  return sopStore.getSopById(selectedSopId.value)
})

function openDetail(sopId: string) {
  selectedSopId.value = sopId
  showDetailModal.value = true
}

function closeDetail() {
  showDetailModal.value = false
  selectedSopId.value = null
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

function getFaultTypeColor(type: string) {
  const colors: Record<string, string> = {
    CPU: 'text-amber-400',
    Memory: 'text-red-400',
    Network: 'text-primary-400',
    CrashLoop: 'text-orange-400',
    Disk: 'text-emerald-400',
    Unavailable: 'text-purple-400'
  }
  return colors[type] || 'text-dark-300'
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-dark-100">SOP 管理台</h2>
        <p class="text-sm text-dark-400">管理故障诊断标准操作流程</p>
      </div>
      <button class="btn-primary flex items-center gap-2">
        <Plus :size="18" />
        新建 SOP
      </button>
    </div>

    <!-- Filters -->
    <div class="card">
      <div class="flex flex-wrap gap-4">
        <!-- Search -->
        <div class="flex-1 min-w-[200px] relative">
          <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
          <input
            type="text"
            class="input-field pl-10"
            placeholder="搜索 SOP..."
            :value="sopStore.searchQuery"
            @input="sopStore.setSearchQuery(($event.target as HTMLInputElement).value)"
          />
        </div>

        <!-- Status Filter -->
        <div class="flex items-center gap-2">
          <Filter :size="16" class="text-dark-400" />
          <select
            :value="sopStore.statusFilter"
            @change="sopStore.setStatusFilter(($event.target as HTMLSelectElement).value as any)"
            class="input-field w-32"
          >
            <option value="all">全部状态</option>
            <option value="active">启用</option>
            <option value="draft">草稿</option>
            <option value="archived">归档</option>
          </select>
        </div>

        <!-- Type Filter -->
        <select
          :value="sopStore.typeFilter"
          @change="sopStore.setTypeFilter(($event.target as HTMLSelectElement).value)"
          class="input-field w-40"
        >
          <option value="all">全部类型</option>
          <option v-for="type in sopStore.faultTypes" :key="type" :value="type">
            {{ type }}
          </option>
        </select>
      </div>
    </div>

    <!-- SOP Table -->
    <div class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-dark-700">
              <th class="text-left text-xs font-medium text-dark-400 px-4 py-3">名称</th>
              <th class="text-left text-xs font-medium text-dark-400 px-4 py-3">故障类型</th>
              <th class="text-left text-xs font-medium text-dark-400 px-4 py-3">状态</th>
              <th class="text-left text-xs font-medium text-dark-400 px-4 py-3">匹配次数</th>
              <th class="text-left text-xs font-medium text-dark-400 px-4 py-3">更新时间</th>
              <th class="text-right text-xs font-medium text-dark-400 px-4 py-3">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="sop in sopStore.filteredSops"
              :key="sop.id"
              class="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors"
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
                <span class="text-sm text-dark-400">
                  {{ new Date(sop.updatedAt).toLocaleDateString('zh-CN') }}
                </span>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center justify-end gap-1">
                  <button
                    @click="openDetail(sop.id)"
                    class="p-1.5 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-600 transition-all cursor-pointer"
                    title="查看详情"
                  >
                    <Eye :size="16" />
                  </button>
                  <button
                    class="p-1.5 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-600 transition-all cursor-pointer"
                    title="编辑"
                  >
                    <Edit2 :size="16" />
                  </button>
                  <button
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

      <!-- Empty State -->
      <div
        v-if="sopStore.filteredSops.length === 0"
        class="flex flex-col items-center justify-center py-12"
      >
        <BookOpen :size="48" class="text-dark-600 mb-4" />
        <p class="text-dark-400">未找到匹配的 SOP</p>
      </div>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-between">
      <p class="text-sm text-dark-400">
        显示 {{ sopStore.filteredSops.length }} / {{ sopStore.sops.length }} 条
      </p>
      <div class="flex items-center gap-2">
        <button class="btn-secondary text-sm px-3 py-1.5" disabled>上一页</button>
        <button class="btn-secondary text-sm px-3 py-1.5">下一页</button>
      </div>
    </div>

    <!-- Detail Modal -->
    <Teleport to="body">
      <div
        v-if="showDetailModal && selectedSop"
        class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
        @click.self="closeDetail"
      >
        <div class="bg-dark-800 border border-dark-700 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-auto">
          <!-- Modal Header -->
          <div class="flex items-center justify-between p-4 border-b border-dark-700">
            <div class="flex items-center gap-3">
              <BookOpen :size="20" class="text-primary-400" />
              <h3 class="text-lg font-semibold text-dark-100">{{ selectedSop.name }}</h3>
              <span :class="getStatusBadgeClass(selectedSop.status)">
                {{ getStatusLabel(selectedSop.status) }}
              </span>
            </div>
            <button
              @click="closeDetail"
              class="p-1 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700 cursor-pointer"
            >
              ✕
            </button>
          </div>

          <!-- Modal Content -->
          <div class="p-4 space-y-4">
            <div>
              <p class="text-sm text-dark-400 mb-1">描述</p>
              <p class="text-sm text-dark-200">{{ selectedSop.description }}</p>
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
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="flex justify-end gap-3 p-4 border-t border-dark-700">
            <button @click="closeDetail" class="btn-secondary">关闭</button>
            <button class="btn-primary">编辑 SOP</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
