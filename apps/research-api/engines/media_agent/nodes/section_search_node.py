"""MediaAgent 搜索节点：基于多维度组合词检索并构建公共证据池。"""

from typing import Any
from loguru import logger

from engines.common.nodes.base_node import BaseNode
from engines.contracts.evidence.models import EvidenceRecord
from engines.media_agent.state import MediaState
from engines.common.io.evidence_io import save_evidence


class SearchNode(BaseNode):
    """遍历各章节，将原始 Query 与专门提炼的关键词组合，使用专属工具发起检索，最终去重聚合为全局证据"""

    async def __call__(self, state: MediaState) -> dict[str, Any]:
        query = state.get("query", "")
        sections = state.get("sections", [])
        search_evidence_records = []
        seen_keys = set()
        executed_queries = []
        from engines.media_agent.local_documents import search_local_documents
        try:
            for record in await search_local_documents(query):
                seen_keys.add(record.id)
                search_evidence_records.append(record)
        except Exception as exc:
            logger.warning(f"本地网页证据读取失败：{type(exc).__name__}")

        # 1. 遍历每个章节，构建维度专属查询词并使用对应的工具
        for section in sections:
            tool = section.get("search_tool", "comprehensive_search")

            # 2. 组合：全局主题 + 专门为搜索引擎优化的子关键词
            search_query = f"{query} {' '.join(section.get('search_keywords') or [])}".strip()

            # 3. 根据工具名执行检索工具
            records: list[EvidenceRecord] = await self.context.execute_search(tool, search_query)
            executed_queries.append(f"[{tool}] {search_query}")

            # 4. 结果聚合并去重，防止不同词召回了同一个新闻网页导致冗余
            for record in records:
                unique_key = record.id  # 兼容不同 record 的唯一键
                if unique_key not in seen_keys:
                    seen_keys.add(unique_key)
                    search_evidence_records.append(record)

        # 5. 日志打印
        logger.info(
            f"[media] 全局多维度检索完成，共执行 {len(sections)} 次独立检索。\n"
            f"五个章节使用的最终搜索词:\n" +
            "\n".join([f"  - {query}" for query in executed_queries]) +
            f"\n共获取 {len(search_evidence_records)} 条去重后的原始证据。"
        )

        # 6. 写入全局状态，供下游的 SummarizeNode 消费
        save_evidence('media', search_evidence_records)
        return {"search_evidence_records": search_evidence_records}
