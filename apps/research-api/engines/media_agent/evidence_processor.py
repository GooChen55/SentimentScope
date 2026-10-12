"""MediaAgent 章节证据:搜索证据组装 + 写回。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from loguru import logger

from engines.common.eventing.publishers import publish_section_read_ready
from engines.common.eventing.event import SectionReadyEvent
from engines.contracts.evidence.render import evaluate_evidence_strength, EvidenceStrength, render_evidence_records
from engines.contracts.evidence.models import EvidenceRecord
from engines.contracts.roles import ROLE_INFOS


@dataclass(frozen=True, slots=True)
class SectionEvidencePack:
    """搜索证据的不可变组装结果;节点只负责把它的字段写回 section 字典。"""

    used_query: str
    evidence_count: int
    evidence_strength: EvidenceStrength = "missing"
    evidence_source_blocks: list[str] = field(default_factory=list)


# 数据包构建
def generate_section_evidence_pack(
        used_query: str,
        records: list[EvidenceRecord],
) -> SectionEvidencePack:
    hit_count = len(records)
    return SectionEvidencePack(
        used_query=used_query,
        evidence_count=hit_count,
        evidence_source_blocks=render_evidence_records(records),
        evidence_strength=evaluate_evidence_strength(hit_count),
    )


# 发布章节内容事件构建
def dispatch_section_ready_event(
        state: Mapping[str, Any],
        section_index: int,
        section: Mapping[str, Any],
) -> None:
    role_key = state.get("role", "media")
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
            source=role_key,   # "media"
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
