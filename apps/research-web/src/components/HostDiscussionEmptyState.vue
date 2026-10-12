<template>
  <div class="host-discussion-empty stagger-3">
    <div class="empty-icon">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="0.8" opacity="0.3">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    </div>
    <p class="empty-title">主持人尚未启动</p>
    <p class="empty-desc">点击「启动主持人」开始 AI 多维研判</p>
  </div>
</template>

<style scoped>
.host-discussion-empty {
  padding: 4rem 2rem;
  text-align: center;
  border: 1px dashed var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.8rem;
}

.empty-title {
  font-size: 1.1rem;
  color: var(--paper-dim);
  font-weight: 500;
}

.empty-desc {
  font-size: 0.82rem;
  color: var(--paper-muted);
}
</style>
