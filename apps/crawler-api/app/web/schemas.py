# -*- coding: utf-8 -*-
"""Pydantic 模型定义"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ====================== 枚举 ======================

class TaskType(str, Enum):
    broad_topic = "broad_topic"
    deep_sentiment = "deep_sentiment"
    pipeline = "pipeline"
    web_page = "web_page"


class TaskStatus(str, Enum):
    pending = "pending"         # 准备中
    running = "running"         # 运行中
    completed = "completed"     # 已完成
    failed = "failed"           # 完成失败
    stopping = "stopping"       # 停止中
    stopped = "stopped"         # 已停止


# ====================== 数据库初始化 ======================

class DbInitRequest(BaseModel):
    host: str = Field(default="127.0.0.1", description="数据库主机地址")
    port: int = Field(default=3306, description="数据库端口")
    user: str = Field(default="root", description="数据库用户名")
    password: str = Field(default="root", description="数据库密码")
    db_name: str = Field(default="media_crawler", description="数据库名")
    charset: str = Field(default="utf8mb4", description="字符集")


class DbInitResponse(BaseModel):
    success: bool
    message: str
    tables_created: List[str] = []
    elapsed_seconds: float = 0
    error: Optional[str] = None


# ====================== 爬虫请求 ======================

class CrawlStartRequest(BaseModel):
    target_date: Optional[str] = Field(default=None, description="目标日期 YYYY-MM-DD，默认今天")
    platforms: Optional[List[str]] = Field(default=None, description="平台列表，不选则默认全平台")
    sources: Optional[List[str]] = Field(default=None, description="新闻源列表")
    max_keywords: Optional[int] = Field(default=None, ge=1, le=50, description="最大关键词数量")
    max_notes: Optional[int] = Field(default=None, ge=1, le=200, description="每关键词最大爬取笔记数")
    login_type: Optional[str] = Field(default=None, description="登录方式: qrcode / phone / cookie")
    keywords: List[str] = Field(default_factory=list, max_length=50)
    urls: List[str] = Field(default_factory=list, max_length=10)
    topic: str = Field(default="", max_length=255)


# ====================== 任务状态 ======================

class TaskProgress(BaseModel):
    stage: Optional[str] = None              # 任务阶段
    current_platform: Optional[str] = None   # 任务所在平台
    platforms_completed: List[str] = []      #
    keywords_total: int = 0                  # 关键词数量
    keywords_processed: int = 0              # 处理过的关键词
    notes_collected: int = 0                 # 收集的消息数
    comments_collected: int = 0
    elapsed_seconds: float = 0               # 过去的时间


class TaskInfo(BaseModel):
    task_id: str                        # 任务ID
    type: TaskType                      # 任务类型
    status: TaskStatus                  # 任务状态
    created_at: str                     # 任务创建时间
    started_at: Optional[str] = None    # 任务开始时间
    ended_at: Optional[str] = None      # 任务结束时间
    config: Dict[str, Any] = {}         # 任务用的配置
    progress: TaskProgress = Field(default_factory=TaskProgress) # 任务处理过程进度
    result: Optional[Dict[str, Any]] = None  # 任务结果
    error: Optional[str] = None              # 任务错误信息


class TaskSummary(BaseModel):
    task_id: str
    type: TaskType
    status: TaskStatus
    created_at: str
    ended_at: Optional[str] = None
    error: Optional[str] = None


class TaskListResponse(BaseModel):
    active: Optional[TaskInfo] = None
    recent: List[TaskSummary] = []


# ====================== 平台与配置 ======================

class PlatformInfo(BaseModel):
    value: str
    label: str
    description: str


class ConfigOptions(BaseModel):
    login_types: List[Dict[str, str]]
    default_max_keywords: int
    default_max_notes: int
    default_login_type: str
    supported_platforms: List[PlatformInfo]


# ====================== 新闻 ======================

class NewsItem(BaseModel):
    news_id: str
    source_platform: str
    title: str
    url: str
    rank_position: int
    crawl_date: str


class NewsResponse(BaseModel):
    date: str
    total: int
    news: List[NewsItem]


class NewsSource(BaseModel):
    value: str
    label: str


# ====================== 话题 ======================

class TopicSummary(BaseModel):
    extract_date: str
    keywords_count: int
    summary: Optional[str] = None
    keywords: List[str] = []


class TopicDetail(BaseModel):
    extract_date: str
    keywords: List[str]
    summary: Optional[str] = None
    created_at: Optional[str] = None


# ====================== 仪表盘 ======================

class DashboardStats(BaseModel):
    news_stats: List[Dict[str, Any]] = []
    topics_stats: List[Dict[str, Any]] = []
    last_crawl: Optional[Dict[str, Any]] = None


# ====================== 通用响应 ======================

class HealthResponse(BaseModel):
    status: str
    db_connected: bool


class TaskCreatedResponse(BaseModel):
    task_id: str
    status: str = "pending"
    type: TaskType
    created_at: str
