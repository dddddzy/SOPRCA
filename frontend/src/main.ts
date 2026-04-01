import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/theme'
import { useSettingsStore } from './stores/settings'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Initialize stores
const themeStore = useThemeStore()
themeStore.initTheme()

const settingsStore = useSettingsStore()
settingsStore.loadSettings()

app.mount('#app')
