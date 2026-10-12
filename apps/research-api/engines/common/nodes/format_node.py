"""最终报告格式化节点: 整合章节内容为最终交付文本。"""

import json
from typing import Any
from loguru import logger

from langchain_core.prompts import PromptTemplate

from engines.common.nodes.base_node import BaseNode
from engines.common.llm.llm_output import clean_markdown_text
from engines.contracts.roles import ROLE_INFOS, RoleInfo
from engines.insight_agent.state import InsightState




class FormatReportNode(BaseNode):
    """负责将已总结的章节列表整合为一份完整的、格式优美的研究报告。"""

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        # 1. 提取基础信息以及构建日志
        role = state.get("role", "insight")
        agent_info = ROLE_INFOS.get(role)
        agent_name = agent_info.display_name if agent_info else role
        query = state.get("query", "未知主题")
        sections = state.get("sections", [])

        # 首行日志：明确执行人、主题与任务量
        logger.info(f"开始执行最终报告排版 [{agent_name}]，关于舆论话题: '{query}'，共 {len(sections)} 个章节等待整合...")

        # 2. 准备报告内容
        report_context = json.dumps(
            [{"title": section.get("title"), "body": section.get("body")} for section in sections],
            ensure_ascii=False,
        )

        # 3. 尝试执行 LLM 排版 (将 query 和 context 透传进去用于渲染 prompt)
        md_report = await self._generate_final_report(agent_info, report_context, query)

        # 4. 如果 LLM 返回空或失败，执行兜底拼接
        if not md_report:
            logger.warning(f"[{role}] LLM 排版失败或返回为空，执行程序化兜底拼接。")
            md_report = _fallback_report(agent_name, query, sections)

        logger.info(f"报告排版完成 [{agent_name}]，最终交付文本共计 {len(md_report)} 字。")

        return {"final_report": md_report, "report_title": query}

    async def _generate_final_report(self, agent_info: RoleInfo, report_context: str, query: str) -> str | None:
        """调用 LLM 进行报告生成，若失败返回 None"""

        # 1. 实例化模板
        system_prompt = PromptTemplate.from_template(agent_info.format_system_prompt).format(
            research_topic=query,
            report_context=report_context
        )
        try:
            # 2. 调用LLM
            raw_text = await self.context.llm_client.generate_text(
                system_prompt=system_prompt,
                user_prompt="请严格按照上述要求和输入数据，输出最终的 Markdown 报告正文。"
            )
            cleaned_text = clean_markdown_text(raw_text)
            return cleaned_text if cleaned_text else None
        except Exception as exc:
            logger.error(f"LLM 报告生成失败: {exc}")
            return None


def _fallback_report(agent_name: str, query: str, sections: list[dict[str, Any]]) -> str:
    lines = [f"# {agent_name} 分析舆论话题:{query}\n"]
    for idx, section in enumerate(sections, 1):
        lines.append(f"\n## {idx}. {section.get('title')}\n\n{section.get('body')}\n")
    return "".join(lines)
