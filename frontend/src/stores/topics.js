import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useTopicsStore = defineStore('topics', () => {
  const chapters = ref([])
  const topics = ref([])
  const currentTopic = ref(null)
  const loading = ref(false)
  const searchResults = ref([])
  const searchQuery = ref('')
  const isSidebarCollapsed = ref(false)

  const topicsByChapter = computed(() => {
    const map = {}
    for (const t of topics.value) {
      const ch = t.chapter || 'Other'
      if (!map[ch]) map[ch] = []
      map[ch].push(t)
    }
    return map
  })

  async function fetchChapters() {
    loading.value = true
    try {
      const res = await api.getChapters()
      chapters.value = res.chapters || []
    } finally {
      loading.value = false
    }
  }

  async function fetchTopics(params = {}) {
    loading.value = true
    try {
      const res = await api.getTopics(params)
      topics.value = res.topics || []
    } finally {
      loading.value = false
    }
  }

  async function fetchTopic(id) {
    loading.value = true
    try {
      currentTopic.value = await api.getTopic(id)
    } finally {
      loading.value = false
    }
  }

  async function search(q) {
    searchQuery.value = q
    if (!q || q.length < 2) { searchResults.value = []; return }
    const res = await api.searchTopics(q)
    searchResults.value = res.topics || []
  }

  return {
    chapters,
    topics,
    currentTopic,
    loading,
    searchResults,
    searchQuery,
    isSidebarCollapsed,
    topicsByChapter,
    fetchChapters,
    fetchTopics,
    fetchTopic,
    search
  }
})
