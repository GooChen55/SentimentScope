<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
const router = useRouter()
const api = useApi()
const recentTasks = ref<any[]>([])
const recentTopics = ref<any[]>([])
const loading = ref(true)
const errors = ref<string[]>([])
const newsCount = ref<number | null>(null)
const platformCount = ref<number | null>(null)
const dbConnected = ref<boolean | null>(null)
const keywordCount = ref<number | null>(null)
const taskCount = ref<number | null>(null)
const labels: Record<string,string> = { pending:'等待启动', running:'采集中', stopping:'正在停止', completed:'已完成', failed:'失败', stopped:'已停止' }
const types: Record<string,string> = { deep_sentiment:'社交采集', broad_topic:'话题采集', web_page:'网页证据', web_evidence:'网页证据', web_document:'网页证据', web:'网页证据' }
const stats = computed(() => [
  { title:'近七天关键词', value:keywordCount.value, note:'已提取话题中的关键词', icon:'⊞' },
  { title:'今日新闻', value:newsCount.value, note:'当前日期的新闻记录', icon:'☷' },
  { title:'支持平台', value:platformCount.value, note:'可选采集适配器，需登录验证', icon:'◫' },
  { title:'最近任务', value:taskCount.value, note:'最近最多 20 条历史记录', icon:'◷' },
])
function timestamp(value?: string) { if (!value) return '时间未知'; const d = new Date(value); return Number.isNaN(d.getTime()) ? value : d.toLocaleString('zh-CN', { timeZone:'Asia/Shanghai', hour12:false }) }
async function loadDashboard() {
  loading.value = true
  errors.value = []
  const names = ['话题', '任务', '新闻', '平台', '数据库']
  const result = await Promise.allSettled([api.fetchTopics(7), api.fetchTasks(20), api.fetchNews(), api.fetchConfigOptions(), api.healthCheck()])
  result.forEach((item, index) => { if (item.status === 'rejected') errors.value.push(`${names[index]}加载失败：${item.reason?.message || '请检查服务连接'}`) })
  if (result[0].status === 'fulfilled') { const topics = result[0].value as any[]; recentTopics.value = topics.slice(0,5); keywordCount.value = topics.reduce((sum:number,item:any) => sum + (Number(item.keywords_count) || 0),0) } else { keywordCount.value = null; recentTopics.value = [] }
  if (result[1].status === 'fulfilled') { recentTasks.value = (result[1].value as any).recent || []; taskCount.value = recentTasks.value.length } else { recentTasks.value = []; taskCount.value = null }
  newsCount.value = result[2].status === 'fulfilled' ? Number((result[2].value as any).total) : null
  platformCount.value = result[3].status === 'fulfilled' ? (result[3].value as any).supported_platforms.length : null
  dbConnected.value = result[4].status === 'fulfilled' ? (result[4].value as any).db_connected : null
  loading.value = false
}
onMounted(loadDashboard)
</script>

