// 结项答辩演示 GIF 采集：把四个实机演示环节录成逐帧截图（由 build_demo_gifs.py 合成 GIF）
// 运行：node scripts/capture-demo-gifs.mjs （需 backend:8000 与 frontend:5173 运行中）
// 输出：frontend/scripts/_gif_frames/gifN_fXX.png + durations.json（帧序与每帧时长 ms）
// GIF1 畅园空间布局+节点详情（第17页） GIF2 沧浪亭游线播放（第19页）
// GIF3 畅园空间关系筛选（第20页）     GIF4 沧浪亭路径查询（第21页）
import { chromium } from 'playwright'
import { mkdirSync, writeFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const BASE = 'http://127.0.0.1:5173'
const FRAMES = resolve(dirname(fileURLToPath(import.meta.url)), '_gif_frames')
mkdirSync(FRAMES, { recursive: true })

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } })
const wait = (ms) => page.waitForTimeout(ms)

let seq = []           // [{name, dur}]
let bufCache = []      // [{name, buf}]
const allDurs = {}
async function snap(durMs) {
  const name = `f${String(seq.length).padStart(2, '0')}`
  bufCache.push({ name, buf: await page.screenshot({ type: 'png' }) })
  seq.push({ name, dur: durMs })
}
async function flush(gifName) {
  for (const { name, buf } of bufCache) {
    writeFileSync(resolve(FRAMES, `${gifName}_${name}.png`), buf)
  }
  allDurs[gifName] = seq.map((s) => s.dur)
  bufCache = []
  seq = []
  console.log('✓', gifName, allDurs[gifName].length, '帧')
}

async function switchGarden(name) {
  await page.locator('.app-garden .el-select').click()
  await wait(600)
  await page.locator('.el-select-dropdown__item:visible', { hasText: name }).first().click()
  await wait(2000)
}
const nav = async (menu) => {
  await page.getByText(menu, { exact: true }).click()
  await wait(2200)
}
async function clickGraphNode(name) {
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
  return true
}
async function pickPathNode(idx, kw) {
  for (let i = 0; i < 3; i++) {
    await page.locator('.path-selects .el-select').nth(idx).click()
    await wait(600)
    await page.locator('.path-selects .el-select').nth(idx).locator('input').fill(kw)
    await wait(900)
    const opt = page.locator('.el-select-dropdown__item:visible', { hasText: kw }).first()
    if ((await opt.count()) > 0) {
      await opt.click()
      await wait(500)
      return true
    }
    await page.keyboard.press('Escape')
    await wait(300)
  }
  return false
}

// ================= GIF1 畅园空间布局 + 节点详情 + 关系模式切换 =================
await page.goto(BASE + '/', { waitUntil: 'networkidle' })
await wait(2000)
await switchGarden('畅园')
await nav('图谱探索')
await snap(1200)                       // 空间布局平面图
if (await clickGraphNode('水香榭')) {
  await wait(300); await snap(300)     // 抽屉滑入
  await wait(700); await snap(1200)    // 抽屉详情停留
  await page.keyboard.press('Escape')
  await wait(800); await snap(800)     // 抽屉关闭
}
await page.getByText('知识关系模式', { exact: true }).click()
await wait(300);  await snap(300)
await wait(700);  await snap(700)      // 力导向排布展开中
await wait(1200); await snap(1200)
await wait(1500); await snap(1500)     // 排布稳定
await flush('gif1')

// ================= GIF2 沧浪亭游线播放 =================
await switchGarden('沧浪亭')
await nav('游线分析')
await snap(1000)                       // 初始动线（虚线）
await page.getByRole('button', { name: '▶ 播放游线' }).click()
for (let i = 0; i < 12; i++) {         // 播放过程逐帧（约 1s/帧）
  await wait(1000)
  await snap(1000)
}
await snap(1200)                       // 播完停留
await flush('gif2')

// ================= GIF3 畅园空间关系：筛选可看 + 详情抽屉 =================
await switchGarden('畅园')
await nav('空间关系分析')
await snap(900)                        // 初始页
await page.locator('.spatial-filters .el-select').nth(1).click()
await wait(500)
await page.locator('.el-select-dropdown__item:visible', { hasText: '可看' }).first().click()
await wait(300);  await snap(300)      // 连线叠加动画起
await wait(900);  await snap(1200)     // 叠加完成
await page.locator('.spatial-row').first().click()
await wait(300);  await snap(300)      // 详情抽屉滑入
await wait(700);  await snap(1200)     // 详情停留
await page.keyboard.press('Escape')
await wait(600);  await snap(800)      // 关闭
await flush('gif3')

// ================= GIF4 沧浪亭路径查询 =================
await switchGarden('沧浪亭')
await nav('路径查询')
await snap(900)
if ((await pickPathNode(0, '沧浪亭假山')) && (await pickPathNode(1, '面水轩'))) {
  await page.locator('.path-selects .el-checkbox').click()
  await wait(300);  await snap(400)    // 勾选"仅空间关系"
  await page.getByRole('button', { name: '查询路径' }).click()
  await wait(300);  await snap(300)    // 路径高亮动画起
  await wait(700);  await snap(800)
  await wait(1200); await snap(1200)   // 高亮完成
  await snap(1500)                     // 结果停留
}
await flush('gif4')

// 时长表（Python 合成时读取）
writeFileSync(resolve(FRAMES, 'durations.json'), JSON.stringify(allDurs, null, 1))
console.log('帧截图完成，输出目录:', FRAMES)
await browser.close()
