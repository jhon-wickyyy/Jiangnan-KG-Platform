<template>
  <div ref="chartEl" class="graph-canvas"></div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch, ref } from 'vue'
import * as echarts from 'echarts'
import { useGraphStore } from '../stores/graph'
import { useAppStore } from '../stores/app'
import { labelColor, lineStyleFor } from '../utils/graphStyle'
import { computeSpatialLayout } from '../utils/spatial'

const props = defineProps({
  mergePairs: { type: Boolean, default: false },
  hiddenRelTypes: { type: Array, default: () => [] },
  adjacencyFilter: { type: String, default: '' }
})

const emit = defineEmits(['node-click', 'node-dblclick'])

const store = useGraphStore()
const app = useAppStore()
const chartEl = ref(null)
let chart = null

// ---------- 工具提示（空间关系语义优先展示，其余键动态兜底） ----------

const LINK_PREF_KEYS = ['相邻类型', '接触类型', '中介', '方向', '距离_m', '极角_度', '环线序号', '关系', '空间关系']
const NODE_PREF_KEYS = ['类型', '品种', '功能', '平面形式', '屋顶形式', '材质', '形式', '时期', '位置']
const NODE_SKIP_KEYS = ['x', 'y', '极径_m', '极角_度', '名称', '编号', '代号']

function tooltipFormatter(p) {
  const rows = []
  if (p.dataType === 'edge') {
    const raw = p.data._raw
    rows.push(`<b>${raw.type}</b>`)
    const pp = raw.props || {}
    const used = new Set()
    for (const k of LINK_PREF_KEYS) {
      if (pp[k] !== undefined && pp[k] !== null) {
        rows.push(`${k}：${pp[k]}`)
        used.add(k)
      }
    }
    for (const [k, v] of Object.entries(pp)) {
      if (!used.has(k) && v !== null && v !== undefined) rows.push(`${k}：${v}`)
    }
  } else if (p.dataType === 'node') {
    const raw = p.data._raw
    rows.push(`<b>${raw.name}</b>`)
    rows.push(`${raw.label} · ${raw.db}`)
    const pp = raw.props || {}
    const used = new Set()
    for (const k of NODE_PREF_KEYS) {
      const v = pp[k]
      if (v !== undefined && v !== null) {
        const s = String(v)
        rows.push(`${k}：${s.length > 32 ? s.slice(0, 32) + '…' : s}`)
        used.add(k)
      }
    }
    for (const [k, v] of Object.entries(pp)) {
      if (used.has(k) || NODE_SKIP_KEYS.includes(k) || v === null || v === undefined) continue
      const s = String(v)
      rows.push(`${k}：${s.length > 24 ? s.slice(0, 24) + '…' : s}`)
    }
  }
  return rows.join('<br/>')
}

// ---------- 边过滤 ----------

function mergePairLinks(ls) {
  const seen = new Set()
  const out = []
  for (const l of ls) {
    const key = [l.source, l.target].sort().join('|') + '|' + l.type
    if (seen.has(key)) continue
    seen.add(key)
    out.push(l)
  }
  return out
}

function filteredLinks() {
  const hidden = new Set(props.hiddenRelTypes)
  let ls = store.linkList
  if (hidden.size) ls = ls.filter((l) => !hidden.has(l.type))
  if (props.mergePairs) ls = mergePairLinks(ls)
  if (props.adjacencyFilter) {
    ls = ls.filter((l) =>
      l.props?.['相邻类型'] ? l.props['相邻类型'] === props.adjacencyFilter : true
    )
  }
  return ls
}

// ---------- 构建 ECharts option ----------

function buildOption() {
  const labels = app.schema?.labels?.length
    ? app.schema.labels
    : [...new Set(store.nodeList.map((n) => n.label))]
  const categories = labels.map((l) => ({
    name: l,
    itemStyle: { color: labelColor(l, labels) }
  }))
  const labelIdx = Object.fromEntries(labels.map((l, i) => [l, i]))

  const degrees = {}
  for (const l of store.linkList) {
    degrees[l.source] = (degrees[l.source] || 0) + 1
    degrees[l.target] = (degrees[l.target] || 0) + 1
  }

  const spatial = store.mode === 'spatial'
  const coords = spatial
    ? computeSpatialLayout(store.nodeList, chart.getWidth(), chart.getHeight())
    : null

  const graphNodes = store.nodeList.map((n) => {
    const item = {
      id: n.id,
      name: n.name,
      category: labelIdx[n.label] ?? 0,
      symbolSize: 14 + Math.min(22, Math.sqrt(degrees[n.id] || 0) * 4),
      _raw: n,
      itemStyle:
        store.selectedId === n.id
          ? { borderColor: '#f56c6c', borderWidth: 3 }
          : undefined
    }
    if (coords) {
      const c = coords(n)
      item.x = c.x
      item.y = c.y
      item.fixed = true
    }
    return item
  })

  const graphLinks = filteredLinks().map((l) => ({
    source: l.source,
    target: l.target,
    _raw: l,
    lineStyle: { ...lineStyleFor(l.type, app.schema?.rel_types || []), width: 1.6 }
  }))

  return {
    animationDurationUpdate: 300,
    tooltip: { confine: true, formatter: tooltipFormatter },
    legend: {
      data: categories.map((c) => c.name),
      top: 8,
      left: 8,
      type: 'scroll',
      textStyle: { fontSize: 12 }
    },
    series: [
      {
        type: 'graph',
        layout: spatial ? 'none' : 'force',
        data: graphNodes,
        links: graphLinks,
        categories,
        roam: true,
        draggable: true,
        label: { show: true, position: 'right', fontSize: 11, color: '#4a4a4a' },
        emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
        force: { repulsion: 260, edgeLength: [60, 130], gravity: 0.1 },
        lineStyle: { opacity: 0.85 },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 7],
        scaleLimit: { min: 0.2, max: 6 }
      }
    ]
  }
}

let lastMode = ''

function render() {
  if (!chart) return
  // 仅模式切换时完全重置（布局算法不同）；选中/展开/过滤等增量更新用 merge，避免力导向重新抖动
  const modeChanged = lastMode !== store.mode
  lastMode = store.mode
  chart.setOption(buildOption(), { notMerge: modeChanged })
}

function onResize() {
  if (chart) {
    chart.resize()
    render() // 空间模式坐标依赖画布尺寸，需重算
  }
}

onMounted(() => {
  chart = echarts.init(chartEl.value)
  chart.on('click', (p) => {
    if (p.dataType === 'node') emit('node-click', p.data.id)
  })
  chart.on('dblclick', (p) => {
    if (p.dataType === 'node') emit('node-dblclick', p.data.id)
  })
  window.addEventListener('resize', onResize)
  // 仅开发环境暴露实例，供无头浏览器端到端测试定位节点
  if (import.meta.env.DEV) window.__graphChart = chart
  render()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})

watch(
  () => [
    store.nodeList,
    store.linkList,
    store.selectedId,
    store.mode,
    props.mergePairs,
    props.hiddenRelTypes,
    props.adjacencyFilter
  ],
  render
)
</script>
