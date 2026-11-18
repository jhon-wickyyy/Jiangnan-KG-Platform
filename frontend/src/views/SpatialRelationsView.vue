<template>
  <div class="spatial-page">
    <div class="spatial-toolbar">
      <div class="spatial-stats">
        <span class="spatial-title">空间关系分析</span>
        <el-tag v-if="app.currentDb" size="small" type="success" effect="plain">
          当前园林：{{ app.gardenName }}
        </el-tag>
        <el-tag size="small" type="primary" effect="plain">相邻关系 {{ relCount('相邻') }}</el-tag>
        <el-tag size="small" type="warning" effect="plain">相接关系 {{ relCount('相接') }}</el-tag>
      </div>
      <el-button size="small" :loading="loading" @click="load">刷新</el-button>
    </div>

    <div class="spatial-filters">
      <el-select v-model="relType" placeholder="关系类型：全部" clearable size="small" style="width: 150px">
        <el-option v-for="v in relTypes" :key="v" :label="v" :value="v" />
      </el-select>
      <el-select v-model="adjacencyType" placeholder="相邻类型：全部" clearable size="small" style="width: 150px">
        <el-option v-for="v in adjacencyValues" :key="v" :label="v" :value="v" />
      </el-select>
      <el-select v-model="contactType" placeholder="接触类型：全部" clearable size="small" style="width: 150px">
        <el-option v-for="v in contactValues" :key="v" :label="v" :value="v" />
      </el-select>
      <el-select v-model="medium" placeholder="中介：全部" clearable size="small" style="width: 150px">
        <el-option v-for="v in mediumValues" :key="v" :label="v" :value="v" />
      </el-select>
      <div class="dist-filter">
        <span class="dist-label">距离 ≤ {{ maxDist }} m</span>
        <el-slider
          v-model="maxDist"
          :min="0"
          :max="maxDistAll"
          :disabled="!spatialLinks.length"
          size="small"
          style="width: 180px; margin-left: 8px"
        />
      </div>
      <span class="filter-count">匹配 {{ filteredLinks.length }} / {{ spatialLinks.length }} 条</span>
    </div>

    <div class="spatial-body">
      <div v-loading="loading" class="spatial-canvas-wrap">
        <div ref="chartEl" class="spatial-canvas"></div>
        <div v-if="!loading && spatialLinks.length === 0" class="spatial-empty">
          <el-empty description="当前园林无空间关系数据" />
        </div>
        <div v-if="!loading && spatialLinks.length && filteredLinks.length === 0" class="spatial-empty-soft">
          无匹配的空间关系，请调整筛选条件
        </div>
        <div class="spatial-hint">
          空间布局底图 + 空间关系连线（彩色=匹配筛选 · 灰色=未匹配）· 点击连线查看关系详情 · 点击节点查看节点详情 · 滚轮缩放/拖拽平移
        </div>
      </div>

      <div class="spatial-side">
        <div class="spatial-side-title">空间关系列表（{{ filteredLinks.length }}）</div>
        <div class="spatial-list">
          <div
            v-for="l in filteredLinks"
            :key="l.id"
            class="spatial-row"
            :class="{ active: l.id === selectedLinkId }"
            @click="selectLink(l)"
          >
            <div class="row-route">
              <span class="row-name">{{ nodeName(l.source) }}</span>
              <span class="row-arrow">→</span>
              <span class="row-name">{{ nodeName(l.target) }}</span>
            </div>
            <div class="row-meta">
              <el-tag size="small" effect="dark" :color="linkColor(l.type)" class="row-type">{{ l.type }}</el-tag>
              <el-tag v-if="semanticOf(l)" size="small" effect="plain" type="info">{{ semanticOf(l) }}</el-tag>
              <el-tag v-if="l.props?.['方向']" size="small" effect="plain">{{ l.props['方向'] }}</el-tag>
              <el-tag v-if="l.props?.['距离_m'] != null" size="small" effect="plain" type="warning">
                {{ l.props['距离_m'] }} m
              </el-tag>
            </div>
            <div v-if="l.props?.['中介']" class="row-medium">中介：{{ l.props['中介'] }}</div>
          </div>
        </div>
      </div>
    </div>

    <el-drawer v-model="detailVisible" :title="detailMode === 'node' ? '节点详情' : '空间关系详情'" size="440px">
      <NodeDetailPanel v-if="detailVisible && detailMode === 'node' && selectedNodeId" :node-id="selectedNodeId" />
      <div v-else-if="detailVisible && detailMode === 'link' && selectedLink" class="link-detail">
        <div class="link-head">
          <span class="link-name">{{ nodeName(selectedLink.source) }}</span>
          <LabelBadge :label="nodeLabel(selectedLink.source)" />
          <span class="link-arrow">→</span>
          <span class="link-name">{{ nodeName(selectedLink.target) }}</span>
          <LabelBadge :label="nodeLabel(selectedLink.target)" />
        </div>
        <el-divider content-position="left">关系信息</el-divider>
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="关系类型">
            <el-tag size="small" effect="dark" :color="linkColor(selectedLink.type)">{{ selectedLink.type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-for="[k, v] in linkPropsEntries" :key="k" :label="k">
            {{ k === '距离_m' ? `${v} m` : formatValue(v) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getGardenGraph, getSpatialRelations } from '../api'
import { useAppStore } from '../stores/app'
import { useGraphStore } from '../stores/graph'
import { labelColor, lineStyleFor } from '../utils/graphStyle'
import NodeDetailPanel from '../components/NodeDetailPanel.vue'
import LabelBadge from '../components/LabelBadge.vue'

// 图表实现与游线页一致：scatter + lines 直角坐标系（数据坐标即屏幕坐标，命中测试正确）

const app = useAppStore()
const graphStore = useGraphStore()
const chartEl = ref(null)
let chart = null

const loading = ref(false)
const garden = ref(null) // 全园子图（全部节点坐标 + 属于关系底图）
const spatial = ref(null) // /api/spatial/relations 返回 {nodes, links}
const detailVisible = ref(false)
const detailMode = ref('node') // 'node' | 'link'
const selectedNodeId = ref('')
const selectedLinkId = ref('')

// 筛选条件
const relType = ref('')
const adjacencyType = ref('')
const contactType = ref('')
const medium = ref('')
const maxDist = ref(100)
const maxDistAll = ref(100)

const spatialLinks = computed(() => spatial.value?.links || [])

// ---------- 数据加载 ----------

async function load() {
  if (!app.currentDb) return
  loading.value = true
  try {
    const [g, s] = await Promise.all([
      getGardenGraph(app.currentDb).then((x) => x.data),
      getSpatialRelations({ db: app.currentDb }).then((x) => x.data)
    ])
    garden.value = g
    spatial.value = s
    // 距离上限取数据最大值向上取整到 10 的倍数
    const ds = spatialLinks.value.map((l) => l.props?.['距离_m']).filter((v) => typeof v === 'number')
    maxDistAll.value = ds.length ? Math.ceil(Math.max(...ds) / 10) * 10 : 100
    maxDist.value = maxDistAll.value
    selectedLinkId.value = ''
    await nextTick()
    chart.resize()
    render()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

// ---------- 统计与筛选选项（全部动态取自数据，无硬编码） ----------

function relCount(type) {
  return spatialLinks.value.filter((l) => l.type === type).length
}

const relTypes = computed(() => [...new Set(spatialLinks.value.map((l) => l.type))])

const adjacencyValues = computed(() =>
  [...new Set(
    spatialLinks.value
      .filter((l) => l.type === '相邻')
      .map((l) => l.props?.['相邻类型'])
      .filter(Boolean)
  )].sort()
)

const contactValues = computed(() =>
  [...new Set(
    spatialLinks.value
      .filter((l) => l.type === '相接')
      .map((l) => l.props?.['接触类型'])
      .filter(Boolean)
  )].sort()
)

// 中介为复合值（如"园路 / 临水游线"），拆分成原子选项
const mediumValues = computed(() =>
  [...new Set(
    spatialLinks.value.flatMap((l) => {
      const v = l.props?.['中介']
      if (!v) return []
      return String(v).split('/').map((p) => p.trim()).filter(Boolean)
    })
  )].sort()
)

const filteredLinks = computed(() => {
  let ls = spatialLinks.value
  if (relType.value) ls = ls.filter((l) => l.type === relType.value)
  if (adjacencyType.value) ls = ls.filter((l) => l.props?.['相邻类型'] === adjacencyType.value)
  if (contactType.value) ls = ls.filter((l) => l.props?.['接触类型'] === contactType.value)
  if (medium.value) ls = ls.filter((l) => String(l.props?.['中介'] || '').includes(medium.value))
  if (maxDist.value < maxDistAll.value) {
    ls = ls.filter((l) => (l.props?.['距离_m'] ?? Infinity) <= maxDist.value)
  }
  return ls
})

function semanticOf(l) {
  return l.props?.['相邻类型'] || l.props?.['接触类型'] || ''
}

function linkColor(type) {
  return lineStyleFor(type, app.schema?.rel_types || []).color
}

// ---------- 节点查询 ----------

const nodeMap = computed(() => {
  const m = new Map()
  for (const n of garden.value?.nodes || []) m.set(n.id, n)
  for (const n of spatial.value?.nodes || []) if (!m.has(n.id)) m.set(n.id, n)
  return m
})

function nodeName(id) {
  return nodeMap.value.get(id)?.name || id
}

function nodeLabel(id) {
  return nodeMap.value.get(id)?.label || ''
}

function nodeCoordMap() {
  const nodes = [...nodeMap.value.values()]
  const pts = nodes.filter((n) => typeof n.props?.x === 'number' && typeof n.props?.y === 'number')
  const cx = pts.length ? pts.reduce((s, n) => s + n.props.x, 0) / pts.length : 0
  const cy = pts.length ? pts.reduce((s, n) => s + n.props.y, 0) / pts.length : 0
  const m = new Map()
  for (const n of nodes) {
    const x = typeof n.props?.x === 'number' ? n.props.x : cx
    const y = typeof n.props?.y === 'number' ? n.props.y : cy
    m.set(n.id, { x, y })
  }
  return m
}

// ---------- 选择与详情 ----------

const selectedLink = computed(() => spatialLinks.value.find((l) => l.id === selectedLinkId.value) || null)

const linkPropsEntries = computed(() => {
  const pp = selectedLink.value?.props || {}
  return Object.entries(pp).filter(([k, v]) => v !== null && v !== undefined)
})

function formatValue(v) {
  return String(v)
}

function selectLink(l) {
  selectedLinkId.value = l.id
  detailMode.value = 'link'
  detailVisible.value = true
  render()
}

function openNodeDetail(id) {
  selectedNodeId.value = id
  graphStore.select(id)
  detailMode.value = 'node'
  detailVisible.value = true
  render()
}

// 筛选变化时若选中项被过滤掉则清除选中
watch(filteredLinks, (ls) => {
  if (selectedLinkId.value && !ls.some((l) => l.id === selectedLinkId.value)) {
    selectedLinkId.value = ''
    if (detailMode.value === 'link') detailVisible.value = false
  }
})

// ---------- 图表 ----------

const NODE_TOOLTIP_KEYS = ['类型', '平面形式', '屋顶形式', '功能']
const LINK_TOOLTIP_KEYS = ['相邻类型', '接触类型', '中介', '方向', '距离_m', '环线序号', '空间关系']

function tooltipFormatter(p) {
  const rows = []
  if (p.seriesType === 'scatter') {
    const raw = p.data._raw
    rows.push(`<b>${raw.name}</b>`)
    rows.push(`${raw.label} · ${raw.db}`)
    const pp = raw.props || {}
    for (const k of NODE_TOOLTIP_KEYS) {
      if (pp[k] !== undefined && pp[k] !== null) rows.push(`${k}：${String(pp[k]).slice(0, 40)}`)
    }
  } else if (p.seriesType === 'lines') {
    const raw = p.data._raw
    if (raw?.spatial) {
      const l = raw
      rows.push(`<b>${l.type}：${nodeName(l.source)} → ${nodeName(l.target)}</b>`)
      for (const k of LINK_TOOLTIP_KEYS) {
        const v = l.props?.[k]
        if (v !== undefined && v !== null) rows.push(`${k}：${k === '距离_m' ? v + ' m' : v}`)
      }
    }
  }
  return rows.join('<br/>')
}

function buildOption() {
  const nodes = [...nodeMap.value.values()]
  const labels = app.schema?.labels?.length
    ? app.schema.labels
    : [...new Set(nodes.map((n) => n.label))]
  const coord = nodeCoordMap()

  // 节点：每类标签一个 scatter 系列
  const series = []
  for (const l of labels) {
    const data = nodes
      .filter((n) => n.label === l)
      .map((n) => {
        const c = coord.get(n.id) || { x: 0, y: 0 }
        return {
          value: [c.x, c.y],
          name: n.name,
          symbolSize: 14,
          _raw: n,
          itemStyle:
            selectedNodeId.value === n.id ? { borderColor: '#f56c6c', borderWidth: 3 } : undefined
        }
      })
    series.push({
      name: l,
      type: 'scatter',
      data,
      itemStyle: { color: labelColor(l, labels) },
      label: { show: true, position: 'right', fontSize: 10, color: '#4a4a4a', formatter: '{b}' },
      emphasis: { scale: 1.4 },
      z: 5
    })
  }

  // 属于关系底图（浅灰、不可交互）
  const belongData = []
  for (const l of garden.value?.links || []) {
    if (l.type !== '属于') continue
    const a = coord.get(l.source)
    const b = coord.get(l.target)
    if (a && b) belongData.push({ coords: [[a.x, a.y], [b.x, b.y]], _raw: l })
  }
  series.push({
    name: '属于关系',
    type: 'lines',
    coordinateSystem: 'cartesian2d',
    data: belongData,
    lineStyle: { color: '#d6dae0', width: 1, opacity: 0.7 },
    silent: true,
    tooltip: { show: false },
    z: 1
  })

  // 空间关系：匹配=彩色可交互；未匹配=浅灰不可交互
  const matchedIds = new Set(filteredLinks.value.map((l) => l.id))
  const unmatchedData = []
  const matchedData = []
  for (const l of spatialLinks.value) {
    const a = coord.get(l.source)
    const b = coord.get(l.target)
    if (!a || !b) continue
    const item = { coords: [[a.x, a.y], [b.x, b.y]], _raw: { ...l, spatial: true } }
    if (matchedIds.has(l.id)) {
      const selected = l.id === selectedLinkId.value
      item.lineStyle = {
        color: linkColor(l.type),
        width: selected ? 5.5 : 2.5,
        opacity: selected ? 1 : 0.9
      }
      matchedData.push(item)
    } else {
      unmatchedData.push(item)
    }
  }
  series.push({
    name: '空间关系（未匹配）',
    type: 'lines',
    coordinateSystem: 'cartesian2d',
    data: unmatchedData,
    lineStyle: { color: '#c8cdd4', width: 1, opacity: 0.6 },
    silent: true,
    tooltip: { show: false },
    z: 2
  })
  series.push({
    name: '空间关系（匹配）',
    type: 'lines',
    coordinateSystem: 'cartesian2d',
    data: matchedData,
    z: 3
  })

  return {
    animationDurationUpdate: 300,
    tooltip: { trigger: 'item', confine: true, formatter: tooltipFormatter },
    legend: {
      data: labels,
      top: 6,
      left: 8,
      type: 'scroll',
      textStyle: { fontSize: 12 }
    },
    grid: { left: 12, right: 12, top: 34, bottom: 12 },
    xAxis: { type: 'value', show: false, min: 'dataMin', max: 'dataMax' },
    yAxis: { type: 'value', show: false, inverse: true, min: 'dataMin', max: 'dataMax' },
    dataZoom: [{ type: 'inside' }],
    series
  }
}

function render() {
  if (!chart) return
  chart.setOption(buildOption())
}

function onResize() {
  if (chart) chart.resize()
}

let resizeObserver = null

onMounted(() => {
  chart = echarts.init(chartEl.value)
  chart.on('click', (p) => {
    if (p.seriesType === 'scatter') {
      openNodeDetail(p.data._raw.id)
    } else if (p.seriesType === 'lines' && p.data?._raw?.spatial) {
      selectLink(p.data._raw)
    }
  })
  window.addEventListener('resize', onResize)
  resizeObserver = new ResizeObserver(onResize)
  resizeObserver.observe(chartEl.value)
  if (import.meta.env.DEV) window.__spatialChart = chart
  load()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  resizeObserver?.disconnect()
  if (chart) {
    chart.dispose()
    chart = null
  }
})

watch([relType, adjacencyType, contactType, medium, maxDist], () => render())
watch(() => app.currentDb, load)
</script>

<style scoped>
.spatial-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.spatial-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.spatial-stats {
  display: flex;
  align-items: center;
  gap: 10px;
}

.spatial-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.spatial-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.dist-filter {
  display: flex;
  align-items: center;
}

.dist-label {
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
}

.filter-count {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
}

.spatial-body {
  display: flex;
  gap: 10px;
  flex: 1;
  min-height: 0;
}

.spatial-canvas-wrap {
  flex: 1;
  position: relative;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fbfcfd;
  min-width: 0;
  min-height: 0;
}

.spatial-canvas {
  width: 100%;
  height: 100%;
}

.spatial-empty,
.spatial-empty-soft {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.spatial-empty {
  background: #fbfcfd;
}

.spatial-empty-soft {
  color: #909399;
  font-size: 13px;
}

.spatial-hint {
  position: absolute;
  left: 10px;
  bottom: 8px;
  font-size: 12px;
  color: #909399;
  pointer-events: none;
}

.spatial-side {
  width: 400px;
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fff;
  min-height: 0;
}

.spatial-side-title {
  padding: 10px 12px;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid #ebeef5;
  color: #303133;
}

.spatial-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.spatial-row {
  padding: 8px 12px;
  border-bottom: 1px solid #f2f4f7;
  cursor: pointer;
}

.spatial-row:hover {
  background: #f5f7fa;
}

.spatial-row.active {
  background: #eef4fb;
}

.row-route {
  font-size: 13px;
  color: #303133;
}

.row-name {
  font-weight: 500;
}

.row-arrow {
  color: #5b8ff9;
  font-weight: 700;
  margin: 0 4px;
}

.row-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.row-type {
  color: #fff;
  border: none;
}

.row-medium {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.link-detail {
  padding: 2px;
}

.link-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.link-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.link-arrow {
  color: #5b8ff9;
  font-weight: 700;
}
</style>
