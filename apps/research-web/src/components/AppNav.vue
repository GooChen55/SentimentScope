<script setup>
defineProps({
  tabs: Array,
  activeTab: String,
  completedRoles: Number,
})

const emit = defineEmits(['update:activeTab'])
</script>

<template>
  <nav class="app-nav stagger-2">
    <div class="nav-inner">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="nav-btn"
        :class="{ active: activeTab === tab.key }"
        @click="emit('update:activeTab', tab.key)"
      >
        <span class="nav-label">{{ tab.label }}</span>
        <span class="nav-desc">{{ tab.desc }}</span>
        <span v-if="tab.key === 'research'" class="nav-badge" v-show="completedRoles">
          {{ completedRoles }}/2
        </span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.app-nav {
  padding: 0 2.5rem;
  border-bottom: 1px solid var(--border);
  background: rgba(8, 10, 13, 0.6);
  backdrop-filter: blur(12px);
  position: sticky; top: 0; z-index: 5;
}

.nav-inner {
  display: flex; gap: 0.25rem;
}

.nav-btn {
  position: relative;
  display: flex; flex-direction: column; align-items: flex-start;
  padding: 0.9rem 1.5rem;
  background: none;
  color: var(--paper-muted);
  transition: color 0.2s;
}
.nav-btn::after {
  content: '';
  position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
  background: var(--amber);
  transform: scaleX(0);
  transition: transform 0.25s var(--ease-out-expo);
}
.nav-btn:hover { color: var(--paper-dim); }
.nav-btn.active { color: var(--amber); }
.nav-btn.active::after { transform: scaleX(1); }

.nav-label { font-size: 0.9rem; font-weight: 500; }
.nav-desc { font-size: 0.65rem; color: inherit; opacity: 0.5; letter-spacing: 0.04em; }

.nav-badge {
  position: absolute; top: 0.5rem; right: -4px;
  min-width: 28px; height: 18px;
  display: grid; place-items: center;
  font-family: var(--font-mono); font-size: 0.6rem; font-weight: 500;
  color: var(--ink); background: var(--amber);
  border-radius: 9px; padding: 0 6px;
}
</style>