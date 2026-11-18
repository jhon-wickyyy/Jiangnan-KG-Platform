# -*- coding: utf-8 -*-
"""Cypher 查询模板集中处：全部参数化，动态标签经白名单校验后反引号包裹。"""
from db import driver


def qlabel(label: str) -> str:
    """动态标签安全引用（反引号包裹）。"""
    return f"`{label}`"


def validate_label(db_name: str, label: str) -> None:
    if label not in driver.get_labels(db_name):
        raise ValueError(f"数据库 {db_name} 中不存在标签: {label}")


def validate_rel_type(db_name: str, rel_type: str) -> None:
    if rel_type not in driver.get_rel_types(db_name):
        raise ValueError(f"数据库 {db_name} 中不存在关系类型: {rel_type}")


# ---------- 实体搜索 / 浏览 ----------

def search_query(label: str | None, q: str | None) -> tuple[str, dict]:
    """返回 (query, params)。label 为 None 时搜索全部业务标签。"""
    parts = ["MATCH (n"]
    if label:
        parts.append(f":{qlabel(label)}")
    parts.append(")")
    conds = ["NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom')"]
    params: dict = {}
    if q:
        conds.append("any(k IN keys(n) WHERE n[k] IS NOT NULL AND toString(n[k]) CONTAINS $q)")
        params["q"] = str(q)
    order = (
        "CASE WHEN any(k IN keys(n) WHERE toString(n[k]) = $q) THEN 0 ELSE 1 END, n.编号"
        if q
        else "n.编号"
    )
    query = (
        " ".join(parts)
        + " WHERE "
        + " AND ".join(conds)
        + " WITH n OPTIONAL MATCH (n)-[r]-(m) RETURN n, count(DISTINCT m) AS degree "
        + f"ORDER BY {order}"
    )
    return query, params


def count_query(label: str | None, q: str | None) -> tuple[str, dict]:
    parts = ["MATCH (n"]
    if label:
        parts.append(f":{qlabel(label)}")
    parts.append(")")
    conds = ["NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom')"]
    params: dict = {}
    if q:
        conds.append("any(k IN keys(n) WHERE n[k] IS NOT NULL AND toString(n[k]) CONTAINS $q)")
        params["q"] = str(q)
    return " ".join(parts) + " WHERE " + " AND ".join(conds) + " RETURN count(n) AS c", params


# ---------- 实体详情 ----------

def node_by_id_query(label: str, bid: str) -> str:
    return f"MATCH (n:{qlabel(label)} {{编号: $bid}}) RETURN n"


def neighbors_of_query(label: str, bid: str) -> str:
    return f"MATCH (n:{qlabel(label)} {{编号: $bid}})-[r]-(m) RETURN n, r, m"


# ---------- 图谱子图 ----------

def subgraph_query(label: str, bid: str, depth: int) -> str:
    """以指定实体为中心的变长路径子图（Python 侧去重）。

    depth 已在调用方白名单化为 1..3 的整数（本版本 Neo4j 不支持
    参数化变长界 [*1..$depth]），此处安全内联。
    """
    return (
        f"MATCH path = (n:{qlabel(label)} {{编号: $bid}})-[*1..{int(depth)}]-(m) RETURN path"
    )


GARDEN_NODES_QUERY = (
    "MATCH (n) WHERE NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom') RETURN n"
)

GARDEN_LINKS_QUERY = (
    "MATCH (a)-[r]->(b) "
    "WHERE NOT any(l IN labels(a) WHERE l STARTS WITH '_Bloom') "
    "AND NOT any(l IN labels(b) WHERE l STARTS WITH '_Bloom') "
    "RETURN r, a, b"
)


def expand_query(label: str, bid: str) -> str:
    """指定节点的一跳新邻居（同时返回两端节点以保证标签信息完整）。"""
    return f"MATCH (n:{qlabel(label)} {{编号: $bid}})-[r]-(m) RETURN r, n, m"


# ---------- 统计与 Schema ----------

LABEL_COUNTS_QUERY = (
    "MATCH (n) WHERE NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom') "
    "UNWIND labels(n) AS l RETURN l AS label, count(*) AS c"
)

RELTYPE_COUNTS_QUERY = "MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS c"


def label_prop_keys_query(label: str) -> str:
    return f"MATCH (n:{qlabel(label)}) UNWIND keys(n) AS k RETURN DISTINCT k"


def rel_prop_keys_query(rel_type: str) -> str:
    return f"MATCH ()-[r:{qlabel(rel_type)}]->() UNWIND keys(r) AS k RETURN DISTINCT k"


def count_label_query(label: str) -> str:
    return f"MATCH (n:{qlabel(label)}) RETURN count(n) AS c"


# ---------- 知识网络分析 ----------

NODE_DEGREES_QUERY = (
    "MATCH (n) WHERE NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom') "
    "OPTIONAL MATCH (n)-[r]-(m) "
    "WHERE NOT any(l IN labels(m) WHERE l STARTS WITH '_Bloom') "
    "RETURN n, count(DISTINCT m) AS degree"
)


def label_nodes_query(label: str) -> str:
    return f"MATCH (n:{qlabel(label)}) RETURN n ORDER BY n.编号 LIMIT 1"
