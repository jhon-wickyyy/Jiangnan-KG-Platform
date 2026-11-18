<template>
  <div class="path-page">
    <div class="path-toolbar">
      <div class="path-stats">
        <span class="path-title">路径查询</span>
        <el-tag v-if="app.currentDb" size="small" type="success" effect="plain">
          当前园林：{{ app.gardenName }}
        </el-tag>
        <template v-if="pathData">
          <el-tag size="small" type="primary" effect="plain">路径 {{ pathData.length }} 跳</el-tag>
          <el-tag v-if="totalDist != null" size="small" type="warning" effect="plain">
            总距离 ≈ {{ totalDist }} m
          </el-tag>
        </template>
      </div>
      <div class="path-selects">
        <el-select
          v-model="sourceId"
          placeholder="起点节点"
          filterable
          clearable
          size="small"
          style="width: 230px"
        >
          <el-option v-for="n in nodes" :key="n.id" :label="`${n.name}（${n.label}）`" :value="n.id" />
        </el-select>
        <el-button size="small" title="交换起点终点" :disabled="!sourceId || !targetId" @click="swap">
          ⇄
        </el-button>
        <el-select
          v-model="targetId"
          placeholder="终点节点"
          filterable
          clearable
          size="small"
          style="width: 230px"
        >
          <el-option v-for="n in nodes" :key="n.id" :label="`${n.name}（${n.label}）`" :value="n.id" />
        </el-select>
        <el-checkbox v-model="spatialOnly" size="small">仅空间关系</el-checkbox>
        <el-button
          type="primary"
          size="small"
          :loading="loading"
          :disabled="!sourceId || !targetId || sourceId === targetId"
          @click="query"
        >
          查询路径
        </el-button>
      </div>
    </div>

    <div class="path-body">
      <div v-loading="loading" class="path-canvas-wrap">
        <div ref="chartEl" class="path-canvas"></div>
        <div v-if="!pathData && !loading" class="path-empty">
          <el-empty description="选择起点与终点节点，查询它们之间的最短路径" :image-size="70" />
        </div>
        <div class="path-hint">
          空间布局底图 + 高亮最短路径（绿=起点 · 红=终点 · 橙=路径节点）· 点击节点查看详情 · 滚轮缩放/拖拽平移
        </div>
      </div>

      <div class="path-side">
        <div class="path-side-title">最短路径序列</div>
        <div v-if="pathData" class="path-desc">{{ pathData.description }}</div>
        <el-steps v-if="pathData" direction="vertical" :active="pathData.length" class="path-steps">
          <el-step v-for="(n, i) in pathNodes" :key="n.id" :description="stepDesc(i)">
            <template #title>
              <div class="step-title" @click="openNodeDetail(n.id)">
                <span>{{ n.name }}</span>
                <LabelBadge :label="n.label" />
                <el-tag v-if="i === 0" size="small" type="success" effect="plain">起点</el-tag>
                <el-tag v-else-if="i === pathNodes.length - 1" size="small" type="danger" effect="plain">终点</el-tag>
              </div>
            </template>
          </el-step>
        </el-steps>
        <el-empty v-else-if="!loading" description="暂无路径" :image-size="60" />
      </div>
    </div>

    <el-drawer v-model="detailVisible" title="节点详情" size="440px">
      <NodeDetailPanel v-if="detailVisible && selectedNodeId" :node-id="selectedNodeId" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getEntities, getGardenGraph, getPath } from '../api'
import { useAppStore } from '../stores/app'
import { useGraphStore } from '../stores/graph'
import { labelColor, lineStyleFor } from '../utils/graphStyle'
import NodeDetailPanel from '../components/NodeDetailPanel.vue'
import LabelBadge from '../components/LabelBadge.vue'

// 图表实现与游线/空间关系页一致：scatter + lines 直角坐标系（真实 x/y 坐标，命中测试正确）

const app = useAppStore()
const graphStore = useGraphStore()
const chartEl = ref(null)
let chart = null

const loading = ref(false)
const nodes = ref([]) // 当前园林全部实体（起点/终点选择）
const garden = ref(null) // 空间底图 {nodes, links}
const pathData = ref(null) // /api/path 返回 {description, length, nodes, links}
const sourceId = ref('')
const targetId = ref('')
const spatialOnly = ref(false) // 仅沿 相邻/相接 空间关系寻路
const detailVisible = ref(false)
const selectedNodeId = ref('')

