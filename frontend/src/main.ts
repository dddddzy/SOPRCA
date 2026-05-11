import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { useThemeStore } from './stores/theme'
import { useSettingsStore } from './stores/settings'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(i18n)

// Initialize stores
const themeStore = useThemeStore()
themeStore.initTheme()

const settingsStore = useSettingsStore()
settingsStore.loadSettings()

app.mount('#app')
