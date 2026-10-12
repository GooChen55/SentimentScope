<script setup>
defineProps({ query: { type: String, default: '' }, researching: Boolean, loadingLatest: Boolean, mode: String })
defineEmits(['update:query', 'research', 'load-latest'])
const steps = [
  { n: '01', title: '检索证据', text: '本地内容与公开信息，保留可核对来源。' },
  { n: '02', title: '双源分析', text: 'Insight 与 Media 从不同视角并行研究。' },
  { n: '03', title: '综合研判', text: 'Host 按五个维度组织讨论，形成报告。' },
]
</script>

<template>
  <section class="research-hero">
    <div class="hero-content">
      <div class="hero-overline"><span></span> RESEARCH WORKSPACE</div>
      <h2>从多源证据，<br />到清晰的舆情判断<span class="title-dot">。</span></h2>
      <p class="hero-desc">让数据、观点与结论相互印证。选择主题，开始一次可追溯的研究。</p>
      <form @submit.prevent="$emit('research')">
        <label for="research-topic" class="input-label">研究主题</label>
        <div class="research-input-wrap">
          <input id="research-topic" :value="query" :readonly="mode === 'demo'" :disabled="researching"
            :placeholder="mode === 'demo' ? '示例品牌配送调整' : '输入事件、品牌或关键词，例如：考研趋势'"
            @input="$emit('update:query', $event.target.value)" />
          <button class="research-btn" type="submit" :disabled="!query.trim() || researching">
            {{ researching ? '分析进行中…' : '开始分析' }} <span v-if="!researching" aria-hidden="true">↗</span>
          </button>
        </div>
      </form>
      <div class="hero-actions">
        <span>{{ mode === 'demo' ? '固定合成样例 · 无模型调用' : '真实分析 · 需配置模型与搜索服务' }}</span>
        <button @click="$emit('load-latest')" :disabled="loadingLatest">{{ loadingLatest ? '正在加载…' : '打开最近完成的研究 →' }}</button>
      </div>
    </div>
    <aside class="workflow" aria-label="研究流程">
      <div class="workflow-label">一次研究，三个阶段</div>
      <div v-for="step in steps" :key="step.n" class="workflow-step">
        <span class="step-number">{{ step.n }}</span>
        <div><h3>{{ step.title }}</h3><p>{{ step.text }}</p></div>
      </div>
      <div class="workflow-foot">证据快照 <span>·</span> 五维讨论 <span>·</span> 报告导出</div>
    </aside>
  </section>
</template>

<style scoped>
.research-hero { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(280px, 1fr); gap: 3rem; padding: 2.5rem; margin-bottom: 1.5rem; background: radial-gradient(ellipse at 0 0, rgba(212,160,52,.08), transparent 65%), var(--ink-light); border: 1px solid var(--border-strong); border-radius: 18px; }
.hero-content { min-width: 0; }
.hero-overline { display: flex; align-items: center; gap: .5rem; font: .65rem var(--font-mono); letter-spacing: .15em; color: var(--amber); margin-bottom: 1rem; }
.hero-overline span { width: 6px; height: 6px; border-radius: 50%; background: var(--amber); }
h2 { font-family: var(--font-body); font-size: clamp(1.65rem, 3vw, 2.6rem); line-height: 1.4; font-weight: 600; letter-spacing: -.03em; }
.title-dot { color: var(--amber); }
.hero-desc { color: var(--paper-dim); font-size: .85rem; line-height: 1.8; margin: 1rem 0 1.6rem; }
.input-label { display: block; color: var(--paper-dim); font-size: .75rem; margin-bottom: .6rem; }
.research-input-wrap { display: flex; padding: .35rem; border: 1px solid var(--border-strong); border-radius: 10px; background: var(--ink); }
.research-input-wrap:focus-within { border-color: var(--amber); box-shadow: 0 0 0 3px var(--amber-ghost); }
input { flex: 1; min-width: 0; border: none; box-shadow: none !important; background: transparent; padding: .75rem; font-size: .88rem; }
input::placeholder { color: var(--paper-muted); }
.research-btn { flex-shrink: 0; padding: .8rem 1.2rem; background: var(--amber); color: var(--ink); border-radius: 7px; font-weight: 600; white-space: nowrap; }
.research-btn:hover:not(:disabled) { background: var(--amber-bright); }
.hero-actions { display: flex; justify-content: space-between; flex-wrap: wrap; gap: .75rem; margin-top: 1rem; font-size: .7rem; color: var(--paper-muted); }
.hero-actions button { color: var(--paper-dim); background: none; }
.hero-actions button:hover { color: var(--amber); }
.workflow { align-self: center; padding: 1.5rem; background: rgba(8,10,13,.55); border: 1px solid var(--border); border-radius: 12px; }
.workflow-label { color: var(--paper-muted); font-size: .75rem; margin-bottom: 1.4rem; }
.workflow-step { display: flex; gap: 1rem; margin-bottom: 1.3rem; }
.step-number { color: var(--amber); font: .75rem var(--font-mono); padding-top: .25rem; }
.workflow-step h3 { font: 500 .85rem var(--font-body); margin-bottom: .4rem; }
.workflow-step p { font-size: .73rem; line-height: 1.7; color: var(--paper-dim); }
.workflow-foot { padding-top: .9rem; border-top: 1px solid var(--border); font-size: .65rem; color: var(--paper-muted); display: flex; justify-content: space-between; }
@media(max-width: 1000px) { .research-hero { gap: 1.5rem; padding: 1.5rem; } }
@media(max-width: 760px) { .research-hero { grid-template-columns: 1fr; padding: 1.25rem; } .workflow { display: none; } }
@media(max-width: 430px) { .research-input-wrap { flex-wrap: wrap; } input { flex-basis: 100%; } .research-btn { width: 100%; } }
</style>