const pathNodes = computed(() => pathData.value?.nodes || [])

// 路径总距离（各段 距离_m 求和，缺失则 null）
const totalDist = computed(() => {
  const links = pathData.value?.links || []
  const ds = links.map((l) => l.props?.['距离_m']).filter((v) => typeof v === 'number')
  if (!ds.length) return null
  return Math.round(ds.reduce((s, v) => s + v, 0) * 10) / 10
})

// ---------- 数据加载 ----------

async function loadBase() {
  if (!app.currentDb) return
  loading.value = true
  try {
    const [ents, g] = await Promise.all([
      getEntities({ db: app.currentDb, page_size: 200 }).then((x) => x.data),
      getGardenGraph(app.currentDb).then((x) => x.data)
    ])
    nodes.value = ents.items
    garden.value = g
    pathData.value = null
    sourceId.value = ''
    targetId.value = ''
    await nextTick()
    chart.resize()
    render()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function query() {
  if (!sourceId.value || !targetId.value) return
  const [, sLabel, sBid] = sourceId.value.split('::')
  const [, tLabel, tBid] = targetId.value.split('::')
  loading.value = true
  try {
    const params = {
      db: app.currentDb,
      source_label: sLabel,
      source_id: sBid,
      target_label: tLabel,
      target_id: tBid
    }
    if (spatialOnly.value) params.rel_types = '相邻,相接'
    pathData.value = (await getPath(params)).data
    await nextTick()
    render()
  } catch (e) {
    pathData.value = null
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function swap() {
  const t = sourceId.value
  sourceId.value = targetId.value
  targetId.value = t
}

function openNodeDetail(id) {
  selectedNodeId.value = id
  graphStore.select(id)
  detailVisible.value = true
}

// 第 i 步 → 第 i+1 步的关系描述
function stepDesc(i) {
  const links = pathData.value?.links || []
  if (i >= links.length) return ''
  const l = links[i]
  const p = l.props || {}
  const parts = [l.type]
  for (const k of ['相邻类型', '接触类型', '方向', '距离_m', '中介']) {
    if (p[k] !== undefined && p[k] !== null) parts.push(k === '距离_m' ? `${p[k]} m` : p[k])
  }
  return parts.join(' · ')
}

// ---------- 图表 ----------

function nodeCoordMap() {
  const all = garden.value?.nodes || []
  const pts = all.filter((n) => typeof n.props?.x === 'number' && typeof n.props?.y === 'number')
  const cx = pts.length ? pts.reduce((s, n) => s + n.props.x, 0) / pts.length : 0
  const cy = pts.length ? pts.reduce((s, n) => s + n.props.y, 0) / pts.length : 0
  const m = new Map()
  for (const n of all) {
    const x = typeof n.props?.x === 'number' ? n.props.x : cx
    const y = typeof n.props?.y === 'number' ? n.props.y : cy
    m.set(n.id, { x, y })
  }
  return m
}

const NODE_TOOLTIP_KEYS = ['类型', '平面形式', '屋顶形式', '功能']
const LINK_TOOLTIP_KEYS = ['相邻类型', '接触类型', '中介', '方向', '距离_m', '空间关系']

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
    if (raw?.pathLink) {
      rows.push(`<b>${raw.type}：${raw.fromName} → ${raw.toName}</b>`)
      for (const k of LINK_TOOLTIP_KEYS) {
        const v = raw.props?.[k]
        if (v !== undefined && v !== null) rows.push(`${k}：${k === '距离_m' ? v + ' m' : v}`)
      }
    }
  }
  return rows.join('<br/>')
}

function buildOption() {
  const baseNodes = garden.value?.nodes || []
  const labels = app.schema?.labels?.length
    ? app.schema.labels
    : [...new Set(baseNodes.map((n) => n.label))]
  const coord = nodeCoordMap()

  // 路径节点角色：首=起点 尾=终点 其余=途经
  const pathNodeIds = pathNodes.value.map((n) => n.id)
  const roleOf = {}
  if (pathNodeIds.length) {
    roleOf[pathNodeIds[0]] = 'start'
    roleOf[pathNodeIds[pathNodeIds.length - 1]] = 'end'
    for (const id of pathNodeIds.slice(1, -1)) roleOf[id] = 'mid'
  }
  const ROLE_BORDER = { start: '#2f8f83', end: '#8b1e1e', mid: '#e6550d' }

  const series = []
  for (const l of labels) {
    const data = baseNodes
      .filter((n) => n.label === l)
      .map((n) => {
        const c = coord.get(n.id) || { x: 0, y: 0 }
        const role = roleOf[n.id]
        return {
          value: [c.x, c.y],
          name: n.name,
          symbolSize: role ? 24 : 12,
          _raw: n,
          itemStyle: role
            ? { borderColor: ROLE_BORDER[role], borderWidth: 3 }
            : selectedNodeId.value === n.id
              ? { borderColor: '#f56c6c', borderWidth: 3 }
              : undefined
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

  // 底图边：全园关系浅灰（路径边除外）
  const pathLinkIds = new Set((pathData.value?.links || []).map((l) => l.id))
  const baseLineData = []
  for (const l of garden.value?.links || []) {
    if (pathLinkIds.has(l.id)) continue
    const a = coord.get(l.source)
    const b = coord.get(l.target)
    if (a && b) baseLineData.push({ coords: [[a.x, a.y], [b.x, b.y]], _raw: l })
  }
  series.push({
    name: '园内关系',
    type: 'lines',
    coordinateSystem: 'cartesian2d',
    data: baseLineData,
    lineStyle: { color: '#c8cdd4', width: 1, opacity: 0.65 },
    silent: true,
    tooltip: { show: false },
    z: 1
  })

  // 路径边：按关系类型着色 + 方向箭头
  const pathLineData = []
  const nodeNameById = new Map(baseNodes.map((n) => [n.id, n.name]))
  for (const l of pathData.value?.links || []) {
    const a = coord.get(l.source)
    const b = coord.get(l.target)
    if (!a || !b) continue
    pathLineData.push({
      coords: [[a.x, a.y], [b.x, b.y]],
      _raw: { ...l, pathLink: true, fromName: nodeNameById.get(l.source) || l.source, toName: nodeNameById.get(l.target) || l.target },
      lineStyle: { color: lineStyleFor(l.type, app.schema?.rel_types || []).color, width: 4, opacity: 1 }
    })
  }
  series.push({
    name: '最短路径',
    type: 'lines',
    coordinateSystem: 'cartesian2d',
    data: pathLineData,
    symbol: ['none', 'arrow'],
    symbolSize: 9,
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
    if (p.seriesType !== 'scatter') return
    openNodeDetail(p.data._raw.id)
  })
  window.addEventListener('resize', onResize)
  resizeObserver = new ResizeObserver(onResize)
  resizeObserver.observe(chartEl.value)
  if (import.meta.env.DEV) window.__pathChart = chart
  loadBase()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  resizeObserver?.disconnect()
  if (chart) {
    chart.dispose()
    chart = null
  }
})

watch(() => app.currentDb, loadBase)
</script>

<style scoped>
.path-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.path-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.path-stats {
  display: flex;
  align-items: center;
  gap: 10px;
}

.path-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.path-selects {
  display: flex;
  align-items: center;
  gap: 8px;
}

.path-body {
  display: flex;
  gap: 10px;
  flex: 1;
  min-height: 0;
}

.path-canvas-wrap {
  flex: 1;
  position: relative;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fbfcfd;
  min-width: 0;
  min-height: 0;
}

.path-canvas {
  width: 100%;
  height: 100%;
}

.path-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fbfcfd;
}

.path-hint {
  position: absolute;
  left: 10px;
  bottom: 8px;
  font-size: 12px;
  color: #909399;
  pointer-events: none;
}

.path-side {
  width: 420px;
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fff;
  min-height: 0;
}

.path-side-title {
  padding: 10px 12px;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid #ebeef5;
  color: #303133;
}

.path-desc {
  padding: 10px 12px;
  font-size: 12px;
  color: #606266;
  background: #f8fafc;
  border-bottom: 1px solid #ebeef5;
  line-height: 1.6;
}

.path-steps {
  padding: 12px;
  overflow-y: auto;
  min-height: 0;
}

.step-title {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  flex-wrap: wrap;
}

.step-title span {
  font-weight: 500;
}
</style>
