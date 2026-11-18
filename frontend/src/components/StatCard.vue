<template>
  <el-card shadow="hover" class="stat-card">
    <div class="stat-value" :style="{ color }">{{ value }}</div>
    <div class="stat-title">{{ title }}</div>
  </el-card>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  value: { type: [String, Number], required: true },
  color: { type: String, default: '#3b6ea5' }
})
</script>

<style scoped>
.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-title {
  color: #909399;
  font-size: 13px;
  margin-top: 4px;
}
</style>
