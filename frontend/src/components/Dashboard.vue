<template>
  <div class="dashboard">
    <!-- Hero Stats Row -->
    <div class="stats-grid fade-in">
      <div class="stat-card card" id="stat-accuracy">
        <div class="stat-icon">🎯</div>
        <div class="stat-body">
          <div class="stat-value" :class="progress?.overall_accuracy >= 60 ? 'good' : 'warn'">
            {{ progress?.overall_accuracy ?? '—' }}<span v-if="progress" class="stat-unit">%</span>
          </div>
          <div class="stat-label">Overall Accuracy</div>
        </div>
      </div>
      <div class="stat-card card" id="stat-streak">
        <div class="stat-icon">🔥</div>
        <div class="stat-body">
          <div class="stat-value gold">{{ progress?.streak_days ?? '—' }}</div>
          <div class="stat-label">Day Streak</div>
        </div>
      </div>
      <div class="stat-card card" id="stat-due">
        <div class="stat-icon">⏰</div>
        <div class="stat-body">
          <div class="stat-value" :class="(progress?.due_today ?? 0) > 0 ? 'warn' : 'good'">
            {{ progress?.due_today ?? '—' }}
          </div>
          <div class="stat-label">Due Today</div>
        </div>
      </div>
      <div class="stat-card card" id="stat-attempts">
        <div class="stat-icon">📝</div>
        <div class="stat-body">
          <div class="stat-value">{{ progress?.total_attempts ?? '—' }}</div>
          <div class="stat-label">Total Attempts</div>
        </div>
      </div>
    </div>

    <div class="dash-grid">
      <!-- Left column -->
      <div class="dash-left">
        <!-- Due Topics -->
        <div class="card section-card fade-in" style="animation-delay:0.1s" id="due-topics-card">
          <div class="section-hdr">
            <h3>⏰ Due for Revision</h3>
            <span class="badge badge-red" v-if="dueTopics.length">{{ dueTopics.length }}</span>
            <router-link to="/test" class="btn btn-primary btn-sm" v-if="dueTopics.length">Start Test</router-link>
          </div>
          <div v-if="loadingDue" class="loading-list">
            <div v-for="i in 3" :key="i" class="skeleton" style="height:48px;border-radius:8px;margin-bottom:6px"></div>
          </div>
          <div v-else-if="!dueTopics.length" class="empty-mini">
            <span>🎉</span>
            <span>All caught up! No topics due today.</span>
          </div>
          <div v-else class="due-list">
            <div
              v-for="t in dueTopics.slice(0, 8)"
              :key="t.topic_id"
              class="due-item"
              @click="$router.push(`/topic/${t.topic_id}`)"
            >
              <div class="due-info">
                <div class="due-title">{{ t.topic_title }}</div>
                <div class="due-meta">
                  <span class="badge badge-teal" style="font-size:0.65rem">{{ t.system }}</span>
                  <span class="due-date">Due: {{ t.next_due_date }}</span>
                </div>
              </div>
              <div class="due-acc">
                {{ topicAccuracy(t) }}<span style="font-size:0.7rem;color:var(--text-muted)">%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Calendar Heatmap -->
        <div class="card section-card fade-in" style="animation-delay:0.2s" id="calendar-card">
          <div class="section-hdr"><h3>📅 Activity</h3></div>
          <div v-if="!calendar.length" class="empty-mini">
            <span>📅</span><span>No activity yet. Start studying!</span>
          </div>
          <div v-else class="heatmap-wrap">
            <div class="heatmap">
              <div
                v-for="day in calendarPadded"
                :key="day.date || day.empty"
                class="heat-cell"
                :class="heatClass(day)"
                :data-tooltip="day.date ? `${day.date}: ${day.count || 0} attempts` : ''"
              ></div>
            </div>
            <div class="heat-legend">
              <span style="color:var(--text-muted);font-size:0.7rem">Less</span>
              <div class="heat-cell heat-0"></div>
              <div class="heat-cell heat-1"></div>
              <div class="heat-cell heat-2"></div>
              <div class="heat-cell heat-3"></div>
              <div class="heat-cell heat-4"></div>
              <span style="color:var(--text-muted);font-size:0.7rem">More</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right column -->
      <div class="dash-right">
        <!-- System accuracy -->
        <div class="card section-card fade-in" style="animation-delay:0.15s" id="system-acc-card">
          <div class="section-hdr"><h3>📊 Accuracy by System</h3></div>
          <div v-if="!systemStats.length" class="empty-mini">
            <span>📊</span><span>Complete some tests to see system stats</span>
          </div>
          <div v-else class="system-list">
            <div v-for="sys in systemStats" :key="sys.name" class="system-row">
              <div class="sys-name-wrap">
                <span class="sys-icon">{{ systemIcon(sys.name) }}</span>
                <span class="sys-name">{{ sys.name }}</span>
                <span class="sys-count">({{ sys.topics }} topics)</span>
              </div>
              <div class="sys-bar-wrap">
                <div class="progress-bar sys-bar">
                  <div class="progress-fill" :style="`width:${sys.accuracy}%; background:${accColor(sys.accuracy)}`"></div>
                </div>
                <span class="sys-pct" :style="`color:${accColor(sys.accuracy)}`">{{ sys.accuracy }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick access -->
        <div class="card section-card fade-in" style="animation-delay:0.25s" id="quick-access-card">
          <div class="section-hdr"><h3>⚡ Quick Access</h3></div>
          <div class="quick-links">
            <router-link to="/test" class="quick-link" id="quick-daily-test">
              <span class="ql-icon">📝</span>
              <div>
                <div class="ql-title">Daily Test</div>
                <div class="ql-sub">{{ progress?.due_today || 0 }} topics due</div>
              </div>
            </router-link>
            <div class="quick-link" @click="handleBrowse" id="quick-browse">
              <span class="ql-icon">📚</span>
              <div>
                <div class="ql-title">Browse Topics</div>
                <div class="ql-sub">Use the sidebar</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useTopicsStore } from '@/stores/topics'

