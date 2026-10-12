<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from './composables/useApi'

const route = useRoute()
const router = useRouter()
const api = useApi()

const activeTaskId = ref<string | null>(null)
const statusText = ref('就绪')
const statusDotClass = ref('gray')
const taskTypeLabels: Record<string, string> = { deep_sentiment: '社交采集', broad_topic: '话题采集', web_page: '网页证据' }
let pollTimer: ReturnType<typeof setInterval> | null = null

const navItems = [
  { path: '/', label: '仪表盘', icon: '◫' },
  { path: '/crawl', label: '采集任务', icon: '⚡' },
  { path: '/topics', label: '话题分析', icon: '⊞' },
  { path: '/news', label: '新闻列表', icon: '☷' },
  { path: '/settings', label: '设置', icon: '⚙' },
]

onMounted(async () => {
  pollTasks()
  pollTimer = setInterval(pollTasks, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function pollTasks() {
  try {
    const data = await api.fetchTasks(5)
    const active = data?.active
    if (active && (active.status === 'pending' || active.status === 'running' || active.status === 'stopping')) {
      activeTaskId.value = active.task_id
      if (active.status === 'running') {
        statusText.value = `采集中：${taskTypeLabels[active.type] || active.type}`
        statusDotClass.value = 'blue'
      } else if (active.status === 'stopping') {
        statusText.value = '正在停止...'
        statusDotClass.value = 'amber'
      } else {
        statusText.value = '等待启动...'
        statusDotClass.value = 'amber'
      }
    } else {
      activeTaskId.value = null
      statusText.value = '就绪'
      statusDotClass.value = 'green'
    }
  } catch {
    statusText.value = '后端离线'
    statusDotClass.value = 'red'
  }
}
</script>

<template>
  <div class="crawler-shell flex h-screen overflow-hidden">
    <!-- Sidebar -->
    <aside class="crawler-sidebar w-52 flex-shrink-0 bg-terminal-panel border-r border-terminal-border flex flex-col">
      <div class="sidebar-brand px-5 py-5 border-b border-terminal-border">
        <h1 class="text-sm font-body font-semibold text-terminal-amber tracking-wide whitespace-nowrap">
          <img src="/sentimentscope.svg" alt="" class="w-6 h-6 inline-block mr-1" />SentimentScope
        </h1>
        <p class="text-[10px] text-terminal-muted mt-1 font-body">舆情研判平台 · 采集控制台</p>
        <a href="http://127.0.0.1:3000" target="_blank" rel="noopener noreferrer" class="block text-xs text-terminal-muted hover:text-terminal-green mt-3">打开研究工作台 ↗</a>
      </div>

      <nav class="sidebar-nav flex-1 py-3" aria-label="采集控制台导航">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-5 py-2.5 text-sm font-body transition-colors duration-150"
          :class="route.path === item.path
            ? 'text-terminal-green bg-terminal-green/5 border-r-2 border-terminal-green'
            : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-border/30'"
        >
          <span class="font-display text-base w-5 text-center">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-status px-5 py-4 border-t border-terminal-border space-y-2">
        <div class="flex items-center gap-2 text-xs">
          <span class="status-dot" :class="statusDotClass"></span>
          <span class="text-terminal-muted">{{ statusText }}</span>
        </div>
        <div v-if="activeTaskId" class="text-[10px] text-terminal-muted font-mono">
          TASK {{ activeTaskId }}
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="crawler-content flex-1 min-w-0 flex flex-col overflow-hidden">
      <main class="crawler-main flex-1 overflow-y-auto">
        <router-view />
      </main>

      <!-- Status Bar -->
      <footer class="h-7 flex-shrink-0 bg-terminal-panel border-t border-terminal-border flex items-center px-4 text-[11px] font-display text-terminal-muted">
        <span>{{ statusText }}</span>
        <span class="mx-3 text-terminal-border">|</span>
        <span v-if="activeTaskId">活跃任务: {{ activeTaskId }}</span>
        <span v-else>无活跃任务</span>
        <span class="flex-1"></span>
        <span class="footer-brand">SentimentScope · 采集控制台</span>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.crawler-main > :deep(div) { max-width: 1440px; margin: 0 auto; }
@media (max-width: 760px) {
  .crawler-shell { flex-direction: column; height: 100dvh; }
  .crawler-sidebar { width: 100%; border-right: 0; }
  .sidebar-brand { padding: .8rem 1rem; display: flex; justify-content: space-between; align-items: center; gap: .5rem; }
  .sidebar-brand p { display: none; }
  .sidebar-brand a { margin-top: 0; font-size: .65rem; }
  .sidebar-nav { display: flex; overflow-x: auto; padding: 0; }
  .sidebar-nav a { flex: 1 0 auto; justify-content: center; padding: .7rem .8rem; border-right: 0; font-size: .75rem; gap: .4rem; }
  .sidebar-nav a.router-link-active { border-bottom: 2px solid #4a9d8f; }
  .sidebar-status { display: none; }
  .footer-brand { display: none; }
  .crawler-main > :deep(div) { padding: 1rem; }
}
</style>
