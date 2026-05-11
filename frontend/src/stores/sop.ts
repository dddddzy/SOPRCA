import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SOP } from '@/types'

export const useSopStore = defineStore('sop', () => {
  const sops = ref<SOP[]>([])
  const loading = ref(false)
  const searchQuery = ref('')
  const statusFilter = ref<'all' | 'active' | 'draft' | 'archived'>('all')
  const typeFilter = ref<string>('all')

  const filteredSops = computed(() => {
    return sops.value.filter(sop => {
      const matchSearch = searchQuery.value === '' ||
        sop.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        sop.description.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        sop.faultType.toLowerCase().includes(searchQuery.value.toLowerCase())

      const matchStatus = statusFilter.value === 'all' || sop.status === statusFilter.value
      const matchType = typeFilter.value === 'all' || sop.faultType === typeFilter.value

      return matchSearch && matchStatus && matchType
    })
  })

  const faultTypes = computed(() => {
    return [...new Set(sops.value.map(s => s.faultType))]
  })

  async function fetchSops() {
    loading.value = true
    try {
      const response = await fetch('/api/sops')
      const data = await response.json()
      if (data.success) {
        sops.value = data.data
      }
    } catch (e) {
      console.error('Failed to fetch SOPs:', e)
    } finally {
      loading.value = false
    }
  }

  async function updateSop(id: string, sop: Partial<SOP>) {
    try {
      const response = await fetch(`/api/sops/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sop)
      })
      const data = await response.json()
      if (data.success) {
        await fetchSops()
        return true
      }
      return false
    } catch (e) {
      console.error('Failed to update SOP:', e)
      return false
    }
  }

  async function deleteSop(id: string) {
    try {
      const response = await fetch(`/api/sops/${id}`, {
        method: 'DELETE'
      })
      const data = await response.json()
      if (data.success) {
        sops.value = sops.value.filter(s => s.id !== id)
        return true
      }
      return false
    } catch (e) {
      console.error('Failed to delete SOP:', e)
      return false
    }
  }

  function setSearchQuery(query: string) {
    searchQuery.value = query
  }

  function setStatusFilter(status: 'all' | 'active' | 'draft' | 'archived') {
    statusFilter.value = status
  }

  function setTypeFilter(type: string) {
    typeFilter.value = type
  }

  function getSopById(id: string) {
    return sops.value.find(s => s.id === id)
  }

  return {
    sops,
    loading,
    searchQuery,
    statusFilter,
    typeFilter,
    filteredSops,
    faultTypes,
    fetchSops,
    updateSop,
    deleteSop,
    setSearchQuery,
    setStatusFilter,
    setTypeFilter,
    getSopById
  }
})