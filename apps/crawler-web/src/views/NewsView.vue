<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'

const api = useApi()
const newsList = ref<any[]>([])
const sources = ref<any[]>([])
const selectedDate = ref(new Date().toISOString().slice(0, 10))
const selectedSource = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await api.fetchNews(selectedDate.value, selectedSource.value || undefined)
    newsList.value = data.news || []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try { sources.value = await api.fetchNewsSources() } catch {}
  load()
})
</script>

<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <div>
      <h2 class="text-lg font-display font-semibold text-terminal-text">新闻列表</h2>
      <p class="text-sm text-terminal-muted mt-0.5">浏览已收集的热点新闻</p>
    </div>

    <div class="flex items-center gap-3 flex-wrap">
      <input
        v-model="selectedDate" type="date"
        class="bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm font-mono text-terminal-text focus:border-terminal-green focus:outline-none"
        @change="load"
      />
      <select
        v-model="selectedSource"
        @change="load"
        class="bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm font-mono text-terminal-text focus:border-terminal-green focus:outline-none"
      >
        <option value="">全部来源</option>
        <option v-for="s in sources" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>
      <span class="text-sm text-terminal-muted">共 {{ newsList.length }} 条</span>
    </div>

    <div v-if="loading" class="text-sm text-terminal-muted text-center py-12">加载中...</div>

    <div v-else-if="newsList.length === 0" class="text-center py-12">
      <div class="text-4xl font-display text-terminal-muted mb-3">☷</div>
      <p class="text-terminal-muted">该日期暂无新闻数据</p>
    </div>

    <div v-else class="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-terminal-border text-left">
            <th class="px-4 py-2 text-xs font-display text-terminal-muted w-12">#</th>
            <th class="px-4 py-2 text-xs font-display text-terminal-muted">标题</th>
            <th class="px-4 py-2 text-xs font-display text-terminal-muted w-24">来源</th>
            <th class="px-4 py-2 text-xs font-display text-terminal-muted w-20">排名</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="n in newsList" :key="n.news_id"
            class="border-b border-terminal-border/50 hover:bg-terminal-border/10 transition-colors"
          >
            <td class="px-4 py-2.5 text-terminal-muted font-mono text-xs">{{ newsList.indexOf(n) + 1 }}</td>
            <td class="px-4 py-2.5">
              <a :href="n.url" target="_blank" class="text-terminal-text hover:text-terminal-green transition-colors line-clamp-1">{{ n.title }}</a>
            </td>
            <td class="px-4 py-2.5">
              <span class="text-xs px-1.5 py-0.5 bg-terminal-bg rounded text-terminal-muted">{{ n.source_platform }}</span>
            </td>
            <td class="px-4 py-2.5 text-terminal-muted font-mono text-xs">{{ n.rank_position }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
