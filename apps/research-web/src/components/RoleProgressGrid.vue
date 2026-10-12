<script setup>
import { ROLE_LABELS, RESEARCH_ROLE_ORDER, ROLE_SUBTITLE } from '../constants/roles.js'

const props = defineProps({
  roleProgress: Object,
  roleResults: Object,
})

function hasResults(role) {
  return props.roleResults?.[role]?.final_report?.length > 0
}

function progressPct(role) {
  return props.roleProgress?.[role]?.progress_pct || 0
}

function roleStatus(role) {
  if (['error', 'cancelled', 'interrupted'].includes(props.roleProgress?.[role]?.status)) return 'error'
  if (hasResults(role)) return 'done'
  if (progressPct(role) > 0) return 'running'
  return 'idle'
}
</script>

<template>
  <section class="role-grid stagger-2">
    <article
      v-for="role in RESEARCH_ROLE_ORDER"
      :key="role"
      class="role-card"
      :class="roleStatus(role)"
    >
      <div class="card-top">
        <div class="card-badge">
          <span class="badge-dot" :class="roleStatus(role)"></span>
          {{ ROLE_LABELS[role] }}
        </div>
        <span class="card-role-code">{{ role.toUpperCase() }}</span>
      </div>

      <p class="card-subtitle">{{ ROLE_SUBTITLE[role] }}</p>
      <p v-if="roleStatus(role) === 'error'" role="alert">{{ props.roleProgress?.[role]?.message || '研究失败' }}</p>

      <div v-if="roleStatus(role) === 'idle'" class="card-state idle-state">
        <div class="idle-ring">
          <svg viewBox="0 0 48 48" fill="none">
            <circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="0.5" opacity="0.2"/>
            <circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="1" stroke-dasharray="6 4" opacity="0.4"/>
          </svg>
        </div>
        <span class="idle-label">待命中</span>
      </div>

      <div v-if="roleStatus(role) === 'running'" class="card-state run-state">
        <div class="progress-track">
          <div
            class="progress-fill"
            :style="{ width: progressPct(role) + '%' }"
          ></div>
        </div>
        <p class="progress-msg">
          {{ props.roleProgress?.[role]?.message || '分析中...' }}
        </p>
        <span class="progress-num">{{ progressPct(role) }}%</span>
      </div>

      <div v-if="roleStatus(role) === 'done'" class="card-state done-state">
        <div class="done-indicator">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 6L9 17l-5-5"/>
          </svg>
          <span>完成</span>
        </div>
        <div
          class="report-preview"
        >{{ props.roleResults?.[role]?.final_report?.slice(0, 280) }}...</div>
      </div>
    </article>
  </section>
</template>

<style scoped>
.role-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  padding: 0 0.5rem;
}

.role-card {
  background: var(--ink-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
  transition: border-color 0.4s, box-shadow 0.4s;
}

.role-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
}

.role-card.running {
  border-color: rgba(212, 160, 52, 0.35);
  box-shadow: 0 0 30px rgba(212, 160, 52, 0.06);
}

.role-card.done {
  border-color: rgba(74, 157, 143, 0.3);
  box-shadow: 0 0 20px rgba(74, 157, 143, 0.05);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.3rem;
}

.card-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--paper);
}

.badge-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--paper-muted);
  transition: background 0.3s;
}

.badge-dot.running {
  background: var(--amber);
  animation: pulse-glow 1.5s infinite;
}

.badge-dot.done {
  background: var(--teal);
}

.card-role-code {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  color: var(--paper-muted);
  letter-spacing: 0.15em;
  opacity: 0.6;
}

.card-subtitle {
  font-size: 0.72rem;
  color: var(--paper-muted);
  margin-bottom: 1.4rem;
  letter-spacing: 0.04em;
}

.card-state {
  min-height: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.idle-ring {
  width: 52px;
  height: 52px;
  margin-bottom: 0.8rem;
  color: var(--paper-muted);
  animation: spin-slow 18s linear infinite;
}

@keyframes spin-slow {
  to { transform: rotate(360deg); }
}

.idle-label {
  font-size: 0.75rem;
  color: var(--paper-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.run-state {
  gap: 0.8rem;
}

.progress-track {
  width: 100%;
  height: 3px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--amber), var(--amber-bright));
  border-radius: 2px;
  transition: width 0.5s var(--ease-out-expo);
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  animation: shimmer 1.8s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}

.progress-msg {
  font-size: 0.78rem;
  color: var(--paper-dim);
  text-align: center;
  line-height: 1.5;
}

.progress-num {
  font-family: var(--font-mono);
  font-size: 1.6rem;
  color: var(--amber);
  font-weight: 300;
}

.done-indicator {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.8rem;
  color: var(--teal);
}

.done-indicator svg {
  width: 16px;
  height: 16px;
}

.done-indicator span {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.report-preview {
  font-size: 0.76rem;
  color: var(--paper-dim);
  line-height: 1.75;
  max-height: 180px;
  overflow-y: auto;
  word-break: break-word;
  width: 100%;
}

@media (max-width: 900px) {
  .role-grid {
    grid-template-columns: 1fr;
    min-width: 0;
    margin: 0 auto;
  }
}
</style>
