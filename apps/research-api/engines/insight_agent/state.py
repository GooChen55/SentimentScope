"""InsightAgent 私有舆情库研究模块：engines/insight_agent/state.py。"""
from typing import TypedDict
from engines.insight_agent.evidence_processor  import EvidencePool, EvidenceRecord
from engines.contracts.evidence.models import EvidenceStrength


class InsightSection(TypedDict, total=False):
    """章节交付物 定义单个章节的内部信息"""

    # 1. 章节规划信息 第一阶段:由PlanNode初始化时的规划信息
    title: str
    goal: list[str]   # 目标
    section_key: str

    # 2. 章节写作结果 第二阶段:由SummarizeNode动态补充的写作结果与元数据
    body: str
    hit_count: int
    evidence_strength: EvidenceStrength


class InsightState(TypedDict, total=False):
    """整个 InsightAgent 全局上下文：定义私域检索智能体专家流转状态"""

    # 入口参数
    query: str
    role: str
    evidence_pool: EvidencePool

    # 2. 执行状态 (中间产物)
    sections: list[InsightSection]
    section_evidence_records: list[list[EvidenceRecord]]

    # 3. 流程控制游标
    cursor: int

    # 4. 最终交付物
    final_report: str
    report_title: str
