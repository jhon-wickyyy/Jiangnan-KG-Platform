// PPT 结项答辩截图自动采集：按 docs/defense_ppt_plan.md 的截图清单逐页截取
// 运行：node scripts/capture-ppt-shots.mjs （需 backend:8000 与 frontend:5173 运行中）
// 输出：docs/ppt_screenshots/*.png（1920×1080，元素级截图）
// 注意：页面切换使用侧边栏 SPA 导航（page.goto 会整页重载并重置园林状态）
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
  const pos = await page.evaluate((nm) => {
    const s = window.__graphChart.getOption().series[0]
    const it = s.data.find((d) => d.name === nm)
    return it ? { x: Math.round(it.x), y: Math.round(it.y) } : null
  }, name)
  if (!pos) return false
  const box = await page.locator('.graph-canvas canvas').first().boundingBox()
  await page.mouse.click(box.x + pos.x, box.y + pos.y)
  await wait(2000)
  return true
}

async function pickPathNode(idx, kw) {
  for (let i = 0; i < 3; i++) {
    await page.locator('.path-selects .el-select').nth(idx).click()
    await wait(700)
    await page.locator('.path-selects .el-select').nth(idx).locator('input').fill(kw)
    await wait(900)
    const opt = page.locator('.el-select-dropdown__item:visible', { hasText: kw }).first()
    if ((await opt.count()) > 0) {
      await opt.click()
      await wait(600)
      return true
    }
    await page.keyboard.press('Escape')
    await wait(400)
  }
  return false
}

// ---------- 首页 Dashboard（默认个园，全局统计） ----------
await page.goto(BASE + '/', { waitUntil: 'networkidle' })
await wait(2500)
await shot('01-dashboard-full')
await shot('03-architecture', '.arch-card')
await shot('04a-stat-cards', '.page > .el-row')
await page.locator('.el-card', { hasText: '各园林知识图谱规模' }).first().scrollIntoViewIfNeeded()
await wait(600)
await shot('04b-garden-table', '.el-card:has-text("各园林知识图谱规模")')
await shot('06-sidebar', '.app-aside')

// ---------- 切换园林：沧浪亭（重点页统一用它；后续全部 SPA 导航保持状态） ----------
await switchGarden('沧浪亭')

// ---------- 7. 空间布局平面图（图谱探索页，默认空间布局模式） ----------
await nav('图谱探索')
await shot('07-spatial-layout', '.graph-canvas-wrap')

// ---------- 7b. 节点详情抽屉（面水轩：空间位置 + 游线序号） ----------
if (await clickGraphNode('面水轩')) {
  await shot('07b-node-detail', '.el-drawer')
  await page.keyboard.press('Escape')
  await wait(1200)
} else {
  console.log('✗ 07b 节点详情（点击未命中）')
}

// ---------- 8. 知识关系模式（力导向） ----------
await page.getByText('知识关系模式', { exact: true }).click()
await wait(3500)
await shot('08-relation-network', '.graph-canvas-wrap')

// ---------- 9. 游线分析：播放中途暂停（沧浪亭 14 站） ----------
await nav('游线分析')
await page.getByRole('button', { name: '▶ 播放游线' }).click()
await wait(4800)
await page.getByRole('button', { name: '⏸ 暂停' }).click()
await wait(800)
await shot('09-route-playing', '.route-page')

// ---------- 10. 空间关系分析：筛选"可看" ----------
await nav('空间关系分析')
await page.locator('.spatial-filters .el-select').nth(1).click()
await wait(600)
await page.locator('.el-select-dropdown__item:visible', { hasText: '可看' }).first().click()
await wait(1000)
await shot('10-spatial-filtered', '.spatial-page')

// ---------- 10b. 空间关系详情抽屉 ----------
await page.locator('.spatial-row').first().click()
await wait(1500)
await shot('10b-relation-detail', '.el-drawer')
await page.keyboard.press('Escape')
await wait(1200)

// ---------- 11. 多园林切换器展开 ----------
await page.locator('.app-garden .el-select').click()
await wait(800)
await shot('11-garden-switcher', '.el-select-dropdown:visible')
await page.keyboard.press('Escape')
await wait(600)

// ---------- 12. 路径查询：空间路径（沧浪亭假山→面水轩，仅空间关系） ----------
await nav('路径查询')
const s1 = await pickPathNode(0, '沧浪亭假山')
const s2 = await pickPathNode(1, '面水轩')
if (s1 && s2) {
  await page.locator('.path-selects .el-checkbox').click()
  await page.getByRole('button', { name: '查询路径' }).click()
  await wait(2500)
  await shot('12-path-spatial', '.path-page')
} else {
  console.log('✗ 12 路径查询（选择失败 s1=' + s1 + ' s2=' + s2 + '）')
}

// ---------- 8b. 知识网络分析页 ----------
await nav('知识网络分析')
await shot('08b-network-analysis', '.page')

// ---------- 12b. 实体浏览（拼图备选） ----------
await nav('实体浏览')
await shot('12b-entities', '.page')

console.log('\n截图完成，输出目录:', OUT)
console.log('运行时错误:', errors.length ? [...new Set(errors)] : '无')
await browser.close()
