"""Tavily Web 搜索 Provider。"""

from typing import Any

from engines.contracts.config import get_settings
from engines.media_agent.web_search.base import BaseSearchClient
from engines.media_agent.web_search.schemas import (
    SearchProviderResponse,
    WebpageResult,
)
from engines.common.runtime.call_retry import with_retry


class TavilySearchClient(BaseSearchClient):

    def __init__(self) -> None:
        super().__init__()
        self.api_key = get_settings().TAVILY_API_KEY
        self.base_url = "https://api.tavily.com/search"
        self._headers = self.build_request_headers(self.api_key, accept="application/json")

    async def comprehensive_search(self, query: str) -> SearchProviderResponse:
        return await self._execute_search(query=query, max_results=10, search_depth="advanced")

    async def source_search(self, query: str) -> SearchProviderResponse:
        return await self._execute_search(query=query, max_results=5, search_depth="basic")

    async def realtime_search(self, query: str) -> SearchProviderResponse:
        # 1. 强制使用 news 话题，这是触发时间范围过滤的前提
        # 2. 移除 social_sources，因为 Tavily 不支持该参数
        return await self._execute_search(
            query=f"{query} 最新进展",
            max_results=5,
            time_range="week",
            topic="news"  # 必须是 news，general 模式经常忽略时间窗口
        )
    @with_retry
    async def _execute_search(
            self,
            query: str,
            max_results: int,
            search_depth: str | None = None,
            time_range: str | None = None,
            topic: str = "general",  # 增加 topic 参数
    ) -> SearchProviderResponse:
        payload: dict[str, object] = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth or "basic",
            "topic": topic,  # 动态传入
        }
        if time_range:
            payload["time_range"] = time_range
            payload["days"] = 7  # 显式指定天数，Tavily 有时更认这个参数

        response = await self.send_request(
            "POST",
            self.base_url,
            {"headers": self._headers, "json": payload},
        )
        return self._process_response(response, query)

    @staticmethod
    def _process_response(response_dict: dict[str, Any], query: str) -> SearchProviderResponse:
        results = response_dict.get("results", [])

        webpages: list[WebpageResult] = []
        for result in results:
            if not isinstance(result, dict):
                continue
            webpages.append(
                WebpageResult(
                    title=result.get("title"),
                    url=result.get("url"),
                    content=result.get("content"),
                    date=result.get("published_date"),
                )
            )

        return SearchProviderResponse(
            query=query,
            provider="tavily",
            webpages=webpages,
        )


if __name__ == "__main__":
    import asyncio


    async def main() -> None:
        client = TavilySearchClient()
        test_query = "高考 难不难"
        print(f"测试检索词: '{test_query}'\n")

        # 1. 测试综合检索 (Top 30)
        print("1. comprehensive_search (全景检索)")
        comp_res = await client.comprehensive_search(test_query)
        print(f"成功召回数据: {len(comp_res.webpages)} 条")
        for i, page in enumerate(comp_res.webpages[:5], 1):
            print(f"[{i}]---标题: {page.name}")
            print(f"        链接: {page.url}")
        print("-" * 50)

        # 2. 测试溯源检索
        print("2. source_search (溯源检索)")
        source_res = await client.source_search(test_query)
        print(f"成功召回数据: {len(source_res.webpages)} 条")
        for i, page in enumerate(source_res.webpages[:5], 1):
            print(f"[{i}]---标题: {page.name}")
            print(f"        链接: {page.url}")
        print("-" * 50)

        # 3. 测试实时追踪检索
        print("3. realtime_search (实时追踪)")
        realtime_res = await client.realtime_search(test_query)
        print(f"成功召回数据: {len(realtime_res.webpages)} 条")
        for i, page in enumerate(realtime_res.webpages[:5], 1):
            print(f"[{i}]---标题: {page.name}")
            print(f"        时间: {page.date}")
            print(f"        链接: {page.url}")


    asyncio.run(main())
