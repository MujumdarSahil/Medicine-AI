<template>
  <div class="home-view">
    <div class="home-header">
      <div class="header-content">
        <h1>🩺 MedMentor <span class="brand-ai">AI</span></h1>
        <p class="header-subtitle">Your intelligent MBBS Medicine tutor — powered by your textbook</p>
      </div>
    </div>
    <Dashboard />
  </div>
</template>

<script setup>
import Dashboard from '@/components/Dashboard.vue'
</script>

<style scoped>
.home-view { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.home-header {
  padding: 28px 24px 20px;
  border-bottom: 1px solid var(--border-default);
  background: linear-gradient(135deg, var(--bg-secondary) 0%, rgba(20,184,166,0.05) 100%);
  flex-shrink: 0;
}
.header-content {}
h1 { font-size: 1.75rem; margin: 0; }
.brand-ai {
  background: linear-gradient(135deg, var(--teal-400), var(--blue-400));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.header-subtitle { color: var(--text-muted); font-size: 0.875rem; margin-top: 4px; }
</style>
