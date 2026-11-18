<template>
  <div class="route-page">
    <div class="route-toolbar">
      <div class="route-stats">
        <span class="route-title">游线分析</span>
        <template v-if="routeData">
          <el-tag size="small" type="success" effect="plain">站点 {{ routeData.stops.length }}</el-tag>
          <el-tag size="small" type="warning" effect="plain">总长 {{ routeData.total_distance_m }} m</el-tag>
          <el-tag size="small" :type="routeData.closed ? 'success' : 'info'" effect="plain">
            {{ routeData.closed ? '闭环游览线' : '未闭环' }}
          </el-tag>
        </template>
      </div>
      <div class="route-controls">
        <el-button-group size="small">
          <el-button :disabled="!routeData" @click="stepBack">上一步</el-button>
          <el-button v-if="!playing" type="primary" :disabled="!routeData" @click="play">
            ▶ 播放游线
          </el-button>
          <el-button v-else type="warning" @click="pause">⏸ 暂停</el-button>
          <el-button :disabled="!routeData" @click="stepNext">下一步</el-button>
        </el-button-group>
        <el-slider
          v-model="currentStep"
          :min="0"
          :max="stopCount"
          :disabled="!routeData"
          style="width: 240px; margin-left: 14px"
          @input="pause"
        />
      </div>
    </div>

    <div class="route-body">
      <div v-loading="loading" class="route-canvas-wrap">
        <div ref="chartEl" class="route-canvas"></div>
        <div v-if="!routeData && !loading" class="route-empty">
          <el-empty description="当前园林无游线数据（缺少带环线序号的边）" />
        </div>
        <div v-if="routeData" class="route-hint">
          {{ playing
            ? '播放中：按环线序号还原游览动线（起点=大门 / 入口）'
            : '空间底图 + 建筑环线游线（点击节点查看详情 · 点击右侧行程可跳转 · 拖动滑块回放 · 滚轮缩放/拖拽平移）' }}
        </div>
      </div>

      <div class="route-side">
        <div class="route-side-title">行程列表（按环线序号）</div>
        <div class="route-stop-list">
          <div
            v-for="s in routeData?.stops || []"
            :key="s.seq"
            class="route-stop"
            :class="{ active: s.seq <= currentStep }"
            @click="currentStep = s.seq"
          >
            <span class="stop-seq">{{ s.seq }}</span>
            <div class="stop-main">
              <div class="stop-route">{{ s.from }} <b>→</b> {{ s.to }}</div>
              <div class="stop-meta">
                <el-tag v-if="s.direction" size="small" effect="plain" type="info">{{ s.direction }}</el-tag>
                <el-tag v-if="s.distance_m != null" size="small" effect="plain" type="warning">
                  {{ s.distance_m }} m
                </el-tag>
                <el-tag v-if="s.medium" size="small" effect="plain">{{ s.medium }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-drawer v-model="detailVisible" title="节点详情" size="440px">
      <NodeDetailPanel v-if="detailVisible && selectedId" :node-id="selectedId" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getGardenGraph, getRoute } from '../api'
import { useAppStore } from '../stores/app'
import { useGraphStore } from '../stores/graph'
import { labelColor, lineStyleFor } from '../utils/graphStyle'
import NodeDetailPanel from '../components/NodeDetailPanel.vue'

// 图表实现说明：空间底图采用「scatter 散点 + lines 线」直角坐标系实现（数据坐标即屏幕坐标，
// 命中测试天然正确），不使用 graph 系列（graph 在 layout:none + roam 下存在视图变换错位问题）。

const app = useAppStore()
const graphStore = useGraphStore()
const chartEl = ref(null)
let chart = null

const loading = ref(false)
const garden = ref(null) // 空间底图 {nodes, links}
const routeData = ref(null) // /api/route 返回
const currentStep = ref(0) // 0=未开始；1..stops.length=推进到的站数
const playing = ref(false)
const detailVisible = ref(false)
const selectedId = ref(null)
let timer = null

const stopCount = computed(() => routeData.value?.stops.length || 0)

// 游线边按稳定 ID 索引（route.links 与 stops 一一对应，props 含 环线序号）
const routeLinkMap = computed(() => {
  const m = new Map()
  for (const l of routeData.value?.links || []) m.set(l.id, l)
  return m
})

// ---------- 数据加载 ----------

