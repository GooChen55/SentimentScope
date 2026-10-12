<script setup>
import { computed, ref, onMounted } from 'vue'
import { getConfig, updateConfig } from '../composables/api.js'
import { CONFIG_GROUPS, SEARCH_TOOL_FIELDS, SEARCH_TOOL_OPTIONS } from '../constants/configGroups.js'

const config = ref({})
const dirty = ref({})
const saving = ref(false)
const message = ref('')
const messageType = ref('success')

const selectedSearchTool = computed(() => dirty.value.SEARCH_TOOL_TYPE || config.value.SEARCH_TOOL_TYPE || 'TavilyAPI')

onMounted(async () => {
  try {
    const res = await getConfig()
    config.value = res?.config || res || {}
  } catch {}
})

function setDirty(key, value) {
  dirty.value = { ...dirty.value, [key]: value }
}

function isDirty(key) {
  return dirty.value[key] !== undefined
}

function visibleFields(fields, group) {
  if (group !== '搜索工具') return fields

  const visibleSearchFields = new Set(['SEARCH_TOOL_TYPE', ...(SEARCH_TOOL_FIELDS[selectedSearchTool.value] || [])])
  return fields.filter(([key]) => visibleSearchFields.has(key))
}

function fieldValue(key) {
  return isDirty(key) ? dirty.value[key] : config.value[key] || ''
}

async function save() {
  saving.value = true
  message.value = ''
  try {
    const response = await updateConfig(dirty.value)
    config.value = response.config
    dirty.value = {}
    message.value = '配置已保存，部分变更需重启服务后生效'
    messageType.value = 'success'
  } catch (e) {
    message.value = '保存失败: ' + (e.message || '未知错误')
    messageType.value = 'error'
  }
  saving.value = false
}

function maskValue(val) {
  if (!val) return '(未设置)'
  if (val.length > 24) return val.slice(0, 10) + '…' + val.slice(-4)
  return val
}
</script>

<template>
  <div class="config-view">
    <header class="view-header stagger-1">
      <div class="header-overline">CONFIG</div>
      <h2 class="view-title">系统配置</h2>
      <p class="view-desc">管理 LLM 模型、API 密钥、搜索工具和数据库连接。已保存密钥仅显示掩码。</p>
    </header>

    <div class="config-groups">
      <section
        v-for="(fields, group) in CONFIG_GROUPS"
        :key="group"
        class="config-group stagger-2"
      >
        <h3 class="group-title">{{ group }}</h3>
        <div class="config-grid">
          <div
            v-for="[key, label, sensitive] in visibleFields(fields, group)"
            :key="key"
            class="config-field"
            :class="{ dirty: isDirty(key) }"
          >
            <label :for="'cfg-' + key" class="field-label">
              {{ label }}
              <span v-if="sensitive" class="sensitive-tag">密钥</span>
            </label>
            <div class="field-input-wrap">
              <select
                v-if="key === 'SEARCH_TOOL_TYPE'"
                :id="'cfg-' + key"
                :value="fieldValue(key)"
                @change="setDirty(key, $event.target.value)"
                class="field-input field-select"
              >
                <option
                  v-for="option in SEARCH_TOOL_OPTIONS"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
              <input
                v-else
                :id="'cfg-' + key"
                :value="fieldValue(key)"
                @input="setDirty(key, $event.target.value)"
                :type="sensitive ? 'password' : 'text'"
                :placeholder="maskValue(config[key])"
                class="field-input"
              />
              <span v-if="isDirty(key)" class="dirty-dot" title="已修改"></span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div class="config-actions stagger-3">
      <button
        class="save-btn"
        @click="save"
        :disabled="saving || !Object.keys(dirty).length"
      >
        <svg v-if="!saving" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
          <polyline points="17 21 17 13 7 13 7 21"/>
          <polyline points="7 3 7 8 15 8"/>
        </svg>
        {{ saving ? '保存中...' : '保存配置' }}
      </button>
      <div v-if="message" class="config-msg" :class="messageType">
        <svg v-if="messageType === 'success'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        {{ message }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ================================================================
   ConfigView — System configuration
   ================================================================ */

.view-header {
  margin-bottom: 2.5rem;
}

.header-overline {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.25em;
  color: var(--amber);
  margin-bottom: 0.5rem;
  opacity: 0.7;
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

/* Groups */
.config-groups {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.config-group {
  background: var(--ink-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
}
.config-group::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent);
}

.group-title {
  font-family: var(--font-display);
  font-size: 1.1rem;
  color: var(--amber);
  margin-bottom: 1.2rem;
  padding-bottom: 0.7rem;
  border-bottom: 1px solid var(--border);
  letter-spacing: 0.03em;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.1rem;
}

@media (max-width: 700px) {
  .config-grid {
    grid-template-columns: 1fr;
  }
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.field-label {
  font-size: 0.76rem;
  color: var(--paper-dim);
  font-weight: 500;
  letter-spacing: 0.03em;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sensitive-tag {
  font-family: var(--font-mono);
  font-size: 0.58rem;
  color: var(--amber);
  background: var(--amber-ghost);
  padding: 0.15em 0.6em;
  border-radius: 3px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.field-input-wrap {
  position: relative;
}

.field-input {
  width: 100%;
  font-size: 0.84rem;
  padding: 0.6em 0.9em;
  background: var(--ink);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--paper);
  outline: none;
  transition: border-color 0.25s, box-shadow 0.25s;
  font-family: var(--font-mono);
}
.field-input:focus {
  border-color: var(--amber);
  box-shadow: 0 0 0 3px var(--amber-ghost);
}
.field-input::placeholder {
  color: var(--paper-muted);
  opacity: 0.4;
}

.field-select {
  appearance: none;
  cursor: pointer;
  padding-right: 2.2em;
  background:
    linear-gradient(45deg, transparent 50%, var(--amber) 50%) calc(100% - 16px) 50% / 5px 5px no-repeat,
    linear-gradient(135deg, var(--amber) 50%, transparent 50%) calc(100% - 11px) 50% / 5px 5px no-repeat,
    var(--ink);
  color-scheme: dark;
}

.field-select option {
  background: var(--ink);
  color: var(--paper);
}

.config-field.dirty .field-input {
  border-color: rgba(212, 160, 52, 0.35);
}

.dirty-dot {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--amber);
  pointer-events: none;
}

/* Actions */
.config-actions {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  margin-top: 2rem;
  flex-wrap: wrap;
}

.save-btn {
  padding: 0.7rem 2rem;
  background: var(--amber);
  color: var(--ink);
  font-weight: 600;
  font-size: 0.88rem;
  letter-spacing: 0.03em;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.save-btn:hover:not(:disabled) {
  background: var(--amber-bright);
}

.config-msg {
  font-size: 0.82rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
}
.config-msg.success {
  color: var(--teal);
  background: var(--teal-ghost);
}
.config-msg.error {
  color: var(--red);
  background: var(--red-ghost);
}
</style>
