# -*- coding: utf-8 -*-
"""核对结项 PPT 所需事实数据（对运行中的后端实测），输出 docs/_ppt_facts.json。

只读脚本：仅调用 GET 接口，不修改任何数据。
"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000/api"


def get(path, timeout=30):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    facts = {}

    # 1. 数据库列表
    dbs = get("/databases?refresh=true")["data"]
    facts["databases"] = dbs  # [{name, garden, nodes, rels}]

    # 2. 总览
    ov = get("/overview")["data"]
    facts["total_nodes"] = ov["total_nodes"]
    facts["total_rels"] = ov["total_rels"]
    facts["by_label"] = ov.get("by_label", {})
    facts["by_rel_type"] = ov.get("by_rel_type", {})

    # 3. 每园游线（闭环、站数、总长）
    routes = {}
    for d in dbs:
        db = d["name"]
        try:
            r = get(f"/route?db={db}")["data"]
            stops = r.get("stops") or []
            routes[db] = {
                "garden": d["garden"],
                "stations": len(stops),
                "total_m": r.get("total_distance_m"),
                "closed": r.get("closed"),
            }
        except Exception as e:
            routes[db] = {"garden": d["garden"], "error": str(e)[:80]}
    facts["routes"] = routes

    # 4. 沧浪亭网络指标
    try:
        net = get("/analysis/network?db=canglangting")["data"]
        facts["canglangting_network"] = {
            "total_nodes": net.get("total_nodes"),
            "total_rels": net.get("total_rels"),
            "avg_degree": net.get("avg_degree"),
            "max_degree_node": net.get("max_degree_node"),
            "top_nodes": net.get("top_nodes", [])[:5],
            "by_label": net.get("by_label"),
            "by_rel_type": net.get("by_rel_type"),
        }
    except Exception as e:
        facts["canglangting_network"] = {"error": str(e)[:80]}

    # 4b. 畅园网络指标（v4.2 案例园）
    try:
        net = get("/analysis/network?db=changyuan")["data"]
        facts["changyuan_network"] = {
            "total_nodes": net.get("total_nodes"),
            "total_rels": net.get("total_rels"),
            "avg_degree": net.get("avg_degree"),
            "max_degree_node": net.get("max_degree_node"),
            "top_nodes": net.get("top_nodes", [])[:5],
            "by_label": net.get("by_label"),
            "by_rel_type": net.get("by_rel_type"),
        }
    except Exception as e:
        facts["changyuan_network"] = {"error": str(e)[:80]}

    # 5. 沧浪亭空间关系：按关系类型统计 links
    try:
        sp = get("/spatial/relations?db=canglangting")["data"]
        by_type = {}
        for lk in sp.get("links", []):
            t = lk.get("type")
            by_type[t] = by_type.get(t, 0) + 1
        facts["canglangting_spatial"] = {
            "nodes": len(sp.get("nodes", [])),
            "links": len(sp.get("links", [])),
            "by_type": by_type,
        }
    except Exception as e:
        facts["canglangting_spatial"] = {"error": str(e)[:80]}

    # 5b. 畅园空间关系（v4.2：后端属性映射后应读出 86 相邻 + 44 相接）
    try:
        sp = get("/spatial/relations?db=changyuan")["data"]
        by_type = {}
        adj_vals = {}
        for lk in sp.get("links", []):
            t = lk.get("type")
            by_type[t] = by_type.get(t, 0) + 1
            if t == "相邻":
                v = str(lk.get("props", {}).get("相邻类型"))
                adj_vals[v] = adj_vals.get(v, 0) + 1
        facts["changyuan_spatial"] = {
            "nodes": len(sp.get("nodes", [])),
            "links": len(sp.get("links", [])),
            "by_type": by_type,
            "adjacency_values": adj_vals,
        }
    except Exception as e:
        facts["changyuan_spatial"] = {"error": str(e)[:80]}

    # 6. 路径查询样例（沧浪亭假山 山石2-1 → 面水轩 建筑5-1，仅空间关系）
    try:
        q = ("/path?db=canglangting&source_label=%E5%B1%B1%E7%9F%B3&source_id=%E5%B1%B1%E7%9F%B32-1"
             "&target_label=%E5%BB%BA%E7%AD%91&target_id=%E5%BB%BA%E7%AD%915-1"
             "&rel_types=%E7%9B%B8%E9%82%BB,%E7%9B%B8%E6%8E%A5")
        p = get(q)["data"]
        facts["path_example"] = {
            "hops": p.get("hops"),
            "total_m": p.get("total_distance_m"),
            "desc": p.get("description"),
        }
    except Exception as e:
        facts["path_example"] = {"error": str(e)[:120]}

    # 7. 游线环线统计（全部园林）
    closed = {k: v for k, v in routes.items() if v.get("closed") and v.get("stations", 0) > 2}
    longest = max(closed.items(), key=lambda kv: kv[1]["stations"]) if closed else None
    facts["route_gardens_closed"] = {
        "count": len(closed),
        "gardens": {k: v["stations"] for k, v in sorted(closed.items(), key=lambda kv: -kv[1]["stations"])},
        "longest": (longest[0], longest[1]) if longest else None,
    }

    # 8. 各园坐标覆盖率（graph/garden 中有 x/y 属性的节点占比，全库统计）
    coverage = {}
    for d in dbs:
        db = d["name"]
        try:
            g = get(f"/graph/garden?db={db}")["data"]
            nodes = g.get("nodes", [])
            with_xy = sum(1 for n in nodes if n.get("props", {}).get("x") is not None)
            coverage[db] = {"garden": d["garden"], "nodes": len(nodes), "with_xy": with_xy}
        except Exception as e:
            coverage[db] = {"error": str(e)[:60]}
    facts["xy_coverage"] = coverage

    out = r"C:\Users\jhon.wick\Desktop\srtp\结项\Jiangnan-KG-Platform\docs\_ppt_facts.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False, indent=1)
    print("saved:", out)
    print("dbs:", len(dbs), "| total:", ov["total_nodes"], "nodes", ov["total_rels"], "rels")
    print("labels:", facts["by_label"])
    print("rel types:", facts["by_rel_type"])
    print("closed route gardens:", facts["route_gardens_closed"]["count"],
          facts["route_gardens_closed"]["gardens"])
    print("longest:", facts["route_gardens_closed"]["longest"])
    print("canglangting net:", facts["canglangting_network"])
    print("canglangting spatial:", facts["canglangting_spatial"])
    print("changyuan net:", facts["changyuan_network"])
    print("changyuan spatial:", facts["changyuan_spatial"])
    print("path:", facts["path_example"])


if __name__ == "__main__":
    main()
