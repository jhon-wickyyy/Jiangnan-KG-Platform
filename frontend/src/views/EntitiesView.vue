<template>
  <div class="page">
    <div class="page-header">
      <span class="page-title">实体浏览</span>
      <el-button size="small" type="primary" plain @click="$router.push('/search')">前往搜索</el-button>
    </div>

    <el-tabs v-model="activeLabel" @tab-change="onFilterChange">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane v-for="l in labels" :key="l" :label="`${l}（${countOf(l)}）`" :name="l" />
    </el-tabs>

    <el-table v-loading="loading" :data="items" size="small" @row-click="openDetail">
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column label="标签" width="100">
        <template #default="{ row }">
          <LabelBadge :label="row.label" />
        </template>
      </el-table-column>
      <el-table-column label="所属园林" min-width="120">
        <template #default="{ row }">{{ app.gardenOfDb(row.db) }}</template>
      </el-table-column>
      <el-table-column prop="degree" label="关联节点数" width="110" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click.stop="jumpToGraph(row)">
            在图谱中查看
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      style="margin-top: 12px; justify-content: flex-end"
      @current-change="load"
    />

    <el-drawer v-model="detailVisible" title="实体详情" size="440px">
      <NodeDetailPanel v-if="detailVisible" :node-id="detailId" @expand="expandDetail" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getEntities, expandNode, getNetworkAnalysis } from '../api'
import { useAppStore } from '../stores/app'
import { useGraphStore } from '../stores/graph'
import LabelBadge from '../components/LabelBadge.vue'
import NodeDetailPanel from '../components/NodeDetailPanel.vue'

const router = useRouter()
const app = useAppStore()
const store = useGraphStore()

const activeLabel = ref('')
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const detailVisible = ref(false)
const detailId = ref('')

const labels = computed(() => app.schema?.labels || [])
const labelCounts = ref({})

function countOf(l) {
  return labelCounts.value[l] ?? '…'
}

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize, db: app.currentDb || undefined }
    if (activeLabel.value) params.label = activeLabel.value
    const r = (await getEntities(params)).data
    items.value = r.items
    total.value = r.total
  } finally {
    loading.value = false
  }
}

// 标签计数按当前园林口径（/api/analysis/network 的 by_label），与表格数据一致
async function loadLabelCounts() {
  if (!app.currentDb) {
    labelCounts.value = {}
    return
  }
  try {
    const a = (await getNetworkAnalysis(app.currentDb)).data
    labelCounts.value = {}
    for (const x of a.by_label) labelCounts.value[x.label] = x.count
  } catch {
    /* 忽略 */
  }
}

function onFilterChange() {
  page.value = 1
  load()
}

function openDetail(row) {
  detailId.value = row.id
  detailVisible.value = true
}

function jumpToGraph(row) {
  router.push({ path: '/graph', query: { focus: row.id } })
}

async function expandDetail() {
  const id = detailId.value
  const [db, label, bid] = id.split('::')
  try {
    const r = (await expandNode({ db, label, id: bid })).data
    store.loadGraph(r)
    store.markExpanded(id)
    ElMessage.success('已展开关联')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

watch(
  () => app.currentDb,
  () => {
    page.value = 1
    load()
    loadLabelCounts()
  }
)

load()
loadLabelCounts()
</script>
