"""InsightAgent 章节证据调拨节点：将全局证据池中的数据按章节维度路由至对应的上下文。"""

from typing import Any
from loguru import logger

from engines.common.nodes.base_node import BaseNode, ResearchNodeContext
from engines.insight_agent.state import InsightState, InsightSection
from engines.insight_agent.evidence_processor  import EvidencePool, EvidenceRecord,generate_section_records


class SectionAllocationNode(BaseNode):
    """负责将全局证据池中的数据，依据章节维度进行筛选、并分发至各章节的上下文容器中。"""

    def __init__(self, context: ResearchNodeContext) -> None:
        super().__init__(context)

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        logger.info("开始进行章节证据分发【维度筛选】...")
        # 1. 提取全局证据池与已规划的章节列表
        pool: EvidencePool = state["evidence_pool"]
        records = pool.records
        sections: list[InsightSection] = list(state.get("sections", []))

        section_evidence_records: list[list[EvidenceRecord]] = []
        allocation_summary: list[str] = []  # 用于收集日志信息

        # 2. 遍历各章节，根据 section_key 路由匹配的证据记录
        for section in sections:
            section_key = section["section_key"]

            # 3. 筛选并截断符合维度的证据
            section_records = generate_section_records(section_key, records)[:20]

            # 4. 将该章节对应的证据记录存入中间容器
            section_evidence_records.append(section_records)

            # 记录当前章节分配到的数量
            allocation_summary.append(f"{section_key}: {len(section_records)}条")

        # 5. 返回更新后的章节列表与对应的证据分发记录，供下游摘要节点消费
        summary_text = ", ".join(allocation_summary)
        logger.info(f"章节证据调拨完成，分配情况: {summary_text}")
        return {
            "sections": sections,
            "section_evidence_records": section_evidence_records
        }
