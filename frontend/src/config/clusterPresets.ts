// 预设集群配置
export interface PresetCluster {
  id: string
  name: string
  server: string
  context: string
  env: 'dev' | 'prod'
  mockMode: boolean
  description: string
}

export const presetClusters: PresetCluster[] = [
  {
    id: 'local-k3s',
    name: 'Local K3s',
    server: 'https://192.168.100.132:6443',
    context: 'default',
    env: 'dev',
    mockMode: false,
    description: '本地 K3s 集群'
  },
  {
    id: 'dev-mock',
    name: '开发环境 (Mock)',
    server: 'https://localhost:6443',
    context: 'dev',
    env: 'dev',
    mockMode: true,
    description: '开发环境，使用 Mock 模式'
  },
  {
    id: 'prod-mock',
    name: '生产环境 (Mock)',
    server: 'https://kubernetes.docker.internal:6443',
    context: 'prod',
    env: 'prod',
    mockMode: true,
    description: '生产环境，使用 Mock 模式'
  }
]