<template>
  <div class="p-6 space-y-6 animate-fade-in">
    <div class="flex flex-wrap gap-4 items-center justify-between">
      <div><p class="text-[10px] tracking-[0.15em] text-terminal-muted font-display mb-2">COLLECTION WORKSPACE</p><h2 class="text-xl font-body font-semibold">采集概览</h2><p class="text-sm text-terminal-muted mt-2">准备可靠证据，为下一次研究提供依据。</p></div>
      <div class="flex items-center gap-3"><span class="text-xs text-terminal-muted"><span class="status-dot mr-2" :class="dbConnected ? 'green' : dbConnected === false ? 'red' : 'gray'"></span>{{ dbConnected ? '数据库已连接' : dbConnected === false ? '数据库未连接' : '连接待确认' }}</span><button :disabled="loading" @click="loadDashboard" class="text-xs border border-terminal-border rounded-lg px-3 py-2 hover:text-terminal-amber disabled:opacity-50">{{ loading ? '刷新中…' : '刷新概览' }}</button></div>
    </div>
    <div v-if="errors.length" role="alert" class="rounded-xl border border-terminal-red/40 bg-terminal-red/10 p-4 text-sm text-terminal-text"><p v-for="message in errors" :key="message">{{ message }}</p><p class="mt-2 text-xs text-terminal-muted">部分模块不可用，其余结果仍可查看。连接恢复后点击刷新概览。</p></div>
    <section class="collection-hero rounded-2xl border border-terminal-border p-6 flex flex-wrap items-center justify-between gap-6">
      <div class="max-w-xl"><span class="text-xs text-terminal-amber">采集 → 证据入库 → 舆情研究</span><h3 class="text-2xl font-body font-semibold mt-3">从一个关键词开始</h3><p class="text-sm text-terminal-muted leading-relaxed mt-3">采集社交讨论，或提取新闻与公告正文。记录入库后，回到研究工作台开展双源分析与五维研判。</p></div>
      <div class="flex flex-col gap-3"><button @click="router.push('/crawl')" class="px-5 py-3 bg-terminal-amber text-terminal-bg font-semibold text-sm rounded-lg hover:brightness-110">创建采集任务 ↗</button><a href="http://127.0.0.1:3000" target="_blank" rel="noopener noreferrer" class="text-xs text-center text-terminal-muted hover:text-terminal-amber">前往研究工作台 →</a></div>
    </section>
    <div class="grid grid-cols-4 gap-4" :aria-busy="loading">
      <div v-for="card in stats" :key="card.title" class="bg-terminal-panel border border-terminal-border rounded-xl p-5"><div class="flex items-center justify-between"><span class="text-xs text-terminal-muted">{{ card.title }}</span><span class="text-terminal-amber">{{ card.icon }}</span></div><div class="text-3xl font-display mt-4">{{ loading ? '…' : card.value ?? '—' }}</div><p class="text-[11px] text-terminal-muted mt-2 leading-relaxed">{{ card.note }}</p></div>
    </div>
    <div class="grid grid-cols-2 gap-5">
      <section class="bg-terminal-panel border border-terminal-border rounded-xl p-5"><div class="flex justify-between items-center mb-4"><h3 class="font-body font-semibold text-sm">最近话题</h3><button @click="router.push('/topics')" class="text-xs text-terminal-amber">查看全部 →</button></div><p v-if="!recentTopics.length" class="py-10 text-center text-sm text-terminal-muted">{{ loading ? '正在读取话题…' : keywordCount === null ? '话题数据暂不可用' : '暂无话题，也可直接输入关键词创建采集任务。' }}</p><div v-for="topic in recentTopics" :key="topic.extract_date" class="flex justify-between items-center border-t border-terminal-border py-4"><span class="text-sm text-terminal-muted font-display">{{ topic.extract_date }}</span><span class="text-xs text-terminal-green">{{ topic.keywords_count }} 个关键词</span></div></section>
      <section class="bg-terminal-panel border border-terminal-border rounded-xl p-5"><div class="flex justify-between items-center mb-4"><h3 class="font-body font-semibold text-sm">最近采集任务</h3><button @click="router.push('/crawl')" class="text-xs text-terminal-amber">任务控制 →</button></div><p v-if="!recentTasks.length" class="py-10 text-center text-sm text-terminal-muted">{{ loading ? '正在读取任务…' : '暂无可展示的采集记录。' }}</p><button v-for="task in recentTasks.slice(0,5)" :key="task.task_id" @click="router.push('/crawl')" class="w-full text-left border-t border-terminal-border py-3 hover:bg-terminal-border/30 rounded"><div class="flex justify-between items-center gap-2"><span class="text-sm">{{ task.config?.keywords?.join('、') || types[task.type] || task.type }}</span><span class="text-[11px] px-2 py-1 rounded-full" :class="task.status === 'completed' ? 'text-terminal-green bg-terminal-green/10' : task.status === 'failed' ? 'text-terminal-red bg-terminal-red/10' : 'text-terminal-muted bg-terminal-border'">{{ labels[task.status] || task.status }}</span></div><div class="text-[10px] text-terminal-muted mt-2 font-display">{{ types[task.type] || task.type }} · {{ timestamp(task.created_at) }}</div></button></section>
    </div>
  </div>
</template>
<style scoped>
.collection-hero { background: radial-gradient(ellipse at 0 0, rgba(212,160,52,.1), transparent 65%), #11151b; }
</style>
