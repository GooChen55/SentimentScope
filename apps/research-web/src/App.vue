<script setup>
import { computed, onMounted, ref } from 'vue'
import { useSSE } from './composables/useSSE.js'
import { TABS } from './constants/navigation.js'
import AppHeader from './components/AppHeader.vue'
import AppNav from './components/AppNav.vue'
import ResearchView from './views/ResearchView.vue'
import ReportView from './views/ReportView.vue'
import HostDiscussionView from './views/HostDiscussionView.vue'
import ConfigView from './views/ConfigView.vue'

const { connected, roleProgress, roleResults, connect, clearResearchState } = useSSE()
const activeTab = ref('research')
const completedRoles = computed(() => Object.keys(roleResults.value).length)

onMounted(() => connect())
</script>

<template>
  <div class="app-shell">
    <div class="accent-bar"></div>
    <AppHeader :connected="connected" />
    <AppNav
      v-model:activeTab="activeTab"
      :tabs="TABS"
      :completedRoles="completedRoles"
    />

    <main class="app-main">
      <ResearchView
        v-show="activeTab === 'research'"
        :roleProgress="roleProgress"
        :roleResults="roleResults"
        @research-started="clearResearchState"
      />
      <ReportView v-if="activeTab === 'report'" />
      <HostDiscussionView v-if="activeTab === 'host'" />
      <ConfigView v-show="activeTab === 'config'" />
    </main>
  </div>
</template>

<style scoped>
.accent-bar {
  position: fixed; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--amber), transparent);
  opacity: 0.6;
  z-index: 10;
  animation: pulse-glow 4s ease-in-out infinite;
}

.app-main {
  padding: 1.5rem 2rem;
  max-width: 1440px;
  margin: 0 auto;
}
@media (max-width: 700px) { .app-main { padding: 1rem .75rem; } }
</style>
