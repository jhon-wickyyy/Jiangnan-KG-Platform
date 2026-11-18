<template>
  <span class="label-badge" :style="{ background: color }">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '../stores/app'
import { labelColor } from '../utils/graphStyle'

const props = defineProps({ label: { type: String, required: true } })
const app = useAppStore()
const color = computed(() => labelColor(props.label, app.schema?.labels || []))
</script>

<style scoped>
.label-badge {
  color: #fff;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  display: inline-block;
  white-space: nowrap;
}
</style>
