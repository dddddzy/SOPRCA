<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import Toast from '@/components/common/Toast.vue'
import { useToast } from '@/composables/useToast'

const { toastVisible, toastMessage, toastType, hide } = useToast()
</script>

<template>
  <div class="flex h-full overflow-hidden bg-dark-900">
    <!-- Sidebar -->
    <AppSidebar class="flex-shrink-0" />

    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden min-w-0">
      <AppHeader class="flex-shrink-0" />
      <main class="flex-1 overflow-auto p-6 bg-dark-900 min-h-0">
        <RouterView v-slot="{ Component }">
          <KeepAlive include="KnowledgeQA">
            <component :is="Component" />
          </KeepAlive>
        </RouterView>
      </main>
    </div>

    <!-- Toast Notification -->
    <Toast
      :visible="toastVisible"
      :message="toastMessage"
      :type="toastType"
      @close="hide"
    />
  </div>
</template>
