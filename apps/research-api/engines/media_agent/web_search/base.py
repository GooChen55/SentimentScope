"""搜索客户端基类"""

import httpx

from abc import ABC, abstractmethod
from typing import TypedDict, Any

from engines.media_agent.web_search.schemas import SearchProviderResponse


class HttpRequestOptions(TypedDict, total=False):
    """统一 HTTP 模板方法的请求参数选项。"""

    headers: dict[str, str]
    params: dict[str, Any]
    json: dict[str, Any]


class BaseSearchClient(ABC):
    """定义搜索能力基类"""

    def __init__(self):
        pass

    @staticmethod
    def build_request_headers(
        api_key: str,
        *,
        accept: str = "application/json"
    ) -> dict[str, str]:
        """统一构造 Provider 共用的 Bearer JSON 请求头。"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": accept,
        }
        return headers

    async def send_request(
            self,
            method: str,
            url: str,
            kwargs: HttpRequestOptions,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=kwargs.get("headers"),
                params=kwargs.get("params"),
                json=kwargs.get("json"),
            )
            data = response.json()
        return data

    @abstractmethod
    async def comprehensive_search(self, query: str) -> SearchProviderResponse:
        """综合搜索:获取关于某个主题的全面信息。"""

    @abstractmethod
    async def source_search(self, query: str) -> SearchProviderResponse:
        """溯源追踪搜索:只获取可核查网页结果。"""

    @abstractmethod
    async def realtime_search(self, query: str) -> SearchProviderResponse:
        """实时追踪搜索:获取最新报道与传播动态。"""
