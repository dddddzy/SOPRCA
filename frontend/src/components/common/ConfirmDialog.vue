<script setup lang="ts">
import { RotateCcw, AlertTriangle } from 'lucide-vue-next'

defineProps<{
  visible: boolean
  title?: string
  message?: string
}>()

defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Transition name="modal">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('cancel')"></div>

      <!-- Modal -->
      <div class="relative bg-dark-800 border border-dark-600 rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
        <!-- Icon -->
        <div class="flex justify-center mb-4">
          <div class="p-3 bg-red-500/20 rounded-full">
            <AlertTriangle :size="32" class="text-red-400" />
          </div>
        </div>

        <!-- Title -->
        <h3 class="text-lg font-semibold text-dark-100 text-center mb-2">
          {{ title || '确认重置' }}
        </h3>

        <!-- Message -->
        <p class="text-sm text-dark-400 text-center mb-6">
          {{ message || '确定要重置所有设置吗？此操作不可撤销。' }}
        </p>

        <!-- Actions -->
        <div class="flex gap-3">
          <button
            @click="$emit('cancel')"
            class="flex-1 px-4 py-2.5 bg-dark-700 text-dark-200 rounded-lg hover:bg-dark-600 transition-colors font-medium"
          >
            取消
          </button>
          <button
            @click="$emit('confirm')"
            class="flex-1 px-4 py-2.5 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium flex items-center justify-center gap-2"
          >
            <RotateCcw :size="16" />
            确认重置
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from > div:last-child,
.modal-leave-to > div:last-child {
  transform: scale(0.95);
}
</style>