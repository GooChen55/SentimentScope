"""
新闻模块 — 新闻 API 获取和存储编排。
"""

from app.broad_topic.news.fetcher import NewApiFetcher, SOURCE_NAMES
from app.broad_topic.news.collector import NewsCollector

__all__ = ["NewsCollector", "NewApiFetcher", "SOURCE_NAMES"]
