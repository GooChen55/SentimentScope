<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { startResearch, listResearchTasks, getResearchTask, cancelResearch, retryResearch, getEvidence, getEvaluation } from '../composables/api.js'
import RoleProgressGrid from '../components/RoleProgressGrid.vue'
import SavedResultsSection from '../components/SavedResultsSection.vue'
import ResearchHero from '../components/ResearchHero.vue'
import { formatBeijingTime } from '../composables/dateTime.js'

defineProps({
  roleProgress: Object,
  roleResults: Object,
})

const emit = defineEmits(['research-started'])

const incomingTopic = new URLSearchParams(window.location.search).get('topic') || ''
const query = ref(incomingTopic || '示例品牌配送调整')
const mode = ref(incomingTopic ? 'live' : 'demo')
const error = ref('')
const tasks = ref([])
const current = ref(null)
const evidence = ref([])
const evaluation = ref(null)
let timer
const researching = ref(false)
const results = ref(null)
const loadingLatest = ref(false)
const historySearch = ref('')
const historyFilter = ref('all')
const evidenceLoading = ref(false)
const statusLabels = { queued: '等待执行', running: '研究中', completed: '已完成', error: '失败', cancelled: '已取消', interrupted: '已中断' }
const filteredTasks = computed(() => tasks.value.filter(task => task.query.toLowerCase().includes(historySearch.value.trim().toLowerCase()) && (historyFilter.value === 'all' || task.status === historyFilter.value)))
const completedCount = computed(() => tasks.value.filter(task => task.status === 'completed').length)


async function handleResearch() {
  if (!query.value.trim() || researching.value) return
  researching.value = true
  results.value = null
  evidence.value = []
  evaluation.value = null
  emit('research-started')
  try {
    error.value = ''
    const task = await startResearch(query.value.trim(), mode.value)
    await selectTask(task.research_id)
  } catch (e) {
    error.value = e.message
    researching.value = false
  }
}

function selectTask(id) {
  localStorage.setItem('research_id', id)
  current.value = null
  results.value = null
  evidence.value = []
  evaluation.value = null
  error.value = ''
  emit('research-started')
  return refreshTasks()
}

async function refreshTasks() {
  try {
    tasks.value = (await listResearchTasks()).tasks
    const id = localStorage.getItem('research_id')
    if (!id) return
    const selected = await getResearchTask(id)
    if (localStorage.getItem('research_id') !== id) return
    current.value = selected
    researching.value = ['queued', 'running'].includes(current.value.status)
    if (current.value.status === 'completed') results.value = current.value.results
    if (current.value.error) error.value = current.value.error
  } catch (e) { error.value = e.message }
}

async function cancel() {
  try { await cancelResearch(current.value.research_id); await refreshTasks() }
  catch (e) { error.value = e.message }
}

async function inspectEvidence() {
  evidenceLoading.value = true
  try {
    const id = current.value.research_id
    const [snapshot, metrics] = await Promise.all([getEvidence(id), getEvaluation(id)])
    if (localStorage.getItem('research_id') !== id) return
    evidence.value = snapshot.records
    evaluation.value = metrics
  } catch (e) { error.value = e.message }
  finally { evidenceLoading.value = false }
}

function safeUrl(value) {
  try { const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) ? url.href : undefined }
  catch { return undefined }
}

async function retry(id) {
  try { error.value = ''; const res = await retryResearch(id); await selectTask(res.research_id) }
  catch (e) { error.value = e.message }
}

onMounted(() => { refreshTasks(); timer = setInterval(refreshTasks, 2000) })
onUnmounted(() => clearInterval(timer))

async function loadLatest() {
  loadingLatest.value = true
  try {
    tasks.value = (await listResearchTasks()).tasks
    const latest = tasks.value.find(task => task.status === 'completed')
    if (!latest) { error.value = '暂无已完成的研究，请先开始分析。'; return }
    await selectTask(latest.research_id)
  } catch (e) { error.value = e.message }
  finally { loadingLatest.value = false }
}
</script>

