<template>
  <div class="case-panel">
    <!-- Header -->
    <div class="case-header">
      <div>
        <h2 class="case-title">🏥 Clinical Case</h2>
        <p class="case-subtitle">{{ topicTitle }}</p>
      </div>
      <div class="header-actions">
        <button id="new-case-btn" class="btn btn-secondary" @click="generateNew" :disabled="loading">
          <span v-if="loading" class="spinner" style="width:14px;height:14px"></span>
          <span v-else>🔄</span>
          New Case
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading && !caseData" class="loading-state fade-in">
      <div class="spinner spinner-lg" style="margin:0 auto 16px"></div>
      <p>Generating clinical case...</p>
      <p style="font-size:0.8rem;color:var(--text-muted)">This may take a moment</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="empty-state">
      <div class="icon">⚠️</div>
      <h3>Failed to generate case</h3>
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="generateNew">Try Again</button>
    </div>

    <!-- Case content -->
    <div v-else-if="caseData" class="case-content fade-in">

      <!-- Vignette Card -->
      <div class="card vignette-card">
        <div class="card-header-row">
          <span class="badge badge-blue">📋 Clinical Vignette</span>
        </div>

        <!-- Chief Complaint -->
        <div class="chief-complaint">
          <span class="cc-label">Chief Complaint</span>
          <p class="cc-text">{{ caseData.vignette?.chief_complaint }}</p>
        </div>

        <!-- History -->
        <div class="section-block">
          <h4 class="section-title">📝 History of Presenting Illness</h4>
          <p class="section-text">{{ caseData.vignette?.history }}</p>
        </div>

        <!-- Past History -->
        <div v-if="caseData.vignette?.past_history" class="section-block">
          <h4 class="section-title">📂 Past Medical History</h4>
          <p class="section-text">{{ caseData.vignette?.past_history }}</p>
        </div>

        <!-- Examination -->
        <div v-if="caseData.vignette?.examination" class="section-block">
          <h4 class="section-title">🩺 Physical Examination</h4>
          <div class="exam-grid">
            <div v-if="caseData.vignette.examination.vitals" class="exam-item">
              <span class="exam-label">Vitals</span>
              <span class="exam-value">{{ caseData.vignette.examination.vitals }}</span>
            </div>
            <div v-if="caseData.vignette.examination.general" class="exam-item">
              <span class="exam-label">General</span>
              <span class="exam-value">{{ caseData.vignette.examination.general }}</span>
            </div>
            <div v-if="caseData.vignette.examination.systemic" class="exam-item">
              <span class="exam-label">Systemic</span>
              <span class="exam-value">{{ caseData.vignette.examination.systemic }}</span>
            </div>
          </div>
          <div v-if="caseData.vignette.examination.specific_findings?.length" class="findings-list">
            <h5 class="findings-title">Specific Findings:</h5>
            <ul>
              <li v-for="f in caseData.vignette.examination.specific_findings" :key="f">{{ f }}</li>
            </ul>
          </div>
        </div>

        <!-- Investigations -->
        <div v-if="caseData.vignette?.investigations" class="section-block">
          <h4 class="section-title">🧪 Investigations</h4>
          <div class="inv-groups">
            <div v-if="caseData.vignette.investigations.bloods?.length" class="inv-group">
              <span class="inv-label">Blood Tests</span>
              <ul><li v-for="i in caseData.vignette.investigations.bloods" :key="i">{{ i }}</li></ul>
            </div>
            <div v-if="caseData.vignette.investigations.imaging?.length" class="inv-group">
              <span class="inv-label">Imaging</span>
              <ul><li v-for="i in caseData.vignette.investigations.imaging" :key="i">{{ i }}</li></ul>
            </div>
            <div v-if="caseData.vignette.investigations.special?.length" class="inv-group">
              <span class="inv-label">Special</span>
              <ul><li v-for="i in caseData.vignette.investigations.special" :key="i">{{ i }}</li></ul>
            </div>
          </div>
        </div>

        <!-- Questions -->
        <div v-if="caseData.questions?.length" class="section-block questions-block">
          <h4 class="section-title">❓ Questions</h4>
          <ol class="questions-list">
            <li v-for="q in caseData.questions" :key="q">{{ q }}</li>
          </ol>
          <button class="btn btn-secondary reveal-btn" @click="showAnswers = !showAnswers" id="reveal-answers-btn">
            {{ showAnswers ? '🙈 Hide Answers' : '👁️ Reveal Answers' }}
          </button>
        </div>
      </div>

      <!-- Answers (collapsible) -->
      <Transition name="expand">
        <div v-if="showAnswers" class="answers-section">

          <!-- Differentials -->
          <div v-if="caseData.differentials?.length" class="card differential-card">
            <div class="card-header-row">
              <span class="badge badge-purple">🔍 Differential Diagnosis</span>
            </div>
            <div class="differentials-list">
              <div
                v-for="diff in caseData.differentials"
                :key="diff.diagnosis"
                class="differential-item"
                :class="diff.likelihood === 'Most likely' ? 'most-likely' : ''"
              >
                <div class="diff-header">
                  <span class="diff-name">{{ diff.diagnosis }}</span>
                  <span class="badge" :class="likelihoodBadge(diff.likelihood)">{{ diff.likelihood }}</span>
                </div>
                <div class="diff-details">
                  <div v-if="diff.supporting_features?.length" class="diff-features">
                    <span class="feature-label for">✓ For:</span>
                    <span v-for="f in diff.supporting_features" :key="f" class="feature-tag for">{{ f }}</span>
                  </div>
                  <div v-if="diff.against_features?.length" class="diff-features">
                    <span class="feature-label against">✗ Against:</span>
                    <span v-for="f in diff.against_features" :key="f" class="feature-tag against">{{ f }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Final Diagnosis -->
          <div class="card diagnosis-card">
            <div class="diagnosis-banner">
              <span class="diagnosis-icon">✅</span>
              <div>
                <div class="diagnosis-label">Final Diagnosis</div>
                <div class="diagnosis-name">{{ caseData.final_diagnosis }}</div>
              </div>
            </div>
            <p class="diagnosis-explanation">{{ caseData.explanation }}</p>
          </div>

          <!-- References -->
          <div v-if="caseData.references?.length" class="card references-card">
            <div class="card-header-row">
              <span class="badge badge-gold">📚 Textbook References</span>
            </div>
            <div class="references-list">
              <div v-for="ref in caseData.references" :key="ref.page" class="ref-item">
                <div class="ref-section">{{ ref.section }}</div>
                <div class="ref-page">Page {{ ref.page }}</div>
                <div v-if="ref.note" class="ref-note">{{ ref.note }}</div>
              </div>
            </div>
          </div>

          <!-- Key Learning Points -->
          <div v-if="caseData.key_learning_points?.length" class="card learning-card">
            <div class="card-header-row">
              <span class="badge badge-teal">⭐ Key Learning Points</span>
            </div>
            <ul class="learning-list">
              <li v-for="pt in caseData.key_learning_points" :key="pt">{{ pt }}</li>
            </ul>
          </div>
        </div>
      </Transition>

    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <div class="icon">🏥</div>
      <h3>No case generated yet</h3>
      <p>Generate a clinical case for this topic to practice diagnosis and management.</p>
      <button id="gen-case-btn" class="btn btn-primary" @click="generateNew">Generate Case</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '@/api'

const props = defineProps({ topicId: String, topicTitle: String })
const caseData = ref(null)
const loading = ref(false)
const error = ref(null)
const showAnswers = ref(false)

async function generateNew() {
  loading.value = true
  error.value = null
  showAnswers.value = false
  try {
    caseData.value = await api.generateCase(props.topicId, true)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// Load existing case on mount
async function loadCase() {
  loading.value = true
  error.value = null
  try {
    caseData.value = await api.generateCase(props.topicId, false)
  } catch (e) {
    error.value = null // Just show empty state
    caseData.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.topicId, () => {
  caseData.value = null
  showAnswers.value = false
  if (props.topicId) loadCase()
}, { immediate: true })

function likelihoodBadge(l) {
  if (!l) return 'badge-teal'
  if (l.includes('Most')) return 'badge-green'
  if (l.includes('Possible')) return 'badge-gold'
  return 'badge-teal'
}
</script>

<style scoped>
.case-panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; }

.case-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-secondary);
  flex-shrink: 0;
}
.case-title { font-size: 1.1rem; font-weight: 700; margin: 0; }
.case-subtitle { font-size: 0.8rem; color: var(--teal-400); margin-top: 2px; }
.header-actions { display: flex; gap: 8px; }

.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  color: var(--text-secondary);
}