async function load() {
  if (!app.currentDb) return
  loading.value = true
  pause()
  try {
    const [g, r] = await Promise.all([
      getGardenGraph(app.currentDb).then((x) => x.data),
      getRoute(app.currentDb).then((x) => x.data)
    ])
    garden.value = g
    routeData.value = r.stops?.length ? r : null
    // 初始展示完整游线（答辩第一眼即可看到闭环）；播放时从头动画
    currentStep.value = stopCount.value
    await nextTick()
    // 容器在首屏布局稳定后才达到最终尺寸，先重测再渲染
    chart.resize()
    render()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

// ---------- 播放控制 ----------

function play() {
  if (!routeData.value) return
  if (currentStep.value >= stopCount.value) currentStep.value = 0
  playing.value = true
  clearInterval(timer)
  timer = setInterval(() => {
    currentStep.value += 1
    if (currentStep.value >= stopCount.value) pause()
  }, 900)
}

function pause() {
  playing.value = false
  clearInterval(timer)
}

function stepNext() {
  pause()
  currentStep.value = Math.min(currentStep.value + 1, stopCount.value)
}

function stepBack() {
  pause()
  currentStep.value = Math.max(currentStep.value - 1, 0)
}

// ---------- 图表构建 ----------

const ROUTE_DONE_COLOR = '#e6550d'
const ROUTE_TODO_COLOR = '#f0b58c'
const NODE_TOOLTIP_KEYS = ['类型', '平面形式', '屋顶形式', '功能']
const LINK_TOOLTIP_KEYS = ['相邻类型', '接触类型', '中介', '方向', '距离_m', '环线序号', '关系', '空间关系']

// 节点坐标映射（无坐标节点回退到质心）
function nodeCoordMap(nodes) {
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

function tooltipFormatter(p) {
  const rows = []
  if (p.seriesType === 'scatter') {
    const raw = p.data._raw
    rows.push(`<b>${raw.name}</b>`)
    rows.push(`${raw.label} · ${raw.db}`)
    const pp = raw.props || {}
    for (const k of NODE_TOOLTIP_KEYS) {
      if (pp[k] !== undefined && pp[k] !== null) {
        rows.push(`${k}：${String(pp[k]).slice(0, 40)}`)
      }
    }
  } else if (p.seriesType === 'lines') {
    const raw = p.data._raw
    if (raw?.route) {
      const s = raw.stop
      rows.push(`<b>游线第 ${raw.seq} 站：${s.from} → ${s.to}</b>`)
      for (const k of ['相邻类型', '方向', '距离_m', '中介']) {
        if (s[k] !== undefined && s[k] !== null) rows.push(`${k}：${s[k]}`)
      }
    } else if (raw) {
      rows.push(`<b>${raw.type}</b>`)
      for (const k of LINK_TOOLTIP_KEYS) {
        const v = raw.props?.[k]
        if (v !== undefined && v !== null) rows.push(`${k}：${v}`)
      }
    }
  }
  return rows.join('<br/>')
}

function buildOption() {
  const nodes = garden.value?.nodes?.length ? garden.value.nodes : routeData.value?.nodes || []
  const links = garden.value?.links?.length ? garden.value.links : []
  const labels = app.schema?.labels?.length
    ? app.schema.labels
    : [...new Set(nodes.map((n) => n.label))]

  const coord = nodeCoordMap(nodes)
  const routeNodeIds = new Set((routeData.value?.nodes || []).map((n) => n.id))
  const stopBySeq = new Map()
  for (const s of routeData.value?.stops || []) stopBySeq.set(s.seq, s)

  // 当前游线推进到的节点：第 currentStep 段的终点；0 时为起点（大门 / 入口）
  const routeLinks = routeData.value?.links || []
  let currentId = null
  if (routeLinks.length) {
    currentId =
      currentStep.value <= 0
        ? routeLinks[0].source
        : routeLinks[Math.min(currentStep.value, routeLinks.length) - 1].target
  }

  // 每类标签一个 scatter 系列（图例按标签控制显隐）
  const series = []
  for (const l of labels) {
    const data = nodes
      .filter((n) => n.label === l)
      .map((n) => {
        const c = coord.get(n.id) || { x: 0, y: 0 }
        const onRoute = routeNodeIds.has(n.id)
        const isCurrent = n.id === currentId
        return {
          value: [c.x, c.y],
          name: n.name,
          symbolSize: isCurrent ? 26 : onRoute ? 17 : 12,
          _raw: n,
          itemStyle: isCurrent
            ? { borderColor: ROUTE_DONE_COLOR, borderWidth: 4 }
            : selectedId.value === n.id
              ? { borderColor: '#f56c6c', borderWidth: 3 }
              : onRoute
                ? { borderColor: ROUTE_DONE_COLOR, borderWidth: 2 }
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
      z: 5 // 高于 lines 系列，保证节点处的悬停/点击命中节点而非线
    })
  }

  // 底图边（全部园内关系，灰色细线）
  const baseLineData = links.map((l) => {
    const a = coord.get(l.source)
    const b = coord.get(l.target)
    if (!a || !b) return null
    return {
      coords: [[a.x, a.y], [b.x, b.y]],
      _raw: l
    }
  }).filter(Boolean)
  series.push({
    name: '园内关系',
    type: 'lines',
    coordinateSystem: 'cartesian2d',
    data: baseLineData,
    lineStyle: { color: '#c8cdd4', width: 1, opacity: 0.7 },
    silent: true,
    tooltip: { show: false },
    z: 1
  })

  // 游线边：未走到的（橙色虚线）与已走到的（橙色实线+方向箭头）
  const routeDone = []
  const routeTodo = []
  for (const rl of routeLinks) {
    const a = coord.get(rl.source)
    const b = coord.get(rl.target)
    if (!a || !b) continue
    const seq = rl.props?.['环线序号'] ?? 0
    const item = { coords: [[a.x, a.y], [b.x, b.y]], _raw: { ...rl, route: true, seq, stop: stopBySeq.get(seq) } }
    ;(seq <= currentStep.value ? routeDone : routeTodo).push(item)
  }
  series.push({
    name: '游线（未走到）',
    type: 'lines',
    coordinateSystem: 'cartesian2d',
    data: routeTodo,
    lineStyle: { color: ROUTE_TODO_COLOR, width: 2.5, type: 'dashed' },
    z: 2
  })
  series.push({
    name: '游线（已走到）',
    type: 'lines',
    coordinateSystem: 'cartesian2d',
    data: routeDone,
    lineStyle: { color: ROUTE_DONE_COLOR, width: 3.5 },
    symbol: ['none', 'arrow'],
    symbolSize: 8,
    z: 3
  })

  return {
    animationDurationUpdate: 400,
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

let resizeObserver = null

function onResize() {
  if (chart) {
    chart.resize()
  }
}

onMounted(() => {
  chart = echarts.init(chartEl.value)
  chart.on('click', (p) => {
    if (p.seriesType !== 'scatter') return
    selectedId.value = p.data._raw.id
    graphStore.select(p.data._raw.id)
    detailVisible.value = true
  })
  window.addEventListener('resize', onResize)
  resizeObserver = new ResizeObserver(onResize)
  resizeObserver.observe(chartEl.value)
  if (import.meta.env.DEV) window.__routeChart = chart
  load()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  resizeObserver?.disconnect()
  clearInterval(timer)
  if (chart) {
    chart.dispose()
    chart = null
  }
})

watch(currentStep, () => render())
watch(() => app.currentDb, load)
</script>

<style scoped>
.route-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.route-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.route-stats {
  display: flex;
  align-items: center;
  gap: 10px;
}

.route-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.route-controls {
  display: flex;
  align-items: center;
}

.route-body {
  display: flex;
  gap: 10px;
  flex: 1;
  min-height: 0;
}

.route-canvas-wrap {
  flex: 1;
  position: relative;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fbfcfd;
  min-width: 0;
  min-height: 0;
}

.route-canvas {
  width: 100%;
  height: 100%;
}

.route-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fbfcfd;
}

.route-hint {
  position: absolute;
  left: 10px;
  bottom: 8px;
  font-size: 12px;
  color: #909399;
  pointer-events: none;
}

.route-side {
  width: 340px;
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fff;
  min-height: 0;
}

.route-side-title {
  padding: 10px 12px;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid #ebeef5;
  color: #303133;
}

.route-stop-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.route-stop {
  display: flex;
  gap: 10px;
  padding: 8px 12px;
  border-bottom: 1px solid #f2f4f7;
  cursor: pointer;
}

.route-stop:hover {
  background: #f5f7fa;
}

.route-stop.active {
  background: #fdf3e7;
}

.stop-seq {
  flex: none;
  width: 22px;
  height: 22px;
  margin-top: 2px;
  border-radius: 50%;
  background: #e6550d;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  line-height: 22px;
}

.route-stop:not(.active) .stop-seq {
  background: #d9dce3;
}

.stop-main {
  min-width: 0;
}

.stop-route {
  font-size: 13px;
  color: #303133;
}

.stop-route b {
  color: #e6550d;
  margin: 0 2px;
}

.stop-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}
</style>
