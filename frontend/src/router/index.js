import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/overview' },
  {
    path: '/overview',
    component: () => import('../views/OverviewView.vue'),
    meta: { title: '数据概览' }
  },
  {
    path: '/entities',
    component: () => import('../views/EntitiesView.vue'),
    meta: { title: '实体浏览' }
  },
  {
    path: '/search',
    component: () => import('../views/SearchView.vue'),
    meta: { title: '实体搜索' }
  },
  {
    path: '/graph',
    component: () => import('../views/GraphExploreView.vue'),
    meta: { title: '图谱探索' }
  },
  {
    path: '/route',
    component: () => import('../views/RouteView.vue'),
    meta: { title: '游线分析' }
  },
  {
    path: '/spatial',
    component: () => import('../views/SpatialRelationsView.vue'),
    meta: { title: '空间关系分析' }
  },
  {
    path: '/analysis',
    component: () => import('../views/AnalysisView.vue'),
    meta: { title: '知识网络分析' }
  },
  {
    path: '/path',
    component: () => import('../views/PathView.vue'),
    meta: { title: '路径查询' }
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
