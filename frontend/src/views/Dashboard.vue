<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import StatsCard from '@/components/dashboard/StatsCard.vue'
import FaultTrendChart from '@/components/dashboard/FaultTrendChart.vue'
import FaultTypeChart from '@/components/dashboard/FaultTypeChart.vue'
import { Activity, AlertTriangle, CheckCircle, Clock, Server, Zap, TrendingUp, Users, Cpu, HardDrive, Wifi, Circle } from 'lucide-vue-next'

// 单集群状态
const clusterStatus = ref({
  name: 'production',
  status: 'healthy' as 'healthy' | 'warning' | 'critical',
  nodeCount: 1,
  uptime: '15天6小时'
})

// 模拟资源数据（合理范围）
const resources = ref({
  cpu: 34,
  memory: 62,
  disk: 45,
  networkIn: '128 Mbps',
  networkOut: '89 Mbps'
})

// Pod状态分布
const podStatus = ref([
  { status: 'Running', count: 10, color: 'emerald' },
  { status: 'Pending', count: 1, color: 'amber' },
  { status: 'Failed', count: 1, color: 'red' }
])

const totalPods = computed(() => podStatus.value.reduce((sum, p) => sum + p.count, 0))

// 统计数据（从历史库读取后计算）
const stats = ref({
  totalDiagnoses: 0,
  todayDiagnoses: 0,
  successRate: 0,
  avgDuration: '0s'
})

// 故障趋势（近7天模拟）
const faultTrend = ref([
  { date: '05-03', count: 3 },
  { date: '05-04', count: 5 },
  { date: '05-05', count: 2 },
  { date: '05-06', count: 7 },
  { date: '05-07', count: 4 },
  { date: '05-08', count: 6 },
  { date: '05-09', count: 5 }
])

// 故障类型分布（从历史库统计）
const faultTypes = ref([
  { type: 'CPU', count: 12, percentage: 32 },
  { type: '内存', count: 10, percentage: 27 },
  { type: '网络', count: 8, percentage: 22 },
  { type: 'Pod重启', count: 5, percentage: 13 },
  { type: '其他', count: 2, percentage: 6 }
])

// 最近诊断记录（从历史库读取）
const recentDiagnoses = ref<any[]>([])

// 快捷诊断问题
const quickActions = [
  { label: 'CPU过高', query: 'CPU使用率超过90%', icon: Cpu },
  { label: '内存泄漏', query: '内存占用过高怎么排查', icon: HardDrive },
  { label: '网络延迟', query: '网络延迟怎么排查', icon: Wifi },
  { label: 'Pod重启', query: 'Pod频繁重启的原因', icon: Circle }
]

const router = useRouter()
const settingsStore = useSettingsStore()
const isMockMode = computed(() => settingsStore.settings.cluster.mockMode)

onMounted(async () => {
  await fetchDashboardData()
})

async function fetchDashboardData() {
  try {
    // 获取历史案例统计
    const historyRes = await fetch('/api/history')
    const historyData = await historyRes.json()

    if (historyData.success && historyData.data) {
      const cases = historyData.data
      stats.value.totalDiagnoses = cases.length

      // 今日诊断
      const today = new Date().toDateString()
      const todayCases = cases.filter((c: any) => new Date(c.createTime).toDateString() === today)
      stats.value.todayDiagnoses = todayCases.length

      // 成功率（假设有根因的就是成功）
      const withRootCause = cases.filter((c: any) => c.rootCause && c.rootCause.trim())
      stats.value.successRate = cases.length > 0 ? Math.round((withRootCause.length / cases.length) * 100 * 10) / 10 : 0

      // 最近5条诊断
      recentDiagnoses.value = cases.slice(0, 5)

      // 统计故障类型
      const typeCount: Record<string, number> = {}
      cases.forEach((c: any) => {
        const type = c.faultType || '其他'
        typeCount[type] = (typeCount[type] || 0) + 1
      })

      const total = cases.length
      faultTypes.value = Object.entries(typeCount).map(([type, count]) => ({
        type,
        count,
        percentage: Math.round((count / total) * 100)
      })).sort((a, b) => b.count - a.count).slice(0, 5)

      // 故障趋势（按天统计最近7天）
      const last7Days: Record<string, number> = {}
      for (let i = 6; i >= 0; i--) {
        const d = new Date()
        d.setDate(d.getDate() - i)
        last7Days[d.toDateString()] = 0
      }

      cases.forEach((c: any) => {
        const dateStr = new Date(c.createTime).toDateString()
        if (dateStr in last7Days) {
          last7Days[dateStr]++
        }
      })

      faultTrend.value = Object.entries(last7Days).map(([date, count]) => ({
        date: new Date(date).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }),
        count
      }))
    }
  } catch (e) {
    console.error('Failed to fetch dashboard data:', e)
  }
}

