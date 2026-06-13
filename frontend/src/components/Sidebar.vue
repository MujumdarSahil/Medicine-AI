<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <!-- Header -->
    <div class="sidebar-header">
      <div class="logo" v-if="!isCollapsed">
        <span class="logo-icon">🩺</span>
        <div class="logo-text">
          <span class="logo-name">MedMentor</span>
          <span class="logo-sub">AI Tutor</span>
        </div>
      </div>
      <button class="collapse-btn btn btn-ghost" @click="isCollapsed = !isCollapsed" :title="isCollapsed ? 'Expand' : 'Collapse'">
        {{ isCollapsed ? '›' : '‹' }}
      </button>
    </div>

    <template v-if="!isCollapsed">
      <!-- Search -->
      <div class="search-wrap">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input
            id="sidebar-search"
            v-model="searchQ"
            class="input search-input"
            placeholder="Search topics..."
            @input="handleSearch"
            autocomplete="off"
          />
          <button v-if="searchQ" class="search-clear" @click="clearSearch">✕</button>
        </div>
        <!-- Search results -->
        <div v-if="store.searchResults.length" class="search-results card">
          <div
            v-for="t in store.searchResults"
            :key="t._id"
            class="search-result-item"
            @click="goTopic(t._id)"
          >
            <span class="result-title">{{ t.title }}</span>
            <span class="badge badge-teal" style="font-size:0.65rem">{{ t.system }}</span>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }" id="nav-home">
          <span class="nav-icon">🏠</span>
          <span>Dashboard</span>
        </router-link>
        <router-link to="/test" class="nav-link" :class="{ active: $route.path === '/test' }" id="nav-test">
          <span class="nav-icon">📝</span>
          <span>Daily Test</span>
          <span v-if="dueCount > 0" class="due-badge">{{ dueCount }}</span>
        </router-link>
      </nav>

      <div class="divider"></div>

      <!-- Chapter Tree -->
      <div class="chapter-section">
        <div class="section-label">CHAPTERS</div>
        <div v-if="store.loading" class="loading-chapters">
          <div v-for="i in 5" :key="i" class="skeleton" style="height:36px;margin-bottom:4px;border-radius:8px"></div>
        </div>
        <div v-else-if="!store.chapters.length" class="empty-state" style="padding:24px 0">
          <div class="icon" style="font-size:1.5rem">📚</div>
          <p>No chapters yet.<br>Run PDF ingestion first.</p>
        </div>
        <div v-else class="chapter-list">
          <div
            v-for="chapter in store.chapters"
            :key="chapter._id"
            class="chapter-item"
          >
            <button
              class="chapter-btn"
              :class="{ expanded: expandedChapters.has(chapter._id) }"
              @click="toggleChapter(chapter)"
              :id="`chapter-${chapter._id}`"
            >
              <span class="chapter-icon">{{ systemIcon(chapter.system) }}</span>
              <span class="chapter-name">{{ chapter.name }}</span>
              <span class="chapter-count">{{ (chapter.topics || []).length }}</span>
              <span class="chevron">{{ expandedChapters.has(chapter._id) ? '▾' : '▸' }}</span>
            </button>
            <!-- Topics list -->
            <Transition name="expand">
              <div v-if="expandedChapters.has(chapter._id)" class="topic-list">
                <div v-if="loadingTopics.has(chapter._id)" class="topic-loading">
                  <div v-for="i in 3" :key="i" class="skeleton" style="height:28px;margin-bottom:3px;border-radius:6px"></div>
                </div>
                <button
                  v-else
                  v-for="topic in chapterTopics[chapter._id] || []"
                  :key="topic._id"
                  class="topic-btn"
                  :class="{ active: $route.params.id === topic._id }"
                  @click="goTopic(topic._id)"
                  :id="`topic-${topic._id}`"
                >
                  <span class="topic-dot" :class="progressDot(topic._id)"></span>
                  <span class="topic-name">{{ topic.title }}</span>
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </template>

    <!-- Collapsed state icons -->
    <template v-else>
      <div class="collapsed-nav">
        <router-link to="/" class="nav-icon-btn" title="Dashboard">🏠</router-link>
        <router-link to="/test" class="nav-icon-btn" title="Daily Test">📝</router-link>
      </div>
    </template>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTopicsStore } from '@/stores/topics'
import { useTestStore } from '@/stores/test'
import api from '@/api'

const store = useTopicsStore()
const testStore = useTestStore()
const router = useRouter()
const route = useRoute()

const isCollapsed = computed({
  get: () => store.isSidebarCollapsed,
  set: (val) => { store.isSidebarCollapsed = val }
})
const searchQ = ref('')
const expandedChapters = ref(new Set())
const chapterTopics = ref({})
const loadingTopics = ref(new Set())
const progressCache = ref({})
const dueCount = ref(0)

onMounted(async () => {
  await store.fetchChapters()
  try {
    const res = await api.getDueTopics()
    dueCount.value = res.count || 0
  } catch {}
})

async function toggleChapter(chapter) {
  const id = chapter._id
  if (expandedChapters.value.has(id)) {
    expandedChapters.value.delete(id)
    expandedChapters.value = new Set(expandedChapters.value)
    return
  }
  expandedChapters.value.add(id)
  expandedChapters.value = new Set(expandedChapters.value)

  if (!chapterTopics.value[id]) {
    loadingTopics.value.add(id)
    loadingTopics.value = new Set(loadingTopics.value)
    try {
      const res = await api.getTopics({ chapter_id: id })
      chapterTopics.value[id] = res.topics || []
    } finally {
      loadingTopics.value.delete(id)
      loadingTopics.value = new Set(loadingTopics.value)
    }
  }
}

