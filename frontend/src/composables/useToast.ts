import { ref } from 'vue'

const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error' | 'info'>('success')

let timeoutId: number | null = null

export function useToast() {
  function show(message: string, type: 'success' | 'error' | 'info' = 'success') {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    toastMessage.value = message
    toastType.value = type
    toastVisible.value = true
  }

  function hide() {
    toastVisible.value = false
    timeoutId = null
  }

  return {
    toastVisible,
    toastMessage,
    toastType,
    show,
    hide
  }
}
