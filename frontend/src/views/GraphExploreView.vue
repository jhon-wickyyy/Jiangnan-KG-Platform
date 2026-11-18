<template>
  <div class="graph-page">
    <div class="graph-toolbar">
      <el-radio-group v-model="store.mode" size="small">
        <el-radio-button value="spatial">空间布局模式</el-radio-button>
        <el-radio-button value="relation">知识关系模式</el-radio-button>
      </el-radio-group>

      <el-button size="small" :loading="loading" @click="loadGarden">重新加载</el-button>

      <el-switch v-model="mergePairs" active-text="合并双向边" size="small" />

      <el-select
        v-model="hiddenRelTypes"
        multiple
        collapse-tags
        clearable
        placeholder="隐藏关系类型"
        size="small"
        style="width: 200px"
      >
        <el-option v-for="t in relTypes" :key="t" :label="t" :value="t" />
      </el-select>

      <el-select
        v-model="adjacencyFilter"
        clearable
        placeholder="相邻类型筛选"
        size="small"
        style="width: 170px"
      >
        <el-option v-for="v in adjacencyValues" :key="v" :label="v" :value="v" />
      </el-select>
    </div>

    <div v-loading="loading" class="graph-canvas-wrap">
      <GraphCanvas
        :merge-pairs="mergePairs"
        :hidden-rel-types="hiddenRelTypes"
        :adjacency-filter="adjacencyFilter"
        @node-click="onNodeClick"
        @node-dblclick="onNodeDblclick"
      />
      <div class="graph-hint">
        {{ store.mode === 'spatial'
          ? '空间布局模式：按节点 x/y 测绘坐标还原园林平面图（无坐标节点置于质心）'
          : '知识关系模式：双击节点展开关联 · 单击查看详情 · 拖拽调整布局' }}
      </div>
    </div>

    <el-drawer v-model="detailVisible" title="节点详情" size="440px">
      <NodeDetailPanel
        v-if="detailVisible && store.selectedId"
        :node-id="store.selectedId"
        @expand="expandSelected"
      />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getGardenGraph, getNeighbors, expandNode } from '../api'
import { useAppStore } from '../stores/app'
import { useGraphStore } from '../stores/graph'
import GraphCanvas from '../components/GraphCanvas.vue'
import NodeDetailPanel from '../components/NodeDetailPanel.vue'

const route = useRoute()
const router = useRouter()
const app = useAppStore()
const store = useGraphStore()

const loading = ref(false)
const mergePairs = ref(false)
const hiddenRelTypes = ref([])
const adjacencyFilter = ref('')
const detailVisible = ref(false)

const relTypes = computed(() =>
  app.schema?.rel_types?.length
    ? app.schema.rel_types
    : [...new Set(store.linkList.map((l) => l.type))]
)

// 相邻类型筛选选项：取自当前已加载链接中的 `相邻类型` 值（动态，无硬编码）
const adjacencyValues = computed(() => {
  const s = new Set()
  for (const l of store.linkList) {
    const v = l.props?.['相邻类型']
    if (v) s.add(String(v))
  }
  return [...s].sort()
})

// ---------- 数据加载 ----------

async function loadGarden() {
  if (!app.currentDb) return
  loading.value = true
  try {
    store.clear()
    const r = (await getGardenGraph(app.currentDb)).data
    store.loadGraph(r)
    store.markGardenLoaded(app.currentDb)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function expandById(id) {
  if (!id || store.expandedIds.includes(id)) return
  const [db, label, bid] = id.split('::')
  try {
    const r = (await expandNode({ db, label, id: bid })).data
    store.loadGraph(r)
    store.markExpanded(id)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

// ---------- 交互 ----------

function onNodeClick(id) {
  store.select(id)
  detailVisible.value = true
}

function onNodeDblclick(id) {
  expandById(id)
}

function expandSelected() {
  expandById(store.selectedId)
}

// ---------- 初始加载与切换 ----------

let focusing = false

async function focusNode(idStr) {
  const [db, label, bid] = idStr.split('::')
  if (!db || !label || !bid) return
  router.replace({ query: {} }) // 消费 focus 参数，防止 watcher 重复触发
  loading.value = true
  try {
    if (app.currentDb !== db) app.currentDb = db // 触发 watcher，但 focusing 标志跳过全量加载
    store.clear()
    const r = (await getNeighbors({ db, label, id: bid, depth: 1 })).data
    store.loadGraph(r)
    store.select(idStr)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

watch(
  [() => app.currentDb, () => route.query.focus],
  async ([db, focus]) => {
    if (!db) return
    if (focus) {
      focusing = true
      try {
        await focusNode(String(focus))
      } finally {
        focusing = false
      }
      return
    }
    if (focusing) return
    if (store.loadedDb !== db || store.nodeList.length === 0) await loadGarden()
  },
  { immediate: true }
)

// 空间布局模式需要全园数据；关系模式无数据时同样加载全园
watch(
  () => store.mode,
  async (m) => {
    if (!app.currentDb || focusing) return
    if (m === 'spatial' && store.loadedDb !== app.currentDb) await loadGarden()
    else if (m === 'relation' && store.nodeList.length === 0) await loadGarden()
  }
)
</script>
