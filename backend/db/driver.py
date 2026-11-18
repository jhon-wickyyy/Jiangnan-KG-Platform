# -*- coding: utf-8 -*-
"""Neo4j 连接管理：driver 单例、业务库枚举、Schema 缓存。"""
import threading
import time

from neo4j import GraphDatabase

from config import settings

_DRIVER = None
_CACHE = {}  # key -> (timestamp, value)
_LOCKS = {}  # key -> 扫描单飞锁（缓存失效时并发请求共享同一次计算）


def get_driver():
    global _DRIVER
    if _DRIVER is None:
        _DRIVER = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _DRIVER


def run(db_name: str, query: str, params: dict | None = None):
    """在指定数据库执行查询，返回 record 列表。"""
    res = get_driver().execute_query(query, parameters_=params or {}, database_=db_name)
    return res.records


def cached(key: str, fn, ttl: float | None = None):
    """带 TTL 的内存缓存（单飞：并发 miss 共享同一次计算，避免扫描风暴）。"""
    ttl = ttl if ttl is not None else settings.cache_ttl
    now = time.time()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    lock = _LOCKS.setdefault(key, threading.Lock())
    with lock:
        hit = _CACHE.get(key)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
        val = fn()
        _CACHE[key] = (time.time(), val)
        return val


def get_labels(db_name: str) -> list[str]:
    """动态读取业务标签（排除 Neo4j Bloom 内部标签）。"""
    def _load():
        rows = run(db_name, "CALL db.labels() YIELD label RETURN label")
        return [r["label"] for r in rows if not r["label"].startswith("_Bloom")]

    return cached(f"labels:{db_name}", _load)


def get_rel_types(db_name: str) -> list[str]:
    """动态读取关系类型。"""
    def _load():
        rows = run(db_name, "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
        return [r["relationshipType"] for r in rows]

    return cached(f"reltypes:{db_name}", _load)


def count_business_nodes(db_name: str) -> int:
    return run(
        db_name,
        "MATCH (n) WHERE NOT any(l IN labels(n) WHERE l STARTS WITH '_Bloom') RETURN count(n) AS c",
    )[0]["c"]


def count_rels(db_name: str) -> int:
    return run(db_name, "MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]


def garden_name(db_name: str) -> str:
    """园林名：优先配置映射（缺根节点的库），回退数据驱动解析（根节点名），再回退库名。"""
    override = settings.garden_name_overrides.get(db_name)
    if override:
        return override
    labels = get_labels(db_name)
    candidates = []
    if "园林" in labels:
        candidates.append("园林")
    for lbl in labels:
        if lbl != "园林":
            c = run(db_name, f"MATCH (n:`{lbl}`) RETURN count(n) AS c")[0]["c"]
            candidates.append(lbl)
            if c == 1:
                break
    for lbl in candidates:
        rows = run(db_name, f"MATCH (n:`{lbl}`) RETURN properties(n) AS p LIMIT 1")
        if rows:
            p = rows[0]["p"]
            name = p.get("编号") or p.get("名称")
            if name:
                return str(name)
    return db_name


def list_business_dbs(force: bool = False) -> list[dict]:
    """枚举在线且非空的业务库（一园一库）。"""
    def _load():
        dbs = []
        rows = run(
            "system",
            "SHOW DATABASES YIELD name, type, currentStatus "
            "WHERE type = 'standard' RETURN name, currentStatus",
        )
        for r in rows:
            name = r["name"]
            if name in settings.db_ignore or r["currentStatus"] != "online":
                continue
            nodes = count_business_nodes(name)
            if nodes == 0:
                continue
            dbs.append({
                "name": name,
                "garden": garden_name(name),
                "nodes": nodes,
                "rels": count_rels(name),
            })
        dbs.sort(key=lambda d: d["garden"])
        return dbs

    if force:
        _CACHE.pop("business_dbs", None)
    return cached("business_dbs", _load)
