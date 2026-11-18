# -*- coding: utf-8 -*-
"""图谱子图 API：全园子图（空间布局模式）、邻域子图（知识关系模式）、增量展开。"""
from fastapi import APIRouter, Query

from db import driver
from services import graph_service, stats_service

router = APIRouter(tags=["graph"])


@router.get("/graph/garden")
def garden(db: str = Query(..., description="数据库名（园林）")):
    """当前园林完整子图：全部节点与关系（含 x/y 空间坐标）。"""
    return {"data": graph_service.garden_subgraph(db)}


@router.get("/graph/neighbors")
def neighbors(
    db: str = Query(..., description="数据库名（园林）"),
    root: bool = Query(False, description="以园林根节点为中心（动态解析）"),
    label: str | None = Query(None, description="中心节点标签（root=false 时必填）"),
    id: str | None = Query(None, description="中心节点编号（root=false 时必填）"),
    depth: int = Query(1, ge=1, le=3),
):
    """以指定实体为中心的邻域子图。"""
    if root:
        label, id = stats_service.resolve_garden_root(db)
    if not label or not id:
        raise ValueError("请提供 root=true，或同时提供 label 与 id")
    # 单独取中心节点本身
    from db import queries
    rows = driver.run(db, queries.node_by_id_query(label, id), {"bid": id})
    center_node = graph_service.node_to_dict(db, rows[0]["n"])
    g = graph_service.subgraph(db, label, id, depth)
    g["center"] = center_node
    return {"data": g}


@router.get("/graph/expand")
def expand(
    db: str = Query(..., description="数据库名（园林）"),
    label: str = Query(..., description="节点标签"),
    id: str = Query(..., description="节点编号"),
):
    """指定节点的一跳新邻居（增量展开）。"""
    return {"data": graph_service.expand_node(db, label, id)}


@router.get("/path")
def path(
    db: str = Query(..., description="数据库名（园林）"),
    source_label: str = Query(..., description="起点标签"),
    source_id: str = Query(..., description="起点编号"),
    target_label: str = Query(..., description="终点标签"),
    target_id: str = Query(..., description="终点编号"),
    rel_types: str | None = Query(None, description="限定关系类型（逗号分隔），缺省不限"),
    max_depth: int = Query(6, ge=1, le=6, description="最大跳数 1–6"),
):
    """两点间最短路径。"""
    return {"data": graph_service.path_between(
        db, source_label, source_id, target_label, target_id, rel_types, max_depth)}