.case-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.vignette-card { display: flex; flex-direction: column; gap: 20px; }
.card-header-row { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }

.chief-complaint {
  background: rgba(20,184,166,0.06);
  border: 1px solid rgba(20,184,166,0.2);
  border-radius: var(--radius-md);
  padding: 16px;
}
.cc-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--teal-400); font-weight: 700; display: block; margin-bottom: 6px; }
.cc-text { font-size: 1.05rem; font-weight: 600; color: var(--text-primary); }

.section-block { display: flex; flex-direction: column; gap: 10px; }
.section-title { font-size: 0.9rem; font-weight: 600; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
.section-text { font-size: 0.875rem; color: var(--text-primary); line-height: 1.7; }

.exam-grid { display: flex; flex-direction: column; gap: 8px; }
.exam-item { display: flex; gap: 12px; }
.exam-label { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); min-width: 60px; padding-top: 2px; }
.exam-value { font-size: 0.875rem; color: var(--text-primary); line-height: 1.5; }
.findings-list { margin-top: 8px; }
.findings-title { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px; font-weight: 600; }
.findings-list ul { padding-left: 20px; }
.findings-list li { font-size: 0.875rem; color: var(--text-primary); margin: 4px 0; }

.inv-groups { display: flex; flex-direction: column; gap: 12px; }
.inv-group ul { padding-left: 20px; margin-top: 4px; }
.inv-group li { font-size: 0.875rem; color: var(--text-primary); margin: 3px 0; }
.inv-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); }

