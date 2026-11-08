/** Уникальный код: при занятом base — суффиксы 2, 3, ... */
export function uniqueCode(base, taken) {
  if (!taken.has(base)) return base
  let n = 2
  while (taken.has(`${base}${n}`)) n += 1
  return `${base}${n}`
}
