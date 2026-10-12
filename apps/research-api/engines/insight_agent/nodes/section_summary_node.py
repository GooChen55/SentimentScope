"""InsightAgent 章节总结节点：基于已调拨的证据进行分析撰写。"""

import json
import time
from typing import Any
from loguru import logger
from engines.common.nodes.base_node import BaseNode
from engines.insight_agent.state import InsightState, InsightSection
from engines.insight_agent.evidence_processor  import SectionEvidencePack,generate_section_evidence_pack,dispatch_section_ready_event
from engines.insight_agent.prompts import SUMMARY_SYSTEM_PROMPT, SUMMARY_USER_PROMPT_TEMPLATE
from engines.common.llm.llm_output import sanitize_markdown as clean_markdown_text

from langchain_core.prompts import PromptTemplate

FALLBACK_BODY = "该维度未有相关内容，本章节暂不做延展"


class SectionSummarizeNode(BaseNode):
    """负责将特定维度的证据转化为结构化分析报告，并发布各章节就绪事件。"""

    async def __call__(self, state: InsightState) -> dict[str, Any]:

        # 1. 获取当前节点状态与游标
        section_index = state.get("cursor", 0)
        sections = list(state.get("sections", []))
        section_evidence_records = list(state.get("section_evidence_records", []))

        # 防御性检查：防止游标溢出
        if section_index >= len(sections):
            return {"sections": sections}

        # 2. 提取当前要处理章节与对应证据记录
        section: InsightSection = sections[section_index]
        logger.info(
            f"开始生成章节摘要 [{section_index + 1}/{len(sections)}]: '{section.get('title')}' ({section.get('section_key')})...")

        records = section_evidence_records[section_index] if section_index < len(section_evidence_records) else []

        # 3. 构建章节证据包并同步元数据
        pack = generate_section_evidence_pack(state["query"], records)
        section["hit_count"] = pack.evidence_count
        section["evidence_strength"] = pack.strength

        # 4. 执行分析摘要生成分支
        if pack.evidence_count <= 0:
            logger.info(f"[insight私域检索专家] 章节 {section.get('title')!r} 证据包为空，跳过生成。")
            section["body"] = FALLBACK_BODY
        else:
            start = time.time()
            section["body"] = await self._generate_section_body(section, pack)
            elapsed = time.time() - start
            logger.info(f'[insight私域检索专家] 章节写作章节:{section.get("section_key")} 耗时:{elapsed:.3f} 秒')

        # 5. 发布章节就绪事件，并推进游标
        dispatch_section_ready_event(state, section_index, section)

        sections[section_index] = section

        logger.info(f"章节摘要生成完成: '{section.get('title')}' ({section.get('section_key')})")
        return {"sections": sections, "cursor": section_index + 1}

    async def _generate_section_body(self, section: InsightSection, pack: SectionEvidencePack) -> str:
        # 1. 封装分析目标
        section_plan = {
            "title": section.get("title", ""),
            "section_key": section.get("section_key", ""),
            "expected_analysis_points": section.get("goal", []),
        }

        # 2. 填充模板并生成内容
        prompt = PromptTemplate.from_template(SUMMARY_USER_PROMPT_TEMPLATE).format(
            used_query=pack.used_query,
            section_plan=json.dumps(section_plan, ensure_ascii=False, indent=2),
            search_evidence_results="\n\n".join(pack.evidence_source_blocks),
            evidence_strength=pack.strength
        )

        try:
            body = await self.context.llm_client.generate_text(SUMMARY_SYSTEM_PROMPT, prompt)
            return clean_markdown_text(body)
        except Exception as exc:
            logger.error(f"[insight私域检索专家] 章节写作 LLM 异常: {exc}")
            return FALLBACK_BODY