function goTopic(id) {
  store.searchResults.splice(0)
  searchQ.value = ''
  router.push(`/topic/${id}`)
}

let searchTimeout = null
function handleSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => store.search(searchQ.value), 300)
}
function clearSearch() {
  searchQ.value = ''
  store.search('')
}

function systemIcon(system) {
  const icons = {
    Cardiology: '❤️', Cardiovascular: '❤️',
    Respiratory: '🫁', Pulmonology: '🫁',
    Nephrology: '🫘', Renal: '🫘',
    Neurology: '🧠', Neurological: '🧠',
    Gastroenterology: '🫃', Gastrointestinal: '🫃',
    Endocrinology: '⚗️', Endocrine: '⚗️',
    'Infectious Diseases': '🦠', Infections: '🦠',
    Hematology: '🩸', Haematology: '🩸',
    Rheumatology: '🦴', Musculoskeletal: '🦴',
    Dermatology: '🧴', Psychiatry: '🧬',
    Oncology: '🔬', Immunology: '🛡️',
  }
  for (const [k, v] of Object.entries(icons)) {
    if (system && system.toLowerCase().includes(k.toLowerCase())) return v
  }
  return '📋'
}

function progressDot(topicId) {
  // green = reviewed, amber = due, grey = not started
  return 'dot-grey'
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.3s;
  position: relative;
  z-index: 10;
}
.sidebar.collapsed {
  width: 56px;
  min-width: 56px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px 16px;
  border-bottom: 1px solid var(--border-default);
  min-height: 72px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-icon { font-size: 1.6rem; }
.logo-text { display: flex; flex-direction: column; }
.logo-name { font-size: 1rem; font-weight: 800; color: var(--teal-400); line-height: 1.2; }
.logo-sub { font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; }

.collapse-btn {
  font-size: 1.2rem;
  padding: 6px 10px;
  border-radius: 8px;
  flex-shrink: 0;
}

.search-wrap { padding: 12px 12px 0; position: relative; }
.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-input);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  transition: var(--transition);
}
.search-box:focus-within { border-color: var(--teal-500); }
.search-box.highlight-flash {
  animation: highlight-flash 1s ease-out;
}
@keyframes highlight-flash {
  0% { box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.4); border-color: var(--teal-500); }
  50% { box-shadow: 0 0 0 8px rgba(20, 184, 166, 0.2); border-color: var(--teal-400); }
  100% { box-shadow: 0 0 0 0 rgba(20, 184, 166, 0); }
}
.search-icon { font-size: 0.85rem; flex-shrink: 0; }
.search-input {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.85rem;
  outline: none;
  flex: 1;
  color: var(--text-primary);
}
.search-input::placeholder { color: var(--text-muted); }
.search-clear {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0;
}
.search-results {
  position: absolute;
  top: calc(100% + 4px);
  left: 12px;
  right: 12px;
  z-index: 50;
  padding: 8px;
  max-height: 280px;
  overflow-y: auto;
}
.search-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition);
}
.search-result-item:hover { background: var(--bg-card-hover); }
.result-title { font-size: 0.825rem; color: var(--text-primary); flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.sidebar-nav { padding: 12px; display: flex; flex-direction: column; gap: 4px; }
.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  transition: var(--transition);
  position: relative;
}
.nav-link:hover { background: var(--bg-card); color: var(--text-primary); }
.nav-link.active { background: rgba(20,184,166,0.12); color: var(--teal-400); }
.nav-icon { font-size: 1rem; }
.due-badge {
  margin-left: auto;
  background: var(--red-500);
  color: #fff;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 1px 7px;
}

.chapter-section { flex: 1; overflow-y: auto; padding: 0 12px 12px; }
.section-label { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em; color: var(--text-muted); text-transform: uppercase; padding: 12px 4px 8px; }

.chapter-list { display: flex; flex-direction: column; gap: 2px; }
.chapter-item {}
.chapter-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-family: var(--font-sans);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: var(--transition);
}
.chapter-btn:hover { background: var(--bg-card); color: var(--text-primary); }
.chapter-btn.expanded { color: var(--text-primary); }
.chapter-icon { flex-shrink: 0; }
.chapter-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chapter-count { font-size: 0.65rem; background: var(--bg-input); padding: 1px 6px; border-radius: 999px; flex-shrink: 0; }
.chevron { font-size: 0.65rem; color: var(--text-muted); flex-shrink: 0; }

.topic-list { padding: 2px 0 4px 24px; display: flex; flex-direction: column; gap: 1px; }
.topic-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--text-muted);
  font-family: var(--font-sans);
  font-size: 0.8rem;
  cursor: pointer;
  text-align: left;
  transition: var(--transition);
  width: 100%;
}
.topic-btn:hover { background: var(--bg-card); color: var(--text-primary); }
.topic-btn.active { background: rgba(20,184,166,0.1); color: var(--teal-400); }
.topic-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.dot-grey { background: var(--text-muted); }
.dot-green { background: var(--green-400); }
.dot-amber { background: var(--gold-400); }
.topic-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.loading-chapters { padding: 8px 0; }
.topic-loading { padding: 4px 0; }

.collapsed-nav {
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.nav-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  font-size: 1.2rem;
  text-decoration: none;
  transition: var(--transition);
  color: var(--text-secondary);
}
.nav-icon-btn:hover { background: var(--bg-card); }

/* Expand animation */
.expand-enter-active, .expand-leave-active {
  transition: max-height 0.25s ease, opacity 0.2s ease;
  overflow: hidden;
}
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0; }
.expand-enter-to, .expand-leave-from { max-height: 600px; opacity: 1; }
</style>
