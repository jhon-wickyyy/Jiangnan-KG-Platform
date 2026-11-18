# API 设计文档（FastAPI 后端）

> 版本：v2.0（2026-10-11）
> 依据：`database/schema.md`（实连 Neo4j 分析结果）与 `docs/platform_design.md` v2.1
> 原则：**接口严格基于当前 Neo4j Schema**——不假设任何标签、关系类型或属性字段；示例数据均为对 `canglangting` 库的真实查询结果。
> 状态标记：✅ 已实现并实测 · 🚧 本阶段开发 · 🔮 预留（三期实现）

---

## 0. 设计总则

### 0.1 基础信息

| 项目 | 值 |
|---|---|
| Base URL | `http://127.0.0.1:8000/api` |
| 格式 | HTTP REST + JSON（UTF-8） |
| 凭证 | 仅存在于后端 `.env`（NEO4J_URI/USER/PASSWORD），前端永不接触 |

### 0.2 响应封装与错误码

- 成功：`{ "data": <业务数据> }`；失败：`{ "detail": "<错误信息>" }`
- 错误码：400（参数非法/标签或关系类型不存在/实体不存在）· 502（Cypher 执行失败）· 503（Neo4j 连接失败）

### 0.3 稳定 ID 与 graph JSON 公共结构（关系图谱/空间接口共用）

```
节点稳定 ID = {db}::{label}::{编号}      例: "canglangting::建筑::建筑5-1"
关系稳定 ID = {db}::{elementId(r)}
名称回退链   = 名称 → 编号 → 标签名（不假设属性存在）
```

```json
{
  "nodes": [
    {
      "id": "canglangting::建筑::建筑5-1",
      "db": "canglangting",
      "label": "建筑",
      "name": "面水轩",
      "props": { "编号": "建筑5-1", "类型": "轩", "功能": "…",
                 "x": -25.2, "y": -5.3, "极径_m": 25.8, "极角_度": 192 },
      "degree": 5
    }
  ],
  "links": [
    {
      "id": "canglangting::5:1060ebb9-…:1152…",
      "source": "canglangting::建筑::建筑5-1",
      "target": "canglangting::池沼::池沼2-3",
      "type": "相邻",
      "props": { "相邻类型": "可看", "中介": "水面", "方向": "西偏南", "距离_m": 32.5 }
    }
  ]
}
```

要点：
- `props` **原样透传全部属性**（含空间坐标 `x`/`y`/`极径_m`/`极角_度` 与空间语义 `相邻类型`/`中介`/`方向`/`距离_m`/`接触类型`），前端按需取用；
- 关系保留方向（source→target）；`相邻`/`相接` 为对称双写边，前端提供"合并双向边"开关；
- 该结构可直接转换为 **ECharts graph/series-graph** 的 `nodes`/`links` 数据格式。

### 0.4 多数据库切换约定

- 一园一库：每个园林对应 Neo4j 上一个独立数据库（当前仅 `canglangting`）。
- 库作用域接口（节点详情、关系图谱、空间布局、空间关系、游线、路径）**必须携带 `db` 参数**；统计与 Schema 接口（不带 db 时）自动跨库聚合，结果携带 `db` 字段。
- 可用库列表由 `GET /api/databases` 动态枚举（排除 `system` 与空库）；新园林 dump 加载后 `?refresh=true` 重扫即生效，前端"园林切换器"选项即来自该接口。

### 0.5 查询安全

1. 用户输入一律 Cypher 参数化（`$param`）；
2. 动态标签/关系类型仅允许取自 `CALL db.labels()` / `db.relationshipTypes()` 返回值（白名单校验），并以反引号包裹；
3. 全库只读（仅 MATCH）；LLM 生成的 Cypher 另经只读白名单 + 行数限制（见 §9）；
4. 本版 Neo4j（2026.09，Cypher 25）不支持参数化变长界 `[*1..$depth]`，跳数参数在服务端白名单化为整数后内联。

---

## 1. 数据库管理接口

### 1.1 获取可用园林数据库列表 ✅

- **URL**：`GET /api/databases`
- **请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `refresh` | bool | 否 | `true` 强制重扫（新园林 dump 加载后使用） |

