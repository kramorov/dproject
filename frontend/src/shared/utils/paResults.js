// shared/utils/paResults.js
// Преобразует вложенный результат подбора ПП (серия → типоразмеры) в плоский
// список карточек для EngineerProductCard — единый вид карточки в каталоге.

export function paResultsToCards(searchResults) {
  const cards = []
  for (const ml of searchResults || []) {
    for (const item of ml.model_line_items || []) {
      cards.push({
        id: item.model_line_item_id,
        code: item.model_line_item_code || '',
        list_title: item.model_line_item_name || '',
        list_params: [
          { label: 'Серия', value: ml.model_line_name || '' },
          { label: 'Корпус', value: item.body_name || '' },
          { label: 'Тип', value: item.actuator_variety_code || '' },
          { label: 'Запас', value: `${Math.round(item.spring_margin || 0)} Нм` },
        ],
        _ml: ml,
        _item: item,
      })
    }
  }
  return cards
}

// Единая навигация «открыть конфигуратор с предвыбором» для мастера и селектора.
// options — дополнительные предвыбранные опции (safety_position, exd, ip,
// manual_override, body_coating, body_material).
export function buildPaConfigQuery(ml, item, options = {}) {
  return {
    model_line_id: ml?.model_line_id || undefined,
    model_line_item_id: item?.model_line_item_id || undefined,
    variety: item?.actuator_variety_code || undefined,
    ...options,
  }
}
