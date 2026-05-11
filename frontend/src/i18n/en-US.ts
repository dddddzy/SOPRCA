export default {
  nav: {
    dashboard: 'Dashboard',
    knowledge: 'Knowledge QA',
    diagnosis: 'Real-time Diagnosis',
    sop: 'SOP Console',
    settings: 'Settings'
  },
  common: {
    save: 'Save',
    cancel: 'Cancel',
    reset: 'Reset',
    search: 'Search',
    filter: 'Filter',
    loading: 'Loading...',
    noData: 'No Data',
    showing: 'Showing',
    records: 'records'
  },
  dashboard: {
    title: 'Dashboard',
    totalDiagnoses: 'Total Diagnoses',
    todayDiagnoses: 'Today',
    successRate: 'Success Rate',
    avgDuration: 'Avg Duration',
    clustersOverview: 'Clusters Overview',
    activeClusters: '{count} Clusters',
    resourceStats: 'Resource Stats',
    totalPods: 'Total Pods',
    services: 'Services',
    recentDiagnoses: 'Recent Diagnoses',
    faultTrend: 'Fault Trend',
    faultTypes: 'Fault Type Distribution'
  },
  diagnosis: {
    title: 'Real-time Diagnosis',
    faultDescription: 'Fault Description',
    startDiagnosis: 'Start Diagnosis',
    stop: 'Stop',
    reset: 'Reset',
    diagnosisSteps: 'Diagnosis Steps',
    running: 'Running...',
    completed: 'Completed {count} steps',
    report: 'Diagnosis Report',
    noReport: 'No Report',
    noReportHint: 'Enter fault description to start diagnosis',
    console: 'Console Output',
    noLogs: 'No logs',
    placeholder: 'Enter fault description...',
    quickInput: 'Quick input:',
    examples: [
      'cartservice has severe TCP blocking and unknown network delay',
      'productcatalogservice CPU usage over 90%',
      'paymentservice Pod frequent restart',
      'userservice OOM causing service unavailable'
    ]
  },
  report: {
    rootCause: 'Root Cause',
    location: 'Location',
    diagnosisTime: 'Diagnosis Time',
    keyClues: 'Key Clues',
    suggestions: 'Suggestions',
    confidence: 'Confidence',
    found: 'Root Cause Found',
    notFound: 'Root Cause Not Found'
  },
  settings: {
    title: 'Settings',
    theme: {
      title: 'Theme',
      description: 'Customize interface appearance',
      dark: 'Dark',
      light: 'Light',
      auto: 'System'
    },
    language: {
      title: 'Language',
      description: 'Select interface language'
    },
    model: {
      title: 'Model Configuration',
      description: 'Configure LLM API connection',
      presets: 'Preset Models',
      apiEndpoint: 'API Endpoint',
      modelName: 'Model Name',
      apiKey: 'API Key',
      maxTokens: 'Max Tokens',
      temperature: 'Temperature',
      saveConfig: 'Save Config',
      saveSuccess: 'Saved! Restart backend to take effect',
      saveFailed: 'Failed to save',
      testConnection: 'Test Connection',
      testSuccess: 'Connection successful'
    },
    server: {
      title: 'Server Configuration',
      description: 'Configure backend connection',
      host: 'Host',
      port: 'Port',
      langgraphUrl: 'LangGraph URL',
      saveSuccess: 'Saved'
    },
    cluster: {
      title: 'Server / Cluster',
      description: 'Configure Kubernetes cluster connection and runtime environment',
      presets: 'Presets',
      server: 'API Server',
      context: 'Context',
      kubeconfig: 'Kubeconfig File',
      env: 'Environment',
      mockMode: 'Mock Mode',
      saveSuccess: 'Saved'
    },
    reset: {
      title: 'Reset All Settings',
      description: 'Restore all settings to default',
      confirmTitle: 'Confirm Reset',
      confirmMessage: 'Are you sure you want to reset all settings? This action cannot be undone.'
    },
    clear: {
      title: 'Clear All Settings',
      description: 'Clear all locally stored settings and restore to initial state',
      button: 'Clear Settings',
      confirmTitle: 'Confirm Clear',
      confirmMessage: 'Are you sure you want to clear all settings? This action cannot be undone.'
    }
  },
  sop: {
    title: 'SOP Console',
    description: 'Manage fault diagnosis standard operating procedures',
    newSop: 'New SOP',
    search: 'Search SOP...',
    statusFilter: 'All Status',
    typeFilter: 'All Types',
    table: {
      name: 'Name',
      faultType: 'Fault Type',
      status: 'Status',
      matchCount: 'Match Count',
      updateTime: 'Updated',
      actions: 'Actions'
    },
    status: {
      active: 'Active',
      draft: 'Draft',
      archived: 'Archived'
    },
    detail: {
      description: 'Description',
      diagnosisSteps: 'Diagnosis Steps'
    },
    edit: {
      title: 'Edit SOP',
      deleteConfirm: 'Are you sure you want to delete this SOP? This action cannot be undone.'
    }
  },
  knowledge: {
    title: 'Knowledge QA',
    description: 'Intelligent Q&A based on historical diagnosis cases and SOP knowledge',
    developing: 'Under Development',
    comingSoon: 'Coming Soon',
    comingSoonDesc: 'Intelligent Q&A system based on historical diagnosis cases and SOP knowledge base. You can ask questions about fault diagnosis, SOP processes, and operational best practices.',
    features: [
      'Historical Case Analysis',
      'SOP Process Consultation',
      'Fault Root Cause Q&A',
      'Operations Knowledge Base'
    ],
    inputPlaceholder: 'Enter your question...'
  }
}
