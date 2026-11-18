# -*- coding: utf-8 -*-
"""实体浏览 / 搜索 / 详情 API。"""
from fastapi import APIRouter, Query

from db import driver
from services import stats_service

router = APIRouter(tags=["entities"])


@router.get("/entities")
def entities(
    db: str | None = Query(None, description="限定数据库（园林），缺省搜索全部业务库"),
    label: str | None = Query(None, description="限定标签"),
    q: str | None = Query(None, description="关键词（全属性模糊匹配，精确匹配优先）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    dbs = driver.list_business_dbs()
    if db:
        dbs = [d for d in dbs if d["name"] == db]
    return {"data": stats_service.search_entities(dbs, label=label, q=q, page=page, page_size=page_size)}


@router.get("/entities/detail")
def entity_detail(
    db: str = Query(..., description="数据库名"),
    label: str = Query(..., description="标签"),
    id: str = Query(..., description="实体编号"),
):
    return {"data": stats_service.entity_detail(db, label, id)}