- **返回格式**：

```json
{
  "data": [
    { "name": "canglangting", "garden": "沧浪亭", "nodes": 29, "rels": 76 }
  ]
}
```

- **Cypher 查询逻辑**：
  1. `SHOW DATABASES`（system 库）过滤出 online 的 standard 库，排除配置忽略库；
  2. 每库统计：`MATCH (n) WHERE NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom') RETURN count(n)`、`MATCH ()-[r]->() RETURN count(r)`；节点数为 0 的空库剔除；
  3. 园林名解析：优先 `MATCH (n:`园林`) RETURN properties(n) LIMIT 1` 取 `编号`/`名称`，回退节点数最少标签上的单节点，再回退库名。

- **多库切换**：前端切换园林 = 调用本接口刷新选项 + 后续所有库作用域请求携带新的 `db` 参数。

### 1.2 后端与 Neo4j 连通检查 ✅

- **URL**：`GET /api/health`
- **请求参数**：无
- **返回格式**：`{ "data": { "status": "ok", "neo4j": "connected", "business_databases": 1 } }`；失败 503。

---

## 2. Schema 接口

### 2.1 获取节点类型与关系类型 ✅

- **URL**：`GET /api/schema`
- **请求参数**：无
- **返回格式**（真实数据，跨库并集）：

```json
{
  "data": {
    "labels": ["园林", "山石", "建筑", "池沼", "花木"],
    "rel_types": ["属于", "相接", "相邻"],
    "label_props": {
      "建筑": ["x", "y", "功能", "名称", "屋顶形式", "平面形式", "极径_m", "极角_度", "类型", "编号"],
      "山石": ["x", "y", "名称", "材质", "极径_m", "极角_度", "类型", "编号"],
      "池沼": ["x", "y", "名称", "平面形式", "形式", "极径_m", "极角_度", "类型", "编号"],
      "花木": ["x", "y", "名称", "品种", "极径_m", "极角_度", "类型", "编号"],
      "园林": ["代号", "位置", "时期", "编号"]
    },
    "rel_props": {
      "属于": ["关系"],
      "相邻": ["中介", "方向", "极角_度", "环线序号", "相邻类型", "空间关系", "距离_m"],
      "相接": ["接触类型", "方向", "极角_度", "空间关系", "距离_m"]
    }
  }
}
```

- **Cypher 查询逻辑**（逐业务库执行后合并）：
  - 节点类型：`CALL db.labels() YIELD label`（过滤 `_Bloom*` 内部标签）
  - 关系类型：`CALL db.relationshipTypes() YIELD relationshipType`
  - 属性键：`MATCH (n:`建筑`) UNWIND keys(n) AS k RETURN DISTINCT k`、`MATCH ()-[r:`相邻`]->() UNWIND keys(r) AS k RETURN DISTINCT k`
- 前端图例、配色、详情面板、筛选器全部依据本接口动态渲染；某键在个别库缺失时按"属性存在才渲染"处理。

---

## 3. 数据统计接口

### 3.1 获取节点/关系数量与分类统计 ✅

- **URL**：`GET /api/overview`
- **请求参数**：无
- **返回格式**（真实数据）：

```json
{
  "data": {
    "total_nodes": 29,
    "total_rels": 76,
    "databases": [{ "name": "canglangting", "garden": "沧浪亭", "nodes": 29, "rels": 76 }],
    "by_label": [
      { "label": "建筑", "count": 14 },
      { "label": "花木", "count": 8 },
      { "label": "山石", "count": 3 },
      { "label": "池沼", "count": 3 },
      { "label": "园林", "count": 1 }
    ],
    "by_rel_type": [
      { "type": "相邻", "count": 34 },
      { "type": "属于", "count": 28 },
      { "type": "相接", "count": 14 }
    ]
  }
}
```

- **Cypher 查询逻辑**（跨库聚合）：
  - 节点总数/关系总数：`MATCH (n) WHERE NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom') RETURN count(n)`、`MATCH ()-[r]->() RETURN count(r)`
  - 分类统计：`MATCH (n) WHERE … UNWIND labels(n) AS l RETURN l AS label, count(*) AS c`、`MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS c`

