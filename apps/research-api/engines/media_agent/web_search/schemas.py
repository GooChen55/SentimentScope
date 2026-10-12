"""MediaAgent Web 搜索的强类型领域模型。"""

from dataclasses import dataclass, field
from typing import Literal

SearchTool = Literal["comprehensive_search", "source_search", "realtime_search"]
SearchProvider = Literal["anspire", "bocha", "tavily"]


@dataclass(frozen=True, slots=True)
class WebpageResult:
    """网页搜索结果"""
    title: str
    url: str
    content: str
    date: str


@dataclass(frozen=True, slots=True)
class SearchProviderResponse:
    """统一搜索提供上响应数据"""
    query: str
    provider: SearchProvider
    webpages: list[WebpageResult] = field(default_factory=list)
