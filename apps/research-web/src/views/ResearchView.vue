<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { startResearch, getLatestResults, listResearchTasks, getResearchTask, cancelResearch, retryResearch, getEvidence, getEvaluation } from '../composables/api.js'
import RoleProgressGrid from '../components/RoleProgressGrid.vue'
import SavedResultsSection from '../components/SavedResultsSection.vue'
import ResearchHero from '../components/ResearchHero.vue'

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
    selectTask(task.research_id)
    await refreshTasks()
  } catch (e) {
    error.value = e.message
    researching.value = false
  }
}

function selectTask(id) {
  localStorage.setItem('research_id', id)
  results.value = null
  emit('research-started')
  refreshTasks()
}

async function refreshTasks() {
  try {
    tasks.value = (await listResearchTasks()).tasks
    const id = localStorage.getItem('research_id')
    if (!id) return
    current.value = await getResearchTask(id)
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
  try {
    const id = current.value.research_id
    evidence.value = (await getEvidence(id)).records
    evaluation.value = await getEvaluation(id)
  } catch (e) { error.value = e.message }
}

function safeUrl(value) {
  try { const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) ? url.href : undefined }
  catch { return undefined }
}

async function retry(id) {
  try { error.value = ''; const res = await retryResearch(id); selectTask(res.research_id) }
  catch (e) { error.value = e.message }
}

onMounted(() => { refreshTasks(); timer = setInterval(refreshTasks, 2000) })
onUnmounted(() => clearInterval(timer))

async function loadLatest() {
  loadingLatest.value = true
  try {
    const data = await getLatestResults()
    if (data?.results) results.value = data.results
  } catch {}
  loadingLatest.value = false
}
</script>

<template>
  <div class="research-view">
    <div class="task-options">
      <label>分析模式 <select v-model="mode" :disabled="researching" @change="query = mode === 'demo' ? '示例品牌配送调整' : ''">
        <option value="demo">模拟演示（合成数据，无模型调用）</option>
        <option value="live">真实分析（需要模型与搜索配置）</option>
      </select></label>
      <p v-if="mode === 'demo'">演示用于验证协作流程，不代表真实事件或模型质量。</p>
      <p v-if="current">当前任务：{{ current.query }} · {{ current.mode === 'demo' ? '模拟' : '真实' }} · {{ current.status }}
        <button v-if="researching" @click="cancel">取消研究</button>
      </p>
      <p v-if="error" role="alert">{{ error }}</p>
    </div>
    <ResearchHero
      v-model:query="query"
      :researching="researching"
      :loading-latest="loadingLatest"
      @research="handleResearch"
      @load-latest="loadLatest"
    />

    <RoleProgressGrid
      :role-progress="roleProgress"
      :role-results="results || roleResults"
    />

    <SavedResultsSection :results="results" />
    <section v-if="current" class="task-options">
      <button @click="inspectEvidence">查看证据与基础评测</button>
      <div v-if="evaluation">
        <p>证据 {{ evaluation.evidence_count }} 条 · 五维覆盖 {{ Math.round(evaluation.dimension_coverage * 100) }}% · 引用有效性 {{ evaluation.citation_validity === null ? '无引用可评估' : Math.round(evaluation.citation_validity * 100) + '%' }} · 耗时 {{ evaluation.elapsed_seconds }} 秒</p>
        <p>{{ evaluation.note }}</p>
        <p v-if="evaluation.unknown_citations.length">无对应证据的引用：{{ evaluation.unknown_citations.join(', ') }}</p>
      </div>
      <details v-for="record in evidence" :key="record.id">
        <summary>[{{ record.id }}] {{ record.source || record.platform }} {{ record.synthetic ? '（合成数据）' : '' }}</summary>
        <p>{{ record.text || record.content }}</p>
        <a v-if="safeUrl(record.url)" :href="safeUrl(record.url)" target="_blank" rel="noopener noreferrer">查看原始来源</a>
      </details>
    </section>
    <section class="task-options">
      <h3>研究历史</h3>
      <div v-for="task in tasks" :key="task.research_id" class="history-row">
        <button @click="selectTask(task.research_id)">{{ task.query }}</button>
        <span>{{ task.mode === 'demo' ? '模拟' : '真实' }} · {{ task.status }}</span>
        <button v-if="!['queued', 'running'].includes(task.status)" @click="retry(task.research_id)">重新研究</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.task-options { padding: 1rem; margin-bottom: 1rem; background: var(--ink-light); border: 1px solid var(--border); border-radius: 12px; color: var(--paper-dim) }
.task-options select, .task-options button { background: var(--ink); color: var(--paper); padding: .5rem; margin: .3rem; border: 1px solid var(--border); border-radius: 6px }
.task-options p { margin-top: .6rem; font-size: .85rem }
.history-row { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap }
[role=alert] { color: var(--red) }
</style>
