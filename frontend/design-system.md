# SOPRCA Frontend Design System

## 1. Concept & Vision

SOPRCA 前端是一个类 Grafana 风格的运维监控与 AI 诊断平台界面。采用深色主题，数据密度高，层级清晰。核心场景是实时故障诊断，通过流式步骤展示 AI Agent 的推理过程，最终输出结构化 RCA 报告。

## 2. Design Language

### Aesthetic Direction
- **参考**: Grafana Dark Theme
- **关键词**: 数据密集、信息层级清晰、暗色专业、运维监控风格

### Color Palette
```
Primary:     #0EA5E9 (Cyan-500)
Accent:      #06B6D4 (Cyan-600)
Success:     #10B981 (Emerald-500)
Warning:     #F59E0B (Amber-500)
Error:       #EF4444 (Red-500)

Dark Mode:
- Background:   #020617 (slate-950)
- Surface:      #0F172A (slate-900)
- Border:       #1E293B (slate-800)
- Text Primary: #F1F5F9 (slate-100)
- Text Secondary: #94A3B8 (slate-400)

Light Mode:
- Background:   #F8FAFC (slate-50)
- Surface:     #FFFFFF
- Border:      #E2E8F0 (slate-200)
- Text Primary: #0F172A (slate-900)
- Text Secondary: #475569 (slate-600)
```

### Typography
- **Primary Font**: Inter (Google Fonts)
- **Monospace Font**: Fira Code (Google Fonts)
- **Scale**: 12/14/16/18/24/32px

### Spatial System
- Base unit: 4px
- Component spacing: 8px / 12px / 16px / 24px
- Section spacing: 24px / 32px / 48px
- Border radius: 8px (small), 12px (medium), 16px (large)

### Motion Philosophy
- Duration: 150-300ms for micro-interactions
- Easing: ease-out for enter, ease-in for exit
- Use transform/opacity only (no layout thrashing)

## 3. Layout & Structure

### Page Structure
- **Sidebar** (fixed, 256px collapsed 64px): 导航菜单 + Logo
- **Header** (fixed, 64px): 页面标题 + 主题切换 + 用户
- **Content** (scrollable): 各页面内容

### Responsive Strategy
- Mobile-first with breakpoints: 375 / 768 / 1024 / 1440px
- Sidebar collapses on mobile
- Grid adapts: 1 col → 2 col → 4 col

## 4. Features & Interactions

### Dashboard
- Stats cards with trend indicators
- Cluster status cards with CPU/Memory bars
- Fault trend line chart
- Fault type distribution chart
- Recent diagnoses list

### Real-time Diagnosis (Core)
- Input: fault description text field
- Output: streaming step timeline + RCA report card + log console
- States: idle, running, complete, error
- Animation: steps appear one by one with fade-in

### SOP Console
- Search + filter (status, type)
- Sortable table with pagination
- Detail modal with SOP steps

### Settings
- Theme selector (dark/light/auto)
- Model config (API endpoint, key, tokens, temperature)
- Server config (host, port, langgraph url)

## 5. Component Inventory

### Cards
- Default: bg-dark-800 border-dark-700 rounded-xl
- Hover: border-dark-600 transition

### Buttons
- Primary: bg-primary-500 hover:bg-primary-600
- Secondary: bg-dark-700 border-dark-600
- Danger: bg-red-600

### Inputs
- Default: bg-dark-800 border-dark-600
- Focus: border-primary-500 ring-1 ring-primary-500

### Badges
- Success: bg-emerald-500/20 text-emerald-400
- Warning: bg-amber-500/20 text-amber-400
- Error: bg-red-500/20 text-red-400
- Info: bg-primary-500/20 text-primary-400

### Log Console
- Monospace font, dark background
- Color-coded by level: info/success/warning/error/primary

## 6. Technical Approach

### Stack
- Vue 3 Composition API + TypeScript
- Vite 5
- Pinia (state management)
- Vue Router 4
- Tailwind CSS 3
- Lucide Vue (icons)

### Directory Structure
```
frontend/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── dashboard/
│   │   ├── diagnosis/
│   │   └── layout/
│   ├── router/
│   ├── stores/
│   ├── types/
│   ├── views/
│   ├── App.vue
│   ├── main.ts
│   └── style.css
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

### State Management
- `useThemeStore`: theme mode (dark/light/auto)
- `useDiagnosisStore`: current diagnosis state, steps, logs, report
- `useSopStore`: SOP list, search, filters
- `useSettingsStore`: model config, server config

### Mock Data
- Dashboard: simulated stats, clusters, trends
- Diagnosis: simulated streaming steps and report
- SOP: 6 sample SOPs with different statuses
