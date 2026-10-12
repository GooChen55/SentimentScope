"""Web 搜索客户端工厂"""
from typing import Optional

from engines.media_agent.web_search.base import BaseSearchClient
from engines.media_agent.web_search.providers.anspire_client import AnspireSearchClient
from engines.media_agent.web_search.providers.bocha_client import BochaSearchClient
from engines.media_agent.web_search.providers.tavily_client import TavilySearchClient
from engines.media_agent.web_search.schemas import SearchProviderResponse


class WebSearchClient:
    CLIENT_MAPPING: dict[str, type[BaseSearchClient]] = {
        "AnspireAPI": AnspireSearchClient,
        "BochaAPI": BochaSearchClient,
        "TavilyAPI": TavilySearchClient,
    }

    def __init__(self, search_switch: Optional[str] | None = None) -> None:
        client_class = self.CLIENT_MAPPING.get(search_switch, TavilySearchClient)
        self._client: BaseSearchClient = client_class()

    async def comprehensive_search(self, query: str) -> SearchProviderResponse:
        return await self._client.comprehensive_search(query)

    async def source_search(self, query: str) -> SearchProviderResponse:
        return await self._client.source_search(query)

    async def realtime_search(self, query: str) -> SearchProviderResponse:
        return await self._client.realtime_search(query)
