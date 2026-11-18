# -*- coding: utf-8 -*-
"""空间关系查询与游线环线查询 API。"""
from fastapi import APIRouter, Query

from services import spatial_service

router = APIRouter(tags=["spatial"])


@router.get("/spatial/relations")
def spatial_relations(
    db: str = Query(..., description="数据库名（园林）"),
    rel_type: str | None = Query(None, description="限定关系类型（相邻/相接），缺省返回全部空间语义边"),
    adjacency_type: str | None = Query(None, description="相邻类型：可看/建筑环线/对景"),
    contact_type: str | None = Query(None, description="接触类型：临水/在山上/在山边"),
    medium: str | None = Query(None, description="中介（模糊匹配）：园路/水面/山径/…"),
    direction: str | None = Query(None, description="方向（中文十六方位）：正北/西偏南/…"),
    max_distance_m: float | None = Query(None, description="距离_m 上限（米）"),
    label: str | None = Query(None, description="仅返回该标签节点的出边"),
):
    return {"data": spatial_service.spatial_relations(
        db, rel_type=rel_type, adjacency_type=adjacency_type, contact_type=contact_type,
        medium=medium, direction=direction, max_distance_m=max_distance_m, label=label,
    )}


@router.get("/route")
def route(db: str = Query(..., description="数据库名（园林）")):
    """游线环线：按 `环线序号` 排序的游览动线（数据缺失时返回空 stops）。"""
    return {"data": spatial_service.tour_route(db)}
