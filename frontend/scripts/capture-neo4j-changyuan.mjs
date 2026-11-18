// Neo4j Browser 畅园库查询截图（第 10 页「图数据库实测查询」配图）
// 运行：node scripts/capture-neo4j-changyuan.mjs （需 Neo4j 7474 运行）
// 输出：docs/ppt_screenshots/05-changyuan-neo4j-graph.png
import { chromium } from 'playwright'
import { mkdirSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const OUT = resolve(dirname(fileURLToPath(import.meta.url)), '../../docs/ppt_screenshots')
mkdirSync(OUT, { recursive: true })

const PASSWORD = process.env.NEO4J_PASSWORD
if (!PASSWORD) throw new Error('请先设置环境变量 NEO4J_PASSWORD')

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 })
await page.goto('http://127.0.0.1:7474/browser/', { waitUntil: 'domcontentloaded', timeout: 30000 })
await page.waitForTimeout(4000)
const wait = (ms) => page.waitForTimeout(ms)

// ---- 连接实例（首次打开时连接对话框已就绪；hostname 不带 scheme，协议为独立字段） ----
await page.locator('input[name=hostname]').first().fill('127.0.0.1:7687')
await wait(300)
await page.locator('input[name=username]').first().fill('neo4j')
await wait(300)
await page.locator('input[name=password]').first().fill(PASSWORD)
await wait(300)
await page.locator('button', { hasText: 'Connect' }).last().click()
await wait(9000)
console.log('URL after connect:', page.url())

// ---- 选择数据库 changyuan（顶部数据库菜单） ----
await page.locator('[data-testid=database-menu-button]').click()
await wait(1500)
await page.locator('[role=menu] [role=menuitem], [role=menu] li, [role=menu] button', { hasText: 'changyuan' }).first().click()
await wait(4000)

// ---- 查询编辑器（CodeMirror）：清空后输入全库查询，Enter 运行 ----
const QUERY = 'MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 40'
const editor = page.locator('.cm-editor').first()
await editor.click()
await page.keyboard.press('Control+a')
await page.keyboard.type(QUERY)
await wait(500)
await page.keyboard.press('Enter')
await wait(14000)
await page.screenshot({ path: `${OUT}/05-changyuan-neo4j-graph.png` })
console.log('saved 05-changyuan-neo4j-graph.png')
await browser.close()
