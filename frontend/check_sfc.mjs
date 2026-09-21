// Временная проверка компиляции SFC (удаляется после проверки)
import { readFileSync } from 'node:fs'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'

const file = 'src/pages/TableOcrTool.vue'
const src = readFileSync(file, 'utf8')
const { descriptor, errors } = parse(src, { filename: file })
if (errors.length) {
  console.error('PARSE ERRORS:')
  for (const e of errors) console.error(String(e))
  process.exit(1)
}
const script = compileScript(descriptor, { id: 'check' })
const tpl = compileTemplate({
  source: descriptor.template.content,
  filename: file,
  id: 'check',
  compilerOptions: { bindingMetadata: script.bindings },
})
if (tpl.errors.length) {
  console.error('TEMPLATE ERRORS:')
  for (const e of tpl.errors) console.error(String(e))
  process.exit(1)
}
console.log('OK: TableOcrTool.vue compiles (template + script)')
