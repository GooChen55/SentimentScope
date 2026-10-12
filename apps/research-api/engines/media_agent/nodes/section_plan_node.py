"""MediaAgent 研究蓝图节点：基于研究主题与可用搜索工具，规划媒体侧五维搜索策略。"""

import json
from typing import Any

from langchain_core.prompts import PromptTemplate
from loguru import logger

from engines.common.nodes.base_node import BaseNode
from engines.contracts.dimensions import DIMENSIONS, get_media_dimensions
from engines.media_agent.web_search.schemas import SearchTool
from engines.media_agent.prompts import PLAN_SYSTEM_PROMPT, PLAN_USER_PROMPT_TEMPLATE
from engines.media_agent.schemas import MediaResearchPlan
from engines.media_agent.state import MediaSection, MediaState

SEARCH_TOOL_DESCRIPTIONS: dict[SearchTool, str] = {
    "comprehensive_search": "综合搜索,适合全面理解事件、原因、影响和多来源报道。",
    "source_search": "溯源检索,适合获取可核查的网页出处、原始媒体标题和广泛的表面事实。",
    "realtime_search": "实时追踪,适合获取事件的最新进展、舆情热度变化和最新的传播动态。",
}


class PlanNode(BaseNode):
    """负责将研究主题转换为媒体侧五维搜索计划，确保所有维度对齐并分配合适的搜索工具和提炼检索词。"""

    async def __call__(self, state: MediaState) -> dict[str, Any]:
        query = state["query"]
        logger.info(f"开始进行章节规划，当前研究主题: '{query}'...")

        # 1. 构建LLM所需的用户提示词
        user_prompt = self._build_plan_prompt(query)

        # 2. 调用LLM生成报告章节结构化大纲
        plan: MediaResearchPlan = await self.context.llm_client.generate_object(
            PLAN_SYSTEM_PROMPT, user_prompt, MediaResearchPlan
        )

        # 3. 将LLM生成的报告章节大纲映射为五章节对象列表
        sections = self._generate_media_section(plan)

        # 4. 返回五章节对应列表
        section_keys = ", ".join(s.get("section_key", "") for s in sections)
        logger.info(f"章节规划完成，共规划 {len(sections)} 个章节信息，包含: {section_keys}")
        return {"sections": sections}

    def _build_plan_prompt(self, query: str) -> str:
        # 1. 获取提示词模板所需的数据变量
        fixed_dimensions = get_media_dimensions()
        available_tools = [
            {"name": tool, "description": description}
            for tool, description in SEARCH_TOOL_DESCRIPTIONS.items()
        ]

        # 2. 填充提示词模板并返回
        return PromptTemplate.from_template(PLAN_USER_PROMPT_TEMPLATE).format(
            research_topic=query,
            fixed_dimensions=json.dumps(fixed_dimensions, ensure_ascii=False, indent=2),
            available_tools=json.dumps(available_tools, ensure_ascii=False, indent=2),
        )

    def _generate_media_section(self, plan: MediaResearchPlan) -> list[MediaSection]:
        media_sections: list[MediaSection] = []

        # 1. 以固定的五维度作为基准遍历
        for dimension in DIMENSIONS.values():

            # 2. 按需查找匹配的LLM章节结果
            llm_section = next(
                (section for section in plan.sections if
                 section.section_key and section.section_key.strip() == dimension.key),
                None
            )

            # 3. 确定最终的章节信息
            if llm_section:
                # 3.1 如果找到了，使用llm生成的标题、目标、搜索工具和专属搜索词列表
                goals = [g.strip() for g in llm_section.goal_analysis_points if g.strip()]
                title = llm_section.title.strip()
                search_tool = llm_section.search_tool
                search_keywords = [k.strip() for k in llm_section.search_keywords if k.strip()]
            else:
                # 3.2 如果没找到，llm把维度漏掉，用默认值
                goals = [dimension.media_goal]
                title = dimension.title
                search_tool = "comprehensive_search"
                search_keywords = [dimension.title]

            # 4. 构建MediaSection
            media_sections.append(MediaSection(
                title=title,
                goal=goals,
                search_tool=search_tool,
                search_keywords=search_keywords,
                section_key=dimension.key,
            ))

        return media_sections
