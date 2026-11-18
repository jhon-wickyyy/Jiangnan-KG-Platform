# -*- coding: utf-8 -*-
"""Neo4j 记录 → 前端 graph JSON 转换与子图装配。"""
from db import driver, queries

# 各园关系属性别名：标准名 → 该园实际属性名（畅园等以表格字段直接入库的库，属性命名与平台标准名不同）。
# 别名仅影响 JSON 输出与筛选语义；源数据空值占位 "\\" 视为无值。
REL_PROP_ALIASES = {
    "changyuan": {
        "相邻": {"相邻类型": "类型", "距离_m": "极径_m"},
        "相接": {"接触类型": "类型", "距离_m": "极径_m"},
    },
}


def normalize_rel_props(db_name: str, rel_type: str, props: dict) -> dict:
    """关系属性按园别名规范化为平台标准名（相邻类型 / 接触类型 / 距离_m / 方向 / 中介）。"""
    aliases = (REL_PROP_ALIASES.get(db_name) or {}).get(rel_type)
    if not aliases:
        return props
    out = dict(props)
    for std, src in aliases.items():
        if std in out:
            continue
        if src not in out:
            continue
        v = out.pop(src)
        out[std] = None if isinstance(v, str) and v.strip() in ("", "\\") else v
    return out


def primary_label(node) -> str:
    """节点主标签（排除 Bloom 内部标签；防御性回退）。"""
    labels = [l for l in node.labels if not l.startswith("_Bloom")] or list(node.labels)
    return labels[0] if labels else "节点"


def node_key(db_name: str, label: str, bid: str) -> str:
    """跨库节点稳定复合 ID：db::label::编号。"""
    return f"{db_name}::{label}::{bid}"


def node_to_dict(db_name: str, node, degree: int | None = None) -> dict:
    label = primary_label(node)
    props = dict(node)
    bid = props.get("编号", node.element_id)
    name = props.get("名称") or props.get("编号") or label
    d = {
        "id": node_key(db_name, label, str(bid)),
        "db": db_name,
        "label": label,
        "name": str(name),
        "props": props,
    }
    if degree is not None:
        d["degree"] = degree
    return d


def _link(db_name: str, rel, s, t) -> dict:
    """由两端节点（带标签）组装关系 JSON，方向即 rel 的实际方向。"""
    s_label, t_label = primary_label(s), primary_label(t)
    s_bid = s.get("编号", s.element_id)
    t_bid = t.get("编号", t.element_id)
    return {
        "id": f"{db_name}::{rel.element_id}",
        "source": node_key(db_name, s_label, str(s_bid)),
        "target": node_key(db_name, t_label, str(t_bid)),
        "type": rel.type,
        "props": normalize_rel_props(db_name, rel.type, dict(rel)),
    }


def link_to_dict_between(db_name: str, rel, n, m) -> dict:
    """n、m 为查询中返回的两端节点；按 element_id 判定方向后组装。"""
    if rel.start_node.element_id == n.element_id:
        return _link(db_name, rel, n, m)
    return _link(db_name, rel, m, n)


def subgraph(db_name: str, label: str, bid: str, depth: int = 1) -> dict:
    """以指定实体为中心的邻域子图（变长路径 + Python 去重）。"""
    queries.validate_label(db_name, label)
    depth = max(1, min(int(depth or 1), 3))
    q = queries.subgraph_query(label, bid, depth)
    nodes, links = {}, {}
    for rec in driver.run(db_name, q, {"bid": bid}):
        path = rec["path"]
        by_eid = {n.element_id: n for n in path.nodes}
        for node in path.nodes:
            nd = node_to_dict(db_name, node)
            nodes[nd["id"]] = nd
        for rel in path.relationships:
            s = by_eid.get(rel.start_node.element_id, rel.start_node)
            t = by_eid.get(rel.end_node.element_id, rel.end_node)
            lk = _link(db_name, rel, s, t)
            links[lk["id"]] = lk
    return {"nodes": list(nodes.values()), "links": list(links.values())}


def garden_subgraph(db_name: str) -> dict:
    """当前园林全库子图（供空间布局模式一次加载）。"""
    nodes, links = {}, {}
    for rec in driver.run(db_name, queries.GARDEN_NODES_QUERY):
        nd = node_to_dict(db_name, rec["n"])
        nodes[nd["id"]] = nd
    for rec in driver.run(db_name, queries.GARDEN_LINKS_QUERY):
        lk = link_to_dict_between(db_name, rec["r"], rec["a"], rec["b"])
        links[lk["id"]] = lk
    return {"nodes": list(nodes.values()), "links": list(links.values())}


def expand_node(db_name: str, label: str, bid: str) -> dict:
    """指定节点的一跳新邻居。"""
    queries.validate_label(db_name, label)
    q = queries.expand_query(label, bid)
    nodes, links = {}, {}
    for rec in driver.run(db_name, q, {"bid": bid}):
        nd = node_to_dict(db_name, rec["m"])
        nodes[nd["id"]] = nd
        lk = link_to_dict_between(db_name, rec["r"], rec["n"], rec["m"])
        links[lk["id"]] = lk
    return {"nodes": list(nodes.values()), "links": list(links.values())}


def path_between(db_name: str, s_label: str, s_bid: str, t_label: str, t_bid: str,
                 rel_types: str | None = None, max_depth: int = 6) -> dict:
    """两点间最短路径（可选限定关系类型），返回描述文本 + graph JSON。"""
    queries.validate_label(db_name, s_label)
    queries.validate_label(db_name, t_label)
    max_depth = max(1, min(int(max_depth or 6), 6))
    if rel_types:
        rts = [t.strip() for t in rel_types.split(",") if t.strip()]
        for t in rts:
            queries.validate_rel_type(db_name, t)
        # Cypher 25 语法：多类型变长关系为 [:A|B*1..n]，管道后不能再写冒号
        rel_part = "[:" + "|".join(queries.qlabel(t) for t in rts) + f"*1..{max_depth}]"
    else:
        rel_part = f"[*1..{max_depth}]"
    q = (
        f"MATCH path = shortestPath((a:{queries.qlabel(s_label)} {{编号: $sid}})"
        f"-{rel_part}-(b:{queries.qlabel(t_label)} {{编号: $tid}})) RETURN path"
    )
    rows = driver.run(db_name, q, {"sid": s_bid, "tid": t_bid})
    if not rows:
        raise ValueError(f"未找到路径：{s_label}.{s_bid} → {t_label}.{t_bid}")
    path = rows[0]["path"]
    nodes, links, desc = {}, [], []
    for i, node in enumerate(path.nodes):
        nd = node_to_dict(db_name, node)
        nodes[nd["id"]] = nd
        desc.append(nd["name"])
        if i < len(path.relationships):
            rel = path.relationships[i]
            lk = link_to_dict_between(db_name, rel, path.nodes[i], path.nodes[i + 1])
            links.append(lk)
            p = dict(rel)
            extras = [f"{k}·{p[k]}" for k in ("相邻类型", "接触类型", "距离_m") if p.get(k) is not None]
            desc.append(rel.type + ("(" + " ".join(extras) + ")" if extras else ""))
    return {
        "description": " →".join(desc),
        "length": len(path.relationships),
        "nodes": list(nodes.values()),
        "links": links,
    }
