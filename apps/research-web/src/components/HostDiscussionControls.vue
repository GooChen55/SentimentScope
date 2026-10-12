<script setup>
defineProps({
  running: Boolean,
  loading: Boolean,
})

defineEmits(['start', 'stop', 'refresh'])
</script>

<template>
  <div class="host-discussion-controls stagger-2">
    <div class="controls-left">
      <button class="ctrl-btn start" @click="$emit('start')" :disabled="running">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
        启动主持人
      </button>
      <button class="ctrl-btn stop" @click="$emit('stop')" :disabled="!running">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <rect x="4" y="4" width="16" height="16" rx="2"/>
        </svg>
        停止主持人
      </button>
    </div>
    <div class="controls-right">
      <span v-if="running" class="host-discussion-live">
        <span class="live-dot"></span>
        主持人监听中
      </span>
      <span v-else class="host-discussion-idle">主持人已停止</span>
      <button class="ctrl-btn refresh" @click="$emit('refresh')" :disabled="loading">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 4v6h6M23 20v-6h-6"/>
          <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
        </svg>
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.host-discussion-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.4rem;
  background: var(--ink-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.controls-left,
.controls-right {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.ctrl-btn {
  padding: 0.55rem 1.2rem;
  font-size: 0.82rem;
  font-weight: 500;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  letter-spacing: 0.03em;
}

.ctrl-btn.start {
  background: var(--teal);
  color: white;
}

.ctrl-btn.stop {
  background: var(--red);
  color: white;
}

.ctrl-btn.refresh {
  background: none;
  color: var(--paper-dim);
  border: 1px solid var(--border-strong);
}

.ctrl-btn:hover:not(:disabled) {
  filter: brightness(1.12);
}

.host-discussion-live,
.host-discussion-idle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  letter-spacing: 0.04em;
}

.host-discussion-live {
  color: var(--teal);
  font-weight: 500;
}

.host-discussion-idle {
  color: var(--paper-muted);
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--teal);
  animation: pulse-glow 1.5s infinite;
}
</style>
