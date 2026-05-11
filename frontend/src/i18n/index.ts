import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import enUS from './en-US'

export type MessageSchema = typeof zhCN

const i18n = createI18n<[MessageSchema], 'zh-CN' | 'en-US'>({
  legacy: false,
  locale: localStorage.getItem('soprca-locale') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
})

export default i18n

export function setLocale(locale: 'zh-CN' | 'en-US') {
  (i18n.global.locale as any).value = locale
  localStorage.setItem('soprca-locale', locale)
}

export function getLocale(): string {
  return (i18n.global.locale as any).value as string
}