> 扩展统计（核心节点/各园林构成/空间语义分布）见 §8 附注与 `docs/platform_design.md` 二期计划，属本组接口的扩展，另行设计。

---

## 4. 节点查询接口

### 4.1 查询节点列表 / 按名称搜索节点 ✅

- **URL**：`GET /api/entities`
- **请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `db` | string | 否 | 限定园林库，缺省跨库 |
| `label` | string | 否 | 限定标签（白名单校验；该库无此标签则跳过） |
| `q` | string | 否 | 关键词：**全属性模糊匹配**，**名称/编号精确命中自动置顶** |
| `page` | int | 否 | 页码 ≥1，默认 1 |
| `page_size` | int | 否 | 每页 1–200，默认 20 |

- **返回格式**（`GET /api/entities?q=面水轩` 真实结果）：

```json
{
  "data": {
    "total": 1, "page": 1, "page_size": 20,
    "items": [
      {
        "id": "canglangting::建筑::建筑5-1",
        "db": "canglangting",
        "label": "建筑",
        "name": "面水轩",
        "props": { "编号": "建筑5-1", "类型": "轩", "平面形式": "临水轩", "屋顶形式": "硬山顶",
                   "功能": "面向园南水面，形成临水观景节点", "x": -25.2, "y": -5.3, "极径_m": 25.8, "极角_度": 192 },
        "degree": 5
      }
    ]
  }
}
```

- **Cypher 查询逻辑**（`label` 缺省时匹配全部业务标签；`q` 缺省时省略搜索条件）：

```cypher
MATCH (n:`建筑`)
WHERE NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom')
  AND any(k IN keys(n) WHERE n[k] IS NOT NULL AND toString(n[k]) CONTAINS $q)
WITH n
OPTIONAL MATCH (n)-[r]-(m)
RETURN n, count(DISTINCT m) AS degree      -- degree=去重邻居数（对称双写边已合并）
ORDER BY CASE WHEN any(k IN keys(n) WHERE toString(n[k]) = $q) THEN 0 ELSE 1 END, n.编号
```

### 4.2 查询节点详细信息 ✅

- **URL**：`GET /api/entities/detail`
- **请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `db` | string | ✅ | 数据库名 |
| `label` | string | ✅ | 标签（白名单校验） |
| `id` | string | ✅ | 实体编号（`编号` 属性值） |

- **返回格式**（`db=canglangting&label=建筑&id=建筑5-1` 真实结果节选）：

```json
{
  "data": {
    "node": { "id": "canglangting::建筑::建筑5-1", "db": "canglangting", "label": "建筑",
              "name": "面水轩", "props": { "编号": "建筑5-1", "类型": "轩", "x": -25.2, "y": -5.3, "…": "…" } },
    "neighbors": [
      { "rel": "属于", "direction": "out", "rel_props": { "关系": "园内" },
        "node": { "id": "canglangting::园林::沧浪亭", "label": "园林", "name": "沧浪亭", "props": { "…": "…" } } },
      { "rel": "相接", "direction": "in", "rel_props": { "接触类型": "临水", "方向": "北偏东", "距离_m": 23.2 },
        "node": { "id": "canglangting::池沼::池沼2-1", "label": "池沼", "name": "园南沧浪水", "props": { "…": "…" } } }
    ]
  }
}
```

- **Cypher 查询逻辑**（`direction` 按 `startNode(r).elementId` 与中心节点比对判定；结果按 关系类型→方向→名称 排序）：

```cypher
MATCH (n:`建筑` {编号: $bid}) RETURN n
MATCH (n:`建筑` {编号: $bid})-[r]-(m) RETURN n, r, m
```

---

## 5. 关系图谱接口

### 5.1 获取一跳关系 / 多跳关系（中心邻域子图） ✅

- **URL**：`GET /api/graph/neighbors`
- **请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `db` | string | ✅ | 数据库名 |
| `root` | bool | 否 | `true`：中心=园林根节点（动态解析：优先 `园林` 标签，回退节点数最少标签） |
| `label` | string | 条件必填 | root=false 时必填（白名单校验） |
| `id` | string | 条件必填 | root=false 时必填（中心节点编号） |
| `depth` | int | 否 | 跳数 1–3，默认 1（服务端白名单化内联） |

