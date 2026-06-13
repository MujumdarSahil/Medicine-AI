<template>
  <div class="topic-view">
    <!-- Topic header -->
    <div class="topic-header" v-if="topic">
      <div class="topic-meta">
        <div class="breadcrumb">
          <span class="bc-system">{{ topic.system }}</span>
          <span class="bc-sep">›</span>
          <span class="bc-chapter">{{ topic.chapter }}</span>
        </div>
        <h1 class="topic-name">{{ topic.title }}</h1>
        <div class="topic-tags">
          <span v-if="topic.page_refs?.length" class="badge badge-teal">
            📄 pp. {{ topic.page_refs.slice(0,3).join(', ') }}{{ topic.page_refs.length > 3 ? '...' : '' }}
          </span>
          <span v-for="sec in (topic.sections || []).slice(0,4)" :key="sec" class="badge badge-blue" style="font-size:0.65rem">{{ sec }}</span>
        </div>
      </div>

      <!-- Tabs -->
      <div class="topic-tabs">
        <div class="tabs">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'chat' }"
            @click="activeTab = 'chat'"
            id="tab-chat"
          >💬 Explain</button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'case' }"
            @click="activeTab = 'case'"
            id="tab-case"
          >🏥 Case</button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'test' }"
            @click="activeTab = 'test'"
            id="tab-test"
          >📝 Test</button>
        </div>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-else-if="loading" class="topic-header skeleton-header">
      <div class="skeleton" style="height:16px;width:180px;border-radius:6px;margin-bottom:10px"></div>
      <div class="skeleton" style="height:32px;width:300px;border-radius:8px;margin-bottom:14px"></div>
      <div style="display:flex;gap:8px">
        <div class="skeleton" style="height:24px;width:80px;border-radius:999px"></div>
        <div class="skeleton" style="height:24px;width:80px;border-radius:999px"></div>
      </div>
    </div>

    <!-- Tab panels -->
    <div class="tab-content" v-if="topic">
      <Transition name="tab" mode="out-in">
        <ChatPanel
          v-if="activeTab === 'chat'"
          :topicId="topicId"
          :topicTitle="topic.title"
          key="chat"
        />
        <CasePanel
          v-else-if="activeTab === 'case'"
          :topicId="topicId"
          :topicTitle="topic.title"
          key="case"
        />
        <TestPanel
          v-else-if="activeTab === 'test'"
          :topicId="topicId"
          :topicTitle="topic.title"
          key="test"
        />
      </Transition>
    </div>

    <!-- Topic not found -->
    <div v-else-if="!loading" class="empty-state">
      <div class="icon">🔍</div>
      <h3>Topic not found</h3>
      <p>This topic may not exist or the PDF hasn't been ingested yet.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTopicsStore } from '@/stores/topics'
import ChatPanel from '@/components/ChatPanel.vue'
import CasePanel from '@/components/CasePanel.vue'
import TestPanel from '@/components/TestPanel.vue'

const route = useRoute()
const store = useTopicsStore()

const activeTab = ref('chat')
const topicId = computed(() => route.params.id)
const topic = computed(() => store.currentTopic)
const loading = computed(() => store.loading)

watch(topicId, async (id) => {
  if (id) {
    activeTab.value = 'chat'
    await store.fetchTopic(id)
  }
}, { immediate: true })
</script>

<style scoped>
.topic-view { display: flex; flex-direction: column; height: 100%; overflow: hidden; }

.topic-header {
  padding: 20px 24px 0;
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-secondary);
  flex-shrink: 0;
}
.skeleton-header { padding: 24px; }

.topic-meta { margin-bottom: 16px; }
.breadcrumb { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.bc-system { font-size: 0.75rem; color: var(--teal-400); font-weight: 600; }
.bc-sep { color: var(--text-muted); }
.bc-chapter { font-size: 0.75rem; color: var(--text-muted); }
.topic-name { font-size: 1.4rem; font-weight: 800; margin: 0 0 10px; line-height: 1.3; }
.topic-tags { display: flex; flex-wrap: wrap; gap: 6px; }

.topic-tabs { padding-bottom: 0; }
.tabs { max-width: 320px; }
.tab-btn { font-size: 0.85rem; }

.tab-content { flex: 1; overflow: hidden; }

/* Tab transition */
.tab-enter-active, .tab-leave-active { transition: opacity 0.2s, transform 0.2s; }
.tab-enter-from { opacity: 0; transform: translateY(8px); }
.tab-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
