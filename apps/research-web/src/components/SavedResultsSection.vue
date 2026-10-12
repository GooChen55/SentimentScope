<script setup>
import { ROLE_LABELS } from '../constants/roles.js'

defineProps({
  results: Object,
})
</script>

<template>
  <section v-if="results" class="saved-results stagger-3">
    <div class="saved-header">
      <h3 class="section-title">已保存的分析结果</h3>
      <span class="section-line"></span>
    </div>
    <div class="saved-grid">
      <article
        v-for="(data, role) in results"
        :key="role"
        class="saved-card"
        v-show="data?.final_report"
      >
        <div class="saved-card-top">
          <span class="saved-role">{{ ROLE_LABELS[role] || role }}</span>
          <span class="saved-file">{{ data.report_file || '' }}</span>
        </div>
        <div class="saved-preview">{{ data.final_report?.slice(0, 400) }}</div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.saved-results {
  margin-top: 4rem;
  padding: 0 0.5rem 3rem;
}

.saved-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.8rem;
}

.section-title {
  font-size: 1.4rem;
  color: var(--paper);
  white-space: nowrap;
}

.section-line {
  flex: 1;
  height: 1px;
  background: var(--border);
}

.saved-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1.2rem;
}

.saved-card {
  background: var(--ink-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.4rem;
  transition: border-color 0.3s;
}

.saved-card:hover {
  border-color: var(--border-strong);
}

.saved-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid var(--border);
}

.saved-role {
  font-weight: 500;
  color: var(--amber);
  font-size: 0.82rem;
  letter-spacing: 0.03em;
}

.saved-file {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--paper-muted);
}

.saved-preview {
  font-size: 0.8rem;
  color: var(--paper-dim);
  line-height: 1.75;
  max-height: 160px;
  overflow-y: auto;
}
</style>
