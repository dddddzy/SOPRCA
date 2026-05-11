export default {
  nav: {
    dashboard: '仪表盘',
    knowledge: '知识问答',
    diagnosis: '实时诊断',
    sop: 'SOP管理台',
    settings: '设置'
  },
  common: {
    save: '保存',
    cancel: '取消',
    reset: '重置',
    search: '搜索',
    filter: '筛选',
    loading: '加载中...',
    noData: '暂无数据',
    showing: '显示',
    records: '条'
  },
  dashboard: {
    title: '仪表盘',
    totalDiagnoses: '总诊断次数',
    todayDiagnoses: '今日诊断',
    successRate: '成功率',
    avgDuration: '平均耗时',
    clustersOverview: '集群概览',
    activeClusters: '共 {count} 个集群',
    resourceStats: '资源统计',
    totalPods: '总Pod数',
    services: '服务数',
    recentDiagnoses: '最近诊断',
    faultTrend: '故障趋势',
    faultTypes: '故障类型分布'
  },
  diagnosis: {
    title: '实时诊断',
    faultDescription: '故障描述',
    startDiagnosis: '开始诊断',
    stop: '停止',
    reset: '重置',
    diagnosisSteps: '诊断步骤',
    running: '执行中...',
    completed: '已完成 {count} 步',
    report: '诊断报告',
    noReport: '暂无诊断报告',
    noReportHint: '请输入故障描述开始诊断',
    console: '控制台输出',
    noLogs: '暂无日志输出',
    placeholder: '请输入故障描述...',
    quickInput: '快速输入:',
    examples: [
      'cartservice 出现严重的 TCP 阻塞和未知网络延迟',
      'productcatalogservice CPU使用率超过90%',
      'paymentservice Pod频繁重启',
      'userservice 内存溢出导致服务不可用'
    ]
  },
  report: {
    rootCause: '根因',
    location: '位置',
    diagnosisTime: '诊断时间',
    keyClues: '关键线索',
    suggestions: '建议',
    confidence: '置信度',
    found: '已找到根因',
    notFound: '未找到根因'
  },
  settings: {
    title: '设置',
    theme: {
      title: '主题设置',
      description: '自定义界面外观',
      dark: '暗色',
      light: '亮色',
      auto: '跟随系统'
    },
    language: {
      title: '语言设置',
      description: '选择界面语言'
    },
    model: {
      title: '模型配置',
      description: '配置 LLM API 连接参数',
      presets: '预设模型',
      apiEndpoint: 'API Endpoint',
      modelName: '模型名称',
      apiKey: 'API Key',
      maxTokens: '最大 Tokens',
      temperature: 'Temperature',
      saveConfig: '保存配置',
      saveSuccess: '保存成功',
      testConnection: '测试连接',
      testSuccess: '连接成功'
    },
    server: {
      title: '服务器配置',
      description: '配置后端服务连接',
      host: 'Host',
      port: 'Port',
      langgraphUrl: 'LangGraph URL',
      saveSuccess: '保存成功'
    },
    cluster: {
      title: '服务器/集群配置',
      description: '配置Kubernetes集群连接和运行环境',
      presets: '预设集群',
      server: 'API Server 地址',
      context: 'Context 名称',
      kubeconfig: 'Kubeconfig 文件',
      env: '环境',
      mockMode: 'Mock 模式',
      saveSuccess: '保存成功'
    },
    reset: {
      title: '重置所有设置',
      description: '将所有配置恢复为默认值',
      confirmTitle: '确认重置',
      confirmMessage: '确定要重置所有设置吗？此操作不可撤销。'
    },
    clear: {
      title: '清除所有设置',
      description: '清除本地存储的所有设置，恢复初始状态',
      button: '清除设置',
      confirmTitle: '确认清除',
      confirmMessage: '确定要清除所有设置吗？此操作不可撤销。'
    }
  },
  sop: {
    title: 'SOP 管理台',
    description: '管理故障诊断标准操作流程',
    newSop: '新建 SOP',
    search: '搜索 SOP...',
    statusFilter: '全部状态',
    typeFilter: '全部类型',
    table: {
      name: '名称',
      faultType: '故障类型',
      status: '状态',
      matchCount: '匹配次数',
      updateTime: '更新时间',
      actions: '操作'
    },
    status: {
      active: '启用',
      draft: '草稿',
      archived: '归档'
    },
    detail: {
      description: '描述',
      diagnosisSteps: '诊断步骤'
    },
    edit: {
      title: '编辑 SOP',
      deleteConfirm: '确定要删除这个SOP吗？此操作不可撤销。'
    }
  },
  knowledge: {
    title: '知识库问答',
    description: '基于历史诊断案例和SOP知识的智能问答',
    developing: '功能开发中',
    comingSoon: '即将上线',
    comingSoonDesc: '基于历史诊断案例和SOP知识库的智能问答系统。您可以询问关于故障诊断、SOP流程、以及运维最佳实践等问题。',
    features: [
      '历史案例分析',
      'SOP流程咨询',
      '故障根因问答',
      '运维知识库'
    ],
    inputPlaceholder: '输入您的问题...'
  }
}
