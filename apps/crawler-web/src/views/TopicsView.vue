<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'

const api = useApi()
const topics = ref<any[]>([])
const loading = ref(true)
const expandedDate = ref<string | null>(null)
const selectedDate = ref(new Date().toISOString().slice(0, 10))
const detail = ref<any>(null)

async function loadTopics() {
  loading.value = true
  try {
    topics.value = await api.fetchTopics(7)
  } finally {
    loading.value = false
  }
}

async function loadDetail(date: string) {
  try {
    const kw = await api.fetchTopicKeywords(date)
    detail.value = kw
    expandedDate.value = date
  } catch { detail.value = null }
}

onMounted(loadTopics)
</script>

<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-display font-semibold text-terminal-text">话题分析</h2>
        <p class="text-sm text-terminal-muted mt-0.5">热点话题关键词及摘要</p>
      </div>
      <div class="flex items-center gap-3">
        <input
          v-model="selectedDate" type="date"
          class="bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm font-mono text-terminal-text focus:border-terminal-green focus:outline-none"
          @change="loadDetail(selectedDate)"
        />
        <button
          @click="loadTopics"
          class="px-3 py-1.5 text-xs border border-terminal-border rounded text-terminal-muted hover:text-terminal-text transition-colors font-display"
        >刷新</button>
      </div>
    </div>

    <div v-if="loading" class="text-sm text-terminal-muted text-center py-12">加载中...</div>

    <div v-else-if="topics.length === 0" class="text-center py-12">
      <div class="text-4xl font-display text-terminal-muted mb-3">⊞</div>
      <p class="text-terminal-muted">暂无话题数据</p>
      <p class="text-sm text-terminal-muted mt-1">请先运行"广义话题提取"模式</p>
    </div>

    <div v-else class="grid grid-cols-1 gap-3">
      <div
        v-for="t in topics" :key="t.extract_date"
        class="bg-terminal-panel border border-terminal-border rounded-lg overflow-hidden"
      >
        <button
          @click="expandedDate === t.extract_date ? expandedDate = null : loadDetail(t.extract_date)"
          class="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-terminal-border/10 transition-colors"
        >
          <div class="flex items-center gap-3">
            <span class="font-mono text-sm text-terminal-text">{{ t.extract_date }}</span>
            <span class="text-xs px-2 py-0.5 bg-terminal-green/10 text-terminal-green rounded">{{ t.keywords_count }} 个关键词</span>
          </div>
          <span class="text-terminal-muted text-xs font-mono">{{ expandedDate === t.extract_date ? '收起' : '展开' }}</span>
        </button>
        <div v-if="expandedDate === t.extract_date && detail" class="px-4 pb-4 border-t border-terminal-border">
          <div class="flex flex-wrap gap-1.5 mt-3">
            <a
              v-for="k in detail.keywords" :key="k"
              :href="'http://127.0.0.1:3000/?topic=' + encodeURIComponent(k)"
              target="_blank" rel="noopener noreferrer"
              title="在舆情工作台研究此关键词"
              class="px-2 py-0.5 bg-terminal-bg border border-terminal-border rounded text-xs font-mono text-terminal-green"
            >{{ k }} → 研判</a>
          </div>
          <p v-if="t.summary" class="text-sm text-terminal-muted mt-3 leading-relaxed">{{ t.summary }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
