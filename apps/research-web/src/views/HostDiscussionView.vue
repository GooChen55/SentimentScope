<script setup>
import { computed, ref, onUnmounted, nextTick } from 'vue'
import { startHost, stopHost, getHostDiscussionLog, getResearchDimensions } from '../composables/api.js'
import { DEFAULT_RESEARCH_DIMENSIONS } from '../constants/roles.js'
import HostDiscussionControls from '../components/HostDiscussionControls.vue'
import HostDiscussionDimensionList from '../components/HostDiscussionDimensionList.vue'
import HostDiscussionEmptyState from '../components/HostDiscussionEmptyState.vue'
import HostDiscussionFinalMessages from '../components/HostDiscussionFinalMessages.vue'

const messages = ref([])
const discussionContent = ref(null)
const researchDimensions = ref(DEFAULT_RESEARCH_DIMENSIONS)
const loading = ref(false)
const hostRunning = ref(false)
const error = ref('')
let pollTimer = null

const finalHostMessages = computed(() =>
  messages.value.filter(msg => msg.speaker_name === 'Host Agent' && !msg.dimension_key)
)

const dimensionRows = computed(() =>
  researchDimensions.value.map(dimension => {
    const scoped = messages.value.filter(msg => msg.dimension_key === dimension.key)
    return {
      ...dimension,
      insight: latestBySpeaker(scoped, 'Insight Engine'),
      media: latestBySpeaker(scoped, 'Media Engine'),
      host: latestBySpeaker(scoped, 'Host Agent'),
      count: scoped.length,
    }
  })
)

const hasStructuredMessages = computed(() =>
  finalHostMessages.value.length || dimensionRows.value.some(row => row.count)
)

function latestBySpeaker(items, speakerName) {
  return [...items].reverse().find(msg => msg.speaker_name === speakerName) || null
}

function normalizeDiscussionRecords(data) {
  const records = data?.discussion_records || data?.parsed_messages || []
  return records.map(record => ({
    speaker_name: record.speaker_name || record.sender || '',
    message_text: record.message_text || record.content || '',
    sent_at: record.sent_at || record.timestamp || '',
    dimension_key: record.dimension_key || record.section_key || '',
  }))
}

async function handleStart() {
  error.value = ''
  try {
    const result = await startHost()
    hostRunning.value = Boolean(result.host_running)
    await refreshLog()
    startPolling()
  } catch (e) {
    error.value = '启动主持人失败'
  }
}

async function handleStop() {
  try {
    await stopHost()
    hostRunning.value = false
    stopPolling()
  } catch (e) {
    error.value = '停止主持人失败'
  }
}

async function refreshLog() {
  if (loading.value) return
  loading.value = true
  try {
    const data = await getHostDiscussionLog()
    const records = normalizeDiscussionRecords(data)
    if (JSON.stringify(records) !== JSON.stringify(messages.value)) {
      // Check after the request: the reader may have scrolled while it was pending.
      const el = discussionContent.value
      const followLatest = !el || el.scrollHeight - el.clientHeight - el.scrollTop <= 48
      messages.value = records
      await nextTick()
      if (followLatest) scrollToBottom()
    }
  } catch {} finally {
    loading.value = false
  }
}

async function loadDimensions() {
  try {
    const data = await getResearchDimensions()
    if (Array.isArray(data?.dimensions) && data.dimensions.length) {
      researchDimensions.value = data.dimensions
    }
  } catch {}
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(refreshLog, 3000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function scrollToBottom() {
  const el = discussionContent.value
  if (el) el.scrollTop = el.scrollHeight
}

onUnmounted(stopPolling)

loadDimensions()
refreshLog()
startPolling()
</script>

<template>
  <div class="host-discussion-view">
    <header class="view-header stagger-1">
      <div class="header-overline">HOST DISCUSSION</div>
      <h2 class="view-title">主持人研判讨论</h2>
      <p class="view-desc">主持人按五个研究维度对齐双 Agent 输出，沉淀阶段裁判与最终研判</p>
    </header>

    <p class="view-desc">主持人随研究任务自动运行，取消操作位于研究页。</p>
    <button @click="refreshLog" :disabled="loading" style="margin:1rem 0;padding:.5rem 1rem">刷新讨论</button>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="messages.length" ref="discussionContent" class="host-discussion-content stagger-3">
      <HostDiscussionFinalMessages :messages="finalHostMessages" />
      <HostDiscussionDimensionList v-if="hasStructuredMessages" :rows="dimensionRows" />
    </div>

    <HostDiscussionEmptyState v-else />
  </div>
</template>

<style scoped>
.view-header {
  margin-bottom: 2rem;
}

.header-overline {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.25em;
  color: var(--amber);
  opacity: 0.7;
  margin-bottom: 0.5rem;
}

.view-title {
  font-size: clamp(1.8rem, 4vw, 2.4rem);
  color: var(--paper);
  margin-bottom: 0.4rem;
  letter-spacing: 0.02em;
}

.view-desc {
  color: var(--paper-dim);
  font-size: 0.9rem;
  line-height: 1.6;
}

.error-msg {
  margin-bottom: 1rem;
  padding: 0.8rem 1rem;
  color: var(--red);
  background: var(--red-ghost);
  border: 1px solid rgba(196, 75, 60, 0.25);
  border-radius: var(--radius);
  font-size: 0.82rem;
}

.host-discussion-content {
  max-height: 66vh;
  overflow-y: auto;
  padding-right: 0.5rem;
}
</style>
