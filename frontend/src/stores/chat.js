import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const sessionId = ref(null)
  const streaming = ref(false)
  const streamingContent = ref('')
  const error = ref(null)

  const hasMessages = computed(() => messages.value.length > 0)

  function reset() {
    messages.value = []
    sessionId.value = null
    streaming.value = false
    streamingContent.value = ''
    error.value = null
  }

  async function loadSession(topicId, sessId) {
    try {
      const res = await api.getSession(topicId, sessId)
      messages.value = res.messages || []
      sessionId.value = sessId
    } catch {}
  }

  async function sendMessage(topicId, userText) {
    error.value = null
    // Add user message
    messages.value.push({ role: 'user', content: userText, timestamp: new Date().toISOString() })
    streaming.value = true
    streamingContent.value = ''

    try {
      const response = await api.explainStream(topicId, {
        query: userText,
        session_id: sessionId.value,
        stream: true
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      // Read SSE stream
      const newSessId = response.headers.get('X-Session-ID')
      if (newSessId) sessionId.value = newSessId

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) continue
          if (trimmed.startsWith('data: ')) {
            const chunk = trimmed.slice(6)
            if (chunk === '[DONE]') break
            try {
              streamingContent.value += JSON.parse(chunk)
            } catch (e) {
              streamingContent.value += chunk
            }
          }
        }
      }

      // Commit streamed message
      messages.value.push({
        role: 'assistant',
        content: streamingContent.value,
        timestamp: new Date().toISOString()
      })
      streamingContent.value = ''
    } catch (e) {
      error.value = e.message
      messages.value.push({
        role: 'error',
        content: `Error: ${e.message}`,
        timestamp: new Date().toISOString()
      })
    } finally {
      streaming.value = false
    }
  }

  return { messages, sessionId, streaming, streamingContent, error, hasMessages, reset, sendMessage, loadSession }
})
