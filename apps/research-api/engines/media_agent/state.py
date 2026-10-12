"""MediaAgent 全网媒体研究模块：engines/media_agent/state.py。"""

from typing import TypedDict

from engines.contracts.evidence.models import EvidenceRecord
from engines.media_agent.web_search.schemas import SearchTool
from engines.contracts.evidence.render import EvidenceStrength


class MediaSection(TypedDict, total=False):
    """一个报告章节:规划字段(plan 产出)+ 研究字段(search/summarize 产出)。"""

    #规划字段(PlanNode 写入)
    title: str  # 章节标题
    section_key: str  # 与全局五维框架对齐的章节键
    goal: list[str]  # 本章预期分析点(1~3 个,写作验收标准)
    search_tool: SearchTool
    search_keywords: list[str]

    # 研究字段(SectionSummarizeNode 写入)
    body: str  # 章节正文
    hit_count: int
    evidence_strength: EvidenceStrength


class MediaState(TypedDict, total=False):
    # 1. 任务上下文 (入口参数)
    query: str
    role: str

    # 2. 执行状态 (中间产物)
    search_evidence_records: list[EvidenceRecord]
    sections: list[MediaSection]

    # 3. 流程控制游标
    cursor: int

    # 4. 最终交付物 (FormatNode 填充)
    final_report: str
    report_title: str
