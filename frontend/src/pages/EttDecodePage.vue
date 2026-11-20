<template>
  <div class="ett-page">
    <h1>{{ t('ett.title') }}</h1>
    <p class="ett-lead">{{ t('ett.lead') }}</p>

    <div class="ett-form">
      <label class="ett-label" for="ett-code">{{ t('ett.inputLabel') }}</label>
      <input
        id="ett-code"
        v-model="code"
        class="ett-input"
        type="text"
        :placeholder="t('ett.placeholder')"
        @keyup.enter="decode"
      />
      <button class="ett-button" :disabled="loading" @click="decode">
        {{ loading ? t('ett.decoding') : t('ett.decode') }}
      </button>
    </div>

    <!-- Ошибка -->
    <div v-if="error" class="ett-block ett-error" role="alert">
      {{ error }}
    </div>

    <!-- Результат -->
    <div v-if="rows.length" class="ett-block ett-result">
      <h2>{{ t('ett.resultTitle') }}</h2>
      <table class="ett-table">
        <tbody>
          <tr v-for="(row, i) in rows" :key="i">
            <td class="ett-param">{{ row.param_name }}</td>
            <td class="ett-value">{{ row.param_value }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/shared/api'
import { useI18n } from '@/shared/i18n'

const { t } = useI18n()

const code = ref('')
const rows = ref([])
const error = ref('')
const loading = ref(false)

async function decode() {
  const value = code.value.trim()
  error.value = ''
  rows.value = []

  // Проверка на пустоту — до отправки на бэк.
  if (!value) {
    error.value = t('ett.emptyError')
    return
  }

  loading.value = true
  try {
    const { data } = await api.post('/ett/decode/', { code: value })
    rows.value = Array.isArray(data.desc_table) ? data.desc_table : []
    if (!rows.value.length) {
      error.value = t('ett.noResult')
    }
  } catch (err) {
    error.value = err.displayMessage || err.message || t('ett.unknownError')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.ett-page {
  max-width: 860px;
  margin: 0 auto;
  padding: 24px 16px 48px;
  font-family: system-ui, sans-serif;
}
h1 {
  font-size: 22px;
  color: #1f2937;
  margin-bottom: 8px;
}
.ett-lead {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 20px;
}
.ett-form {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  flex-wrap: wrap;
}
.ett-label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #374151;
  flex: 1 1 320px;
}
.ett-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}
.ett-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}
.ett-button {
  padding: 10px 20px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}
.ett-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.ett-block {
  margin-top: 20px;
  padding: 14px 16px;
  border-radius: 8px;
  font-size: 14px;
}
.ett-error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}
.ett-result {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}
.ett-result h2 {
  font-size: 16px;
  color: #1f2937;
  margin: 0 0 12px;
}
.ett-table {
  width: 100%;
  border-collapse: collapse;
}
.ett-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #eef0f3;
  vertical-align: top;
}
.ett-table tr:last-child td {
  border-bottom: none;
}
.ett-param {
  width: 45%;
  color: #6b7280;
}
.ett-value {
  color: #1f2937;
}
</style>
