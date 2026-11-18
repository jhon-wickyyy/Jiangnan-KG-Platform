# -*- coding: utf-8 -*-
"""空间关系查询与游线环线查询。"""
from db import driver, queries
from services import graph_service

# 查询条件属性名适配：标准名 → 该库实际属性名；None 表示该库无此属性（跳过该条件）。
# 畅园的 相邻类型/接触类型 共用 `类型` 列（两关系类型的取值集合不相交：可看/路径 vs 连接/空值），距离用 `极径_m`。
QUERY_PROP_ALIASES = {
    "changyuan": {"相邻类型": "类型", "接触类型": "类型", "距离_m": "极径_m", "方向": None, "中介": None},
}


def _prop_name(db_name: str, std: str) -> str | None:
    """标准属性名 → 该库查询用属性名（未适配的库原样使用标准名）。"""
    if db_name not in QUERY_PROP_ALIASES:
        return std
    return QUERY_PROP_ALIASES[db_name].get(std, std)


def _spatial_rel_types(db_name: str) -> list[str]:
    """动态判定空间语义关系类型：rel_props 含 `相邻类型` / `接触类型` / `空间关系` 标记的类型。"""
    types = []
    for t in driver.get_rel_types(db_name):
        keys = {r["k"] for r in driver.run(db_name, queries.rel_prop_keys_query(t))}
        if "相邻类型" in keys or "接触类型" in keys or "空间关系" in keys:
            types.append(t)
    return types


def spatial_relations(db_name: str, rel_type: str | None = None,
                      adjacency_type: str | None = None, contact_type: str | None = None,
                      medium: str | None = None, direction: str | None = None,
                      max_distance_m: float | None = None, label: str | None = None) -> dict:
    """按空间语义条件组合查询节点对，返回 graph JSON。"""
    conds = [
        "NOT any(l IN labels(a) WHERE l STARTS WITH '_Bloom')",
        "NOT any(l IN labels(b) WHERE l STARTS WITH '_Bloom')",
    ]
    params: dict = {}
    a_clause = "a"
    if label:
        queries.validate_label(db_name, label)
        a_clause = f"a:{queries.qlabel(label)}"

    if rel_type:
        queries.validate_rel_type(db_name, rel_type)
        conds.append("type(r) = $rel_type")
        params["rel_type"] = rel_type
    else:
        types = _spatial_rel_types(db_name)
        if not types:
            return {"nodes": [], "links": []}
        conds.append("type(r) IN $rel_types")
        params["rel_types"] = types

    pn_adj = _prop_name(db_name, "相邻类型")
    pn_con = _prop_name(db_name, "接触类型")
    pn_med = _prop_name(db_name, "中介")
    pn_dir = _prop_name(db_name, "方向")
    pn_dist = _prop_name(db_name, "距离_m")
    if adjacency_type and pn_adj:
        conds.append(f"r.{pn_adj} = $adjacency_type")
        params["adjacency_type"] = adjacency_type
    if contact_type and pn_con:
        conds.append(f"r.{pn_con} = $contact_type")
        params["contact_type"] = contact_type
    if medium and pn_med:
        conds.append(f"r.{pn_med} CONTAINS $medium")
        params["medium"] = medium
    if direction and pn_dir:
        conds.append(f"r.{pn_dir} = $direction")
        params["direction"] = direction
    if max_distance_m is not None and pn_dist:
        conds.append(f"r.{pn_dist} <= $max_distance_m")
        params["max_distance_m"] = float(max_distance_m)

    q = f"MATCH ({a_clause})-[r]->(b) WHERE " + " AND ".join(conds) + " RETURN r, a, b"
    nodes, links = {}, {}
    for rec in driver.run(db_name, q, params):
        for n in (rec["a"], rec["b"]):
            nd = graph_service.node_to_dict(db_name, n)
            nodes[nd["id"]] = nd
        lk = graph_service.link_to_dict_between(db_name, rec["r"], rec["a"], rec["b"])
        links[lk["id"]] = lk
    return {"nodes": list(nodes.values()), "links": list(links.values())}


def tour_route(db_name: str) -> dict:
    """游线环线：取全部带 `环线序号` 的边按序号排序，还原游览动线。

    当前数据下该边集与 `相邻(相邻类型=建筑环线)` 完全一致（14 站闭环）；
    数据驱动守卫保证未来其他命名的环线语义同样可识别。
    """
    q = (
        "MATCH (a)-[r]->(b) "
        "WHERE r.环线序号 IS NOT NULL "
        "AND NOT any(l IN labels(a) WHERE l STARTS WITH '_Bloom') "
        "AND NOT any(l IN labels(b) WHERE l STARTS WITH '_Bloom') "
        "RETURN a, r, b ORDER BY r.环线序号"
    )
    stops, nodes, links = [], {}, {}
    for rec in driver.run(db_name, q):
        a, r, b = rec["a"], rec["r"], rec["b"]
        stops.append({
            "seq": r.get("环线序号"),
            "from": str(a.get("名称") or a.get("编号") or "节点"),
            "to": str(b.get("名称") or b.get("编号") or "节点"),
            "rel": r.type,
            "adjacency_type": r.get("相邻类型"),
            "direction": r.get("方向"),
            "distance_m": r.get("距离_m"),
            "medium": r.get("中介"),
        })
        for n in (a, b):
            nd = graph_service.node_to_dict(db_name, n)
            nodes[nd["id"]] = nd
        lk = graph_service.link_to_dict_between(db_name, r, a, b)
        links[lk["id"]] = lk
    total = round(sum(
        s["distance_m"] for s in stops if isinstance(s["distance_m"], (int, float))
    ), 1)
    closed = bool(stops) and stops[0]["from"] == stops[-1]["to"]
    return {
        "stops": stops,
        "total_distance_m": total,
        "closed": closed,
        "nodes": list(nodes.values()),
        "links": list(links.values()),
    }
