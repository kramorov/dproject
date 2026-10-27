/* Отладка: перенос слота SETPOINT ИЗ его текущего раздела В «Дистанционное
 * управление» (CMD_INPUTS, id 11) — сценарий, на котором сейчас падает.
 *
 * Запуск:  cd frontend && node debug_repro_slot_section.cjs
 * Вход — впрыснутая sessionid-кука (файл debug_sessionid.txt).
 */
const fs = require('fs')
const puppeteer = require('puppeteer')

const BASE = 'http://localhost:5173'
const TARGET_SECTION_ID = '11' // CMD_INPUTS «Дистанционное управление»

const sessionRaw = fs.readFileSync('debug_sessionid.txt', 'utf8').trim()
if (!sessionRaw) {
  console.error('Нет debug_sessionid.txt — сначала создай сессию (manage.py shell).')
  process.exit(1)
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

async function main() {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1680, height: 1050 })

  page.on('console', m => {
    const t = m.text()
    console.log('CONSOLE', t.startsWith('[DEBUG]') ? '' : `(${m.type()})`, t)
  })
  page.on('pageerror', e => console.log('PAGEERROR', e.message))
  page.on('request', req => {
    const u = req.url()
    if (req.method() !== 'GET' && u.includes('/ea-control/')) {
      console.log('REQ ', req.method(), u, req.postData() ? 'BODY=' + req.postData() : '')
    }
  })
  page.on('response', async res => {
    const u = res.url()
    if (res.request().method() !== 'GET' && u.includes('/ea-control/slots')) {
      let body = ''
      try { body = await res.text() } catch (e) { /* noop */ }
      console.log('RESP', res.status(), u, body.slice(0, 600))
    }
  })

  await page.setCookie({ name: 'sessionid', value: sessionRaw, url: BASE + '/' })

  console.log('== goto', BASE + '/admin/ea-control')
  await page.goto(BASE + '/admin/ea-control', { waitUntil: 'networkidle2', timeout: 90000 })
  await page.waitForSelector('.node-item', { timeout: 30000 })
  await sleep(500)

  const nodeInfo = []
  for (const n of await page.$$('.node-item')) {
    const label = await n.$eval('.label', el => el.textContent.trim()).catch(() => '')
    const code = await n.$eval('.code', el => el.textContent.trim()).catch(() => '')
    nodeInfo.push(`${label} [${code}]`)
  }
  console.log('== узлы слева:', nodeInfo.join(' | '))

  // ── 1. найти узел, в котором сейчас лежит SETPOINT, и кликнуть ───────
  let found = false
  for (const n of await page.$$('.node-item')) {
    await n.click()
    await sleep(400)
    const chips = await page.$$('.chip')
    let has = false
    for (const c of chips) {
      const text = await c.evaluate(el => el.textContent.trim())
      if (/SETPOINT/.test(text) || /Установка положения/.test(text)) { has = true; break }
    }
    const code = await n.$eval('.code', el => el.textContent.trim()).catch(() => '')
    if (has) {
      console.log('== SETPOINT найден в узле', code)
      found = true
      break
    }
  }
  if (!found) throw new Error('узел со слотом SETPOINT не найден')

  // ── 2. кликнуть чип SETPOINT ─────────────────────────────────────────
  let slotClicked = false
  for (const c of await page.$$('.chip')) {
    const text = await c.evaluate(el => el.textContent.trim())
    if (/SETPOINT/.test(text) || /Установка положения/.test(text)) {
      await c.click()
      slotClicked = true
      break
    }
  }
  if (!slotClicked) throw new Error('чип SETPOINT не найден')
  await page.waitForSelector('.editor.nested select', { timeout: 10000 })
  await sleep(300)

  // ── 3. сменить раздел на CMD_INPUTS (11) через новый dropdown ───────
  await page.waitForSelector('.editor.nested .sp-btn', { timeout: 10000 })
  const valText = () => page.$eval('.editor.nested .sp-val', el => el.textContent.trim())
  console.log('== раздел ДО смены:', await valText())
  await page.click('.editor.nested .sp-btn')
  await sleep(300)
  let picked = false
  for (const item of await page.$$('.editor.nested .sp-item')) {
    const text = await item.evaluate(el => el.textContent.trim())
    if (text === 'Дистанционное управление') {
      await item.click()
      picked = true
      break
    }
  }
  if (!picked) throw new Error('пункт «Дистанционное управление» не найден в меню')
  console.log('== раздел ПОСЛЕ смены:', await valText())

  // ── 4. «Сохранить» в редакторе слота ────────────────────────────────
  const btn = await page.evaluateHandle(() => {
    const editor = document.querySelector('.editor.nested')
    if (!editor) return null
    const btns = [...editor.querySelectorAll('.editor-actions .ea-btn')]
    return btns.find(b => b.textContent.trim() === 'Сохранить') || null
  })
  const btnEl = btn.asElement()
  if (!btnEl) throw new Error('кнопка «Сохранить» слота не найдена')
  console.log('== кнопка «Сохранить» слота disabled =', await btnEl.evaluate(el => el.disabled))
  await btnEl.click()

  // ── 5. баннер ────────────────────────────────────────────────────────
  const banner = await page.waitForFunction(() => {
    const ok = document.querySelector('.save-ok')
    const err = document.querySelector('.save-error')
    if (ok && ok.textContent.trim()) return { kind: 'ok', text: ok.textContent.trim() }
    if (err && err.textContent.trim()) return { kind: 'err', text: err.textContent.trim() }
    return null
  }, { timeout: 25000 }).catch(() => null)
  if (banner) console.log('== баннер:', JSON.stringify(await banner.jsonValue().catch(() => null)))
  await sleep(500)

  // ── 6. где теперь SETPOINT после reload ─────────────────────────────
  await page.reload({ waitUntil: 'networkidle2' })
  await page.waitForSelector('.node-item', { timeout: 30000 })
  await sleep(400)
  const checkNode = async (code) => {
    const ns = await page.$$('.node-item')
    for (const n of ns) {
      const c = await n.$eval('.code', el => el.textContent.trim()).catch(() => '')
      if (c === code) {
        await n.click()
        await sleep(500)
        const cs = await page.$$('.chip')
        const texts = []
        for (const x of cs) texts.push(await x.evaluate(el => el.textContent.trim()))
        return texts
      }
    }
    return ['(узел не найден)']
  }
  console.log('== после reload, слоты CMD_INPUTS:', (await checkNode('CMD_INPUTS')).join(' | '))
  console.log('== после reload, слоты CU_POWER_SUPPLY:', (await checkNode('CU_POWER_SUPPLY')).join(' | '))

  await page.screenshot({ path: 'debug_slot_section.png' })
  console.log('== скриншот: debug_slot_section.png')
  await browser.close()
}

main().then(() => process.exit(0)).catch(e => { console.error('FATAL', e); process.exit(1) })
