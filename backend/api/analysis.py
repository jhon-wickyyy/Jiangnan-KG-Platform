# -*- coding: utf-8 -*-
"""知识网络分析 API。"""
from fastapi import APIRouter, HTTPException, Query

from db import driver
from services import stats_service

router = APIRouter(tags=["analysis"])


@router.get("/analysis/network")
def network_analysis(db: str = Query(..., description="园林数据库名"),
                     top_n: int = Query(10, ge=1, le=50, description="Top 核心节点数量")):
    if db not in [d["name"] for d in driver.list_business_dbs()]:
        raise HTTPException(status_code=400, detail=f"未知的数据库: {db}")
    try:
        return {"data": stats_service.network_analysis(db, top_n)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Neo4j 查询失败: {e}")
