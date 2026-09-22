// components/admin/useJsonTextMode.js — режим редактирования JSON как текста
// с валидацией. Используется JSON-редакторами EquipmentType (spec_template,
// param_semantics, ai_hints).
import { ref } from 'vue'

export function useJsonTextMode({ getValue, applyValue, isArray }) {
  const rawMode = ref(false)
  const rawText = ref('')
  const rawError = ref('')

  function validate(text) {
    const s = text == null ? '' : String(text)
    if (!s.trim()) return { value: isArray ? [] : {}, error: '' }
    let parsed
    try {
      parsed = JSON.parse(s)
    } catch (e) {
      return { error: 'Невалидный JSON: ' + e.message }
    }
    if (isArray ? !Array.isArray(parsed) : (parsed === null || Array.isArray(parsed) || typeof parsed !== 'object')) {
      return { error: isArray ? 'Ожидается массив JSON' : 'Ожидается объект JSON' }
    }
    return { value: parsed, error: '' }
  }

  function enterRaw() {
    rawText.value = JSON.stringify(getValue(), null, 2)
    rawError.value = ''
    rawMode.value = true
  }

  function applyRaw() {
    const res = validate(rawText.value)
    if (res.error) {
      rawError.value = res.error
      return false
    }
    rawError.value = ''
    applyValue(res.value)
    rawMode.value = false
    return true
  }

  function toggle() {
    if (rawMode.value) applyRaw()
    else enterRaw()
  }

  function onRawInput() {
    rawError.value = validate(rawText.value).error || ''
  }

  function formatRaw() {
    const res = validate(rawText.value)
    if (res.error) {
      rawError.value = res.error
      return
    }
    rawText.value = JSON.stringify(res.value, null, 2)
    rawError.value = ''
  }

  return { rawMode, rawText, rawError, toggle, onRawInput, formatRaw }
}
