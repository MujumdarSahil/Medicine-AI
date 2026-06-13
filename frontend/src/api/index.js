import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' }
})

// Request interceptor
api.interceptors.request.use(config => config, err => Promise.reject(err))

// Response interceptor
api.interceptors.response.use(
  res => res.data,
  err => {
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    return Promise.reject(new Error(msg))
  }
)

export default {
  // Chapters
  getChapters: () => api.get('/chapters'),
  getChapter: (id) => api.get(`/chapters/${id}`),

  // Topics
  getTopics: (params) => api.get('/topics', { params }),
  searchTopics: (q) => api.get('/topics/search', { params: { q } }),
  getTopic: (id) => api.get(`/topic/${id}`),

  // Explain (non-streaming)
  explainTopic: (topicId, body) => api.post(`/topic/${topicId}/explain`, body),
  getSessions: (topicId) => api.get(`/topic/${topicId}/sessions`),
  getSession: (topicId, sessionId) => api.get(`/topic/${topicId}/session/${sessionId}`),

  // Streaming explain (raw fetch)
  explainStream: (topicId, body) => {
    return fetch(`/api/topic/${topicId}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, stream: true })
    })
  },

  // Cases
  generateCase: (topicId, forceNew = false) =>
    api.post(`/topic/${topicId}/case`, null, { params: { force_new: forceNew } }),
  getCases: (topicId) => api.get(`/topic/${topicId}/cases`),
  getCase: (caseId) => api.get(`/cases/${caseId}`),

  // Tests
  generateTest: (body) => api.post('/test/generate', body),
  submitAnswer: (body) => api.post('/test/submit', body),
  getDailyQuestions: () => api.get('/test/daily'),
  getTopicQuestions: (topicId) => api.get(`/test/topic/${topicId}`),

  // Progress
  getProgress: () => api.get('/progress'),
  getDueTopics: () => api.get('/progress/due'),
  getTopicProgress: (topicId) => api.get(`/progress/topic/${topicId}`),
  getAttemptHistory: () => api.get('/progress/history'),
  getCalendar: () => api.get('/progress/calendar'),
}
