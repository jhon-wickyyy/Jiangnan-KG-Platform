import { defineStore } from 'pinia'
import { getDatabases, getSchema } from '../api'

export const useAppStore = defineStore('app', {
  state: () => ({
    databases: [], // 业务库列表 [{name, garden, nodes, rels}]
    currentDb: '', // 当前园林（库名）
    schema: null, // 动态 Schema {labels, rel_types, label_props, rel_props}
    loading: false
  }),

  getters: {
    gardenName: (s) => {
      const d = s.databases.find((x) => x.name === s.currentDb)
      return d?.garden || s.currentDb || '未连接'
    },
    gardenOfDb: (s) => (name) => {
      const d = s.databases.find((x) => x.name === name)
      return d?.garden || name
    }
  },

  actions: {
    async init() {
      this.loading = true
      try {
        const dbs = (await getDatabases()).data
        this.databases = dbs
        if (!this.currentDb || !dbs.find((x) => x.name === this.currentDb)) {
          this.currentDb = dbs[0]?.name || ''
        }
        await this.loadSchema()
      } finally {
        this.loading = false
      }
    },

    // 强制重扫业务库（新园林 dump 加载后使用）
    async rescan() {
      this.loading = true
      try {
        const dbs = (await getDatabases(true)).data
        this.databases = dbs
        if (!this.currentDb || !dbs.find((x) => x.name === this.currentDb)) {
          this.currentDb = dbs[0]?.name || ''
        }
        await this.loadSchema()
        return dbs.length
      } finally {
        this.loading = false
      }
    },

    async loadSchema() {
      this.schema = (await getSchema()).data
    },

    setDb(name) {
      this.currentDb = name
    }
  }
})
