<template>
  <div class="test-panel">
    <!-- Loading -->
    <div v-if="loading" class="loading-state fade-in">
      <div class="spinner spinner-lg" style="margin:0 auto 16px"></div>
      <p>Generating questions...</p>
    </div>

    <!-- No questions -->
    <div v-else-if="!store.questions.length" class="empty-state">
      <div class="icon">📝</div>
      <h3>Ready to test?</h3>
      <p>Generate questions for this topic to start practicing for your NEXT exam.</p>
      <div class="gen-controls">
        <div class="control-row">
          <label class="control-label">Questions</label>
          <div class="count-btns">
            <button v-for="n in [3,5,10]" :key="n" class="count-btn" :class="{active: genCount===n}" @click="genCount=n">{{ n }}</button>
          </div>
        </div>
        <div class="control-row">
          <label class="control-label">Difficulty</label>
          <div class="count-btns">
            <button v-for="d in ['Easy','Mixed','Hard']" :key="d" class="count-btn" :class="{active: genDiff===d}" @click="genDiff=d">{{ d }}</button>
          </div>
        </div>
        <button id="gen-test-btn" class="btn btn-primary" @click="generateTest">
          🎯 Generate Test
        </button>
      </div>
    </div>

    <!-- Quiz interface -->
    <div v-else class="quiz-wrap">
      <!-- Progress bar -->
      <div class="quiz-header">
        <div class="quiz-meta">
          <span class="quiz-counter">{{ store.currentIndex + 1 }} / {{ store.totalQuestions }}</span>
          <span class="badge" :class="diffBadge(currentQ?.difficulty)">{{ currentQ?.difficulty }}</span>
          <span v-if="currentQ?.section" class="badge badge-teal" style="font-size:0.7rem">{{ currentQ.section }}</span>
        </div>
        <div class="quiz-score" v-if="store.answeredCount > 0">
          <span class="score-text">Score: {{ store.score.correct }}/{{ store.score.total }}</span>
          <span class="score-pct" :class="store.score.pct >= 60 ? 'good' : 'bad'">{{ store.score.pct }}%</span>
        </div>
      </div>
      <div class="progress-bar" style="margin:0 24px">
        <div class="progress-fill" :style="`width:${((store.currentIndex) / store.totalQuestions) * 100}%`"></div>
      </div>

      <!-- Question card -->
      <div class="question-area" v-if="currentQ">
        <div class="card question-card fade-in" :key="store.currentIndex">
          <div class="question-text">{{ currentQ.question }}</div>

          <!-- Options -->
          <div class="options-list">
            <button
              v-for="(optText, optKey) in currentQ.options"
              :key="optKey"
              class="option-btn"
              :class="optionClass(optKey, currentQ._id)"
              :disabled="!!answers[currentQ._id]"
              @click="selectAnswer(currentQ._id, optKey)"
              :id="`option-${optKey}`"
            >
              <span class="option-label">{{ optKey }}</span>
              <span class="option-text">{{ optText }}</span>
            </button>
          </div>

          <!-- Explanation (after answering) -->
          <Transition name="slide-up">
            <div v-if="answers[currentQ._id]" class="explanation-block">
              <div class="exp-header" :class="answers[currentQ._id].isCorrect ? 'correct' : 'wrong'">
                <span class="exp-icon">{{ answers[currentQ._id].isCorrect ? '✅' : '❌' }}</span>
                <span class="exp-label">{{ answers[currentQ._id].isCorrect ? 'Correct!' : 'Incorrect' }}</span>
                <span v-if="!answers[currentQ._id].isCorrect" class="exp-correct">
                  Correct: <strong>{{ answers[currentQ._id].result?.correct_answer }}</strong>
                </span>
              </div>
              <div class="exp-text">{{ answers[currentQ._id].result?.explanation }}</div>
              <div v-if="currentQ.page_reference" class="exp-ref">
                📚 Reference: {{ currentQ.page_reference }}
              </div>
            </div>
          </Transition>
        </div>

        <!-- Navigation -->
        <div class="nav-btns">
          <button class="btn btn-secondary" @click="store.prevQuestion()" :disabled="store.currentIndex === 0" id="prev-q-btn">
            ← Previous
          </button>
          <button
            v-if="store.currentIndex < store.totalQuestions - 1"
            class="btn btn-primary"
            @click="store.nextQuestion()"
            id="next-q-btn"
          >
            Next →
          </button>
          <button v-else class="btn btn-primary" @click="showResults = true" id="finish-btn">
            Finish ✓
          </button>
        </div>
      </div>

      <!-- Results overlay -->
      <Transition name="fade">
        <div v-if="showResults" class="results-overlay">
          <div class="results-card card-glass fade-in-up">
            <div class="results-icon">{{ store.score.pct >= 80 ? '🏆' : store.score.pct >= 60 ? '👍' : '📖' }}</div>
            <h2>Test Complete!</h2>
            <div class="results-score">
              <span class="big-score" :class="store.score.pct >= 60 ? 'good' : 'bad'">{{ store.score.pct }}%</span>
              <span class="score-detail">{{ store.score.correct }} / {{ store.score.total }} correct</span>
            </div>
            <p class="results-msg">{{ resultsMessage }}</p>
            <div class="results-actions">
              <button class="btn btn-primary" @click="retryTest">🔄 Try Again</button>
              <button class="btn btn-secondary" @click="generateTest">📝 New Questions</button>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useTestStore } from '@/stores/test'