.questions-block { background: rgba(96, 165, 250, 0.06); border-radius: var(--radius-md); padding: 16px; border: 1px solid rgba(96,165,250,0.2); }
.questions-list { padding-left: 20px; display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
.questions-list li { font-size: 0.9rem; color: var(--text-primary); font-weight: 500; line-height: 1.5; }
.reveal-btn { align-self: flex-start; }

/* Differentials */
.differential-card {}
.differentials-list { display: flex; flex-direction: column; gap: 12px; margin-top: 8px; }
.differential-item {
  background: var(--bg-input);
  border-radius: var(--radius-md);
  padding: 14px;
  border: 1px solid var(--border-default);
  transition: var(--transition);
}
.differential-item.most-likely {
  border-color: rgba(34,197,94,0.4);
  background: rgba(34,197,94,0.05);
}
.diff-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.diff-name { font-weight: 600; font-size: 0.9rem; }
.diff-details { display: flex; flex-direction: column; gap: 6px; }
.diff-features { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.feature-label { font-size: 0.7rem; font-weight: 700; min-width: 60px; }
.feature-label.for { color: var(--green-400); }
.feature-label.against { color: var(--red-400); }
.feature-tag { padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; }
.feature-tag.for { background: rgba(34,197,94,0.1); color: var(--green-400); }
.feature-tag.against { background: rgba(239,68,68,0.1); color: var(--red-400); }

/* Diagnosis */
.diagnosis-card {}
.diagnosis-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 14px;
  background: rgba(34,197,94,0.08);
  border-radius: var(--radius-md);
  padding: 16px;
  border: 1px solid rgba(34,197,94,0.25);
}
.diagnosis-icon { font-size: 2rem; }
.diagnosis-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--green-400); font-weight: 700; }
.diagnosis-name { font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-top: 2px; }
.diagnosis-explanation { font-size: 0.875rem; color: var(--text-secondary); line-height: 1.7; }

/* References */
.references-list { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
.ref-item {
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  border-left: 3px solid var(--gold-400);
}
.ref-section { font-weight: 600; font-size: 0.875rem; }
.ref-page { font-size: 0.75rem; color: var(--gold-400); margin-top: 2px; }
.ref-note { font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; font-style: italic; }

/* Learning Points */
.learning-list { padding-left: 20px; display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.learning-list li { font-size: 0.875rem; color: var(--text-primary); line-height: 1.6; }

/* Expand transition */
.answers-section { display: flex; flex-direction: column; gap: 16px; }
.expand-enter-active, .expand-leave-active { transition: all 0.35s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
