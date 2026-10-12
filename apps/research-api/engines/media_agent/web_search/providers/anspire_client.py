"""Anspire Web 搜索 Provider。"""

import datetime
from typing import Any

from engines.contracts.config import get_settings
from engines.media_agent.web_search.base import BaseSearchClient
from engines.media_agent.web_search.schemas import (
    SearchProviderResponse,
    WebpageResult,
)

# AUTHORITATIVE_SOURCES = "gov.cn,xinhuanet.com,news.cctv.com,thepaper.cn"
AUTHORITATIVE_SOURCES = "news.cctv.com"
SOCIAL_SOURCES = "weibo.com,zhihu.com,toutiao.com"


class AnspireSearchClient(BaseSearchClient):

    def __init__(self) -> None:
        super().__init__()
        self.api_key = get_settings().ANSPIRE_API_KEY
        self.base_url = get_settings().ANSPIRE_BASE_URL
        self._headers = self.build_request_headers(self.api_key, accept="application/json")

    async def comprehensive_search(self, query: str) -> SearchProviderResponse:

        return await self._execute_search(query=query, top_k=15, insite="")

    async def source_search(self, query: str) -> SearchProviderResponse:
        enhanced_query = f"{query} 通报 OR 回应 OR 官方"   # 增强
        return await self._execute_search(query=enhanced_query, top_k=10, insite=AUTHORITATIVE_SOURCES)

    async def realtime_search(self, query: str) -> SearchProviderResponse:
        to_time = datetime.datetime.now()
        from_time = to_time - datetime.timedelta(weeks=1)
        enhanced_query = f"{query} 最新 OR 热搜"
        return await self._execute_search(
            query=enhanced_query,
            top_k=10,
            insite=SOCIAL_SOURCES,
            from_time=from_time.strftime("%Y-%m-%d %H:%M:%S"),
            to_time=to_time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    async def _execute_search(
            self,
            query: str,
            top_k: int,
            insite: str,
            from_time: str = "",
            to_time: str = "",
    ) -> SearchProviderResponse:
        params = {
            "query": query,
            "top_k": top_k,
            "Insite": insite,
            "FromTime": from_time,
            "ToTime": to_time,
        }
        response = await self.send_request(
            "GET",
            self.base_url,
            {"headers": self._headers, "params": params},
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
                    date=result.get("date"),
                )
            )

        return SearchProviderResponse(
            query=query,
            provider="anspire",
            webpages=webpages,
        )


if __name__ == "__main__":
    import asyncio


    async def main() -> None:
        client = AnspireSearchClient()
        test_query = "高考 难不难"
        print(f"测试检索词: '{test_query}'\n")

        # 1. 测试综合检索 (Top 30)
        print("1. comprehensive_search (全景检索)")
        comp_res = await client.comprehensive_search(test_query)
        print(f"成功召回数据: {len(comp_res.webpages)} 条")
        for i, page in enumerate(comp_res.webpages[:5], 1):
            print(f"[{i}]---标题: {page.content}")
            print(f"        链接: {page.url}")
        print("-" * 50)

        # 2. 测试溯源检索
        print("2. source_search (溯源检索)")
        source_res = await client.source_search(test_query)
        print(f"成功召回数据: {len(source_res.webpages)} 条")
        for i, page in enumerate(source_res.webpages[:5], 1):
            print(f"[{i}]---标题: {page.content}")
            print(f"        链接: {page.url}")
        print("-" * 50)

        # 3. 测试实时追踪检索
        print("3. realtime_search (实时追踪)")
        realtime_res = await client.realtime_search(test_query)
        print(f"成功召回数据: {len(realtime_res.webpages)} 条")
        for i, page in enumerate(realtime_res.webpages[:5], 1):
            print(f"[{i}]---标题: {page.content}")
            print(f"        时间: {page.date}")
            print(f"        链接: {page.url}")


    asyncio.run(main())
