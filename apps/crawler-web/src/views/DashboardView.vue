<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'

const router = useRouter()
const api = useApi()
const statCards = ref([
  { title: '最近话题', value: '--', subtitle: '等待加载', icon: '⊞', color: 'text-terminal-green' },
  { title: '新闻记录', value: '--', subtitle: '等待加载', icon: '☷', color: 'text-terminal-blue' },
  { title: '活跃平台', value: '--', subtitle: '等待加载', icon: '⚡', color: 'text-terminal-amber' },
  { title: '最近爬取', value: '--', subtitle: '等待加载', icon: '◷', color: 'text-terminal-text' },
])
const recentTasks = ref<any[]>([])
const recentTopics = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [topics, tasks] = await Promise.all([
      api.fetchTopics(7),
      api.fetchTasks(5),
    ])

    if (topics.length > 0) {
      const latest = topics[0]
      const totalKeywords = topics.reduce((s: number, t: any) => s + t.keywords_count, 0)
      statCards.value[0].value = String(totalKeywords)
      statCards.value[0].subtitle = `${topics.length} 天数据，最新: ${latest.extract_date}`
    } else {
      statCards.value[0].value = '0'
      statCards.value[0].subtitle = '暂无话题数据'
    }

    if (tasks?.recent?.length > 0) {
      const lastCrawl = tasks.recent[0]
      statCards.value[3].value = lastCrawl.status === 'completed' ? '成功' : lastCrawl.status
      statCards.value[3].subtitle = `${lastCrawl.type} · ${lastCrawl.created_at?.slice(0, 10)}`
      recentTasks.value = tasks.recent.slice(0, 5)
    } else {
      statCards.value[3].value = '--'
      statCards.value[3].subtitle = '暂无爬取记录'
    }

    statCards.value[2].value = '7'
    statCards.value[2].subtitle = 'xhs, dy, ks, bili, wb, tieba, zhihu'

    recentTopics.value = topics.slice(0, 5)
    statCards.value[1].value = '--'
    statCards.value[1].subtitle = '新闻数据待加载'

  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="p-6 space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-display font-semibold text-terminal-text">仪表盘</h2>
        <p class="text-sm text-terminal-muted mt-0.5">爬虫系统运行概览</p>
      </div>
      <button
        @click="router.push('/crawl')"
        class="px-4 py-2 bg-terminal-green text-black text-sm font-semibold rounded hover:bg-terminal-green/90 transition-colors font-display"
      >
        开始新爬取 →
      </button>
    </div>

    <!-- Stat Cards -->
    <div class="grid grid-cols-4 gap-4">
      <div
        v-for="card in statCards"
        :key="card.title"
        class="bg-terminal-panel border border-terminal-border rounded-lg p-4 hover:border-terminal-border/80 transition-colors"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs text-terminal-muted font-body">{{ card.title }}</span>
          <span class="font-display text-lg" :class="card.color">{{ card.icon }}</span>
        </div>
        <div class="text-2xl font-display font-semibold" :class="card.color">{{ card.value }}</div>
        <div class="text-xs text-terminal-muted mt-1">{{ card.subtitle }}</div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <!-- Recent Topics -->
      <div class="bg-terminal-panel border border-terminal-border rounded-lg p-4">
        <h3 class="text-sm font-display font-semibold text-terminal-text mb-3">最近话题</h3>
        <div v-if="recentTopics.length === 0" class="text-sm text-terminal-muted text-center py-8">
          暂无话题数据，请先运行爬虫
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="t in recentTopics"
            :key="t.extract_date"
            class="flex items-center justify-between py-2 border-b border-terminal-border/50 last:border-0"
          >
            <span class="text-sm font-mono text-terminal-muted">{{ t.extract_date }}</span>
            <div class="flex items-center gap-2">
              <span class="text-xs text-terminal-green">{{ t.keywords_count }} 关键词</span>
              <button
                @click="router.push('/topics')"
                class="text-xs text-terminal-blue hover:underline"
              >查看</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Tasks -->
      <div class="bg-terminal-panel border border-terminal-border rounded-lg p-4">
        <h3 class="text-sm font-display font-semibold text-terminal-text mb-3">最近爬取</h3>
        <div v-if="recentTasks.length === 0" class="text-sm text-terminal-muted text-center py-8">
          暂无爬取记录
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="task in recentTasks"
            :key="task.task_id"
            class="flex items-center justify-between py-2 border-b border-terminal-border/50 last:border-0"
          >
            <div>
              <span class="text-xs font-mono text-terminal-muted mr-2">{{ task.task_id }}</span>
              <span class="text-xs px-1.5 py-0.5 rounded"
                :class="task.status === 'completed' ? 'bg-terminal-green/15 text-terminal-green' :
                         task.status === 'failed' ? 'bg-terminal-red/15 text-terminal-red' :
                         'bg-terminal-muted/15 text-terminal-muted'"
              >{{ task.status }}</span>
            </div>
            <span class="text-xs text-terminal-muted">{{ task.type }} · {{ task.created_at?.slice(0, 16) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