- **返回格式**：`{ "center": {节点}, "nodes": [...], "links": [...] }`（graph JSON 公共结构，§0.3）。真实规模：`root=true, depth=1` → 29 节点（因全部要素经 `属于` 直连根节点，一跳即全园）/ 28 边；`山石2-1, depth=2` → 29 节点 / 43 边。
- **Cypher 查询逻辑**（变长路径一次取出，服务端按稳定 ID 去重）：

```cypher
MATCH path = (n:`山石` {编号: $bid})-[*1..2]-(m)
RETURN path
```

### 5.2 获取一跳关系（增量展开） ✅

- **URL**：`GET /api/graph/expand`
- **请求参数**：`db` ✅ · `label` ✅（白名单校验）· `id` ✅
- **返回格式**：`{ "nodes": [...], "links": [...] }`（不含中心节点本身；前端按稳定 ID 去重合并进画布）。真实规模：`建筑5-1` → 5 节点 / 7 边。
- **Cypher 查询逻辑**：

```cypher
MATCH (n:`建筑` {编号: $bid})-[r]-(m)
RETURN r, n, m
```

### 5.3 多跳关系路径查询（两点最短路径，扩展） ✅

- **URL**：`GET /api/path`
- **请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `db` | string | ✅ | 数据库名 |
| `source_label` / `source_id` | string | ✅ | 起点（标签+编号） |
| `target_label` / `target_id` | string | ✅ | 终点 |
| `rel_types` | string | 否 | 限定关系类型（逗号分隔，白名单校验），如 `相邻,相接`；缺省不限类型 |
| `max_depth` | int | 否 | 最大跳数 1–6，默认 6 |

- **返回格式**（`山石2-1 → 建筑5-1`，rel_types=相接,相邻，真实结果）：

```json
{
  "data": {
    "description": "沧浪亭假山 →相接(在山上·9.6m)→ 沧浪亭 →相邻(可看·63.9m)→ 园南沧浪水 →相接(临水·23.2m)→ 面水轩",
    "length": 3,
    "nodes": [ /* 4 个节点（graph JSON 结构） */ ],
    "links": [ /* 3 条边（含类型与空间语义 props） */ ]
  }
}
```

- **Cypher 查询逻辑**（rel_types 缺省时 `-[*1..6]-`）：

```cypher
MATCH path = shortestPath(
  (a:`山石` {编号: $sid})-[:`相接`|`相邻`*1..6]-(b:`建筑` {编号: $tid}))
RETURN path
```

---

## 6. 空间布局接口（重点） ✅

**用途**：返回园林空间布局数据——利用数据库中的 `x` 坐标、`y` 坐标、`极径_m`、`极角_度`，供前端 ECharts 散点图 / 关系图渲染园林平面图。

### 6.1 获取园林空间布局数据

- **URL**：`GET /api/graph/garden`
- **请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `db` | string | ✅ | 数据库名（园林） |

- **返回格式**（graph JSON 公共结构，真实数据规模：29 节点 / 76 边）：

```json
{
  "data": {
    "nodes": [
      {
        "id": "canglangting::建筑::建筑5-1",
        "db": "canglangting",
        "label": "建筑",
        "name": "面水轩",
        "props": {
          "x": -25.2, "y": -5.3,          ← 笛卡尔坐标（米，大门入口为原点）
          "极径_m": 25.8, "极角_度": 192,  ← 极坐标（与 x/y 等价冗余）
          "类型": "轩", "功能": "…"
        }
      },
      { "id": "canglangting::山石::山石2-1", "label": "山石", "name": "沧浪亭假山",
        "props": { "x": -39.0, "y": 27.0, "极径_m": 47.4, "极角_度": 145, "…": "…" } },
      { "id": "canglangting::园林::沧浪亭", "label": "园林", "name": "沧浪亭",
        "props": { "编号": "沧浪亭", "时期": "北宋始建，清代重修", "位置": "…" } }
    ],
    "links": [ /* 76 条：属于 28 / 相邻 34 / 相接 14，含空间语义 props */ ]
  }
}
```

