import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 30000 })

http.interceptors.response.use(
  (res) => res.data,
  (err) => Promise.reject(new Error(err.response?.data?.detail || err.message))
)

export const getHealth = () => http.get('/health')
export const getDatabases = (refresh = false) =>
  http.get('/databases', { params: refresh ? { refresh: true } : {} })
export const getOverview = () => http.get('/overview')
export const getSchema = () => http.get('/schema')
export const getEntities = (params) => http.get('/entities', { params })
export const getEntityDetail = (params) => http.get('/entities/detail', { params })
export const getGardenGraph = (db) => http.get('/graph/garden', { params: { db } })
export const getNeighbors = (params) => http.get('/graph/neighbors', { params })
export const expandNode = (params) => http.get('/graph/expand', { params })
export const getRoute = (db) => http.get('/route', { params: { db } })
export const getSpatialRelations = (params) => http.get('/spatial/relations', { params })
export const getNetworkAnalysis = (db) => http.get('/analysis/network', { params: { db } })
export const getPath = (params) => http.get('/path', { params })
