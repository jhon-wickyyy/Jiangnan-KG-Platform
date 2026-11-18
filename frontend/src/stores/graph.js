import { defineStore } from 'pinia'

export const useGraphStore = defineStore('graph', {
  state: () => ({
    nodes: {}, // id -> node（跨库稳定复合 ID 去重）
    links: {}, // id -> link
    selectedId: null,
    mode: 'spatial', // 'relation' 知识关系模式 | 'spatial' 空间布局模式（默认，真实 x/y 平面图）
    expandedIds: [], // 已执行过增量展开的节点
    loadedDb: '' // 已全量加载（空间布局模式数据）的库名
  }),

  getters: {
    nodeList: (s) => Object.values(s.nodes),
    linkList: (s) => Object.values(s.links),
    selectedNode: (s) => (s.selectedId ? s.nodes[s.selectedId] : null)
  },

  actions: {
    clear() {
      this.nodes = {}
      this.links = {}
      this.selectedId = null
      this.expandedIds = []
      this.loadedDb = ''
    },

    loadGraph({ nodes, links }) {
      for (const n of nodes || []) this.nodes[n.id] = n
      for (const l of links || []) this.links[l.id] = l
    },

    select(id) {
      this.selectedId = id
    },

    setMode(mode) {
      this.mode = mode
    },

    markExpanded(id) {
      if (!this.expandedIds.includes(id)) this.expandedIds.push(id)
    },

    markGardenLoaded(db) {
      this.loadedDb = db
    }
  }
})
