from dataclasses import dataclass, field
from typing import Any,Mapping
from collections import Counter
from loguru import logger

from engines.common.eventing.publishers import publish_section_read_ready
from engines.common.eventing.event import SectionReadyEvent
from engines.contracts.evidence.render import render_evidence_records,evaluate_evidence_strength
from engines.contracts.dimensions import dimension_for_key
from engines.contracts.evidence.models import (
    EvidenceRecord,
    EvidenceStrength
)
from engines.contracts.roles import ROLE_INFOS


# InsightAgent私有全局容器与聚合根
@dataclass(slots=True)
class EvidenceCluster:
    """证据聚类簇（组）"""

    # 簇基础描述
    id: str
    label: str
    summary: str

    # 簇成员
    member_record_ids: list[str] = field(default_factory=list)
    representative_ids: list[str] = field(default_factory=list)
    size: int = 0


@dataclass(slots=True)
class EvidencePool:
    """全局证据池。"""
    query: str

    # 资产清单
    records: list[EvidenceRecord] = field(default_factory=list)
    clusters: list[EvidenceCluster] = field(default_factory=list)




@dataclass(slots=True)
class SectionEvidencePack:
    """章节证据包(LLM 写作文本块  + 缺口说明)。"""
    used_query: str = ""
    evidence_count: int = 0
    strength: EvidenceStrength = "missing"
    evidence_source_blocks: list[str] = field(default_factory=list)





def generate_plan_overview(pool: EvidencePool) -> dict[str, Any]:
    records_by_id = {r.id: r for r in pool.records if r.id}
    dimension_clusters: list[dict[str, Any]] = []

    for cluster in pool.clusters:
        representative_quotes = []
        for record_id in cluster.representative_ids[:3]:
            record = records_by_id.get(record_id)
            if record is None:
                continue
            representative_quotes.append({
                "platform": record.platform,
                "content": record.content[:150],
            })

        dimension_clusters.append({
            "dimension_goal": _resolve_dimension_goal(cluster.id),
            "label": cluster.label,
            "size": cluster.size,
            "representative_quotes": representative_quotes,
        })

    return {
        "total_records": len(pool.records),
        "platform_distribution": dict(Counter(r.platform for r in pool.records)),
        "dimension_clusters": dimension_clusters,
    }


def _resolve_dimension_goal(cluster_id: str) -> str:
    dimension = dimension_for_key(cluster_id.removeprefix("cluster_"))
    return dimension.insight_goal if dimension else ""


def generate_section_records(section_key: str, records: list[EvidenceRecord]) -> list[EvidenceRecord]:
    """精简后的选择器：直取目标簇，直接排序"""
    matched_records = [r for r in records if r.cluster_id == f"cluster_{section_key}"]
    if not matched_records:
        return []

    sort_key = _calculate_comment_score if section_key in {"sentiment_and_opinion",
                                                           "deep_causes_and_impact"} else _calculate_heat_score
    return sorted(matched_records, key=sort_key, reverse=True)


def _calculate_comment_score(record: EvidenceRecord) -> float:
    eng = record.engagement
    score = (
            float(record.final_score) +
            min(len(record.content) / 100, 1.0) * 0.5 +
            min(float(eng.replies) / 5, 1.0) * 0.3 +
            min(float(eng.likes) / 500, 1.0) * 0.2
    )
    return round(score, 3)


def _calculate_heat_score(record: EvidenceRecord) -> float:
    # 仅将 final_score 作为辅助维度提升权重
    score = float(record.hotness_score) + float(record.final_score) * 0.1

    # TODO 额外逻辑：如果 record 有特定的互动数据需要作为微小的加分项，
    return round(score, 3)


# ===== 章节证据包构建 =====

def generate_section_evidence_pack(
        used_query: str,
        selected: list[EvidenceRecord],
) -> SectionEvidencePack:
    count = len(selected)
    return SectionEvidencePack(
        used_query=used_query,
        evidence_count=count,
        strength=evaluate_evidence_strength(count),
        evidence_source_blocks=render_evidence_records(selected),
    )



# ===== 发布章节内容事件构建 =====


def dispatch_section_ready_event(
        state: Mapping[str, Any],
        section_index: int,
        section: Mapping[str, Any]
) -> None:
    """
    章节就绪发布事件 适配Insight私域搜索专家
    """
    role_key = state.get("role", "insight")
    role_info = ROLE_INFOS.get(role_key)
    agent_name = role_info.display_name

    try:
        # 1. 提取元数据
        section_metadata = {
            "hit_count": section.get("hit_count", 0),
            "evidence_strength": section.get("evidence_strength", "missing"),
        }

        # 2. 构建章节准备发布事件数据包
        event = SectionReadyEvent(
            source=role_key,
            agent_name=agent_name,
            section_key=section.get("section_key", ""),
            section_index=section_index,
            title=section.get("title", ""),
            query=state.get("query", ""),
            body=section.get("body", ""),
            section_metadata=section_metadata

        )

        # 3. 发布章节就绪事件
        publish_section_read_ready(event)

        logger.info(
            f"[{agent_name}] section_ready 已发布 "
            f"section_key={event.section_key} index={event.section_index} "
            f"hit_count={event.section_metadata['hit_count']}"
        )
    except Exception as exc:
        logger.warning(f"[{agent_name}] section_ready 事件发布失败: {exc}")