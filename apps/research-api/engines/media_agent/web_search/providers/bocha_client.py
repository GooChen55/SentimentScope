"""Bocha Web 搜索 Provider。"""

import json
from loguru import logger

from engines.contracts.config import get_settings
from engines.media_agent.web_search.base import BaseSearchClient
from engines.media_agent.web_search.schemas import (
    SearchProviderResponse,
    WebpageResult,
)


class BochaSearchClient(BaseSearchClient):

    def __init__(self) -> None:
        super().__init__()
        self.api_key = get_settings().BOCHA_API_KEY
        self.base_url = get_settings().BOCHA_BASE_URL
        self._headers = self.build_request_headers(self.api_key, accept="*/*")

    async def comprehensive_search(self, query: str) -> SearchProviderResponse:
        return await self._execute_search(query=query, count=15)

    async def source_search(self, query: str) -> SearchProviderResponse:
        return await self._execute_search(query=query, count=10)

    async def realtime_search(self, query: str) -> SearchProviderResponse:
        return await self._execute_search(
            query=query,
            count=5,
            freshness="oneWeek",
        )

    async def _execute_search(
            self,
            query: str,
            count: int,
            freshness: str | None = None,
    ) -> SearchProviderResponse:

        payload: dict[str, object] = {
            "stream": False,
            "query": query,
            "count": count,
        }
        if freshness is not None:
            payload["freshness"] = freshness

        response = await self.send_request(
            "POST",
            self.base_url,
            {"headers": self._headers, "json": payload},
        )
        return self._process_response(response, query)

    @staticmethod
    def _process_response(response_dict: dict[str, object], query: str) -> SearchProviderResponse:

        webpages: list[WebpageResult] = []
        raw_messages = response_dict.get("messages", [])
        messages = raw_messages if isinstance(raw_messages, list) else []

        for message in messages:
            if (
                    not isinstance(message, dict)
                    or message.get("role") != "assistant"
                    or message.get("type") != "source"
                    or message.get("content_type") != "webpage"
            ):
                continue
            raw_content = message.get("content")
            if not isinstance(raw_content, str):
                continue
            try:
                content = json.loads(raw_content)
            except json.JSONDecodeError as exc:
                logger.warning(f"[media] Bocha 网页来源解析失败: {exc}")
                continue

            results = content.get("value", [])
            for item in results:
                if not isinstance(item, dict):
                    continue
                webpages.append(
                    WebpageResult(
                        title=item.get("name"),
                        url=item.get("url"),
                        content=item.get("snippet"),
                        date=item.get("dateLastCrawled")
                    )
                )

        return SearchProviderResponse(
            query=query,
            provider="bocha",
            webpages=webpages,
        )


if __name__ == "__main__":
    import asyncio


    async def main() -> None:
        client = BochaSearchClient()
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
