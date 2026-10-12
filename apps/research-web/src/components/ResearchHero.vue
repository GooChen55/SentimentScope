<script setup>
defineProps({
  query: {
    type: String,
    default: '',
  },
  researching: Boolean,
  loadingLatest: Boolean,
})

defineEmits(['update:query', 'research', 'load-latest'])
</script>

<template>
  <section class="research-hero stagger-1">
    <div class="hero-overline">RESEARCH</div>
    <h2 class="hero-title">深度舆情研究</h2>
    <p class="hero-desc">
      双引擎并行分析
      <span class="hero-sep">—</span>
      <span class="hero-pill">数据挖掘</span>
      <span class="hero-pill">舆情分析</span>
    </p>

    <form class="research-form" @submit.prevent="$emit('research')">
      <div class="research-input-wrap">
        <svg class="research-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/>
          <path d="M21 21l-4.35-4.35"/>
        </svg>
        <input
          :value="query"
          class="research-input"
          placeholder="输入研究主题，例如：2026年AI芯片市场趋势..."
          :disabled="researching"
          autofocus
          @input="$emit('update:query', $event.target.value)"
        />
        <button class="research-btn" type="submit" :disabled="!query.trim() || researching">
          <span v-if="!researching" class="btn-label">开始分析</span>
          <span v-else class="btn-label">
            <span class="btn-dot"></span>
            分析中...
          </span>
        </button>
      </div>
    </form>

    <button class="latest-btn" @click="$emit('load-latest')" :disabled="loadingLatest">
      <svg class="latest-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M1 4v6h6M23 20v-6h-6"/>
        <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
      </svg>
      {{ loadingLatest ? '加载中...' : '载入最近分析结果' }}
    </button>
  </section>
</template>

<style scoped>
.research-hero {
  text-align: center;
  padding: 3.5rem 1rem 2.5rem;
  position: relative;
}

.hero-overline {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.25em;
  color: var(--amber);
  margin-bottom: 0.8rem;
  opacity: 0.7;
}

.hero-title {
  font-size: clamp(2.2rem, 5vw, 3.4rem);
  color: var(--paper);
  margin-bottom: 0.6rem;
  letter-spacing: 0.02em;
}

.hero-desc {
  font-size: 0.92rem;
  color: var(--paper-dim);
  margin-bottom: 2.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.hero-sep {
  color: var(--paper-muted);
  margin: 0 0.3rem;
}

.hero-pill {
  padding: 0.2rem 0.8rem;
  background: var(--ink-lighter);
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 0.78rem;
  color: var(--paper-dim);
  letter-spacing: 0.04em;
}

.research-form {
  max-width: 720px;
  margin: 0 auto;
}

.research-input-wrap {
  display: flex;
  align-items: center;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg);
  background: var(--ink-light);
  transition: border-color 0.25s, box-shadow 0.25s;
  overflow: hidden;
}

.research-input-wrap:focus-within {
  border-color: var(--amber);
  box-shadow: 0 0 0 4px var(--amber-ghost);
}

.research-icon {
  width: 20px;
  height: 20px;
  margin-left: 1.2rem;
  color: var(--paper-muted);
  flex-shrink: 0;
}

.research-input {
  flex: 1;
  border: none;
  padding: 1rem 1rem;
  font-size: 1rem;
  background: transparent;
  color: var(--paper);
}

.research-input::placeholder {
  color: var(--paper-muted);
  opacity: 0.5;
}

.research-btn {
  padding: 1rem 2rem;
  background: var(--amber);
  color: var(--ink);
  font-weight: 600;
  font-size: 0.88rem;
  letter-spacing: 0.04em;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.research-btn:hover:not(:disabled) {
  background: var(--amber-bright);
}

.btn-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ink);
  animation: pulse-glow 1.2s ease-in-out infinite;
}

.latest-btn {
  margin-top: 1.4rem;
  padding: 0.55rem 1.4rem;
  background: none;
  color: var(--paper-dim);
  font-size: 0.8rem;
  border: 1px dashed var(--border-strong);
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: border-color 0.2s, color 0.2s;
}

.latest-btn:hover {
  color: var(--amber);
  border-color: var(--amber);
}

.latest-icon {
  width: 15px;
  height: 15px;
}
</style>
