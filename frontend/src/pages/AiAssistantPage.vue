<template>
  <div class="ai-page">
    <h1>AI Ассистент</h1>

    <div class="input-section">
      <textarea
        v-model="query"
        placeholder="Введите запрос, например: подбери пневмопривод для дискового затвора ДУ300 с моментом 150"
        :disabled="loading"
        @keydown.ctrl.enter="submit"
      />
      <button :disabled="loading || !query.trim()" @click="submit">
        {{ loading ? 'Обработка...' : 'Отправить (Ctrl+Enter)' }}
      </button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="result" class="result-panel">
      <h3>Результат</h3>
      <div class="field"><b>Intent:</b> {{ result.intent }} | <b>Confidence:</b> {{ (result.confidence * 100).toFixed(0) }}%</div>
      <div class="field"><b>Conversation:</b> #{{ result.conversation_id }}</div>
      <div class="field"><b>Ответ:</b> {{ result.reply_text }}</div>

      <details v-if="result.decompose_text" open>
        <summary>Pass 0: Анализ запроса (deepseek-v4-pro)</summary>
        <pre class="decompose">{{ result.decompose_text }}</pre>
      </details>

      <div v-if="result.sub_requests && result.sub_requests.length">
        <h4>Подзапросы ({{ result.sub_requests.length }})</h4>
        <div v-for="(sr, idx) in result.sub_requests" :key="idx" class="sub-request">
          <details>
            <summary><b>#{{ idx + 1 }}</b> {{ sr.intent }}{{ sr.equipment_type ? ' • ' + sr.equipment_type : '' }} — {{ sr.reply }}</summary>
            <div class="field"><b>Текст:</b> {{ sr.text }}</div>
            <div class="field"><b>Intent:</b> {{ sr.intent }} (hint: {{ sr.intent_hint }})</div>
            <template v-if="sr.raw_filters && Object.keys(sr.raw_filters).length">
              <p><b>Pass 1 — Raw:</b></p>
              <pre>{{ JSON.stringify(sr.raw_filters, null, 2) }}</pre>
            </template>
            <template v-if="sr.resolved_ids && Object.keys(sr.resolved_ids).length">
              <p><b>Pass 2 — Resolved:</b></p>
              <pre>{{ JSON.stringify(sr.resolved_ids, null, 2) }}</pre>
            </template>
            <template v-if="sr.search_results && Object.keys(sr.search_results).length">
              <p><b>Результат:</b></p>
              <pre>{{ JSON.stringify(sr.search_results, null, 2) }}</pre>
            </template>
          </details>
        </div>
      </div>
    </div>

    <div v-if="stats.length" class="stats-panel">
      <h3>Статистика токенов</h3>
      <table>
        <thead>
          <tr><th>#</th><th>Intent</th><th>Confidence</th><th>Tokens</th><th>Cost ($)</th><th>Latency</th></tr>
        </thead>
        <tbody>
          <tr v-for="s in stats" :key="s.id">
            <td>{{ s.id }}</td>
            <td>{{ s.intent }}</td>
            <td>{{ (s.confidence * 100).toFixed(0) }}%</td>
            <td>{{ s.tokens || '-' }}</td>
            <td>{{ s.cost || '-' }}</td>
            <td>{{ s.latency_ms ? s.latency_ms + 'ms' : '-' }}</td>
          </tr>
        </tbody>
      </table>
      <div class="totals">
        <b>Всего токенов:</b> {{ totalTokens }} &nbsp;|&nbsp;
        <b>Всего cost:</b> ${{ totalCost.toFixed(6) }}
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/shared/api'

export default {
  name: 'AiAssistantPage',
  data() {
    return {
      query: '',
      loading: false,
      error: '',
      result: null,
      stats: [],
    }
  },
  computed: {
    totalTokens() {
      return this.stats.reduce((sum, s) => sum + (s.tokens || 0), 0)
    },
    totalCost() {
      return this.stats.reduce((sum, s) => sum + (s.cost || 0), 0)
    },
  },
  methods: {
    async submit() {
      if (!this.query.trim() || this.loading) return
      this.loading = true
      this.error = ''
      this.result = null
      try {
        const { data } = await api.post('/ai-assistant/query/', { text: this.query.trim() })
        this.result = data
        this.stats.push({
          id: data.conversation_id,
          intent: data.intent,
          confidence: data.confidence,
          tokens: data.total_tokens,
          cost: data.total_cost,
          latency_ms: data.latency_ms,
        })
      } catch (e) {
        this.error = e.displayMessage || e.message || 'Ошибка запроса'
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.ai-page { max-width: 800px; margin: 0 auto; padding: 20px; }
h1 { margin-bottom: 16px; }
.input-section { display: flex; gap: 10px; margin-bottom: 16px; }
textarea { flex: 1; height: 80px; padding: 10px; font-size: 14px; border: 1px solid #ccc; border-radius: 6px; resize: vertical; }
textarea:disabled { background: #f5f5f5; }
button { padding: 10px 24px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; white-space: nowrap; }
button:disabled { background: #94a3b8; cursor: default; }
.error { color: #dc2626; background: #fef2f2; padding: 10px; border-radius: 6px; margin-bottom: 16px; }

.result-panel { background: #f0fdf4; border: 1px solid #86efac; padding: 16px; border-radius: 8px; margin-bottom: 16px; }
.result-panel .field { margin-bottom: 6px; }
.result-panel details { margin-top: 10px; }
.result-panel pre { background: #fff; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px; }
.result-panel .decompose { white-space: pre-wrap; font-size: 14px; line-height: 1.5; }

.stats-panel { background: #f8fafc; border: 1px solid #e2e8f0; padding: 16px; border-radius: 8px; }
.stats-panel table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
.stats-panel th, .stats-panel td { padding: 6px 10px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 13px; }
.stats-panel th { background: #f1f5f9; }
.totals { font-size: 14px; color: #334155; }
</style>
