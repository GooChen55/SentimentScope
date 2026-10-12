<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import type { Platform } from '@/types'

const api = useApi()
const platformList = ref<Platform[]>([])
const dbStatus = ref<'idle' | 'running' | 'success' | 'error'>('idle')
const dbResult = ref<string>('')
const dbElapsed = ref(0)
const dbError = ref<string | null>(null)

const dbForm = reactive({
  host: '127.0.0.1',
  port: 13326,
  user: 'sentiment',
  password: '',
  db_name: 'sentiment_demo',
  charset: 'utf8mb4',
})

onMounted(async () => {
  try {
    const opts = await api.fetchConfigOptions()
    platformList.value = opts.supported_platforms
  } catch {}
})

async function handleInitDb() {
  dbStatus.value = 'running'
  dbResult.value = ''
  dbError.value = null
  try {
    const res = await api.initDb({ ...dbForm })
    if (res.success) {
      dbStatus.value = 'success'
      dbResult.value = `成功创建 ${res.tables_created.join(', ')}`
      dbElapsed.value = res.elapsed_seconds
    } else {
      dbStatus.value = 'error'
      dbError.value = res.error || '初始化失败'
    }
  } catch (e: any) {
    dbStatus.value = 'error'
    dbError.value = e.message
  }
}
</script>

<template>
  <div class="p-6 space-y-6 animate-fade-in">
    <div>
      <h2 class="text-lg font-display font-semibold text-terminal-text">设置</h2>
      <p class="text-sm text-terminal-muted mt-0.5">数据库初始化与系统信息</p>
    </div>

    <!-- 数据库初始化表单 -->
    <div class="bg-terminal-panel border border-terminal-border rounded-lg p-5 max-w-lg">
      <h3 class="text-sm font-display font-semibold text-terminal-text mb-4">数据库初始化</h3>

      <div class="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label class="text-xs text-terminal-muted">主机地址</label>
          <input
            v-model="dbForm.host"
            class="w-full mt-1 bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm font-mono text-terminal-text focus:border-terminal-green focus:outline-none"
            placeholder="127.0.0.1"
          />
        </div>
        <div>
          <label class="text-xs text-terminal-muted">端口</label>
          <input
            v-model.number="dbForm.port"
            type="number"
            class="w-full mt-1 bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm font-mono text-terminal-text focus:border-terminal-green focus:outline-none"
          />
        </div>
        <div>
          <label class="text-xs text-terminal-muted">用户名</label>
          <input
            v-model="dbForm.user"
            class="w-full mt-1 bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm font-mono text-terminal-text focus:border-terminal-green focus:outline-none"
            placeholder="root"
          />
        </div>
        <div>
          <label class="text-xs text-terminal-muted">密码</label>
          <input
            v-model="dbForm.password"
            type="password"
            class="w-full mt-1 bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm font-mono text-terminal-text focus:border-terminal-green focus:outline-none"
          />
        </div>
        <div>
          <label class="text-xs text-terminal-muted">数据库名 <span class="text-terminal-muted/60">（请先在 MySQL 中创建此库）</span></label>
          <input
            v-model="dbForm.db_name"
            class="w-full mt-1 bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm font-mono text-terminal-text focus:border-terminal-green focus:outline-none"
            placeholder="media_crawler"
          />
        </div>
        <div>
          <label class="text-xs text-terminal-muted">字符集</label>
          <select
            v-model="dbForm.charset"
            class="w-full mt-1 bg-terminal-bg border border-terminal-border rounded px-3 py-1.5 text-sm font-mono text-terminal-text focus:border-terminal-green focus:outline-none"
          >
            <option value="utf8mb4">utf8mb4</option>
            <option value="utf8">utf8</option>
          </select>
        </div>
      </div>

      <button
        @click="handleInitDb"
        :disabled="dbStatus === 'running'"
        class="px-5 py-2 rounded text-sm font-semibold font-display transition-all"
        :class="dbStatus === 'running'
          ? 'bg-terminal-muted text-terminal-bg cursor-wait'
          : dbStatus === 'success'
            ? 'bg-terminal-green text-black'
            : dbStatus === 'error'
              ? 'bg-terminal-red text-white'
              : 'bg-terminal-blue text-white hover:bg-terminal-blue/80'"
      >
        <span v-if="dbStatus === 'running'" class="spinner inline-block mr-2">◌</span>
        {{ dbStatus === 'idle' ? '初始化数据库' : dbStatus === 'running' ? '初始化中...' :
           dbStatus === 'success' ? '初始化成功' : '初始化失败 (点击重试)' }}
      </button>

      <div v-if="dbStatus === 'success'" class="mt-3 text-sm text-terminal-green font-mono">
        {{ dbResult }} · 耗时 {{ dbElapsed }}s
      </div>
      <div v-if="dbStatus === 'error' && dbError" class="mt-3 text-sm text-terminal-red font-mono">
        {{ dbError }}
      </div>
    </div>

    <!-- 平台信息 -->
    <div>
      <h3 class="text-sm font-display font-semibold text-terminal-text mb-3">支持的平台</h3>
      <div class="grid grid-cols-4 gap-3">
        <div
          v-for="p in platformList" :key="p.value"
          class="bg-terminal-panel border border-terminal-border rounded-lg p-3 hover:border-terminal-border/60 transition-colors"
        >
          <div class="font-display text-sm font-semibold text-terminal-text">{{ p.label }}</div>
          <div class="text-xs text-terminal-muted font-mono mt-0.5">{{ p.value }}</div>
          <div class="text-xs text-terminal-muted mt-1.5 leading-relaxed">{{ p.description }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
