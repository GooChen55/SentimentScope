"""InsightAgent 研究蓝图节点：基于舆论主题与证据概览，规划报告章节的结构化大纲。"""

import json
from typing import Any
from loguru import logger

from engines.common.nodes.base_node import BaseNode, ResearchNodeContext
from engines.insight_agent.schemas import InsightResearchPlan
from engines.insight_agent.state import InsightState, InsightSection
from engines.insight_agent.prompts import PLAN_SYSTEM_PROMPT, PLAN_USER_PROMPT_TEMPLATE
from engines.insight_agent.evidence_processor  import EvidencePool,generate_plan_overview
from engines.contracts.dimensions import get_insight_dimensions, DIMENSIONS


from langchain_core.prompts import PromptTemplate


class SectionPlanNode(BaseNode):
    """负责将舆论主题转换为标准化的报告章节大纲，确保所有维度分析点对齐。"""

    def __init__(self, context: ResearchNodeContext) -> None:
        super().__init__(context)

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        logger.info(f"开始进行章节规划，当前研究主题: '{state.get('query')}'...")
        # 1. 构建LLM所需的用户提示词
        plan_user_prompt = self._build_plan_prompt(state)

        # 2. 调用LLM生成报告章节结构化大纲
        plan: InsightResearchPlan = await self.context.llm_client.generate_object(
            PLAN_SYSTEM_PROMPT, plan_user_prompt, InsightResearchPlan
        )

        # 3. 将LLM生成的报告章节大纲映射为五章节对象列表
        sections = self.generate_insight_section(plan)

        # 4. 返回五章节对应列表
        section_keys = ", ".join(s.get("section_key", "") for s in sections)
        logger.info(f"章节规划完成，共规划 {len(sections)} 个章节信息，包含: {section_keys}")
        return {"sections": sections}

    def _build_plan_prompt(self, state: InsightState) -> str:

        # 1. 获取提示词模板所需的数据变量
        pool: EvidencePool = state["evidence_pool"]
        research_topic = state["query"]
        fixed_dimensions_data = get_insight_dimensions()
        plan_overview_evidence = generate_plan_overview(pool)

        # 2. 填充提示词模板数据变量
        prompt_template = PromptTemplate.from_template(PLAN_USER_PROMPT_TEMPLATE)

        # 3. 序列化数据并返回提示词prompt
        return prompt_template.format(
            research_topic=research_topic,
            fixed_dimensions=json.dumps(fixed_dimensions_data, ensure_ascii=False, indent=2),
            evidence_overview=json.dumps(plan_overview_evidence, ensure_ascii=False, indent=2),
        )

    def generate_insight_section(self, plan: InsightResearchPlan) -> list[InsightSection]:
        insight_sections: list[InsightSection] = []

        # 1. 以固定的五维度作为基准遍历
        for dimension in DIMENSIONS.values():

            # 2. 按需查找匹配的LLM章节结果
            llm_section = next(
                (section for section in plan.sections if
                 section.section_key and section.section_key.strip() == dimension.key),
                None
            )
            # 3. 确定最终的章节信息（LLM 优先，若缺失则 fallback 至默认维度配置）
            if llm_section:
                # 3.1 如果找到了，使用llm生成的标题和目标
                goals = [g.strip() for g in llm_section.goal_analysis_points if g.strip()]
                title = llm_section.title.strip()
            else:
                # 3.2 如果没找到，llm把维度漏掉，用默认值
                goals = [dimension.insight_goal]
                title = dimension.title

            # 4. 构建InsightSection
            insight_sections.append(InsightSection(
                title=title,
                goal=goals,
                section_key=dimension.key
            ))

        return insight_sections
