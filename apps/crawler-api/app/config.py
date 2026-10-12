# -*- coding: utf-8 -*-
"""
SentimentScope 采集服务配置。

配置从环境变量和工作区配置文件读取，采集服务独立管理运行设置。
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from app.paths import SERVICE_ROOT, ENV_FILE
PROJECT_ROOT: Path = SERVICE_ROOT
load_dotenv(ENV_FILE)


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


# ====================== 数据库配置 ======================
DB_DIALECT: str = _env("DB_DIALECT", "mysql")
DB_HOST: str = _env("DB_HOST", "127.0.0.1")
DB_PORT: int = _env_int("DB_PORT", 3306)
DB_USER: str = _env("DB_USER", "root")
DB_PASSWORD: str = _env("DB_PASSWORD", "root")
DB_NAME: str = _env("DB_NAME", "media_crawler")
DB_CHARSET: str = _env("DB_CHARSET", "utf8mb4")

# ====================== 爬虫 LLM 配置（话题提取用） ======================
CRAWLER_LLM_API_KEY: Optional[str] = os.getenv("CRAWLER_LLM_API_KEY")
CRAWLER_LLM_BASE_URL: Optional[str] = os.getenv("CRAWLER_LLM_BASE_URL")
CRAWLER_LLM_MODEL_NAME: str = _env("CRAWLER_LLM_MODEL_NAME", "deepseek-chat")

# ====================== 新闻 API 配置 ======================
NEWS_API_BASE_URL: str = _env("NEWS_API_BASE_URL", "https://newsnow.busiyi.world")

# ====================== 爬取参数默认值 ======================
DEFAULT_MAX_KEYWORDS: int = _env_int("CRAWLER_MAX_KEYWORDS", 5)
DEFAULT_MAX_NOTES: int = _env_int("CRAWLER_MAX_NOTES", 20)
DEFAULT_LOGIN_TYPE: str = _env("CRAWLER_LOGIN_TYPE", "qrcode")
CRAWLER_HEADLESS: bool = _env("CRAWLER_HEADLESS", "False") == "True"
CRAWLER_ENABLE_CDP_MODE: bool = _env("CRAWLER_ENABLE_CDP_MODE", "False") == "True"
CRAWLER_DISABLE_SSL_VERIFY: bool = _env("CRAWLER_DISABLE_SSL_VERIFY", "False") == "True"

# 支持的全部平台
SUPPORTED_PLATFORMS: list[str] = ["xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"]
