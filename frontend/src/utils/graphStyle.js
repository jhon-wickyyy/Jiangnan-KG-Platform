// 图谱样式：标签调色板与关系线型（按动态 Schema 顺序分配，无硬编码标签名）

export const CATEGORY_PALETTE = [
  '#8b1e1e', // 园林
  '#3b6ea5', // 建筑
  '#8a6d3b', // 山石
  '#2f8f83', // 池沼
  '#4e7a3a', // 花木
  '#7b5ea7',
  '#b05c86',
  '#c98a3d',
  '#5f9ea0',
  '#9c6b8f'
]

// 已知标签的语义配色（按名称匹配，保证 建筑=蓝 / 山石=棕 / 池沼=青 / 花木=绿）
const KNOWN_LABEL_COLORS = {
  园林: '#8b1e1e', // 深红
  建筑: '#3b6ea5', // 蓝
  山石: '#8a6d3b', // 棕
  池沼: '#2f8f83', // 青
  花木: '#4e7a3a' // 绿
}

// 已知空间语义关系类型的推荐线型（未知类型自动循环配色）
const KNOWN_LINE_STYLES = {
  属于: { color: '#909399', type: 'dashed' },
  相邻: { color: '#5b8ff9', type: 'solid' },
  相接: { color: '#e6a23c', type: 'dotted' }
}

export function labelColor(label, labels = []) {
  if (KNOWN_LABEL_COLORS[label]) return KNOWN_LABEL_COLORS[label]
  const i = labels.indexOf(label)
  return CATEGORY_PALETTE[(i >= 0 ? i : 0) % CATEGORY_PALETTE.length]
}

export function lineStyleFor(type, relTypes = []) {
  if (KNOWN_LINE_STYLES[type]) return { ...KNOWN_LINE_STYLES[type] }
  const i = relTypes.indexOf(type)
  return {
    color: CATEGORY_PALETTE[((i >= 0 ? i : 0) + 2) % CATEGORY_PALETTE.length],
    type: 'solid'
  }
}
