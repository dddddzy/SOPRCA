import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SOP } from '@/types'

export const useSopStore = defineStore('sop', () => {
  const sops = ref<SOP[]>([
    {
      id: 'sop-001',
      name: 'CPU过高诊断流程',
      description: '用于诊断Kubernetes中Pod CPU使用率过高的问题',
      faultType: 'CPU',
      status: 'active',
      createdAt: '2024-01-15T10:30:00Z',
      updatedAt: '2024-03-20T14:22:00Z',
      matchCount: 128,
      steps: [
        { order: 1, tool: 'get_relevant_metric', description: '获取CPU指标', expectedResult: 'CPU使用率数据' },
        { order: 2, tool: 'pod_analyze', description: '分析Pod状态', expectedResult: 'Pod详情和重启次数' },
        { order: 3, tool: 'check_events', description: '检查相关事件', expectedResult: 'CPU节流事件' }
      ]
    },
    {
      id: 'sop-002',
      name: '内存溢出诊断流程',
      description: '用于诊断Pod内存溢出(OOM)问题',
      faultType: 'Memory',
      status: 'active',
      createdAt: '2024-01-20T09:15:00Z',
      updatedAt: '2024-03-18T11:45:00Z',
      matchCount: 89,
      steps: [
        { order: 1, tool: 'get_relevant_metric', description: '获取内存指标', expectedResult: '内存使用率数据' },
        { order: 2, tool: 'pod_analyze', description: '分析Pod状态', expectedResult: 'OOMKilled状态' },
        { order: 3, tool: 'check_events', description: '检查OOM事件', expectedResult: 'OOMKilled事件' }
      ]
    },
    {
      id: 'sop-003',
      name: '网络延迟诊断流程',
      description: '用于诊断服务间网络延迟问题',
      faultType: 'Network',
      status: 'active',
      createdAt: '2024-02-05T16:00:00Z',
      updatedAt: '2024-03-25T08:30:00Z',
      matchCount: 67,
      steps: [
        { order: 1, tool: 'collect_trace', description: '收集链路追踪', expectedResult: 'Trace数据' },
        { order: 2, tool: 'analyze_trace_latency', description: '分析延迟分布', expectedResult: 'P50/P90/P99延迟' },
        { order: 3, tool: 'get_relevant_metric', description: '获取网络指标', expectedResult: '网络吞吐和错误率' }
      ]
    },
    {
      id: 'sop-004',
      name: 'Pod重启诊断流程',
      description: '用于诊断Pod频繁重启问题',
      faultType: 'CrashLoop',
      status: 'active',
      createdAt: '2024-02-10T13:20:00Z',
      updatedAt: '2024-03-22T17:10:00Z',
      matchCount: 156,
      steps: [
        { order: 1, tool: 'pod_analyze', description: '分析Pod状态', expectedResult: '重启次数和原因' },
        { order: 2, tool: 'get_pod_logs', description: '获取Pod日志', expectedResult: '错误日志内容' },
        { order: 3, tool: 'check_events', description: '检查Events', expectedResult: '重启相关事件' }
      ]
    },
    {
      id: 'sop-005',
      name: '服务不可用诊断流程',
      description: '用于诊断Service无法访问的问题',
      faultType: 'Unavailable',
      status: 'draft',
      createdAt: '2024-03-01T11:00:00Z',
      updatedAt: '2024-03-15T09:30:00Z',
      matchCount: 23,
      steps: [
        { order: 1, tool: 'service_analyze', description: '分析Service状态', expectedResult: 'Service端点信息' },
        { order: 2, tool: 'pod_analyze', description: '分析Pod状态', expectedResult: 'Pod运行状态' },
        { order: 3, tool: 'check_events', description: '检查相关事件', expectedResult: '调度失败事件' }
      ]
    },
    {
      id: 'sop-006',
      name: '磁盘空间不足诊断流程',
      description: '用于诊断PVC或节点磁盘空间不足问题',
      faultType: 'Disk',
      status: 'archived',
      createdAt: '2024-01-25T14:00:00Z',
      updatedAt: '2024-02-28T16:45:00Z',
      matchCount: 34,
      steps: [
        { order: 1, tool: 'get_node_status', description: '获取节点状态', expectedResult: '磁盘使用率' },
        { order: 2, tool: 'check_events', description: '检查磁盘事件', expectedResult: 'DiskPressure事件' }
      ]
    }
  ])

  const searchQuery = ref('')
  const statusFilter = ref<'all' | 'active' | 'draft' | 'archived'>('all')
  const typeFilter = ref<string>('all')

  const filteredSops = computed(() => {
    return sops.value.filter(sop => {
      const matchSearch = searchQuery.value === '' ||
        sop.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        sop.description.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        sop.faultType.toLowerCase().includes(searchQuery.value.toLowerCase())

      const matchStatus = statusFilter.value === 'all' || sop.status === statusFilter.value
      const matchType = typeFilter.value === 'all' || sop.faultType === typeFilter.value

      return matchSearch && matchStatus && matchType
    })
  })

  const faultTypes = computed(() => {
    return [...new Set(sops.value.map(s => s.faultType))]
  })

  function setSearchQuery(query: string) {
    searchQuery.value = query
  }

  function setStatusFilter(status: 'all' | 'active' | 'draft' | 'archived') {
    statusFilter.value = status
  }

  function setTypeFilter(type: string) {
    typeFilter.value = type
  }

  function getSopById(id: string) {
    return sops.value.find(s => s.id === id)
  }

  return {
    sops,
    searchQuery,
    statusFilter,
    typeFilter,
    filteredSops,
    faultTypes,
    setSearchQuery,
    setStatusFilter,
    setTypeFilter,
    getSopById
  }
})
