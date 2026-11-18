<template>
  <div class="page">
    <div class="page-header">
      <span class="page-title">数据概览</span>
      <el-tag v-if="app.currentDb" size="small" effect="plain" type="success" style="margin-left: 10px">
        当前园林：{{ app.gardenName }}
      </el-tag>
      <el-button size="small" :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-card shadow="never" class="arch-card">
      <template #header>平台总体架构</template>
      <div class="arch">
        <div class="arch-layer" style="--layer-color: #2f4b3c">
          <div class="layer-label">数据层</div>
          <div class="layer-body">
            <div class="layer-title">Neo4j 图数据库</div>
            <div class="layer-sub">江南古典园林知识图谱数据</div>
          </div>
        </div>
        <div class="arch-arrow">↓</div>
        <div class="arch-layer" style="--layer-color: #3b6ea5">
          <div class="layer-label">知识层</div>
          <div class="layer-body">
            <div class="layer-title">园林实体（建筑 · 花木 · 山石 · 池沼）</div>
            <div class="layer-sub">空间关系 · 游线关系</div>
          </div>
        </div>
        <div class="arch-arrow">↓</div>
        <div class="arch-layer" style="--layer-color: #2f8f83">
          <div class="layer-label">展示层</div>
          <div class="layer-body">
            <div class="layer-chips">
              <div class="layer-chip" @click="goto('/graph', 'spatial')">空间布局可视化</div>
              <div class="layer-chip" @click="goto('/graph', 'relation')">知识网络探索</div>
              <div class="layer-chip" @click="goto('/route')">游线分析</div>
              <div class="layer-chip" @click="goto('/spatial')">空间关系分析</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="14">
      <el-col :span="6">
        <StatCard title="实体节点总数" :value="ov?.total_nodes ?? '-'" color="#3b6ea5" />
      </el-col>
      <el-col :span="6">
        <StatCard title="关系总数" :value="ov?.total_rels ?? '-'" color="#8a6d3b" />
      </el-col>
      <el-col :span="6">
        <StatCard title="实体标签类型" :value="ov?.by_label?.length ?? '-'" color="#2f8f83" />
      </el-col>
      <el-col :span="6">
        <StatCard title="园林数量" :value="ov?.databases?.length ?? '-'" color="#8b1e1e" />
      </el-col>
    </el-row>

    <el-row :gutter="14" style="margin-top: 14px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>节点类型统计</template>
          <div ref="barEl" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>关系类型统计</template>
          <div ref="pieEl" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-top: 14px">
      <template #header>各园林知识图谱规模</template>
      <el-table :data="ov?.databases || []" size="small">
        <el-table-column prop="garden" label="园林" min-width="140" />
        <el-table-column prop="name" label="数据库" min-width="140" />
        <el-table-column prop="nodes" label="节点数" width="100" />
        <el-table-column prop="rels" label="关系数" width="100" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getOverview } from '../api'
import { useAppStore } from '../stores/app'
import { useGraphStore } from '../stores/graph'
import StatCard from '../components/StatCard.vue'
import { labelColor } from '../utils/graphStyle'

const app = useAppStore()
const router = useRouter()
const graphStore = useGraphStore()

// 架构图展示层模块跳转（空间布局/知识网络 需预设图谱页模式）
function goto(path, mode) {
  if (mode) graphStore.setMode(mode)
  router.push(path)
}
const loading = ref(false)
const ov = ref(null)
const barEl = ref(null)
const pieEl = ref(null)
let barChart = null
let pieChart = null

async function load() {
  loading.value = true
  try {
    ov.value = (await getOverview()).data
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  if (barEl.value) {
    barChart = barChart || echarts.init(barEl.value)
    const data = (ov.value?.by_label || []).map((x) => ({ name: x.label, value: x.count }))
    barChart.setOption({
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: data.map((d) => d.name) },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        {
          type: 'bar',
          data: data.map((d) => ({
            value: d.value,
            itemStyle: { color: labelColor(d.name, data.map((x) => x.name)) }
          })),
          barMaxWidth: 46
        }
      ]
    })
  }
  if (pieEl.value) {
    pieChart = pieChart || echarts.init(pieEl.value)
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, type: 'scroll' },
      series: [
        {
          type: 'pie',
          radius: ['30%', '62%'],
          center: ['50%', '45%'],
          data: (ov.value?.by_rel_type || []).map((x) => ({ name: x.type, value: x.count })),
          label: { formatter: '{b}: {c}' }
        }
      ]
    })
  }
}

function onResize() {
  barChart?.resize()
  pieChart?.resize()
}

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  barChart?.dispose()
  pieChart?.dispose()
})

// 库列表变化（新园林加载）后自动刷新
watch(() => app.databases.length, load)
</script>

<style scoped>
.chart-box {
  height: 300px;
}

/* ---------- 平台总体架构图 ---------- */

.arch-card {
  margin-bottom: 14px;
}

.arch {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.arch-layer {
  display: flex;
  align-items: stretch;
  width: 100%;
  max-width: 760px;
  border: 1px solid color-mix(in srgb, var(--layer-color) 35%, #fff);
  border-radius: 6px;
  background: color-mix(in srgb, var(--layer-color) 6%, #fff);
  overflow: hidden;
}

.layer-label {
  flex: none;
  width: 84px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--layer-color);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 2px;
  writing-mode: horizontal-tb;
}

.layer-body {
  flex: 1;
  padding: 10px 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.layer-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.layer-sub {
  font-size: 13px;
  color: #606266;
}

.layer-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.layer-chip {
  padding: 5px 16px;
  border-radius: 16px;
  background: var(--layer-color);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.layer-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.18);
}

.arch-arrow {
  font-size: 16px;
  color: #909399;
  line-height: 1;
  padding: 1px 0;
}
</style>