- **Cypher 查询逻辑**：

```cypher
MATCH (n) WHERE NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom') RETURN n
MATCH (a)-[r]->(b) WHERE NOT any(l IN labels(a) WHERE l STARTS WITH '_Bloom')
  AND NOT any(l IN labels(b) WHERE l STARTS WITH '_Bloom') RETURN r, a, b
```

- **前端消费约定**：
  - **平面布局**：`layout:'none'`，取 `props.x / props.y`（y 轴翻转适配屏幕），按全体坐标边界缩放居中——还原园林平面图；`园林` 根节点无坐标 → 置于质心；
  - **极坐标投影（可选）**：直接使用 `极径_m`/`极角_度` 作极坐标散点/环形布局（ECharts 极坐标系），展示要素相对入口的方位—距离分布；
  - 两种投影共用同一份数据，无需额外接口。

---

## 7. 空间关系接口（重点） ✅

**用途**：返回园林空间语义关系——`相邻` 关系（相邻类型/中介/方向/距离_m）与 `相接` 关系（接触类型/方向/距离_m），支持按空间语义条件组合筛选，返回 graph JSON 可直接上图。

### 7.1 查询空间关系

- **URL**：`GET /api/spatial/relations`
- **请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `db` | string | ✅ | 数据库名 |
| `rel_type` | string | 否 | 限定关系类型（`相邻` 或 `相接`，白名单校验）；缺省返回全部空间语义边（动态判定：`rel_props` 含 `相邻类型`/`接触类型` 的关系类型） |
| `adjacency_type` | string | 否 | `相邻类型` 取值：可看 / 建筑环线 / 对景 |
| `contact_type` | string | 否 | `接触类型` 取值：临水 / 在山上 / 在山边 |
| `medium` | string | 否 | `中介` 取值（模糊匹配）：园路 / 水面 / 山径 / 竹林 / 建筑组团 / … |
| `direction` | string | 否 | `方向` 取值（中文十六方位）：正北 / 西偏南 / 东偏北 / … |
| `max_distance_m` | float | 否 | `距离_m` 上限（米） |
| `label` | string | 否 | 仅返回该标签节点的出边 |

- **返回格式**（`?rel_type=相邻&adjacency_type=可看&medium=水面` 真实结果）：

```json
{
  "data": {
    "nodes": [
      { "id": "canglangting::建筑::建筑5-1", "label": "建筑", "name": "面水轩",
        "props": { "x": -25.2, "y": -5.3, "…": "…" } },
      { "id": "canglangting::池沼::池沼2-3", "label": "池沼", "name": "西南曲水",
        "props": { "x": -57.0, "y": -12.0, "…": "…" } }
    ],
    "links": [
      { "source": "canglangting::建筑::建筑5-1", "target": "canglangting::池沼::池沼2-3",
        "type": "相邻",
        "props": { "相邻类型": "可看", "中介": "水面", "方向": "西偏南", "距离_m": 32.5 } },
      { "source": "canglangting::池沼::池沼2-3", "target": "canglangting::建筑::建筑5-1",
        "type": "相邻",
        "props": { "相邻类型": "可看", "中介": "水面", "方向": "东偏北", "距离_m": 32.5 } }
    ]
  }
}
```

- **Cypher 查询逻辑**（条件按参数存在与否动态拼装，值全部参数化）：

```cypher
MATCH (a)-[r]->(b)
WHERE NOT any(l IN labels(a) WHERE l STARTS WITH '_Bloom')
  AND NOT any(l IN labels(b) WHERE l STARTS WITH '_Bloom')
  AND type(r) = $rel_type              -- 仅当 rel_type 提供
  AND r.相邻类型 = $adjacency_type      -- 仅当 adjacency_type 提供
  AND r.接触类型 = $contact_type        -- 仅当 contact_type 提供
  AND r.中介 CONTAINS $medium           -- 仅当 medium 提供
  AND r.方向 = $direction               -- 仅当 direction 提供
  AND r.距离_m <= $max_distance_m       -- 仅当 max_distance_m 提供
RETURN r, a, b
```

