<template>
  <div class="page">
    <div class="page-header">
      <span class="page-title">知识网络分析</span>
      <div style="display: flex; align-items: center; gap: 10px">
        <el-tag v-if="app.currentDb" size="small" type="success" effect="plain">
          当前园林：{{ app.gardenName }}
        </el-tag>
        <el-button size="small" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="14">
      <el-col :span="6">
        <StatCard title="节点数量" :value="a?.total_nodes ?? '-'" color="#3b6ea5" />
      </el-col>
      <el-col :span="6">
        <StatCard title="关系数量" :value="a?.total_rels ?? '-'" color="#8a6d3b" />
      </el-col>
      <el-col :span="6">
        <StatCard title="平均连接度" :value="a?.avg_degree ?? '-'" color="#2f8f83" />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="最大关联节点"
          :value="a?.max_degree_node ? `${a.max_degree_node.name}（${a.max_degree_node.degree}）` : '-'"
          color="#8b1e1e"
        />
      </el-col>
    </el-row>

    <el-row :gutter="14" style="margin-top: 14px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>节点类型统计</template>
          <div ref="labelBarEl" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>关系类型统计</template>
          <div ref="relPieEl" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-top: 14px">
      <template #header>Top 核心节点（按关联节点数）</template>
      <div ref="topBarEl" class="chart-box top-chart"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getNetworkAnalysis } from '../api'
import { useAppStore } from '../stores/app'
import StatCard from '../components/StatCard.vue'
import { labelColor } from '../utils/graphStyle'

const app = useAppStore()
const loading = ref(false)
const a = ref(null) // /api/analysis/network 返回

const labelBarEl = ref(null)
const relPieEl = ref(null)
const topBarEl = ref(null)
let labelBarChart = null
let relPieChart = null
let topBarChart = null

async function load() {
  if (!app.currentDb) return
  loading.value = true
  try {
    a.value = (await getNetworkAnalysis(app.currentDb)).data
    await nextTick()
    renderCharts()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  const labels = (a.value?.by_label || []).map((x) => x.label)

  // 节点类型统计（柱状，按标签语义配色）
  if (labelBarEl.value) {
    labelBarChart = labelBarChart || echarts.init(labelBarEl.value)
    const data = a.value?.by_label || []
    labelBarChart.setOption({
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: data.map((d) => d.label) },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        {
          type: 'bar',
          data: data.map((d) => ({
            value: d.count,
            itemStyle: { color: labelColor(d.label, labels) }
          })),
          barMaxWidth: 46,
          label: { show: true, position: 'top' }
        }
      ]
    })
  }

  // 关系类型统计（环形饼图）
  if (relPieEl.value) {
    relPieChart = relPieChart || echarts.init(relPieEl.value)
    relPieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, type: 'scroll' },
      series: [
        {
          type: 'pie',
          radius: ['32%', '62%'],
          center: ['50%', '45%'],
          data: (a.value?.by_rel_type || []).map((x) => ({ name: x.type, value: x.count })),
          label: { formatter: '{b}: {c}' }
        }
      ]
    })
  }

  // Top 核心节点（横向条形，按节点标签配色）
  if (topBarEl.value) {
    topBarChart = topBarChart || echarts.init(topBarEl.value)
    const top = a.value?.top_nodes || []
    const yData = top.map((n) => n.name).reverse()
    const seriesData = top
      .map((n) => ({ name: n.name, value: n.degree, label: n.label }))
      .reverse()
    topBarChart.setOption({
      tooltip: {
        trigger: 'item',
        formatter: (p) => `${p.data.label} · ${p.data.name}<br/>关联节点数：${p.data.value}`
      },
      grid: { left: 130, right: 50, top: 10, bottom: 26 },
      xAxis: { type: 'value', minInterval: 1 },
      yAxis: {
        type: 'category',
        data: yData,
        axisLabel: { fontSize: 12, width: 120, overflow: 'truncate' }
      },
      series: [
        {
          type: 'bar',
          data: seriesData.map((d) => ({
            value: d.value,
            name: d.name,
            label: d.label,
            itemStyle: { color: labelColor(d.label, labels) }
          })),
          barMaxWidth: 22,
          label: { show: true, position: 'right' }
        }
      ]
    })
  }
}

function onResize() {
  labelBarChart?.resize()
  relPieChart?.resize()
  topBarChart?.resize()
}

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  labelBarChart?.dispose()
  relPieChart?.dispose()
  topBarChart?.dispose()
})

watch(() => app.currentDb, load)
</script>

<style scoped>
.chart-box {
  height: 300px;
}

.top-chart {
  height: 320px;
}
</style>
