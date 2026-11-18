# 多园林知识图谱平台接入方案

> 版本：v1.1（2026-10-12）
> 依据：对 backend/frontend 现状的逐项核查 + 本会话真实运行验证（24 个业务库在线、切换联动实测）
> 结论先行：**平台自设计之初即按"一园一库 + 多库路由"实现，多园林接入的主体能力已经具备**。本方案梳理现状、列出现存差距与修改清单。
> v1.1 更新：P0/P1/P2/P3 修复已实施并验证（§2 各项标注 ✅）；新增多库体检实测发现（§6）。

---

## 1. 现状核查结果

### 1.1 Backend 的 Neo4j 数据库配置方式

- 连接配置仅在 `backend/.env`（`NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` / `NEO4J_DB_IGNORE`），**没有任何逐库配置**；
- 多库路由已实现（`db/driver.py`）：
  - `run(db_name, query, params)`：每次查询以 `database_=` 参数路由到指定库；
  - `list_business_dbs()`：`SHOW DATABASES`（system 库）动态枚举 → 过滤 `system`/忽略库/非 online/**空库** → 每库统计节点/关系数、解析园林名（`园林` 标签根节点 → 节点数最少标签 → 库名回退链）→ 30s TTL 内存缓存（`?refresh=true` 强制重扫）；
  - 标签/关系类型白名单校验按库执行（`get_labels` / `get_rel_types`）。
- **结论**：新园林库加载后无需任何代码或配置改动，即可被平台自动识别。

### 1.2 全部 API 的 `db` 参数核对

| 接口 | db 参数 | 说明 |
|---|---|---|
| `GET /api/health` | 无 | 全局连通检查 |
| `GET /api/databases` | 无 | 枚举全部业务库（`refresh=true` 强制重扫） |
| `GET /api/overview` | 无 | 跨库聚合统计 |
| `GET /api/schema` | 无 | 跨库并集（标签/关系/属性键） |
| `GET /api/entities` | **可选** | 缺省跨库；传 db 限定单园 |
| `GET /api/entities/detail` | 必填 ✅ | |
| `GET /api/graph/garden` | 必填 ✅ | |
| `GET /api/graph/neighbors` | 必填 ✅ | |
| `GET /api/graph/expand` | 必填 ✅ | |
| `GET /api/path` | 必填 ✅ | |
| `GET /api/spatial/relations` | 必填 ✅ | |
| `GET /api/route` | 必填 ✅ | |
| `GET /api/analysis/network` | 必填 ✅ | |

**结论**：所有园林作用域接口均已支持 `db`；全局接口按设计跨库聚合。接口层无需修改。

### 1.3 前端园林切换器

- 已实现：`App.vue` 顶栏"当前园林"下拉框（选项来自 `/api/databases`），Pinia `app` store 维护 `databases` / `currentDb` / `schema`；
- 各页面已 `watch(currentDb)` 自动重载并清空旧数据：图谱探索、实体浏览、实体搜索、游线分析、空间关系分析、路径查询、知识网络分析 ✅；
- 本会话实测：18 → 24 库在线期间，切换园林（个园 ↔ 沧浪亭）各页面数据正确联动（如分析页节点数 18 → 29）。

### 1.4 数据库加载现状（cypher-shell 实测）

Neo4j 服务器当前 **24 个业务库全部 online**：

```
canglangting · changyuan · geyuan1.0 · guozhuang · heyuan · jieziyuan
lejiaoyuan · liuyuan · nanxunxiaolianzhuang · ouyuan · pingshantangxiyuan
qcoy · qiaoyuan · qingchuzhanyuan · qiyuan · shizilin · tuisiyuan
wsy2.0 · wuyuan · yingyuan · yiyuan · yp2.0 · zhuozhengyuan · zy2.0
```

- `database/` 目录 23 个 dump 已全部加载（库 `qiyuan` 在库列表中出现、dump 目录中无对应文件，疑为直接建库或早期加载，建议核对数据来源）；
- ⚠️ **目标架构示例中的 `wangshiyuan`（网师园）在 dump 与库列表中均不存在**——如需接入网师园，需要先补充其 dump 数据文件。

---

## 2. 需要修改的地方（真实差距清单）

### 【后端】P0-1 加载期间的扫描风暴与服务阻塞 ✅ 已修复

**现象**：向 Neo4j 加载 dump 期间（如 `yiyuan` 库写入中），读请求触发 `BookmarkTimeout` 瞬态错误，驱动器反复重试；`/api/databases` 的全库扫描被重试拖长至分钟级，`/api/health`（同样依赖 `list_business_dbs`）随之 60s+ 无响应。

**已实施修改**：
1. `db/driver.py` `cached()` 加单飞锁（并发 miss 共享同一次计算）；
2. `api/overview.py` `health` 轻量化：只查 `system` 库 `SHOW DATABASES` 计数，不再依赖全库扫描；
3. `config.py` 缓存 TTL 默认 30s → 300s。

**实测**：health 0.5s（原 60s+ 超时）、databases 首扫 1.7s、缓存命中 0.02s。

### 【前端】P1-1 园林列表"重新扫描"入口 ✅ 已实施

`api/index.js` `getDatabases(refresh)` + `stores/app.js` `rescan()` + `App.vue` 切换器旁"⟳"按钮（新库加载后一键重扫，提示"共 N 个园林库"）。

### 【前端】P1-2 实体浏览页标签计数作用域 ✅ 已实施

`EntitiesView` 标签计数改用 `/api/analysis/network` 的 `by_label`（当前园林口径），并随园林切换刷新，与表格数据一致。

### 【前端·语义决策】P2-1 Dashboard 的作用域

**已定**：保持全局总览（方案 A）——Dashboard 展示全平台统计与各园林规模表；园林切换器作用于 7 个园林级页面。

### 【前端】P2-2 实体搜索"全部园林"入口 ✅ 已实施

`SearchView` 增加园林下拉（清空=全部园林，默认跟随当前园林；园林切换时若未被手动覆盖则自动跟随），`db` 参数按选择传入。

### 【验证】P3-1 多库体检脚本 ✅ 已实施

`scripts/verify-multidb.mjs`：对全部业务库并行调用 `garden/route/spatial/analysis` 接口，输出逐园一览表（节点/关系/坐标占比/游线站/闭环/空间边/核心节点/ID 重复检测）与异常汇总。已实测 23 库。

---

## 3. 新园林接入标准流程（运维手册）

```bash
# 1. dump 放入 database/（命名约定：<库名>-<日期>.dump）
# 2. 加载到 Neo4j（Desktop UI，或命令行）：
neo4j-admin database load <库名> --from-path=database/<文件> --overwrite-destination=true
# 3. 前端顶栏点"重新扫描"（P1-1 实现后），或后端 GET /api/databases?refresh=true
# 4. 抽查：GET /api/graph/garden?db=<库名>（坐标占比）、/api/route（游线）、/api/analysis/network
```

平台对每库 Schema 差异已动态兜底：标签/关系/属性全部运行时读取；某库缺 x/y 坐标 → 节点回退质心；缺环线数据 → 游线页提示"无游线数据"；缺空间语义 → 相应筛选选项为空。**无需为任何新园改代码**。

---

## 4. 目标架构达成度

```
Neo4j（一园一库，24 库在线）                 ✅ 已达成
        ↑ SHOW DATABASES 自动发现
FastAPI 多库路由（db 参数 + 白名单校验）       ✅ 已达成
        ↑ /api/*
Vue3 园林选择器 → 各页面 watch 联动刷新        ✅ 已达成（7 个园林级页面）
```

**总体达成度约 90%**。剩余工作 = §2 清单：P0-1（后端健壮性，建议优先）、P1-1/P1-2（前端小修）、P2-1（Dashboard 语义待确认）、P3-1（多库回归）。

## 5. 风险与兜底

| 风险 | 兜底 |
|---|---|
| 各园 schema 不一致（标签/属性差异） | 动态 Schema + 名称回退链已实现；P3-1 脚本逐园体检 |
| 某园数据缺坐标/缺游线 | 已实现优雅降级（质心 / 空提示） |
| 库加载期间 API 抖动 | P0-1 已修复（单飞锁 + 轻量 health + TTL 300s） |
| 库数量增长导致 overview/schema 变慢 | 均为缓存 + 小数据量；必要时 overview 改为列表页懒加载 |

## 6. 多库体检实测发现（2026-10-12，23 库全量扫描）

| # | 发现 | 影响与建议 |
|---|---|---|
| 1 | **网师园已接入**：`wsy2.0` 库解析为"网师园"（26 节点）——v1.0 中"网师园缺失"判断有误，目标架构中的 wangshiyuan 即 wsy2.0 | 无需补充数据 |
| 2 | **平山堂西园（pingshantangxiyuan）为空库**，被平台自动排除（API 枚举 23 个业务库） | 符合"空库自动排除"设计；如需接入需重新加载 dump |
| 3 | ~~10 个园缺"园林"根节点~~ ✅ **已修复（2026-10-12）**：`backend/config.py` 新增 `garden_name_overrides` 库名→园名映射（乔园/南浔小莲庄/何园/畅园/偶园（青州）/启园/芥子园/怡园/留园/清初瞻园/郭庄，共 11 库；qcoy=偶园（青州）经数据考证确认），`driver.garden_name()` 优先查映射、其余库仍动态解析。23 园名称全部正确 | 切换器显示正常园名 |
| 4 | **12 个园无空间语义数据**（游线 0 站 + 空间边 0）：数据只有"属于"关系，无 相邻/相接/环线序号 | 平台已优雅降级（游线/空间关系页空提示）；如需空间功能需补充数据 |
| 5 | **yp2.0（艺圃）存在重复编号/无标签节点**（物理 36 节点 vs 稳定 ID 去重后 14，"建筑4-01"出现 3 次），违反"编号唯一"假设 | 平台按稳定 ID 合并展示（不崩溃）；建议修复该库数据；体检脚本已加"ID 重复"检测 |
| 6 | 数据最完整的园：沧浪亭、狮子林、耦园、乐郊园、拙政园、退思园、影园（含游线闭环） | 演示优先用这些园 |
