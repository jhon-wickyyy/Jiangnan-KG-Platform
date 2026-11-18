<template>
  <div v-loading="loading" class="node-detail">
    <template v-if="detail">
      <!-- 节点信息头 -->
      <div class="detail-head">
        <div class="detail-name">{{ detail.node.name }}</div>
        <div class="detail-tags">
          <LabelBadge :label="detail.node.label" />
          <span class="detail-db">{{ gardenName }}</span>
          <el-tag v-if="tourSeq != null" size="small" type="warning" effect="plain">
            游线第 {{ tourSeq }} 站
          </el-tag>
        </div>
      </div>

      <!-- 基础信息 -->
      <el-divider content-position="left">基础信息</el-divider>
      <el-descriptions :column="1" size="small" border>
        <el-descriptions-item label="名称">{{ detail.node.name }}</el-descriptions-item>
        <el-descriptions-item label="标签">{{ detail.node.label }}</el-descriptions-item>
        <el-descriptions-item label="编号">{{ bid }}</el-descriptions-item>
        <el-descriptions-item label="所属园林">{{ gardenName }}</el-descriptions-item>
      </el-descriptions>

      <!-- 空间位置（数据驱动：存在空间键才显示，兼容缺坐标的园林） -->
      <template v-if="hasSpatial">
        <el-divider content-position="left">空间位置</el-divider>
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item v-if="hasXY" label="平面坐标">
            x = {{ nodeProps.x }} m · y = {{ nodeProps.y }} m
          </el-descriptions-item>
          <el-descriptions-item v-if="hasPolar" label="极坐标">
            极径 {{ nodeProps['极径_m'] }} m · 极角 {{ nodeProps['极角_度'] }}°
          </el-descriptions-item>
        </el-descriptions>
      </template>

      <!-- 全部属性（动态键，无字段假设） -->
      <el-divider content-position="left">全部属性</el-divider>
      <el-descriptions :column="1" size="small" border>
        <el-descriptions-item v-for="[k, v] in sortedProps" :key="k" :label="k">
          {{ formatValue(v) }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 关联节点（按关系类型分组，含空间语义徽标） -->
      <el-divider content-position="left">关联节点（{{ detail.neighbors.length }}）</el-divider>
      <el-collapse v-model="openGroups">
        <el-collapse-item v-for="g in groups" :key="g.rel" :name="g.rel">
          <template #title>
            <b>{{ g.rel }}</b>
            <span class="group-count">（{{ g.list.length }}）</span>
          </template>
          <div v-for="nb in g.list" :key="nb.node.id" class="neighbor-item" @click="onPick(nb.node.id)">
            <span class="dir-arrow">{{ nb.direction === 'out' ? '→' : '←' }}</span>
            <span class="neighbor-name">{{ nb.node.name }}</span>
            <LabelBadge :label="nb.node.label" />
            <span v-for="b in relBadges(nb.rel_props)" :key="b" class="rel-badge">{{ b }}</span>
            <el-tag
              v-if="nb.rel_props?.['环线序号'] != null"
              size="small"
              type="warning"
              effect="plain"
            >
              游线第 {{ nb.rel_props['环线序号'] }} 站
            </el-tag>
          </div>
        </el-collapse-item>
      </el-collapse>

      <div class="detail-actions">
        <el-button size="small" type="primary" plain @click="$emit('expand')">展开关联</el-button>
      </div>
    </template>
    <el-empty v-else-if="!loading" description="暂无详情" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getEntityDetail } from '../api'
import { useAppStore } from '../stores/app'
import { useGraphStore } from '../stores/graph'
import LabelBadge from './LabelBadge.vue'

const props = defineProps({ nodeId: { type: String, default: '' } })
defineEmits(['expand'])

const app = useAppStore()
const store = useGraphStore()
const loading = ref(false)
const detail = ref(null)
const openGroups = ref([])

const PREF_KEYS = ['编号', '名称', '代号', '类型', '品种', '平面形式', '屋顶形式', '形式', '材质', '功能', '时期', '位置']
const REL_BADGE_KEYS = ['相邻类型', '接触类型', '中介', '方向', '距离_m']

const nodeProps = computed(() => detail.value?.node?.props || {})
const bid = computed(() => detail.value?.node?.props?.['编号'] ?? '—')
const gardenName = computed(() => app.gardenOfDb(detail.value?.node?.db))

// ---------- 空间位置（数据驱动） ----------

const hasXY = computed(
  () => typeof nodeProps.value.x === 'number' && typeof nodeProps.value.y === 'number'
)
const hasPolar = computed(
  () => nodeProps.value['极径_m'] != null || nodeProps.value['极角_度'] != null
)
const hasSpatial = computed(() => hasXY.value || hasPolar.value)

// ---------- 游线序号（数据驱动：关系带 环线序号 即游线边） ----------

const tourSeq = computed(() => {
  const nbs = detail.value?.neighbors || []
  // 出站环线边 → 本站游览序号
  for (const nb of nbs) {
    if (nb.direction === 'out' && nb.rel_props?.['环线序号'] != null) {
      return nb.rel_props['环线序号']
    }
  }
  // 仅入站环线边 → 环线末端站（入站序号 + 1）
  let lastIn = null
  for (const nb of nbs) {
    if (nb.rel_props?.['环线序号'] != null) lastIn = nb.rel_props['环线序号']
  }
  return lastIn != null ? lastIn + 1 : null
})

// ---------- 属性与关联 ----------

const sortedProps = computed(() => {
  const entries = Object.entries(nodeProps.value)
  entries.sort((a, b) => {
    const ia = PREF_KEYS.indexOf(a[0])
    const ib = PREF_KEYS.indexOf(b[0])
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
  })
  return entries
})

const groups = computed(() => {
  const m = new Map()
  for (const nb of detail.value?.neighbors || []) {
    if (!m.has(nb.rel)) m.set(nb.rel, [])
    m.get(nb.rel).push(nb)
  }
  return [...m.entries()].map(([rel, list]) => ({ rel, list }))
})

function formatValue(v) {
  if (v === null || v === undefined) return '—'
  return String(v)
}

function relBadges(relProps) {
  return REL_BADGE_KEYS.filter((k) => relProps?.[k] !== undefined && relProps?.[k] !== null).map(
    (k) => (k === '距离_m' ? `${relProps[k]} m` : `${k}·${relProps[k]}`)
  )
}

function onPick(id) {
  store.select(id)
}

async function fetchDetail() {
  if (!props.nodeId) return
  const [db, label, bidStr] = props.nodeId.split('::')
  loading.value = true
  try {
    detail.value = (await getEntityDetail({ db, label, id: bidStr })).data
    openGroups.value = groups.value.map((g) => g.rel)
  } catch (e) {
    detail.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.nodeId, fetchDetail, { immediate: true })
</script>

<style scoped>
.detail-head {
  margin-bottom: 6px;
}

.detail-name {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.detail-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  flex-wrap: wrap;
}

.detail-db {
  color: #909399;
  font-size: 12px;
}

.group-count {
  color: #909399;
  font-size: 12px;
  margin-left: 4px;
}

.dir-arrow {
  color: #e6a23c;
  font-weight: 700;
}

.detail-actions {
  margin-top: 12px;
  text-align: center;
}
</style>