const topicsStore = useTopicsStore()

const progress = ref(null)
const dueTopics = ref([])
const calendar = ref([])
const loadingDue = ref(true)

function handleBrowse() {
  topicsStore.isSidebarCollapsed = false
  setTimeout(() => {
    const searchInput = document.getElementById('sidebar-search')
    if (searchInput) {
      searchInput.focus()
      const searchBox = searchInput.closest('.search-box')
      if (searchBox) {
        searchBox.classList.add('highlight-flash')
        setTimeout(() => searchBox.classList.remove('highlight-flash'), 1000)
      }
    }
  }, 100)
}

const systemStats = computed(() => {
  if (!progress.value?.system_stats) return []
  return Object.entries(progress.value.system_stats)
    .map(([name, s]) => ({ name, ...s }))
    .sort((a, b) => b.topics - a.topics)
    .slice(0, 10)
})

const calendarPadded = computed(() => {
  if (!calendar.value.length) return []
  // Build last 90 days map
  const map = {}
  for (const d of calendar.value) map[d.date] = d
  const days = []
  const today = new Date()
  for (let i = 89; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    days.push(map[key] || { date: key, count: 0, correct: 0 })
  }
  return days
})

onMounted(async () => {
  try { progress.value = await api.getProgress() } catch {}
  try { const res = await api.getDueTopics(); dueTopics.value = res.due_topics || [] } catch {}
  try { const res = await api.getCalendar(); calendar.value = res.calendar || [] } catch {}
  loadingDue.value = false
})

function topicAccuracy(t) {
  const h = t.accuracy_history || []
  if (!h.length) return '—'
  const c = h.filter(x => x.correct).length
  return Math.round(c / h.length * 100)
}

function heatClass(day) {
  if (!day.count) return 'heat-0'
  if (day.count >= 20) return 'heat-4'
  if (day.count >= 10) return 'heat-3'
  if (day.count >= 5) return 'heat-2'
  return 'heat-1'
}

function accColor(pct) {
  if (pct >= 80) return 'var(--green-400)'
  if (pct >= 60) return 'var(--gold-400)'
  return 'var(--red-400)'
}

