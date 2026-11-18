# -*- coding: utf-8 -*-
"""数据概览与 Schema API。"""
from fastapi import APIRouter, HTTPException, Query

from db import driver
from services import stats_service

router = APIRouter(tags=["overview"])


@router.get("/health")
def health():
    """轻量连通检查：只查 system 库的库列表，不触发全库扫描
    （加载 dump 期间全库扫描可能因瞬态错误重试而变慢）。"""
    try:
        rows = driver.run(
            "system",
            "SHOW DATABASES YIELD name, currentStatus "
            "WHERE name <> 'system' AND currentStatus = 'online' RETURN count(name) AS c",
        )
        return {"data": {"status": "ok", "neo4j": "connected", "online_databases": rows[0]["c"]}}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Neo4j 连接失败: {e}")


@router.get("/databases")
def databases(refresh: bool = Query(False, description="强制刷新业务库列表")):
    return {"data": driver.list_business_dbs(force=refresh)}


@router.get("/overview")
def overview():
    dbs = driver.list_business_dbs()
    return {"data": stats_service.overview_data(dbs)}


@router.get("/schema")
def schema():
    dbs = driver.list_business_dbs()
    return {"data": stats_service.schema_data(dbs)}