- **真实数据支撑**（当前库取值全集，筛选选项可由本接口结果或 §3 统计动态生成）：`相邻类型` 3 种（可看 16 / 建筑环线 14 / 对景 4）· `接触类型` 3 种（在山边 8 / 临水 4 / 在山上 2）· `方向` 15 种方位词 · `中介` 18 种（园路、水面、山径、竹林、桂树、建筑组团…）。

---

## 8. 游线分析接口（重点） ✅

**用途**：利用 `相邻类型 = 建筑环线` 的边及其 `环线序号`，生成园林游览路径——返回站点行程（序号/起止/方向/距离/中介）+ 图数据（供空间底图渲染与逐步动画）。

### 8.1 获取游览游线

- **URL**：`GET /api/route`
- **请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `db` | string | ✅ | 数据库名 |

- **返回格式**（canglangting 真实数据：14 站闭环，总长 487.7m）：

```json
{
  "data": {
    "stops": [
      { "seq": 1, "from": "大门 / 入口", "to": "面水轩", "rel": "相邻",
        "adjacency_type": "建筑环线", "direction": "西偏南", "distance_m": 25.8, "medium": "园路" },
      { "seq": 2, "from": "面水轩", "to": "观鱼处", "rel": "相邻",
        "adjacency_type": "建筑环线", "direction": "西偏北", "distance_m": 54.3, "medium": "园路 / 临水游线" }
    ],
    "total_distance_m": 487.7,
    "closed": true,
    "nodes": [ /* 游线涉及全部节点（graph JSON，含 x/y） */ ],
    "links": [ /* 游线边序列（与 stops 一一对应，graph JSON） */ ]
  }
}
```

> 真实游线全程：大门 / 入口 → 面水轩 → 观鱼处 → 沧浪亭 → 明道堂 → 清香馆 → 五百名贤祠 → 仰止亭 → 翠玲珑 → 看山楼 → 瑶华境界 → 御碑亭 → 厕所 → 沧浪胜迹坊 → **大门 / 入口（闭环）**。

- **Cypher 查询逻辑**：

```cypher
MATCH (a)-[r]->(b)
WHERE r.相邻类型 = '建筑环线' AND r.环线序号 IS NOT NULL
RETURN a, r, b
ORDER BY r.环线序号
```

- **实现说明**：实现采用数据驱动守卫 `WHERE r.环线序号 IS NOT NULL`（当前数据下与上式结果完全一致——全部 14 条环线边均属 `建筑环线`），未来其他园林若有不同命名的环线语义仍可识别；服务端计算 `total_distance_m`（∑ 距离_m）与 `closed`（首站起点 == 末站终点）。数据缺失时 `stops: []`，前端提示"当前园林无游线数据"。

---

## 9. 为 LLM 问答预留接口 🔮

### 9.1 自然语言问答（预留，三期实现）

- **URL**：`POST /api/qa`
- **请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| body.question | string | ✅ | 自然语言问题，如"沧浪亭有哪些临水建筑？" |
| body.db | string | 否 | 限定园林库 |

- **返回格式**（设计约定）：

```json
{
  "data": {
    "question": "沧浪亭有哪些临水建筑？",
    "answer": "沧浪亭园内临水建筑包括：面水轩、观鱼处……",
    "cypher": "MATCH (n:`建筑`)-[r:`相接` {接触类型:'临水'}]->() RETURN DISTINCT n.名称",
    "results": [ /* 结构化结果，前端可联动"在图谱中查看" */ ]
  }
}
```

- **查询逻辑（流程）**：
  1. LLM 语义解析：注入 `GET /api/schema` 的动态 Schema + few-shot 示例，生成 Cypher；
  2. **只读白名单校验**：仅允许 `MATCH…RETURN`（拒绝 CREATE/MERGE/DELETE/SET/CALL），限制返回行数 ≤50；
  3. 执行查询（`db` 参数路由到对应园林库）；
  4. LLM 依据结构化结果生成自然语言回答。
- LLM Provider 抽象（openai/claude/qwen/deepseek），配置在 `.env`（`LLM_PROVIDER`/`LLM_API_KEY`/`LLM_MODEL`）；**未配置时该路由不挂载**，不影响其他功能。

---

## 10. 知识网络分析接口 ✅

