<template>
  <div class="test-view">
    <div class="view-header">
      <div>
        <h1>📝 Daily Test</h1>
        <p class="header-sub">Spaced repetition — {{ dueCount }} topics due today</p>
      </div>
      <button id="refresh-daily-btn" class="btn btn-secondary" @click="loadDaily" :disabled="store.loading">
        <span v-if="store.loading" class="spinner" style="width:14px;height:14px"></span>
        <span v-else>🔄</span>
        Refresh
      </button>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="loading-state">
      <div class="spinner spinner-lg" style="margin:0 auto 16px"></div>
      <p>Loading today's questions...</p>
    </div>

    <!-- No questions due -->
    <div v-else-if="!store.questions.length" class="empty-state" style="flex:1">
      <div class="icon">🎉</div>
      <h3>All caught up!</h3>
      <p>No topics are due for revision today. Come back tomorrow, or browse any topic to practice.</p>
    </div>

    <!-- Quiz -->
    <div v-else class="daily-quiz-wrap">
      <!-- Tabs for due topics -->
      <div class="q-header">
        <div class="quiz-progress">
          <span class="qp-text">Question {{ store.currentIndex + 1 }} of {{ store.totalQuestions }}</span>
          <div class="progress-bar" style="width:200px">
            <div class="progress-fill" :style="`width:${(store.answeredCount/store.totalQuestions)*100}%`"></div>
          </div>
          <span class="qp-score" v-if="store.answeredCount">{{ store.score.pct }}%</span>
        </div>
      </div>

      <!-- Use TestPanel for the quiz UI -->
      <div class="daily-test-panel">
        <div class="question-area" v-if="currentQ">
          <div class="card question-card fade-in" :key="store.currentIndex">
            <div class="q-meta">
              <span class="badge badge-teal" style="font-size:0.7rem">{{ currentQ.topic_title }}</span>
              <span class="badge" :class="diffBadge(currentQ.difficulty)">{{ currentQ.difficulty }}</span>
            </div>
            <div class="question-text">{{ currentQ.question }}</div>

            <div class="options-list">
              <button
                v-for="(optText, optKey) in currentQ.options"
                :key="optKey"
                class="option-btn"
                :class="optionClass(optKey, currentQ._id)"
                :disabled="!!store.answers[currentQ._id]"
                @click="selectAnswer(currentQ._id, optKey)"
                :id="`daily-opt-${optKey}`"
              >
                <span class="option-label">{{ optKey }}</span>
                <span class="option-text">{{ optText }}</span>
              </button>
            </div>

            <Transition name="slide-up">
              <div v-if="store.answers[currentQ._id]" class="explanation-block">
                <div class="exp-header" :class="store.answers[currentQ._id].isCorrect ? 'correct' : 'wrong'">
                  <span>{{ store.answers[currentQ._id].isCorrect ? '✅' : '❌' }}</span>
                  <span class="exp-label">{{ store.answers[currentQ._id].isCorrect ? 'Correct!' : 'Incorrect' }}</span>
                  <span v-if="!store.answers[currentQ._id].isCorrect" class="exp-correct">
                    Correct: <strong>{{ store.answers[currentQ._id].result?.correct_answer }}</strong>
                  </span>
                </div>
                <div class="exp-text">{{ store.answers[currentQ._id].result?.explanation }}</div>
              </div>
            </Transition>
          </div>

          <div class="nav-btns">
            <button class="btn btn-secondary" @click="store.prevQuestion()" :disabled="store.currentIndex === 0">← Previous</button>
            <button
              v-if="store.currentIndex < store.totalQuestions - 1"
              class="btn btn-primary"
              @click="store.nextQuestion()"
            >Next →</button>
            <button v-else class="btn btn-primary" @click="showResults = true" id="finish-daily-btn">Finish ✓</button>
          </div>
        </div>
      </div>

      <!-- Results overlay -->
      <Transition name="fade">
        <div v-if="showResults" class="results-overlay">
          <div class="results-card card-glass fade-in-up">
            <div class="results-icon">{{ store.score.pct >= 80 ? '🏆' : '👍' }}</div>
            <h2>Session Complete!</h2>
            <div class="big-score" :class="store.score.pct >= 60 ? 'good' : 'bad'">{{ store.score.pct }}%</div>
            <div class="score-detail">{{ store.score.correct }} / {{ store.score.total }} correct</div>
            <button class="btn btn-primary" @click="loadDaily" style="margin-top:8px">Done</button>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTestStore } from '@/stores/test'

const store = useTestStore()
const showResults = ref(false)
const dueCount = computed(() => store.dueCount)
const currentQ = computed(() => store.currentQuestion)

onMounted(() => loadDaily())

async function loadDaily() {
  showResults.value = false
  await store.loadDaily()
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
</script>

<style scoped>
.test-view { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 24px 20px;
  border-bottom: 1px solid var(--border-default);
  flex-shrink: 0;
}
.view-header h1 { margin: 0; font-size: 1.5rem; }
.header-sub { font-size: 0.8rem; color: var(--teal-400); margin-top: 2px; }

.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.daily-quiz-wrap { flex: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }
.q-header {
  padding: 14px 24px;
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-secondary);
  flex-shrink: 0;
}
.quiz-progress { display: flex; align-items: center; gap: 16px; }
.qp-text { font-size: 0.85rem; color: var(--text-muted); }
.qp-score { font-weight: 700; color: var(--teal-400); }

.daily-test-panel { flex: 1; overflow-y: auto; }
.question-area { padding: 24px; display: flex; flex-direction: column; gap: 16px; }

.question-card { display: flex; flex-direction: column; gap: 16px; }
.q-meta { display: flex; gap: 8px; align-items: center; }
.question-text { font-size: 1rem; font-weight: 500; line-height: 1.7; }
.options-list { display: flex; flex-direction: column; gap: 10px; }
.option-text { flex: 1; line-height: 1.5; }

.explanation-block {
  background: var(--bg-input);
  border-radius: var(--radius-md);
  padding: 16px;
  border: 1px solid var(--border-default);
}
.exp-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.exp-header.correct .exp-label { color: var(--green-400); font-weight: 700; }
.exp-header.wrong .exp-label { color: var(--red-400); font-weight: 700; }
.exp-correct { color: var(--text-muted); font-size: 0.85rem; margin-left: auto; }
.exp-text { font-size: 0.875rem; color: var(--text-secondary); line-height: 1.7; }

.nav-btns { display: flex; justify-content: space-between; }

.results-overlay {
  position: absolute;
  inset: 0;
  background: rgba(10,15,30,0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}
.results-card {
  max-width: 380px;
  width: 90%;
  text-align: center;
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.results-icon { font-size: 3.5rem; }
.big-score { font-size: 3rem; font-weight: 800; }
.big-score.good { color: var(--green-400); }
.big-score.bad { color: var(--red-400); }
.score-detail { color: var(--text-secondary); }

.slide-up-enter-active { transition: all 0.3s ease; }
.slide-up-enter-from { opacity: 0; transform: translateY(12px); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
