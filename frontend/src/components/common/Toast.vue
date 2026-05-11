<script setup lang="ts">
import { ref, watch } from 'vue'
import { CheckCircle, AlertCircle, X } from 'lucide-vue-next'

const props = defineProps<{
  message: string
  type: 'success' | 'error' | 'info'
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

watch(() => props.visible, (val) => {
  if (val) {
    setTimeout(() => {
      emit('close')
    }, 2000)
  }
})
</script>

<template>
  <Transition name="toast">
    <div
      v-if="visible"
      class="fixed top-4 right-4 z-[100] flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg max-w-sm"
      :class="{
        'bg-emerald-500/90 text-white': type === 'success',
        'bg-red-500/90 text-white': type === 'error',
        'bg-dark-700/90 text-dark-100 border border-dark-600': type === 'info'
      }"
    >
      <CheckCircle v-if="type === 'success'" :size="20" />
      <AlertCircle v-else-if="type === 'error'" :size="20" />
        <span v-else :size="20" />
        <span class="text-sm font-medium">{{ message }}</span>
        <button
          @click="emit('close')"
          class="ml-2 p-1 rounded hover:bg-white/20 transition-colors"
        >
          <X :size="14" />
        </button>
      </div>
  </Transition>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100px);
}
</style>
