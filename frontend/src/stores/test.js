import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useTestStore = defineStore('test', () => {
  const questions = ref([])
  const currentIndex = ref(0)
  const answers = ref({})  // questionId -> { selected, isCorrect, result }
  const loading = ref(false)
  const progress = ref(null)
  const dueCount = ref(0)

  const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
  const totalQuestions = computed(() => questions.value.length)
  const answeredCount = computed(() => Object.keys(answers.value).length)
  const score = computed(() => {
    const vals = Object.values(answers.value)
    const correct = vals.filter(a => a.isCorrect).length
    return { correct, total: vals.length, pct: vals.length ? Math.round(correct/vals.length*100) : 0 }
  })
  const isFinished = computed(() => answeredCount.value >= totalQuestions.value && totalQuestions.value > 0)

  function reset() {
    questions.value = []
    currentIndex.value = 0
    answers.value = {}
  }

  async function generateForTopic(topicId, count = 5, difficulty = 'Mixed') {
    loading.value = true
    reset()
    try {
      const res = await api.generateTest({ topic_id: topicId, count, difficulty })
      questions.value = res.questions || []
    } finally {
      loading.value = false
    }
  }

  async function loadDaily() {
    loading.value = true
    reset()
    try {
      const res = await api.getDailyQuestions()
      questions.value = res.questions || []
      dueCount.value = res.due_count || 0
    } finally {
      loading.value = false
    }
  }

  async function submitAnswer(questionId, selected) {
    const res = await api.submitAnswer({ question_id: questionId, selected_answer: selected })
    answers.value[questionId] = {
      selected,
      isCorrect: res.is_correct,
      result: res
    }
    return res
  }

  function nextQuestion() {
    if (currentIndex.value < questions.value.length - 1) currentIndex.value++
  }

  function prevQuestion() {
    if (currentIndex.value > 0) currentIndex.value--
  }

  async function fetchProgress() {
    progress.value = await api.getProgress()
  }

  return {
    questions, currentIndex, answers, loading, progress, dueCount,
    currentQuestion, totalQuestions, answeredCount, score, isFinished,
    reset, generateForTopic, loadDaily, submitAnswer, nextQuestion, prevQuestion, fetchProgress
  }
})
