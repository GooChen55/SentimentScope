"""MediaAgent LLM 结构化输出模型。"""

from pydantic import BaseModel, Field
from engines.media_agent.web_search.schemas import SearchTool


class MediaSectionPlan(BaseModel):
    title: str = Field(..., description="当前固定维度下的章节标题")
    section_key: str = Field(..., description="必须严格原样返回固定维度框架中的 section_key")
    goal_analysis_points: list[str] = Field(
        min_length=1,
        max_length=3,
        description="本章节的预期分析点(1~3 个),必须与固定维度对应",
    )
    search_tool: SearchTool = Field(
        description="本章节使用的搜索工具,必须来自 available_tools",
    )
    search_keywords: list[str] = Field(
        min_length=1,
        max_length=3,
        description="专为搜索引擎提取的补充关键词，1-3个。必须是离散的词汇（如 '官方通报', '警方回应'），绝不能是完整句子。"
    )

class MediaResearchPlan(BaseModel):
    sections: list[MediaSectionPlan] = Field(
        min_length=5,
        max_length=5,
        description="固定 5 个章节维度的搜索计划,顺序必须与 fixed_dimensions 一致",
    )
