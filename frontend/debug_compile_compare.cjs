/* Сравнить компиляцию селекта «Раздел» с @change и без него. */
const fs = require('fs')
const { parse, compileTemplate } = require('@vue/compiler-sfc')

const src = fs.readFileSync('src/pages/admin/EaControlStructurePage.vue', 'utf8')
const { descriptor } = parse(src)
const t = descriptor.template.content

const tWith = t
const tWithout = t.replace('@change="onSectionChange"', '')

function findSelect(code) {
  const i = code.indexOf('_createElementVNode("select"')
  if (i < 0) return '(select не найден)'
  return code.slice(i, i + 1100)
}

console.log('=== WITH @change ===')
console.log(findSelect(compileTemplate({ source: tWith, id: 'w' }).code))
console.log()
console.log('=== WITHOUT @change ===')
console.log(findSelect(compileTemplate({ source: tWithout, id: 'n' }).code))
