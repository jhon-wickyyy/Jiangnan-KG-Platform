# -*- coding: utf-8 -*-
"""江南古典园林空间知识图谱可视化平台 —— 后端入口。

启动：cd backend && uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j.exceptions import Neo4jError

from api import analysis, entities, graph, overview, spatial

app = FastAPI(
    title="江南古典园林空间知识图谱可视化平台 API",
    description="基于 Neo4j 的江南古典园林空间知识图谱只读查询服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router, prefix="/api")
app.include_router(entities.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(spatial.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Neo4jError)
async def neo4j_error_handler(request: Request, exc: Neo4jError):
    return JSONResponse(status_code=502, content={"detail": f"Neo4j 查询失败: {exc}"})


@app.get("/")
def root():
    return {"name": "江南古典园林空间知识图谱可视化平台 API", "docs": "/docs"}