function systemIcon(s) {
  const icons = {
    Cardiology: '❤️', Cardiovascular: '❤️', Respiratory: '🫁', Nephrology: '🫘',
    Neurology: '🧠', Gastroenterology: '🫃', Endocrinology: '⚗️',
    'Infectious Diseases': '🦠', Hematology: '🩸', Rheumatology: '🦴',
  }
  for (const [k, v] of Object.entries(icons)) {
    if (s && s.toLowerCase().includes(k.toLowerCase())) return v
  }
  return '📋'
}
</script>

<style scoped>
.dashboard { padding: 24px; display: flex; flex-direction: column; gap: 20px; height: 100%; overflow-y: auto; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  transition: var(--transition);
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-teal); }
.stat-icon { font-size: 1.8rem; }
.stat-value { font-size: 2rem; font-weight: 800; line-height: 1; }
.stat-value.good { color: var(--green-400); }
.stat-value.warn { color: var(--gold-400); }
.stat-value.gold { color: var(--gold-400); }
.stat-unit { font-size: 1rem; font-weight: 400; }
.stat-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; font-weight: 500; }

.dash-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  flex: 1;
}
.dash-left, .dash-right { display: flex; flex-direction: column; gap: 16px; }

.section-card { padding: 20px; }
.section-hdr {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.section-hdr h3 { font-size: 0.95rem; font-weight: 700; flex: 1; }
.btn-sm { padding: 6px 12px; font-size: 0.75rem; }

.empty-mini {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-muted);
  font-size: 0.85rem;
  padding: 12px 0;
}

/* Due list */
.due-list { display: flex; flex-direction: column; gap: 6px; }
.due-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition);
}
.due-item:hover { background: var(--bg-card-hover); }
.due-info { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.due-title { font-size: 0.85rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.due-meta { display: flex; align-items: center; gap: 8px; }
.due-date { font-size: 0.7rem; color: var(--text-muted); }
.due-acc { font-size: 1.1rem; font-weight: 700; color: var(--teal-400); min-width: 40px; text-align: right; }

/* Heatmap */
.heatmap-wrap { display: flex; flex-direction: column; gap: 10px; }
.heatmap {
  display: grid;
  grid-template-columns: repeat(13, 1fr);
  gap: 3px;
}
.heat-cell { width: 100%; aspect-ratio: 1; border-radius: 2px; }
.heat-0 { background: var(--bg-input); }
.heat-1 { background: rgba(20,184,166,0.25); }
.heat-2 { background: rgba(20,184,166,0.45); }
.heat-3 { background: rgba(20,184,166,0.7); }
.heat-4 { background: var(--teal-400); }
.heat-legend { display: flex; align-items: center; gap: 4px; justify-content: flex-end; }

/* System bars */
.system-list { display: flex; flex-direction: column; gap: 12px; }
.system-row { display: flex; flex-direction: column; gap: 6px; }
.sys-name-wrap { display: flex; align-items: center; gap: 8px; }
.sys-icon { font-size: 0.9rem; }
.sys-name { font-size: 0.85rem; font-weight: 600; flex: 1; }
.sys-count { font-size: 0.7rem; color: var(--text-muted); }
.sys-bar-wrap { display: flex; align-items: center; gap: 10px; }
.sys-bar { flex: 1; }
.sys-pct { font-size: 0.8rem; font-weight: 700; min-width: 36px; text-align: right; }

/* Quick links */
.quick-links { display: flex; flex-direction: column; gap: 8px; }
.quick-link {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: var(--bg-input);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--text-primary);
  cursor: pointer;
  transition: var(--transition);
  border: 1px solid var(--border-default);
}
.quick-link:hover { border-color: var(--teal-500); background: rgba(20,184,166,0.08); }
.ql-icon { font-size: 1.5rem; }
.ql-title { font-weight: 600; font-size: 0.9rem; }
.ql-sub { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

@media (max-width: 1100px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .dash-grid { grid-template-columns: 1fr; }
}
</style>
