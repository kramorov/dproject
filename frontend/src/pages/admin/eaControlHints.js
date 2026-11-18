// Доменные подсказки слотов БУ — вынесены из generic-рендера конфигуратора.
// Рендер-слой не знает кодов БУ (CU_POWER_SUPPLY / CU_CABLE_GLANDS / PU_SHARED):
// он передаёт текущий выбор и колбэк видимости, а все коды живут здесь.

export function slotHint(slot, selection, isVisible) {
  if (slot.code !== 'CU_POWER_SUPPLY') return ''
  const pu = selection['CU_POWER_SUPPLY']
  if (!pu) return ''
  const glandsVisible = isVisible('CU_CABLE_GLANDS')
  if (pu === 'PU_SHARED') {
    return glandsVisible
      ? 'отверстия для подбора КВ: корпус привода + БУ'
      : 'отверстия для подбора КВ: корпус привода'
  }
  return 'отверстия для подбора КВ: БУ (отдельный кабель)'
}
