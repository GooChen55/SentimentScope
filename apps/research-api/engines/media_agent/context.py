"""MediaAgent 全网媒体研究模块：engines/media_agent/context.py。"""

from typing import Callable, get_args
from loguru import logger
import hashlib
from engines.common.llm.llm_client import LLMClient
from engines.common.nodes.base_node import ProgressUpdate
from engines.contracts.evidence.models import EvidenceRecord
from engines.media_agent.web_search.schemas import SearchTool
from engines.media_agent.web_search.factory import WebSearchClient
from engines.media_agent.web_search.schemas import SearchProviderResponse


class MediaContext:
    """media 研究角色实例的依赖容器(Web 搜索)。"""

    def __init__(
            self,
            role: str,
            llm_client: LLMClient,
            output_dir: str,
            progress_callback: Callable[[ProgressUpdate], None] | None = None,
    ) -> None:
        self.role = role
        self.llm_client = llm_client
        self.output_dir = output_dir
        self.progress_callback = progress_callback
        self._web_search_client = WebSearchClient()

    async def execute_search(self, tool_name: SearchTool, query: str) -> list[EvidenceRecord]:

        # 1. 获取校验后的工具
        validated_tool: SearchTool = tool_name if tool_name in get_args(SearchTool) else "comprehensive_search"

        try:
            # 2. 获取搜索结果
            web_response = await self._search_webpage(validated_tool, query)

            # 3. 转换结果并返回
            return self._map_to_evidence_records(web_response, query)

        except Exception as exc:
            logger.error(f"{self.role} 搜索失败 tool={validated_tool} query={query} 异常={exc}")
            return []

    async def _search_webpage(
            self,
            tool_name: SearchTool,
            query: str,
    ) -> SearchProviderResponse:

        match tool_name:
            # 溯源检索
            case "source_search":
                response = await  self._web_search_client.source_search(query)
            # 实时检索
            case "realtime_search":
                response = await  self._web_search_client.realtime_search(query)
            # 综合检索
            case _:
                response = await  self._web_search_client.comprehensive_search(query)

        return response

    def _map_to_evidence_records(
            self,
            response: SearchProviderResponse,
            query: str,
    ) -> list[EvidenceRecord]:
        """转换Web搜索结果对象为证据下游需要记录对象"""

        if response is None:
            return []
        return [
            EvidenceRecord(
                id=_generate_content_hash_id(page.content, page.url),
                platform=response.provider,
                source_table=response.provider,
                source_keyword=query,
                content=page.content,
                published_at=page.date,
                url=page.url,
            )
            for page in response.webpages
        ]


def _generate_content_hash_id(content: str, url: str) -> str:
    raw_key = content + url
    return hashlib.md5(raw_key.encode("utf-8")).hexdigest()