**用途**：单园知识网络分析——基础网络指标（节点/关系数量、平均连接度、最大关联节点）、Top 核心节点（按连接度排序）、标签与关系类型统计，供"知识网络分析"页面展示。

### 10.1 获取网络分析数据

- **URL**：`GET /api/analysis/network`
- **请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `db` | string | ✅ | 园林数据库名（须在业务库列表中） |
| `top_n` | int | 否 | Top 核心节点数量 1–50，默认 10 |

- **返回格式**（`db=canglangting` 真实结果）：

```json
{
  "data": {
    "db": "canglangting",
    "garden": "沧浪亭",
    "total_nodes": 29,
    "total_rels": 76,
    "avg_degree": 4.07,
    "max_degree_node": {
      "id": "canglangting::园林::沧浪亭", "db": "canglangting",
      "label": "园林", "name": "沧浪亭", "props": { "…": "…" }, "degree": 28
    },
    "top_nodes": [
      { "id": "canglangting::园林::沧浪亭", "label": "园林", "name": "沧浪亭", "degree": 28 },
      { "id": "canglangting::建筑::建筑7-1", "label": "建筑", "name": "明道堂", "degree": 6 }
    ],
    "by_label": [
      { "label": "建筑", "count": 14 },
      { "label": "花木", "count": 8 }
    ],
    "by_rel_type": [
      { "type": "相邻", "count": 34 },
      { "type": "属于", "count": 28 }
    ]
  }
}
```

- **Cypher 查询逻辑**：

```cypher
MATCH (n) WHERE NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom')
OPTIONAL MATCH (n)-[r]-(m) WHERE NOT any(l IN labels(m) WHERE l STARTS WITH '_Bloom')
RETURN n, count(DISTINCT m) AS degree
```

- **实现说明**：
  - 连接度 = **去重邻居数**（对称双写边合并，避免 2E/N 高估）；
  - `avg_degree` = 全体节点连接度均值；`max_degree_node`/`top_nodes` 按连接度降序（同值按稳定 ID）；
  - 标签/关系类型统计复用 `LABEL_COUNTS_QUERY`/`RELTYPE_COUNTS_QUERY`；
  - 节点 JSON 复用 graph JSON 公共结构（§0.3，含全部属性）；
  - 未知 `db` 返回 400；园林根节点通常为度最高节点（网络枢纽），属真实分析结论，前端如实展示。

---

## 附录 A：错误码速查

| 状态码 | 场景 | 示例 detail |
|---|---|---|
| 400 | 参数非法/白名单校验失败 | `数据库 canglangting 中不存在标签: 建筑X` |
| 400 | 实体不存在 | `未找到实体：建筑.编号=建筑99-1` |
| 502 | Cypher 执行失败 | `Neo4j 查询失败: …` |
| 503 | Neo4j 连接失败 | `Neo4j 连接失败: …` |

## 附录 B：接口实现状态对照

| 分组 | 接口 | 状态 |
|---|---|---|
| 1 数据库管理 | `/api/databases`、`/api/health` | ✅ |
| 2 Schema | `/api/schema` | ✅ |
| 3 数据统计 | `/api/overview` | ✅ |
| 4 节点查询 | `/api/entities`、`/api/entities/detail` | ✅ |
| 5 关系图谱 | `/api/graph/neighbors`、`/api/graph/expand`、`/api/path` | ✅ |
| 6 空间布局 | `/api/graph/garden` | ✅ |
| 7 空间关系 | `/api/spatial/relations` | ✅ |
| 8 游线分析 | `/api/route` | ✅ |
| 10 知识网络分析 | `/api/analysis/network` | ✅ |
| 9 LLM 预留 | `/api/qa` | 🔮 预留（三期） |

## 附录 C：扩展性说明

- **新园林接入**：dump 加载为同名数据库 → `GET /api/databases?refresh=true` 即自动识别，全部接口经 `db` 参数直接可用；
- **Schema 演进**：新增标签/关系/属性无需改接口——搜索全属性匹配、属性原样透传、图例与筛选动态生成；
- **空间语义缺省**：某库无 x/y 或环线数据时对应接口优雅降级（节点置质心 / `stops: []`），不报错。
