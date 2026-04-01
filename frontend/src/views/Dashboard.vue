<script setup lang="ts">
import { ref, onMounted } from 'vue'
import StatsCard from '@/components/dashboard/StatsCard.vue'
import ClusterCard from '@/components/dashboard/ClusterCard.vue'
import FaultTrendChart from '@/components/dashboard/FaultTrendChart.vue'
import FaultTypeChart from '@/components/dashboard/FaultTypeChart.vue'
import { Activity, AlertTriangle, CheckCircle, Clock, Server, Zap, TrendingUp } from 'lucide-vue-next'

const stats = ref({
  totalDiagnoses: 256,
  todayDiagnoses: 12,
  successRate: 94.2,
  avgDuration: '2m 34s',
  activeClusters: 3,
  totalPods: 1247
})

const clusters = ref([
  {
    name: 'production',
    status: 'healthy' as const,
    podCount: 456,
    cpuUsage: 42,
    memoryUsage: 58,
    serviceCount: 23
  },
  {
    name: 'staging',
    status: 'warning' as const,
    podCount: 234,
    cpuUsage: 71,
    memoryUsage: 65,
    serviceCount: 15
  },
  {
    name: 'development',
    status: 'critical' as const,
    podCount: 89,
    cpuUsage: 89,
    memoryUsage: 82,
    serviceCount: 8
  }
])

const faultTrend = ref([
  { date: '03-24', count: 8 },
  { date: '03-25', count: 12 },
  { date: '03-26', count: 6 },
  { date: '03-27', count: 15 },
  { date: '03-28', count: 9 },
  { date: '03-29', count: 11 },
  { date: '03-30', count: 12 }
])

const faultTypes = ref([
  { type: 'CPU', count: 89, percentage: 35 },
  { type: 'Memory', count: 67, percentage: 26 },
  { type: 'Network', count: 45, percentage: 18 },
  { type: 'CrashLoop', count: 34, percentage: 13 },
  { type: 'Other', count: 21, percentage: 8 }
])

const recentDiagnoses = ref([
  { id: 1, faultInfo: 'cartservice TCP网络延迟', result: '网络延迟导致超时', time: '10分钟前', status: 'success' },
  { id: 2, faultInfo: 'productservice CPU过高', result: 'CPU资源不足', time: '25分钟前', status: 'success' },
  { id: 3, faultInfo: 'paymentservice Pod重启', result: 'OOMKilled', time: '1小时前', status: 'success' },
  { id: 4, faultInfo: 'userservice 无法访问', result: 'Service端点异常', time: '2小时前', status: 'warning' }
])
</script>

<template>
  <div class="space-y-6">
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatsCard
        title="总诊断次数"
        :value="stats.totalDiagnoses"
        icon="Activity"
        color="primary"
        trend="+12%"
        :trend-up="true"
      />
      <StatsCard
        title="今日诊断"
        :value="stats.todayDiagnoses"
        icon="Clock"
        color="accent"
        trend="较昨日"
        :trend-up="true"
      />
      <StatsCard
        title="成功率"
        :value="`${stats.successRate}%`"
        icon="CheckCircle"
        color="emerald"
        trend="+2.3%"
        :trend-up="true"
      />
      <StatsCard
        title="平均耗时"
        :value="stats.avgDuration"
        icon="Zap"
        color="amber"
        trend="-15s"
        :trend-up="false"
      />
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Cluster Status Cards -->
      <div class="lg:col-span-2 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-dark-100">集群概览</h2>
          <span class="badge-info">共 {{ stats.activeClusters }} 个集群</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ClusterCard
            v-for="cluster in clusters"
            :key="cluster.name"
            :cluster="cluster"
          />
        </div>
      </div>

      <!-- Right Sidebar Stats -->
      <div class="space-y-4">
        <!-- Pods & Services -->
        <div class="card">
          <h3 class="text-sm font-medium text-dark-300 mb-4">资源统计</h3>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Server :size="16" class="text-dark-400" />
                <span class="text-sm text-dark-300">总Pod数</span>
              </div>
              <span class="text-lg font-semibold text-dark-100">{{ stats.totalPods }}</span>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Activity :size="16" class="text-dark-400" />
                <span class="text-sm text-dark-300">服务数</span>
              </div>
              <span class="text-lg font-semibold text-dark-100">46</span>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="card">
          <h3 class="text-sm font-medium text-dark-300 mb-4">最近诊断</h3>
          <div class="space-y-3">
            <div
              v-for="item in recentDiagnoses"
              :key="item.id"
              class="flex items-start gap-3 p-2 rounded-lg hover:bg-dark-700 transition-colors"
            >
              <div
                :class="[
                  'w-2 h-2 rounded-full mt-1.5',
                  item.status === 'success' ? 'bg-emerald-500' : 'bg-amber-500'
                ]"
              ></div>
              <div class="flex-1 min-w-0">
                <p class="text-sm text-dark-200 truncate">{{ item.faultInfo }}</p>
                <p class="text-xs text-dark-400">{{ item.result }} · {{ item.time }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-medium text-dark-300">故障趋势</h3>
          <TrendingUp :size="16" class="text-dark-400" />
        </div>
        <FaultTrendChart :data="faultTrend" />
      </div>
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-medium text-dark-300">故障类型分布</h3>
          <AlertTriangle :size="16" class="text-dark-400" />
        </div>
        <FaultTypeChart :data="faultTypes" />
      </div>
    </div>
  </div>
</template>
