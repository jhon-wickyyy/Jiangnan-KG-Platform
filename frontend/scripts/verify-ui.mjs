// 端到端 UI 验证：无头浏览器加载平台，逐页截图并捕获运行时错误
// 运行：node scripts/verify-ui.mjs  （需先启动 backend:8000 与 frontend:5173）
// 流程对应答辩演示：首页 Dashboard → 图谱探索（默认空间布局模式）→ 知识关系模式 → 节点详情 → 实体浏览/搜索
import { chromium } from 'playwright'

const BASE = 'http://127.0.0.1:5173'
const OUT = 'C:/Users/jhon.wick/AppData/Local/Temp/kg-shots'
import { mkdirSync } from 'fs'
mkdirSync(OUT, { recursive: true })

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
const errors = []
page.on('console', (m) => {
  if (m.type() === 'error') errors.push('console: ' + m.text())
})
page.on('pageerror', (e) => errors.push('pageerror: ' + e.message))

try {
  // 1. 首页 Dashboard（数据概览，/ 默认路由）
  await page.goto(BASE + '/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1800)
  await page.screenshot({ path: OUT + '/shot-1-dashboard.png' })
  console.log('1. Dashboard 统计卡片:', (await page.locator('.stat-value').allTextContents()).join(' / '))
  const gardenTag = await page.locator('.el-tag').first().textContent().catch(() => '')
  console.log('   当前园林标签:', gardenTag.replace(/\s+/g, ' '))
  const archLayers = await page.locator('.arch-layer').count()
  const archChips = await page.locator('.layer-chip').count()
  const archText = (await page.locator('.arch').textContent().catch(() => '')).replace(/\s+/g, ' ')
  console.log('   架构图层数:', archLayers, '| 模块入口数:', archChips)
  console.log('   架构图内容:', archText.slice(0, 130))
  await page.screenshot({ path: OUT + '/shot-1b-architecture.png' })

  // 2. 图谱探索页：默认空间布局模式（layout=none，按 x/y 真实坐标，非力导向）
  await page.getByText('图谱探索', { exact: true }).click()
  await page.waitForTimeout(2000)
  const spatialInfo = await page.evaluate(() => {
    const ch = window.__graphChart
    if (!ch) return null
    const s = ch.getOption().series[0]
    return { layout: s.layout, nodes: s.data.length, allFixed: s.data.every((d) => d.fixed) }
  })
  console.log('2. 空间布局模式:', JSON.stringify(spatialInfo))
  await page.screenshot({ path: OUT + '/shot-2-spatial.png' })

  // 3. 切换到知识关系模式（力导向，验证模式切换可用）
  await page.getByText('知识关系模式', { exact: true }).click()
  await page.waitForTimeout(3000) // 等力导向布局稳定
  const forceLayout = await page.evaluate(() => window.__graphChart?.getOption().series[0].layout)
  console.log('3. 知识关系模式 layout:', forceLayout)
  await page.screenshot({ path: OUT + '/shot-3-relation.png' })

  // 4. 切回空间布局模式，点击“面水轩”节点 → 应弹出详情抽屉
  await page.getByText('空间布局模式', { exact: true }).click()
  await page.waitForTimeout(1500)
  const pos = await page.evaluate(() => {
    const chart = window.__graphChart
    if (!chart) return null
    const it = chart.getOption().series[0].data.find((d) => d.name === '面水轩')
    return it ? { x: Math.round(it.x), y: Math.round(it.y) } : null
  })
  if (pos) {
    const box = await page.locator('canvas').first().boundingBox()
    await page.mouse.click(box.x + pos.x, box.y + pos.y)
    await page.waitForTimeout(1500)
    await page.screenshot({ path: OUT + '/shot-4-node-click.png' })
    const drawer = (await page.locator('.el-drawer').textContent().catch(() => ''))
      .replace(/\s+/g, ' ')
    console.log('4. 点击节点后详情抽屉:', drawer.slice(0, 140))
  } else {
    console.log('4. 未找到“面水轩”节点（可能图未渲染）')
  }
  await page.keyboard.press('Escape')
  await page.waitForTimeout(800)

  // 5. 实体浏览页 + 行点击 → 详情抽屉
  await page.getByText('实体浏览', { exact: true }).click()
  await page.waitForTimeout(1500)
  const rows = await page.locator('.el-table__row').count()
  console.log('5. 实体表格行数:', rows)
  if (rows > 0) {
    await page.locator('.el-table__row').first().click()
    await page.waitForTimeout(1500)
    await page.screenshot({ path: OUT + '/shot-5-entities-detail.png' })
    const drawer = (await page.locator('.el-drawer').textContent().catch(() => ''))
      .replace(/\s+/g, ' ')
    console.log('   详情抽屉内容:', drawer.slice(0, 120))
  }
  await page.keyboard.press('Escape')
  await page.waitForTimeout(800)

  // 6. 实体搜索页
  await page.getByText('实体搜索', { exact: true }).click()
  await page.waitForTimeout(800)
  await page.locator('input[placeholder*="面水轩"]').fill('面水轩')
  await page.getByRole('button', { name: '搜索' }).click()
  await page.waitForTimeout(1500)
  const found = await page.locator('.el-table__row').count()
  await page.screenshot({ path: OUT + '/shot-6-search.png' })
  console.log('6. 搜索“面水轩”结果行数:', found)

  // 7. 游线分析页：空间底图（scatter+lines）+ 14 站行程列表 + 播放动画
  await page.getByText('游线分析', { exact: true }).click()
  await page.waitForTimeout(2500)
  const routeInfo = await page.evaluate(() => {
    const ch = window.__routeChart
    if (!ch) return null
    const series = ch.getOption().series
    const scatterNodes = series.filter((s) => s.type === 'scatter').reduce((n, s) => n + s.data.length, 0)
    const done = series.find((s) => s.name === '游线（已走到）')
    const todo = series.find((s) => s.name === '游线（未走到）')
    const base = series.find((s) => s.name === '园内关系')
    return {
      scatterNodes,
      baseEdges: base?.data?.length,
      doneEdges: done?.data?.length,
      todoEdges: todo?.data?.length
    }
  })
  console.log('7. 游线页初始状态:', JSON.stringify(routeInfo))
  const stopRows = await page.locator('.route-stop').count()
  console.log('   行程列表行数:', stopRows)
  await page.screenshot({ path: OUT + '/shot-7-route-full.png' })

  // 播放动画：从 0 开始，等待 2 步后检查推进状态（已走到边数增加、未走到减少）
  await page.getByRole('button', { name: '▶ 播放游线' }).click()
  await page.waitForTimeout(2300)
  const playingInfo = await page.evaluate(() => {
    const series = window.__routeChart.getOption().series
    const done = series.find((s) => s.name === '游线（已走到）')
    const todo = series.find((s) => s.name === '游线（未走到）')
    return { done: done.data.length, todo: todo.data.length }
  })
  console.log('   播放中 已走到/未走到:', playingInfo.done + '/' + playingInfo.todo)
  await page.getByRole('button', { name: '⏸ 暂停' }).click()
  await page.screenshot({ path: OUT + '/shot-8-route-playing.png' })

  // 8. 空间关系分析页：统计 + 筛选 + 列表 + 地图叠加
  await page.getByText('空间关系分析', { exact: true }).click()
  await page.waitForTimeout(2500)
  const statsTags = await page.locator('.spatial-stats .el-tag').allTextContents()
  const allRows = await page.locator('.spatial-row').count()
  console.log('8. 空间关系统计标签:', statsTags.map((t) => t.replace(/\s+/g, ' ')).join(' | '))
  console.log('   全部关系行数:', allRows)
  await page.screenshot({ path: OUT + '/shot-9-spatial-all.png' })

  // 筛选：相邻类型=可看 → 行数应小于全部（数据相关，不硬编码）
  await page.locator('.spatial-filters .el-select').nth(1).click()
  await page.waitForTimeout(500)
  await page.locator('.el-select-dropdown__item', { hasText: '可看' }).first().click()
  await page.waitForTimeout(800)
  const filteredRows = await page.locator('.spatial-row').count()
  console.log('   筛选「可看」后行数:', filteredRows, '（全部', allRows, '）')
  await page.screenshot({ path: OUT + '/shot-10-spatial-filtered.png' })

  // 点击第一条关系 → 关系详情抽屉
  await page.locator('.spatial-row').first().click()
  await page.waitForTimeout(1200)
  const drawerVis = await page.evaluate(() => {
    const d = document.querySelector('.el-drawer')
    return d ? getComputedStyle(d).display !== 'none' && d.offsetParent !== null : false
  })
  const drawerTxt = (await page.locator('.el-drawer').textContent().catch(() => ''))
    .replace(/\s+/g, ' ')
    .slice(0, 90)
  console.log('   点击关系抽屉可见:', drawerVis, '| 内容:', drawerTxt)
  await page.keyboard.press('Escape')
  await page.waitForTimeout(500)

  // 点击地图上的关系连线（匹配系列中线）→ 同样打开关系详情
  const lineHit = await page.evaluate(() => {
    const ch = window.__spatialChart
    if (!ch) return null
    const opt = ch.getOption()
    const s = opt.series.find((s) => s.name === '空间关系（匹配）')
    if (!s || !s.data.length) return null
    const si = opt.series.indexOf(s)
    const c = s.data[0].coords || s.data[0].value
    const a = ch.convertToPixel({ seriesIndex: si }, c[0])
    const b = ch.convertToPixel({ seriesIndex: si }, c[1])
    return { x: Math.round(a[0] * 0.5 + b[0] * 0.5), y: Math.round(a[1] * 0.5 + b[1] * 0.5) }
  })
  if (lineHit) {
    const box = await page.locator('.spatial-canvas canvas').first().boundingBox()
    await page.mouse.click(box.x + lineHit.x, box.y + lineHit.y)
    await page.waitForTimeout(1200)
    const vis2 = await page.evaluate(() => {
      const d = document.querySelector('.el-drawer')
      return d ? getComputedStyle(d).display !== 'none' && d.offsetParent !== null : false
    })
    console.log('   点击地图连线抽屉可见:', vis2)
    await page.keyboard.press('Escape')
    await page.waitForTimeout(400)
  }

  // 9. 架构图模块入口跳转：回到首页点「游线分析」入口 → 应到达 /route
  await page.getByText('数据概览', { exact: true }).click()
  await page.waitForTimeout(1200)
  await page.locator('.layer-chip', { hasText: '游线分析' }).click()
  await page.waitForTimeout(1500)
  console.log('9. 架构图入口跳转后 URL:', page.url().replace(BASE, ''))
  await page.screenshot({ path: OUT + '/shot-11-arch-jump.png' })

  // 10. 知识网络分析页：基础指标卡 + 三张图表
  await page.getByText('知识网络分析', { exact: true }).click()
  await page.waitForTimeout(2500)
  const metricValues = await page.locator('.stat-value').allTextContents()
  console.log('10. 网络指标卡:', metricValues.join(' / '))
  const chartInfo = await page.evaluate(() => {
    const canvases = document.querySelectorAll('.page canvas')
    return { canvasCount: canvases.length }
  })
  console.log('    图表 canvas 数:', chartInfo.canvasCount)
  await page.screenshot({ path: OUT + '/shot-12-analysis.png' })

  // 切换园林 → 指标随库变化
  const before = metricValues[0]
  await page.locator('.app-garden .el-select').click()
  await page.waitForTimeout(600)
  const opt = page.locator('.el-select-dropdown__item', { hasText: '沧浪亭' }).first()
  if ((await opt.count()) > 0) {
    await opt.click()
    await page.waitForTimeout(2000)
    const after = (await page.locator('.stat-value').first().textContent()).trim()
    console.log('    切换园林后节点数:', before, '→', after)
  } else {
    console.log('    未找到沧浪亭选项（跳过切换测试）')
  }

  // 11. 路径查询页：选择起点/终点 → 查询 → 路径序列 + 地图高亮
  await page.getByText('路径查询', { exact: true }).click()
  await page.waitForTimeout(1800)
  await page.locator('.path-selects .el-select').nth(0).click()
  await page.waitForTimeout(400)
  await page.locator('.path-selects .el-select').nth(0).locator('input').fill('沧浪亭假山')
  await page.waitForTimeout(500)
  await page.locator('.el-select-dropdown__item:visible', { hasText: '沧浪亭假山' }).first().click()
  await page.waitForTimeout(400)
  await page.locator('.path-selects .el-select').nth(1).click()
  await page.waitForTimeout(400)
  await page.locator('.path-selects .el-select').nth(1).locator('input').fill('面水轩')
  await page.waitForTimeout(500)
  await page.locator('.el-select-dropdown__item:visible', { hasText: '面水轩' }).first().click()
  await page.waitForTimeout(400)
  await page.getByRole('button', { name: '查询路径' }).click()
  await page.waitForTimeout(2000)
  const desc = (await page.locator('.path-desc').textContent().catch(() => '')).replace(/\s+/g, ' ').slice(0, 130)
  const stepCount = await page.locator('.path-steps .el-step').count()
  const tags = await page.locator('.path-stats .el-tag').allTextContents()
  console.log('11. 路径描述:', desc)
  console.log('    步骤数:', stepCount, '| 标签:', tags.map((t) => t.replace(/\s+/g, ' ')).join(' | '))
  const pathMapInfo = await page.evaluate(() => {
    const ch = window.__pathChart
    if (!ch) return null
    const opt = ch.getOption()
    const s = opt.series.find((s) => s.name === '最短路径')
    return { pathEdges: s?.data?.length ?? 0 }
  })
  console.log('    地图路径边数:', JSON.stringify(pathMapInfo))
  await page.screenshot({ path: OUT + '/shot-13-path.png' })
} finally {
  console.log('运行时错误:', errors.length ? errors : '无')
  await browser.close()
}
