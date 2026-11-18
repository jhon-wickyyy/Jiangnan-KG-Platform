# -*- coding: utf-8 -*-
"""全局配置：从 .env 读取（凭证不写入代码）。"""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


@dataclass
class Settings:
    neo4j_uri: str = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")
    db_ignore: list = field(default_factory=lambda: [
        d.strip() for d in os.getenv("NEO4J_DB_IGNORE", "system").split(",") if d.strip()
    ])
    cache_ttl: float = float(os.getenv("CACHE_TTL", "300"))
    # 库名 → 园林名映射：部分库缺"园林"根节点，数据驱动解析会回退到建筑名；
    # 此处按库名（dump 文件名拼音）给出正确园名，其余库仍动态解析。
    garden_name_overrides: dict = field(default_factory=lambda: {
        "qiaoyuan": "乔园",
        "nanxunxiaolianzhuang": "南浔小莲庄",
        "heyuan": "何园",
        "changyuan": "畅园",
        "qcoy": "偶园（青州）",
        "qiyuan": "启园",
        "jieziyuan": "芥子园",
        "yiyuan": "怡园",
        "liuyuan": "留园",
        "qingchuzhanyuan": "清初瞻园",
        "guozhuang": "郭庄",
    })


settings = Settings()
