"""  热度评分权重 热度召回时间范围"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

HotRecallPeriod = Literal["24h", "week", "year"]

ENGAGEMENT_METRICS = {
    "likes": "like",
    "comments": "comment",
    "shares": "share",
    "collects": "collect",
    "replies": "reply",
}


@dataclass
class HotScoreWeights:
    shares: float = 5.0
    comments: float = 4.0
    replies: float = 3.0
    collects: float = 2.0
    likes: float = 1.0


def hot_recall_start_time(time_period: HotRecallPeriod) -> datetime:
    days_by_period = {"24h": 1, "week": 7, "year": 365}
    return datetime.now() - timedelta(days=days_by_period[time_period])