function startQuickDiagnosis(query: string) {
  router.push({ path: '/diagnosis', query: { q: query } })
}

function getStatusColor(status: string) {
  switch (status) {
    case 'healthy': return 'emerald'
    case 'warning': return 'amber'
    case 'critical': return 'red'
    default: return 'gray'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- 集群状态 Header -->
    <div class="card">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <Server :size="20" class="text-dark-400" />
            <span class="text-dark-200 font-medium">集群:</span>
            <span class="text-dark-100 font-semibold">{{ clusterStatus.name }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span :class="['w-2 h-2 rounded-full', `bg-${getStatusColor(clusterStatus.status)}-500`, clusterStatus.status === 'healthy' ? 'animate-pulse' : '']"></span>
            <span :class="[`text-${getStatusColor(clusterStatus.status)}-400`, 'text-sm']">
              {{ clusterStatus.status === 'healthy' ? '运行中' : clusterStatus.status === 'warning' ? '警告' : '异常' }}
            </span>
          </div>
          <div class="flex items-center gap-2 text-dark-400 text-sm">
            <Users :size="14" />
            <span>{{ clusterStatus.nodeCount }} 节点</span>
          </div>
          <div class="flex items-center gap-2 text-dark-400 text-sm">
            <Clock :size="14" />
            <span>在线 {{ clusterStatus.uptime }}</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="isMockMode" class="badge-warning">Mock 模式</span>
          <span v-else class="badge-success">真实模式</span>
        </div>
      </div>
    </div>

    <!-- 资源统计 + Pod状态 -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <!-- CPU -->
      <div class="card">
        <div class="flex items-center gap-2 mb-3">
          <Cpu :size="16" class="text-primary-400" />
          <span class="text-dark-300 text-sm">CPU</span>
        </div>
        <div class="text-2xl font-bold text-dark-100 mb-1">{{ resources.cpu }}%</div>
        <div class="h-1.5 bg-dark-700 rounded-full overflow-hidden">
          <div class="h-full bg-primary-500 rounded-full" :style="{ width: resources.cpu + '%' }"></div>
        </div>
      </div>

      <!-- 内存 -->
      <div class="card">
        <div class="flex items-center gap-2 mb-3">
          <HardDrive :size="16" class="text-amber-400" />
          <span class="text-dark-300 text-sm">内存</span>
        </div>
        <div class="text-2xl font-bold text-dark-100 mb-1">{{ resources.memory }}%</div>
        <div class="h-1.5 bg-dark-700 rounded-full overflow-hidden">
          <div class="h-full bg-amber-500 rounded-full" :style="{ width: resources.memory + '%' }"></div>
        </div>
      </div>

      <!-- 磁盘 -->
      <div class="card">
        <div class="flex items-center gap-2 mb-3">
          <HardDrive :size="16" class="text-emerald-400" />
          <span class="text-dark-300 text-sm">磁盘</span>
        </div>
        <div class="text-2xl font-bold text-dark-100 mb-1">{{ resources.disk }}%</div>
        <div class="h-1.5 bg-dark-700 rounded-full overflow-hidden">
          <div class="h-full bg-emerald-500 rounded-full" :style="{ width: resources.disk + '%' }"></div>
        </div>
      </div>

      <!-- 网络入口 -->
      <div class="card">
        <div class="flex items-center gap-2 mb-3">
          <Wifi :size="16" class="text-cyan-400" />
          <span class="text-dark-300 text-sm">入流量</span>
        </div>
        <div class="text-2xl font-bold text-dark-100 mb-1">{{ resources.networkIn }}</div>
        <div class="text-dark-500 text-xs">eth0</div>
      </div>

      <!-- 网络出口 -->
      <div class="card">
        <div class="flex items-center gap-2 mb-3">
          <Wifi :size="16" class="text-purple-400" />
          <span class="text-dark-300 text-sm">出流量</span>
        </div>
        <div class="text-2xl font-bold text-dark-100 mb-1">{{ resources.networkOut }}</div>
        <div class="text-dark-500 text-xs">eth0</div>
      </div>
    </div>

    <!-- 统计卡片 + Pod状态分布 -->
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
      <StatsCard title="总诊断次数" :value="stats.totalDiagnoses" icon="Activity" color="primary" />
      <StatsCard title="今日诊断" :value="stats.todayDiagnoses" icon="Clock" color="accent" />
      <StatsCard title="成功率" :value="stats.successRate > 0 ? stats.successRate + '%' : '-'" icon="CheckCircle" color="emerald" />
      <StatsCard title="平均耗时" :value="stats.avgDuration" icon="Zap" color="amber" />
    </div>

    <!-- Pod状态 + 故障类型 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Pod状态分布 -->
      <div class="card">
        <h3 class="text-sm font-medium text-dark-300 mb-4">Pod 状态分布</h3>
        <div class="flex items-center gap-4 mb-4">
          <div class="text-3xl font-bold text-dark-100">{{ totalPods }}</div>
          <div class="text-dark-400 text-sm">总Pod数</div>
        </div>
        <div class="space-y-3">
          <div v-for="pod in podStatus" :key="pod.status" class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span :class="['w-2 h-2 rounded-full', `bg-${pod.color}-500`]"></span>
              <span class="text-dark-300 text-sm">{{ pod.status }}</span>
            </div>
            <div class="flex items-center gap-3">
              <div class="w-24 h-1.5 bg-dark-700 rounded-full overflow-hidden">
                <div :class="['h-full rounded-full', `bg-${pod.color}-500`]" :style="{ width: (pod.count / totalPods * 100) + '%' }"></div>
              </div>
              <span class="text-dark-200 text-sm w-6 text-right">{{ pod.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 故障类型分布 -->
      <div class="card lg:col-span-2">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-medium text-dark-300">故障类型分布</h3>
          <AlertTriangle :size="16" class="text-dark-400" />
        </div>
        <FaultTypeChart :data="faultTypes" />
      </div>
    </div>

    <!-- 最近诊断 + 快捷入口 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- 最近诊断记录 -->
      <div class="card lg:col-span-2">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-medium text-dark-300">最近诊断记录</h3>
          <button @click="router.push('/diagnosis')" class="text-primary-400 text-sm hover:text-primary-300">查看全部 →</button>
        </div>
        <div v-if="recentDiagnoses.length === 0" class="text-center py-8 text-dark-400">
          暂无诊断记录
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="item in recentDiagnoses"
            :key="item.id"
            class="flex items-start gap-3 p-3 rounded-lg hover:bg-dark-700/50 transition-colors"
          >
            <div :class="['w-2 h-2 rounded-full mt-1.5', item.rootCause ? 'bg-emerald-500' : 'bg-amber-500']"></div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-dark-200">{{ item.faultInfo }}</p>
              <p class="text-xs text-dark-400 mt-1">
                <span v-if="item.rootCause">{{ item.rootCause }}</span>
                <span v-else class="text-amber-400">未定位到根因</span>
                <span class="mx-2">·</span>
                <span>{{ new Date(item.createTime).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }}</span>
              </p>
            </div>
            <span :class="['px-2 py-0.5 rounded text-xs', item.faultType === 'CPU' ? 'bg-primary-500/20 text-primary-400' : item.faultType === '内存' ? 'bg-amber-500/20 text-amber-400' : 'bg-dark-600 text-dark-300']">
              {{ item.faultType }}
            </span>
          </div>
        </div>
      </div>

      <!-- 快捷诊断入口 -->
      <div class="card">
        <h3 class="text-sm font-medium text-dark-300 mb-4">快捷诊断</h3>
        <div class="grid grid-cols-2 gap-3">
          <button
            v-for="action in quickActions"
            :key="action.label"
            @click="startQuickDiagnosis(action.query)"
            class="flex flex-col items-center gap-2 p-4 rounded-lg bg-dark-700/50 hover:bg-dark-700 border border-dark-600 hover:border-primary-500/50 transition-all group"
          >
            <component :is="action.icon" :size="24" class="text-dark-400 group-hover:text-primary-400 transition-colors" />
            <span class="text-dark-300 text-sm group-hover:text-dark-100 transition-colors">{{ action.label }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 故障趋势 -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-medium text-dark-300">故障趋势（近7天）</h3>
        <TrendingUp :size="16" class="text-dark-400" />
      </div>
      <FaultTrendChart :data="faultTrend" />
    </div>
  </div>
</template>