const props = defineProps({ topicId: String, topicTitle: String })
const store = useTestStore()

const loading = ref(false)
const showResults = ref(false)
const genCount = ref(5)
const genDiff = ref('Mixed')
const answers = computed(() => store.answers)
const currentQ = computed(() => store.currentQuestion)

const resultsMessage = computed(() => {
  const p = store.score.pct
  if (p === 100) return "Perfect score! You've mastered this topic! 🌟"
  if (p >= 80) return "Excellent work! You have a strong grasp of this topic."
  if (p >= 60) return "Good effort! Review the questions you missed."
  return "Keep studying! Focus on the explanations for incorrect answers."
})

async function generateTest() {
  loading.value = true
  showResults.value = false
  try {
    await store.generateForTopic(props.topicId, genCount.value, genDiff.value)
  } finally {
    loading.value = false
  }
}

async function selectAnswer(qId, answer) {
  if (store.answers[qId]) return
  await store.submitAnswer(qId, answer)
}

function optionClass(optKey, qId) {
  const ans = store.answers[qId]
  if (!ans) return ''
  if (optKey === ans.result?.correct_answer) return 'correct'
  if (optKey === ans.selected) return 'wrong'
  return ''
}

function diffBadge(d) {
  if (!d) return 'badge-teal'
  if (d === 'Easy') return 'badge-green'
  if (d === 'Hard') return 'badge-red'
  return 'badge-gold'
}

function retryTest() {
  store.reset()
  showResults.value = false
  store.questions = [...store.questions]
  store.currentIndex = 0
  store.answers = {}
}

watch(() => props.topicId, () => {
  store.reset()
  showResults.value = false
})
</script>

<style scoped>
.test-panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; position: relative; }

.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.gen-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
  align-items: center;
  width: 100%;
  max-width: 320px;
}
.control-row { display: flex; align-items: center; gap: 16px; width: 100%; }
.control-label { font-size: 0.8rem; color: var(--text-muted); min-width: 80px; font-weight: 600; }
.count-btns { display: flex; gap: 6px; }
.count-btn {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
  background: var(--bg-input);
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: var(--transition);
}
.count-btn.active { border-color: var(--teal-500); color: var(--teal-400); background: rgba(20,184,166,0.1); }

/* Quiz */
.quiz-wrap { display: flex; flex-direction: column; height: 100%; }
.quiz-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px 12px;
  flex-shrink: 0;
}
.quiz-meta { display: flex; align-items: center; gap: 10px; }
.quiz-counter { font-weight: 700; font-size: 0.9rem; color: var(--text-secondary); }
.quiz-score { display: flex; align-items: center; gap: 8px; }
.score-text { font-size: 0.85rem; color: var(--text-muted); }
.score-pct { font-weight: 800; font-size: 1rem; }
.score-pct.good { color: var(--green-400); }
.score-pct.bad { color: var(--red-400); }

.question-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-card { display: flex; flex-direction: column; gap: 20px; }
.question-text { font-size: 1rem; font-weight: 500; line-height: 1.7; color: var(--text-primary); }
.options-list { display: flex; flex-direction: column; gap: 10px; }

.option-text { flex: 1; line-height: 1.5; }

/* Explanation */
.explanation-block {
  background: var(--bg-input);
  border-radius: var(--radius-md);
  padding: 16px;
  border: 1px solid var(--border-default);
}
.exp-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.exp-header.correct .exp-label { color: var(--green-400); font-weight: 700; }
.exp-header.wrong .exp-label { color: var(--red-400); font-weight: 700; }
.exp-correct { color: var(--text-muted); font-size: 0.85rem; margin-left: auto; }
.exp-text { font-size: 0.875rem; color: var(--text-secondary); line-height: 1.7; }
.exp-ref { font-size: 0.8rem; color: var(--gold-400); margin-top: 8px; font-style: italic; }

.nav-btns { display: flex; justify-content: space-between; gap: 12px; }

/* Results overlay */
.results-overlay {
  position: absolute;
  inset: 0;
  background: rgba(10,15,30,0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
  padding: 24px;
}
.results-card {
  max-width: 400px;
  width: 100%;
  text-align: center;
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.results-icon { font-size: 3.5rem; }
.results-score { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.big-score { font-size: 3rem; font-weight: 800; }
.big-score.good { color: var(--green-400); }
.big-score.bad { color: var(--red-400); }
.score-detail { font-size: 1rem; color: var(--text-secondary); }
.results-msg { color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6; }
.results-actions { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }

/* Animations */
.slide-up-enter-active { transition: all 0.3s ease; }
.slide-up-enter-from { opacity: 0; transform: translateY(12px); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
