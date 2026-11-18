// 多库体检：对每个业务库调用核心接口，汇总各园数据健康度
// 运行：node scripts/verify-multidb.mjs  （需 backend:8000 与 Neo4j 运行中）
// 输出：逐园一览表 + 异常汇总（缺坐标 / 缺游线 / 缺空间关系）
const BASE = 'http://127.0.0.1:8000/api'

async function getJson(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${await res.text().then((t) => t.slice(0, 120))}`)
  return (await res.json()).data
}

const dbs = await getJson(`${BASE}/databases?refresh=true`)
console.log(`共 ${dbs.length} 个业务库，逐园体检中…\n`)

const rows = []
for (const d of dbs) {
  try {
    const [g, r, sp, a] = await Promise.all([
      getJson(`${BASE}/graph/garden?db=${d.name}`),
      getJson(`${BASE}/route?db=${d.name}`),
      getJson(`${BASE}/spatial/relations?db=${d.name}`),
      getJson(`${BASE}/analysis/network?db=${d.name}`)
    ])
    const nodes = g.nodes || []
    const withXY = nodes.filter(
      (n) => typeof n.props?.x === 'number' && typeof n.props?.y === 'number'
    ).length
    // 物理节点数（分析）与稳定 ID 去重后节点数（子图）不一致 → 存在重复编号/无标签节点
    const dupIds = a.total_nodes !== nodes.length
    rows.push({
      园林: d.garden,
      库: d.name,
      节点: nodes.length,
      关系: (g.links || []).length,
      坐标: `${withXY}/${nodes.length}`,
      游线站: r.stops?.length ?? 0,
      闭环: r.closed === true ? '✓' : r.closed === false ? '✗' : '—',
      空间边: (sp.links || []).length,
      核心节点: a.max_degree_node ? `${a.max_degree_node.name}(${a.max_degree_node.degree})` : '—',
      ID重复: dupIds ? `⚠ 物理${a.total_nodes}/去重${nodes.length}` : ''
    })
  } catch (e) {
    rows.push({ 园林: d.garden, 库: d.name, 节点: 'ERROR', 关系: e.message.slice(0, 40) })
  }
}

console.table(rows)

const bad = rows.filter((r) => {
  if (r.节点 === 'ERROR') return true
  const [, have, total] = String(r.坐标).split('/').map(Number)
  return have !== total || r.游线站 === 0 || r.空间边 === 0 || r.ID重复
})
console.log('\n异常汇总：')
if (!bad.length) {
  console.log('  全部园林数据完整（坐标/游线/空间关系齐备）')
} else {
  for (const b of bad) {
    const parts = []
    if (b.节点 === 'ERROR') parts.push('接口调用失败')
    else {
      if (String(b.坐标).split('/')[0] !== String(b.坐标).split('/')[1]) parts.push(`坐标 ${b.坐标}`)
      if (b.游线站 === 0) parts.push('无游线')
      if (b.空间边 === 0) parts.push('无空间关系')
      if (b.ID重复) parts.push(b.ID重复)
    }
    console.log(`  ⚠ ${b.园林}（${b.库}）: ${parts.join(' · ')}`)
  }
}
