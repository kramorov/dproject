// Удаление с защитой FK: если сервер вернул 409 с перечнем использования
// (usage: [{label, count}]), спрашиваем подтверждение и повторяем DELETE с
// ?cascade=1 — зависимые строки удаляются вместе с объектом.
// При отказе бросается ошибка с флагом cancelled (тихая отмена).
import api from '@/shared/api'
import { API_PREFIX } from '@/shared/config'

export function deleteCancelled() {
  const e = new Error('cancelled')
  e.cancelled = true
  return e
}

export async function guardedDelete(url) {
  try {
    await api.delete(url)
  } catch (e) {
    const data = e.response && e.response.data
    const usage = data && data.usage
    if (e.response && e.response.status === 409 &&
        Array.isArray(usage) && usage.length) {
      const parts = usage.map(u => `${u.label} (${u.count})`).join(', ')
      const ok = confirm(
        `Удаляемые данные используются в: ${parts}. ` +
        'Действительно удалить вместе с зависимыми записями?')
      if (!ok) throw deleteCancelled()
      // сервер отдаёт абсолютный путь (/api/...), у клиента свой baseURL —
      // префикс снимаем, иначе получится /api/api/...
      const cascadeUrl = data.cascade_url ||
        (url + (url.includes('?') ? '&' : '?') + 'cascade=1')
      const stripped = cascadeUrl.startsWith(API_PREFIX + '/')
        ? cascadeUrl.slice(API_PREFIX.length)
        : cascadeUrl
      await api.delete(stripped)
    } else {
      throw e
    }
  }
}
