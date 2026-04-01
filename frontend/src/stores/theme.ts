import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<'dark' | 'light' | 'auto'>('dark')

  const isDark = ref(true)

  function updateDarkMode() {
    if (theme.value === 'auto') {
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    } else {
      isDark.value = theme.value === 'dark'
    }
    applyTheme()
  }

  function applyTheme() {
    const html = document.documentElement
    if (isDark.value) {
      html.classList.add('dark')
      html.classList.remove('light')
    } else {
      html.classList.add('light')
      html.classList.remove('dark')
    }
  }

  function setTheme(newTheme: 'dark' | 'light' | 'auto') {
    theme.value = newTheme
    localStorage.setItem('soprca-theme', newTheme)
    updateDarkMode()
  }

  function initTheme() {
    const saved = localStorage.getItem('soprca-theme') as 'dark' | 'light' | 'auto' | null
    if (saved) {
      theme.value = saved
    }
    updateDarkMode()

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (theme.value === 'auto') {
        updateDarkMode()
      }
    })
  }

  return { theme, isDark, setTheme, initTheme }
})
