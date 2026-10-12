# -*- coding: utf-8 -*-
"""
爬虫项目数据库模型。

定义爬虫内部使用的业务表（daily_news、daily_topics）。
内容表（bilibili_video、xhs_note 等）由 MediaCrawler 自己的 ORM 管理。
"""

from datetime import date
from sqlalchemy import BigInteger, Date, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class CrawlRecord(Base):
    __tablename__ = "crawler_record"
    record_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    platform: Mapped[str] = mapped_column(String(32))
    kind: Mapped[str] = mapped_column(String(16))
    remote_id: Mapped[str] = mapped_column(String(255))
    source_table: Mapped[str] = mapped_column(String(64))
    payload: Mapped[str] = mapped_column(Text)
    last_run: Mapped[str] = mapped_column(String(64))
    collected_at: Mapped[int] = mapped_column(BigInteger)

class WebDocument(Base):
    __tablename__ = "crawler_document"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(255))
    published_at: Mapped[str | None] = mapped_column(String(64))
    collected_at: Mapped[int] = mapped_column(BigInteger)
    content_hash: Mapped[str] = mapped_column(String(64))


class DailyNews(Base):
    """每日热点新闻"""
    __tablename__ = "daily_news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    news_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    source_platform: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str | None] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    extra_info: Mapped[str | None] = mapped_column(Text)
    crawl_date: Mapped[date | None] = mapped_column(Date)
    rank_position: Mapped[int | None] = mapped_column(Integer)
    add_ts: Mapped[int | None] = mapped_column(BigInteger)
    last_modify_ts: Mapped[int | None] = mapped_column(BigInteger)


class DailyTopic(Base):
    """每日话题分析"""
    __tablename__ = "daily_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    topic_name: Mapped[str | None] = mapped_column(String(255))
    topic_description: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[str | None] = mapped_column(Text)
    extract_date: Mapped[date | None] = mapped_column(Date)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    news_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_status: Mapped[str] = mapped_column(String(16), default="pending")
    add_ts: Mapped[int | None] = mapped_column(BigInteger)
    last_modify_ts: Mapped[int | None] = mapped_column(BigInteger)
