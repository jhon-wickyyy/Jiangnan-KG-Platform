// PPT 结项答辩截图：畅园案例版（45 节点 / 130 关系）
// 运行：node scripts/capture-changyuan-shots.mjs （需 backend:8000 与 frontend:5173 运行中）
// 输出：docs/ppt_screenshots/cy-*.png —— 空间布局 / 节点详情 / 知识关系网络 / 网络分析 / 空间关系分析 / 实体浏览
// 说明：畅园无游线数据，游线 / 路径两页沿用沧浪亭截图
import { chromium } from 'playwright'
import { mkdirSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const BASE = 'http://127.0.0.1:5173'
const OUT = resolve(dirname(fileURLToPath(import.meta.url)), '../../docs/ppt_screenshots')
mkdirSync(OUT, { recursive: true })

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 })
const errors = []
page.on('pageerror', (e) => errors.push(e.message.slice(0, 120)))

const shot = async (name, sel) => {
  await (sel ? page.locator(sel).first() : page).screenshot({ path: `${OUT}/${name}.png` })
  console.log('✓', name)
}
const wait = (ms) => page.waitForTimeout(ms)
const nav = async (menu) => {
  await page.getByText(menu, { exact: true }).click()
  await wait(2500)
}

async function switchGarden(name) {
  await page.locator('.app-garden .el-select').click()
  await wait(600)
  await page.locator('.el-select-dropdown__item:visible', { hasText: name }).first().click()
  await wait(2500)
}

async function clickGraphNode(name) {
  // 空间布局模式下 ECharts 会对整图做自动缩放适配（view.group.transform），
  // 需按 transform 换算真实屏幕坐标后再点击
  const pos = await page.evaluate((nm) => {
    const chart = window.__graphChart
    const s = chart.getOption().series[0]
    const it = s.data.find((d) => d.name === nm)
    if (!it) return null
    const sm = chart.getModel().getSeriesByIndex(0)
    const view = chart.getViewOfSeriesModel(sm)
    const m = view.group.transform
    return { x: it.x * m[0] + m[4], y: it.y * m[3] + m[5] }
  }, name)
  if (!pos) return false
  const box = await page.locator('.graph-canvas canvas').first().boundingBox()
  await page.mouse.click(box.x + pos.x, box.y + pos.y)
  await wait(2000)
  return true
}

// ---------- 切换园林：畅园 ----------
await page.goto(BASE + '/', { waitUntil: 'networkidle' })
await wait(2500)
await switchGarden('畅园')

// ---------- 7. 空间布局平面图（默认空间布局模式，真实坐标） ----------
await nav('图谱探索')
await shot('cy-07-spatial-layout', '.graph-canvas-wrap')

// ---------- 7b. 节点详情抽屉（水香榭：临水建筑 · 歇山顶） ----------
if (await clickGraphNode('水香榭')) {
  await shot('cy-07b-node-detail', '.el-drawer')
  await page.keyboard.press('Escape')
  await wait(1200)
} else {
  console.log('✗ cy-07b 节点详情（点击未命中 水香榭）')
}

// ---------- 8. 知识关系模式（自动网络排布） ----------
await page.getByText('知识关系模式', { exact: true }).click()
await wait(3500)
await shot('cy-08-relation-network', '.graph-canvas-wrap')

// ---------- 8b. 知识网络分析页 ----------
await nav('知识网络分析')
await shot('cy-08b-network-analysis', '.page')

// ---------- 10. 空间关系分析：筛选"可看"（畅园 72 条） ----------
await nav('空间关系分析')
await page.locator('.spatial-filters .el-select').nth(1).click()
await wait(600)
await page.locator('.el-select-dropdown__item:visible', { hasText: '可看' }).first().click()
await wait(1000)
await shot('cy-10-spatial-filtered', '.spatial-page')

// ---------- 10b. 空间关系详情抽屉 ----------
await page.locator('.spatial-row').first().click()
await wait(1500)
await shot('cy-10b-relation-detail', '.el-drawer')
await page.keyboard.press('Escape')
await wait(1200)

// ---------- 12b. 实体浏览 ----------
await nav('实体浏览')
await shot('cy-12b-entities', '.page')

console.log('\n畅园截图完成，输出目录:', OUT)
console.log('运行时错误:', errors.length ? [...new Set(errors)] : '无')
await browser.close()
