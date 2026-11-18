<template>
  <el-container class="app">
    <el-header class="app-header" height="56px">
      <div class="app-title">🏞 江南古典园林空间知识图谱可视化平台</div>
      <div class="app-garden">
        <span class="garden-label">当前园林：</span>
        <el-select
          v-model="app.currentDb"
          placeholder="暂无可用数据库"
          size="small"
          style="width: 170px"
          @change="onDbChange"
        >
          <el-option v-for="d in app.databases" :key="d.name" :label="d.garden" :value="d.name" />
        </el-select>
        <el-button
          size="small"
          text
          title="重新扫描园林列表（新库加载后使用）"
          :loading="app.loading"
          style="color: #fff; margin-left: 4px"
          @click="rescan"
        >
          ⟳
        </el-button>
      </div>
    </el-header>
    <el-container class="app-body">
      <el-aside width="170px" class="app-aside">
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/graph">图谱探索</el-menu-item>
          <el-menu-item index="/route">游线分析</el-menu-item>
          <el-menu-item index="/spatial">空间关系分析</el-menu-item>
          <el-menu-item index="/analysis">知识网络分析</el-menu-item>
          <el-menu-item index="/path">路径查询</el-menu-item>
          <el-menu-item index="/overview">数据概览</el-menu-item>
          <el-menu-item index="/entities">实体浏览</el-menu-item>
          <el-menu-item index="/search">实体搜索</el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from './stores/app'

const app = useAppStore()

onMounted(() => {
  app.init().catch((e) => ElMessage.error('平台初始化失败：' + e.message))
})

function onDbChange() {
  ElMessage.success(`已切换园林：${app.gardenName}`)
}

async function rescan() {
  try {
    const n = await app.rescan()
    ElMessage.success(`园林列表已刷新：共 ${n} 个园林库`)
  } catch (e) {
    ElMessage.error('重新扫描失败：' + e.message)
  }
}
</script>

<style scoped>
.app {
  height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #2f4b3c;
  color: #fff;
}

.app-title {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 1px;
}

.garden-label {
  font-size: 13px;
  opacity: 0.85;
}

.app-aside {
  background: #fff;
  border-right: 1px solid #e4e7ed;
}

.app-body {
  min-height: 0; /* 防止内容把 flex 高度链撑破视口（min-height:auto 是默认下限） */
}

.app-main {
  padding: 14px;
  overflow: hidden;
  min-height: 0;
}
</style>
