<template>
  <div class="page">
    <div class="page-header">
      <span class="page-title">实体搜索</span>
    </div>

    <el-card shadow="never">
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="输入实体名称或关键词，如：面水轩 / 亭 / 临水"
          clearable
          style="width: 380px"
          @keyup.enter="search"
        >
          <template #append>
            <el-button type="primary" :loading="loading" @click="search">搜索</el-button>
          </template>
        </el-input>
        <el-select v-model="filterLabel" placeholder="全部标签" clearable size="default" style="width: 150px">
          <el-option v-for="l in labels" :key="l" :label="l" :value="l" />
        </el-select>
        <el-select v-model="filterDb" placeholder="全部园林" clearable size="default" style="width: 150px">
          <el-option v-for="d in app.databases" :key="d.name" :label="d.garden" :value="d.name" />
        </el-select>
        <el-checkbox v-model="exactHint" disabled style="margin-left: 8px">精确匹配优先</el-checkbox>
      </div>

      <el-table v-loading="loading" :data="results" size="small" style="margin-top: 12px" @row-click="openDetail">
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column label="标签" width="100">
          <template #default="{ row }">
            <LabelBadge :label="row.label" />
          </template>
        </el-table-column>
        <el-table-column label="所属园林" min-width="130">
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
        <template #empty>
          <el-empty v-if="!loading && searched" description="未找到匹配实体" :image-size="60" />
          <div v-else>输入关键词开始搜索</div>
        </template>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 12px; justify-content: flex-end"
        @current-change="search"
      />
    </el-card>

    <el-drawer v-model="detailVisible" title="实体详情" size="440px">
      <NodeDetailPanel v-if="detailVisible" :node-id="detailId" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getEntities } from '../api'
import { useAppStore } from '../stores/app'
import LabelBadge from '../components/LabelBadge.vue'
import NodeDetailPanel from '../components/NodeDetailPanel.vue'

const router = useRouter()
const app = useAppStore()

const keyword = ref('')
const filterLabel = ref('')
const filterDb = ref(app.currentDb || '') // 空 = 全部园林；默认跟随当前园林
const page = ref(1)
const pageSize = 20
const total = ref(0)
const results = ref([])
const loading = ref(false)
const searched = ref(false)
const detailVisible = ref(false)
const detailId = ref('')

const labels = computed(() => app.schema?.labels || [])

async function search() {
  if (!keyword.value) return
  loading.value = true
  try {
    const params = { q: keyword.value, page: page.value, page_size: pageSize, db: filterDb.value || undefined }
    if (filterLabel.value) params.label = filterLabel.value
    const r = (await getEntities(params)).data
    results.value = r.items
    total.value = r.total
    searched.value = true
  } finally {
    loading.value = false
  }
}

function openDetail(row) {
  detailId.value = row.id
  detailVisible.value = true
}

function jumpToGraph(row) {
  router.push({ path: '/graph', query: { focus: row.id } })
}

// 园林切换：若搜索园林跟随当前园林（未被手动覆盖），则同步切换并重搜
watch(
  () => app.currentDb,
  (nv, ov) => {
    if (filterDb.value === ov || (!filterDb.value && ov)) filterDb.value = nv || ''
    if (searched.value) search()
  }
)
</script>

<style scoped>
.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
