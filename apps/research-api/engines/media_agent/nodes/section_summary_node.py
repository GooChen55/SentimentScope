"""MediaAgent 章节总结节点：基于全局搜索证据池进行分析撰写。"""

import json
import time
from typing import Any

from loguru import logger
from engines.common.nodes.base_node import BaseNode
from engines.common.llm.llm_output import clean_markdown_text
from engines.media_agent.evidence_processor import (
    dispatch_section_ready_event,
    generate_section_evidence_pack,
)
from engines.media_agent.prompts import SUMMARY_USER_PROMPT_TEMPLATE, SUMMARY_SYSTEM_PROMPT
from engines.media_agent.state import MediaSection, MediaState
from engines.media_agent.evidence_processor import SectionEvidencePack

from langchain_core.prompts import PromptTemplate

FALLBACK_BODY = "【数据缺口】该维度未在可用数据源中检索到相关内容,本章节暂无分析结论。"


class SectionSummarizeNode(BaseNode):
    """负责将全局搜索证据转化为特定章节的分析报告,并发布各章节就绪事件。"""

    async def __call__(self, state: MediaState) -> dict[str, Any]:

        # 1. 获取当前节点状态与游标
        cursor = state.get("cursor", 0)
        sections = list(state.get("sections"))

        # 防御性检查:防止游标溢出
        if cursor >= len(sections):
            return {"sections": sections}

        # 2. 提取当前要处理的章节
        section: MediaSection = sections[cursor]
        logger.info(
            f"开始生成章节摘要 [{cursor + 1}/{len(sections)}]: '{section.get('title')}' ({section.get('section_key')})..."
        )

        # 3. 获取搜索证据
        query = state.get("query")
        records = state.get("search_evidence_records", [])

        # 3. 构建章节证据包并同步元数据
        evidence_pack = generate_section_evidence_pack(
            records=records[:8],
            used_query=query
        )

        section["hit_count"] = evidence_pack.evidence_count
        section["evidence_strength"] = evidence_pack.evidence_strength

        # 4. 执行分析摘要生成分支
        if evidence_pack.evidence_count <= 0:
            logger.info(f"[media检索专家] 章节 {section.get('title')!r} 证据包为空，跳过生成。")
            section["body"] = FALLBACK_BODY
        else:
            start_time = time.time()
            section["body"] = await self._generate_section_body(section, evidence_pack)
            elapsed = time.time() - start_time
            logger.info(f"[media] 章节写作 section_key={section.get('section_key')} 耗时:{elapsed:.3f} 秒")

        # 5. 发布章节就绪事件,并推进游标
        dispatch_section_ready_event(state, cursor, section)
        sections[cursor] = section
        return {"sections": sections, "cursor": cursor + 1}

    async def _generate_section_body(self, section: MediaSection, pack: SectionEvidencePack) -> str:

        section_plan = {
            "title": section.get("title"),
            "section_key": section.get("section_key"),
            "expected_analysis_points": section.get("goal"),
        }
        user_prompt = PromptTemplate.from_template(SUMMARY_USER_PROMPT_TEMPLATE).format(
            used_query=pack.used_query,
            section_plan=json.dumps(section_plan, ensure_ascii=False, indent=2),
            evidence_strength=pack.evidence_strength,
            search_evidence_results="\n\n".join(pack.evidence_source_blocks),
        )

        try:
            body = await self.context.llm_client.generate_text(
                SUMMARY_SYSTEM_PROMPT, user_prompt
            )
            return clean_markdown_text(body)
        except Exception as exc:
            logger.error(f"[media] 章节写作 LLM 调用失败: {exc}")
            return FALLBACK_BODY