<template>
  <div class="research-view">
    <div class="workspace-heading">
      <div><p class="eyebrow">OVERVIEW</p><h2>研究工作台</h2></div>
      <div class="mode-control"><label for="research-mode">分析模式</label><select id="research-mode" v-model="mode" :disabled="researching" @change="query = mode === 'demo' ? '示例品牌配送调整' : ''"><option value="demo">模拟演示</option><option value="live">真实分析</option></select></div>
    </div>
    <div v-if="error" role="alert" class="error-banner"><span>{{ error }}</span><button aria-label="关闭错误提示" @click="error = ''">×</button></div>
    <ResearchHero v-model:query="query" :mode="mode" :researching="researching" :loading-latest="loadingLatest" @research="handleResearch" @load-latest="loadLatest" />
    <div class="workspace-summary">
      <div><span>研究记录</span><strong>{{ tasks.length }}<small> 次</small></strong></div>
      <div><span>已完成研究</span><strong>{{ completedCount }}<small> 次</small></strong></div>
      <div><span>当前分析方式</span><strong class="summary-mode">{{ mode === 'demo' ? '模拟演示' : '真实分析' }}</strong></div>
    </div>
    <section v-if="current" class="current-task" aria-label="当前研究任务">
      <div class="current-info"><span class="eyebrow">当前查看</span><h3>{{ current.query }}</h3><p>{{ current.mode === 'demo' ? '模拟研究 · 合成证据' : '真实研究' }} · {{ formatBeijingTime(current.created_at) }}</p></div>
      <span class="status-pill" :class="current.status">{{ statusLabels[current.status] || current.status }}</span>
      <button v-if="researching" class="subtle-button" @click="cancel">取消研究</button>
    </section>
    <div class="section-heading"><div><h3>Agent 研究进展</h3><p>查看双源分析的执行阶段和结果</p></div><span class="section-note">Insight / Media</span></div>
    <RoleProgressGrid :role-progress="roleProgress" :role-results="results || roleResults" />
    <details v-if="results" class="results-disclosure"><summary>查看已保存的完整研究产物</summary><SavedResultsSection :results="results" /></details>
    <section v-if="current" class="surface evidence-section">
      <div class="section-heading"><div><h3>证据与基础评测</h3><p>核对来源和结构完整性，辅助判断结论</p></div><button class="subtle-button" :disabled="evidenceLoading" @click="inspectEvidence">{{ evidenceLoading ? '读取中…' : '查看证据与基础评测' }}</button></div>
      <div v-if="evaluation" class="evaluation-stats">
        <div><span>证据数量</span><strong>{{ evaluation.evidence_count }}</strong></div>
        <div><span>五维覆盖</span><strong>{{ Math.round(evaluation.dimension_coverage * 100) }}%</strong></div>
        <div><span>引用有效性</span><strong>{{ evaluation.citation_validity === null ? '—' : Math.round(evaluation.citation_validity * 100) + '%' }}</strong></div>
        <div><span>耗时</span><strong>{{ evaluation.elapsed_seconds }}<small> 秒</small></strong></div>
      </div>
      <p v-if="evaluation" class="evaluation-note">{{ evaluation.note }}</p>
      <p v-if="evaluation?.unknown_citations.length" class="error-text">无对应证据的引用：{{ evaluation.unknown_citations.join(', ') }}</p>
      <details v-for="record in evidence" :key="record.id" class="evidence-record"><summary><span class="evidence-id">{{ record.id }}</span> {{ record.source || record.platform }} {{ record.synthetic ? '· 合成数据' : '' }}</summary><p>{{ record.text || record.content }}</p><a v-if="safeUrl(record.url)" :href="safeUrl(record.url)" target="_blank" rel="noopener noreferrer">查看原始来源 ↗</a></details>
      <p v-if="evaluation && !evidence.length" class="empty-state">当前任务暂无可展示的证据。</p>
    </section>
    <section class="surface history-section">
      <div class="section-heading"><div><h3>研究历史</h3><p>按主题检索，打开记录或再次研究</p></div><span class="section-note">{{ filteredTasks.length }} 条记录</span></div>
      <div class="history-toolbar"><input v-model="historySearch" type="search" aria-label="搜索研究历史" placeholder="搜索研究主题…" /><select v-model="historyFilter" aria-label="筛选研究状态"><option value="all">全部状态</option><option value="completed">已完成</option><option value="running">研究中</option><option value="error">失败</option><option value="cancelled">已取消</option><option value="interrupted">已中断</option></select></div>
      <div v-for="task in filteredTasks" :key="task.research_id" class="history-row" :class="{ selected: current?.research_id === task.research_id }">
        <button class="history-title" @click="selectTask(task.research_id)"><strong>{{ task.query }}</strong><span>{{ task.mode === 'demo' ? '模拟' : '真实' }} · {{ formatBeijingTime(task.created_at) }}</span></button>
        <span class="status-pill" :class="task.status">{{ statusLabels[task.status] || task.status }}</span>
        <button v-if="!['queued', 'running'].includes(task.status)" class="subtle-button" :disabled="researching" @click="retry(task.research_id)">重新研究</button>
      </div>
      <p v-if="!filteredTasks.length" class="empty-state">{{ tasks.length ? '没有匹配的研究记录，试试其他关键词或状态。' : '暂无研究记录，从上方开始第一次分析。' }}</p>
    </section>
  </div>
</template>

