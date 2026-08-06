<template>
  <div class="ai-page">
    <div class="ai-header">
      <h2>{{ schema.title || 'AI подбор' }}</h2>
      <p v-if="schema.description" class="ai-desc">{{ schema.description }}</p>
    </div>

    <!-- Chat area -->
    <div class="ai-chat" ref="chatEl">
      <div v-if="!messages.length" class="ai-empty">
        {{ schema.placeholder || 'Опишите, какое оборудование вам нужно...' }}
      </div>
      <div v-for="(msg, i) in messages" :key="i" class="ai-msg" :class="msg.role">
        <div class="ai-msg-bubble">{{ msg.text }}</div>
        <!-- Suggestion chips from AI -->
        <div v-if="msg.chips && msg.chips.length" class="ai-chat-chips">
          <button
            v-for="chip in msg.chips"
            :key="chip.id"
            class="ai-chip"
            @click="sendChip(chip)"
          >
            {{ chip.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Input area -->
    <div class="ai-input-area">
      <div class="ai-input-row">
        <input
          v-model="inputText"
          type="text"
          class="ai-input"
          :placeholder="schema.placeholder || 'Опишите, какое оборудование вам нужно...'"
          @keydown.enter="sendMessage"
          :disabled="loading"
        />
        <button class="ai-send" @click="sendMessage" :disabled="loading || !inputText.trim()">
          →
        </button>
      </div>

      <!-- Suggestion chips -->
      <div v-if="schema.hints && schema.hints.length" class="ai-hints">
        <button
          v-for="hint in schema.hints"
          :key="hint.id"
          class="ai-chip"
          @click="sendHint(hint)"
        >
          {{ hint.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import globalApi from '@/shared/api'

const props = defineProps({
  equipmentCode: { type: String, required: true },
})

const schema = ref({ title: '', description: '', placeholder: '', hints: [] })
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const chatEl = ref(null)

onMounted(async () => {
  try {
    const { data } = await globalApi.get(`/core/ai-schema/${props.equipmentCode}/`)
    schema.value = data
  } catch (e) {
    console.error('[AiPage] Failed to load schema', e)
  }
})

function scrollToBottom() {
  nextTick(() => {
    if (chatEl.value) chatEl.value.scrollTop = chatEl.value.scrollHeight
  })
}

function sendMessage() {
  const text = inputText.value.trim()
  if (!text) return
  messages.value.push({ role: 'user', text })
  inputText.value = ''
  scrollToBottom()

  // Placeholder AI response
  loading.value = true
  setTimeout(() => {
    messages.value.push({
      role: 'assistant',
      text: 'Это заглушка AI-подбора. Здесь будет ответ от AI-ассистента с уточняющими вопросами.',
      chips: schema.value.hints?.slice(0, 5) || [],
    })
    loading.value = false
    scrollToBottom()
  }, 1000)
}

function sendHint(hint) {
  messages.value.push({ role: 'user', text: hint.label })
  scrollToBottom()
  // Placeholder response
  loading.value = true
  setTimeout(() => {
    messages.value.push({
      role: 'assistant',
      text: `Выбран параметр: ${hint.label}. Здесь будет уточнение от AI.`,
    })
    loading.value = false
    scrollToBottom()
  }, 800)
}

function sendChip(chip) {
  messages.value.push({ role: 'user', text: chip.label })
  scrollToBottom()
}
</script>

<style scoped>
.ai-page {
  max-width: 700px;
  margin: 0 auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  font-family: system-ui, sans-serif;
}
.ai-header { margin-bottom: 1rem; }
.ai-header h2 { margin: 0; font-size: 1.3rem; }
.ai-desc { color: #64748b; margin: 0.25rem 0 0; font-size: 0.9rem; }

.ai-chat {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  background: #f8fafc;
}
.ai-empty { color: #94a3b8; text-align: center; padding: 2rem; }
.ai-msg { margin-bottom: 1rem; }
.ai-msg.user { text-align: right; }
.ai-msg-bubble {
  display: inline-block;
  padding: 0.6rem 1rem;
  border-radius: 12px;
  max-width: 80%;
  font-size: 0.95rem;
  line-height: 1.4;
}
.ai-msg.user .ai-msg-bubble {
  background: #2563eb;
  color: #fff;
}
.ai-msg.assistant .ai-msg-bubble {
  background: #fff;
  border: 1px solid #e2e8f0;
}
.ai-chat-chips { margin-top: 0.5rem; }

.ai-input-area {
  border-top: 1px solid #e2e8f0;
  padding-top: 0.75rem;
}
.ai-input-row { display: flex; gap: 0.5rem; }
.ai-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 1rem;
  outline: none;
}
.ai-input:focus { border-color: #2563eb; }
.ai-send {
  padding: 0.75rem 1.25rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 1.2rem;
  cursor: pointer;
}
.ai-send:disabled { background: #cbd5e1; cursor: not-allowed; }

.ai-hints { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem; }
.ai-chip {
  padding: 0.4rem 1rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  font-size: 0.85rem;
  cursor: pointer;
  color: #334155;
  transition: all 0.15s;
}
.ai-chip:hover { background: #e0e7ff; border-color: #2563eb; color: #1d4ed8; }
</style>
