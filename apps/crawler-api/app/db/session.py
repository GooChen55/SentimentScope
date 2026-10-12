"""
统一数据库会话管理 — 全进程共享单一异步连接池。

DB 连接配置优先级：.db_config.json（init-db 成功后写入）> .env 环境变量。
"""

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from loguru import logger

from app.config import (
    DB_DIALECT, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_CHARSET,
)

_async_session_factory: async_sessionmaker | None = None
from app.paths import DB_CONFIG_FILE
_DB_CONFIG_FILE = DB_CONFIG_FILE


def _build_url(user: str, password: str, host: str, port: int, db_name: str, charset: str) -> str:
    return f"{DB_DIALECT}+aiomysql://{user}:{quote_plus(password)}@{host}:{port}/{db_name}?charset={charset}"


def _load_db_config() -> dict | None:
    """从 .db_config.json 加载持久化的 DB 配置。"""
    try:
        if _DB_CONFIG_FILE.exists():
            return json.loads(_DB_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def save_db_config(
        host: str, port: int, user: str, password: str, db_name: str, charset: str,
) -> None:
    """在成功 init-db 后持久化 DB 配置，session 模块将优先使用此文件。"""
    _DB_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _DB_CONFIG_FILE.write_text(
        json.dumps({
            "host": host, "port": port, "user": user,
            "password": password, "db_name": db_name, "charset": charset,
        }, indent=2),
        encoding="utf-8",
    )
    logger.info("数据库配置已保存到 .db_config.json")


def _get_db_params() -> dict:
    """读取 DB 参数：优先 .db_config.json，其次 .env 默认值。"""
    saved = None if os.getenv('CRAWLER_IGNORE_SAVED_DB') == '1' else _load_db_config()
    if saved:
        return saved
    return {
        "host": DB_HOST, "port": DB_PORT, "user": DB_USER,
        "password": DB_PASSWORD, "db_name": DB_NAME, "charset": DB_CHARSET,
    }


def create_db_engine(
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        db_name: str | None = None,
        charset: str | None = None,
) -> AsyncEngine:
    """创建异步数据库引擎，显式参数优先级最高，其次持久化配置，最后 .env 默认值。"""
    params = _get_db_params()
    url = _build_url(
        user or params["user"],
        password or params["password"],
        host or params["host"],
        port or params["port"],
        db_name or params["db_name"],
        charset or params["charset"],
    )
    return create_async_engine(url, pool_pre_ping=True, pool_recycle=1800)


def _get_factory() -> async_sessionmaker:
    global _async_session_factory
    if _async_session_factory is None:
        engine = create_db_engine()
        params = _get_db_params()
        _async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
        logger.info(f"异步数据库引擎已初始化: {params['db_name']}")
    return _async_session_factory


@asynccontextmanager
async def get_session() -> AsyncSession:
    factory = _get_factory()
    async with factory() as session:
        yield session


async def dispose_engine():
    global _async_session_factory
    if _async_session_factory is not None:
        await _async_session_factory.kw["bind"].dispose()
        _async_session_factory = None
        logger.info("数据库引擎已关闭")