<style scoped>
.workspace-heading { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin: .5rem 0 1.5rem; }
.eyebrow { font: .65rem var(--font-mono); letter-spacing: .13em; color: var(--paper-muted); margin-bottom: .5rem; }
.workspace-heading h2 { font: 600 1.3rem var(--font-body); }
.mode-control { display: flex; gap: .7rem; align-items: center; font-size: .75rem; color: var(--paper-dim); }
.mode-control select { font-size: .8rem; border-radius: 8px; }
.error-banner { display: flex; justify-content: space-between; gap: 1rem; background: var(--red-ghost); border: 1px solid var(--red); color: #e7998f; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; font-size: .85rem; overflow-wrap: anywhere; }
.error-banner button { background: none; color: inherit; font-size: 1.1rem; }
.workspace-summary { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); margin-bottom: 1.5rem; border: 1px solid var(--border); border-radius: 12px; background: var(--ink-light); }
.workspace-summary > div { padding: 1.2rem 1.5rem; border-right: 1px solid var(--border); }
.workspace-summary > div:last-child { border: 0; }
.workspace-summary span, .evaluation-stats span { display: block; color: var(--paper-muted); font-size: .7rem; margin-bottom: .5rem; }
.workspace-summary strong { font: 500 1.5rem var(--font-mono); }
small { font: .7rem var(--font-body); color: var(--paper-muted); }
.workspace-summary .summary-mode { font: 500 1rem var(--font-body); }
.current-task { display: flex; align-items: center; gap: 1rem; padding: 1.2rem 1.5rem; margin-bottom: 1.8rem; background: var(--teal-ghost); border: 1px solid rgba(74,157,143,.25); border-radius: 12px; }
.current-info { flex: 1; min-width: 0; }
.current-info h3 { font: 500 .95rem var(--font-body); overflow-wrap: anywhere; }
.current-info p { font-size: .7rem; color: var(--paper-dim); margin-top: .5rem; }
.section-heading { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 1rem; }
.section-heading h3 { font: 500 .95rem var(--font-body); }
.section-heading p { font-size: .75rem; color: var(--paper-muted); margin-top: .4rem; }
.section-note { font: .65rem var(--font-mono); color: var(--paper-muted); white-space: nowrap; }
.surface { padding: 1.5rem; margin-top: 1.5rem; border: 1px solid var(--border-strong); border-radius: 14px; background: var(--ink-light); }
.subtle-button { padding: .5rem .8rem; background: var(--ink); border: 1px solid var(--border-strong); border-radius: 7px; font-size: .75rem; color: var(--paper-dim); white-space: nowrap; }
.subtle-button:hover:not(:disabled) { color: var(--amber); border-color: var(--amber); }
.status-pill { border-radius: 20px; padding: .3rem .7rem; color: var(--paper-dim); background: var(--ink-lighter); font-size: .7rem; white-space: nowrap; }
.status-pill.completed { color: #81c9b9; background: var(--teal-ghost); }
.status-pill.running, .status-pill.queued { color: var(--amber); background: var(--amber-ghost); }
.status-pill.error, .status-pill.interrupted { color: #e7998f; background: var(--red-ghost); }
.results-disclosure { margin-top: 1.2rem; }
.results-disclosure > summary { cursor: pointer; color: var(--paper-dim); font-size: .8rem; padding: .8rem; border: 1px dashed var(--border-strong); border-radius: 8px; }
.evaluation-stats { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 1rem; margin: 1.5rem 0; }
.evaluation-stats strong { font: 500 1.15rem var(--font-mono); }
.evaluation-note { font-size: .75rem; color: var(--paper-muted); margin-bottom: 1rem; }
.evidence-record { border-top: 1px solid var(--border); padding: .8rem 0; }
.evidence-record summary { cursor: pointer; font-size: .8rem; }
.evidence-id { color: var(--amber); font-family: var(--font-mono); }
.evidence-record p { font-size: .85rem; line-height: 1.9; padding: 1rem 0; overflow-wrap: anywhere; white-space: pre-wrap; }
.evidence-record a { font-size: .75rem; }
.history-toolbar { display: flex; gap: .75rem; margin-bottom: 1rem; }
.history-toolbar input { flex: 1; }
.history-toolbar input, .history-toolbar select { font-size: .8rem; border-radius: 8px; }
.history-row { display: flex; align-items: center; gap: 1rem; padding: 1rem .75rem; border-top: 1px solid var(--border); border-left: 2px solid transparent; }
.history-row.selected { border-left-color: var(--amber); background: var(--amber-ghost); }
.history-title { flex: 1; min-width: 0; text-align: left; background: none; color: var(--paper); }
.history-title strong { display: block; font-weight: 500; font-size: .85rem; overflow-wrap: anywhere; }
.history-title span { display: block; font-size: .65rem; color: var(--paper-muted); margin-top: .4rem; }
.empty-state { padding: 2rem .5rem; text-align: center; color: var(--paper-muted); font-size: .8rem; }
.error-text { color: var(--red); }
@media(max-width: 620px) { .workspace-heading { flex-wrap: wrap; } .workspace-summary > div { padding: .9rem; } .workspace-summary strong { font-size: 1.2rem; } .workspace-summary .summary-mode { font-size: .8rem; } .current-task { flex-wrap: wrap; padding: 1rem; } .current-info { flex-basis: 65%; } .surface { padding: 1rem; } .section-heading { flex-wrap: wrap; } .evaluation-stats { grid-template-columns: repeat(2,minmax(0,1fr)); } .history-row { gap: .5rem; flex-wrap: wrap; } .history-title { flex-basis: 65%; } .history-row > .subtle-button { margin-left: auto; } }
</style>
