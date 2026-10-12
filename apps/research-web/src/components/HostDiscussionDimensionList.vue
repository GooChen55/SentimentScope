<script setup>
import { SENDER_STYLE } from '../constants/roles.js'

defineProps({
  rows: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <section class="dimension-list">
    <article
      v-for="row in rows"
      :key="row.key"
      class="dimension-panel"
      :class="{ complete: row.host, waiting: row.count && !row.host }"
    >
      <div class="dimension-head">
        <span class="dimension-index">{{ row.index }}</span>
        <div>
          <h3 class="dimension-title">{{ row.title }}</h3>
          <p class="dimension-state">
            <span v-if="row.host">主持人已完成阶段裁判</span>
            <span v-else-if="row.count">等待同维度双 Agent 对齐</span>
            <span v-else>暂无该维度发言</span>
          </p>
        </div>
      </div>

      <div v-if="row.host" class="host-judgement">
        <div class="msg-meta">
          <span class="msg-sender" :style="{ color: SENDER_STYLE[row.host.speaker_name]?.color }">
            <span class="msg-icon">{{ SENDER_STYLE[row.host.speaker_name]?.icon }}</span>
            {{ row.host.speaker_name }}
          </span>
          <span class="msg-role">{{ SENDER_STYLE[row.host.speaker_name]?.role }}</span>
          <span class="msg-time">{{ row.host.sent_at }}</span>
        </div>
        <div class="msg-content">{{ row.host.message_text }}</div>
      </div>

      <div v-else class="host-placeholder">
        <span class="pending-dot"></span>
        <span>等待主持人裁判</span>
      </div>

      <details class="agent-details">
        <summary>
          <span>查看双 Agent 摘要</span>
          <span class="detail-count">{{ [row.insight, row.media].filter(Boolean).length }}/2</span>
        </summary>
        <div class="agent-grid">
          <article class="agent-summary" :class="{ empty: !row.insight }">
            <div class="summary-title" :style="{ color: SENDER_STYLE['Insight Engine'].color }">
              <span>{{ SENDER_STYLE['Insight Engine'].icon }}</span>
              Insight 摘要
            </div>
            <p v-if="row.insight" class="msg-content">{{ row.insight.message_text }}</p>
            <p v-else class="summary-empty">尚未收到该维度摘要</p>
          </article>
          <article class="agent-summary" :class="{ empty: !row.media }">
            <div class="summary-title" :style="{ color: SENDER_STYLE['Media Engine'].color }">
              <span>{{ SENDER_STYLE['Media Engine'].icon }}</span>
              Media 摘要
            </div>
            <p v-if="row.media" class="msg-content">{{ row.media.message_text }}</p>
            <p v-else class="summary-empty">尚未收到该维度摘要</p>
          </article>
        </div>
      </details>
    </article>
  </section>
</template>

<style scoped>
.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.dimension-panel {
  padding: 1rem 1.2rem;
  transition: border-color 0.25s;
  background: var(--ink-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.dimension-panel.complete {
  border-color: rgba(74, 157, 143, 0.28);
}

.dimension-panel.waiting {
  border-color: rgba(212, 160, 52, 0.22);
}

.dimension-head {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 0.9rem;
}

.dimension-index {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--amber);
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  padding: 0.2rem 0.5rem;
}

.dimension-title {
  font-family: var(--font-body);
  font-size: 1rem;
  font-weight: 600;
  color: var(--paper);
  letter-spacing: 0;
}

.dimension-state {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--paper-muted);
}

.host-judgement {
  padding: 0.95rem 1rem;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.host-placeholder {
  min-height: 48px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--paper-muted);
  font-size: 0.8rem;
  border: 1px dashed var(--border);
  border-radius: var(--radius-md);
  padding: 0 1rem;
}

.pending-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--paper-muted);
}

.agent-details {
  margin-top: 0.8rem;
}

.agent-details summary {
  cursor: pointer;
  color: var(--paper-dim);
  font-size: 0.78rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.45rem 0;
}

.detail-count {
  font-family: var(--font-mono);
  color: var(--paper-muted);
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.8rem;
  margin-top: 0.5rem;
}

.agent-summary {
  min-height: 140px;
  padding: 0.9rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.12);
}

.agent-summary.empty {
  border-style: dashed;
}

.summary-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 600;
  margin-bottom: 0.55rem;
}

.summary-empty {
  color: var(--paper-muted);
  font-size: 0.78rem;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.5rem;
}

.msg-icon {
  font-size: 0.7rem;
}

.msg-sender {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.msg-role {
  font-size: 0.65rem;
  color: var(--paper-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.msg-time {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--paper-muted);
}

.msg-content {
  font-size: 0.84rem;
  color: var(--paper-dim);
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 760px) {
  .agent-grid {
    grid-template-columns: 1fr;
  }

  .msg-meta {
    flex-wrap: wrap;
  }

  .msg-time {
    margin-left: 0;
  }
}
</style>
