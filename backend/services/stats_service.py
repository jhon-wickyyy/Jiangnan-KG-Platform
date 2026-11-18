# -*- coding: utf-8 -*-
"""跨库聚合统计、动态 Schema 采集、实体搜索、实体详情、园林根节点解析。"""
from db import driver, queries
from services import graph_service


# ---------- 园林根节点 ----------

def resolve_garden_root(db_name: str) -> tuple[str, str]:
    """动态解析园林根节点 → (label, 编号)。优先 `园林` 标签，回退节点数最少的标签。"""
    labels = driver.get_labels(db_name)
    candidates = [l for l in labels if l == "园林"]
    counts = []
    for lbl in labels:
        if lbl == "园林":
            continue
        c = driver.run(db_name, queries.count_label_query(lbl))[0]["c"]
        counts.append((lbl, c))
    if counts:
        candidates.append(min(counts, key=lambda x: x[1])[0])
    for lbl in candidates:
        rows = driver.run(db_name, queries.label_nodes_query(lbl))
        if rows:
            node = rows[0]["n"]
            bid = node.get("编号", node.element_id)
            return lbl, str(bid)
    raise ValueError(f"数据库 {db_name} 中未找到园林根节点")


# ---------- 总览统计 ----------

def overview_data(db_infos: list[dict]) -> dict:
    by_label, by_rel = {}, {}
    total_nodes = total_rels = 0
    for d in db_infos:
        db_name = d["name"]
        total_nodes += d["nodes"]
        total_rels += d["rels"]
        for rec in driver.run(db_name, queries.LABEL_COUNTS_QUERY):
            by_label[rec["label"]] = by_label.get(rec["label"], 0) + rec["c"]
        for rec in driver.run(db_name, queries.RELTYPE_COUNTS_QUERY):
            by_rel[rec["t"]] = by_rel.get(rec["t"], 0) + rec["c"]
    return {
        "total_nodes": total_nodes,
        "total_rels": total_rels,
        "databases": db_infos,
        "by_label": [
            {"label": k, "count": v} for k, v in sorted(by_label.items(), key=lambda x: -x[1])
        ],
        "by_rel_type": [
            {"type": k, "count": v} for k, v in sorted(by_rel.items(), key=lambda x: -x[1])
        ],
    }


# ---------- 动态 Schema ----------

def schema_data(db_infos: list[dict]) -> dict:
    labels, rel_types = set(), set()
    label_props, rel_props = {}, {}
    for d in db_infos:
        db_name = d["name"]
        for lbl in driver.get_labels(db_name):
            labels.add(lbl)
            keys = label_props.setdefault(lbl, set())
            for rec in driver.run(db_name, queries.label_prop_keys_query(lbl)):
                keys.add(rec["k"])
        for t in driver.get_rel_types(db_name):
            rel_types.add(t)
            keys = rel_props.setdefault(t, set())
            for rec in driver.run(db_name, queries.rel_prop_keys_query(t)):
                keys.add(rec["k"])
    return {
        "labels": sorted(labels),
        "rel_types": sorted(rel_types),
        "label_props": {k: sorted(v) for k, v in label_props.items()},
        "rel_props": {k: sorted(v) for k, v in rel_props.items()},
    }


# ---------- 知识网络分析 ----------

def network_analysis(db_name: str, top_n: int = 10) -> dict:
    """单园知识网络分析：节点/关系规模、平均连接度、最大关联节点、Top 核心节点、
    标签与关系类型统计。连接度 = 去重邻居数（对称双写边合并）。"""
    nodes_with_degree = []
    for rec in driver.run(db_name, queries.NODE_DEGREES_QUERY):
        nd = graph_service.node_to_dict(db_name, rec["n"], degree=rec["degree"])
        nodes_with_degree.append(nd)
    nodes_with_degree.sort(key=lambda x: (-x["degree"], x["id"]))

    top_n = max(1, min(int(top_n), 50))
    by_label, by_rel = {}, {}
    for rec in driver.run(db_name, queries.LABEL_COUNTS_QUERY):
        by_label[rec["label"]] = by_label.get(rec["label"], 0) + rec["c"]
    for rec in driver.run(db_name, queries.RELTYPE_COUNTS_QUERY):
        by_rel[rec["t"]] = by_rel.get(rec["t"], 0) + rec["c"]

    total_nodes = len(nodes_with_degree)
    total_rels = driver.count_rels(db_name)
    degrees = [x["degree"] for x in nodes_with_degree]
    return {
        "db": db_name,
        "garden": driver.garden_name(db_name),
        "total_nodes": total_nodes,
        "total_rels": total_rels,
        "avg_degree": round(sum(degrees) / len(degrees), 2) if degrees else 0,
        "max_degree_node": nodes_with_degree[0] if nodes_with_degree else None,
        "top_nodes": nodes_with_degree[:top_n],
        "by_label": [
            {"label": k, "count": v} for k, v in sorted(by_label.items(), key=lambda x: -x[1])
        ],
        "by_rel_type": [
            {"type": k, "count": v} for k, v in sorted(by_rel.items(), key=lambda x: -x[1])
        ],
    }


# ---------- 实体搜索 / 浏览 ----------

def search_entities(db_infos: list[dict], label: str | None = None,
                    q: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    items = []
    for d in db_infos:
        db_name = d["name"]
        if label and label not in driver.get_labels(db_name):
            continue  # 该库无此标签
        qry, params = queries.search_query(label, q)
        for rec in driver.run(db_name, qry, params):
            items.append(graph_service.node_to_dict(db_name, rec["n"], degree=rec["degree"]))
    if q:
        qs = str(q)
        items.sort(key=lambda it: (
            0 if qs in (str(it["props"].get("名称")), str(it["props"].get("编号"))) else 1,
            it["id"],
        ))
    else:
        items.sort(key=lambda it: it["id"])
    total = len(items)
    start = (page - 1) * page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items[start:start + page_size],
    }


# ---------- 实体详情 ----------

def entity_detail(db_name: str, label: str, bid: str) -> dict:
    queries.validate_label(db_name, label)
    rows = driver.run(db_name, queries.node_by_id_query(label, bid), {"bid": bid})
    if not rows:
        raise ValueError(f"未找到实体：{label}.编号={bid}")
    node = rows[0]["n"]
    node_d = graph_service.node_to_dict(db_name, node)
    neighbors = []
    for rec in driver.run(db_name, queries.neighbors_of_query(label, bid), {"bid": bid}):
        rel, m = rec["r"], rec["m"]
        direction = "out" if rel.start_node.element_id == node.element_id else "in"
        neighbors.append({
            "rel": rel.type,
            "direction": direction,
            "rel_props": dict(rel),
            "node": graph_service.node_to_dict(db_name, m),
        })
    neighbors.sort(key=lambda x: (x["rel"], x["direction"], x["node"]["name"]))
    return {"node": node_d, "neighbors": neighbors}
