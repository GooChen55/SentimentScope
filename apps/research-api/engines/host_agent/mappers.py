"""HostAgent 防腐层映射器:领域对象 → 外部集成事件 DTO。

职责:将 host_agent 内部领域对象(SectionResult / SectionJudgement / 最终裁判 str)
映射为事件总线契约 HostDiscussionMessageEvent,隔离领域模型与外部数据集成格式。
"""

from datetime import datetime

from engines.common.eventing.event import HostDiscussionMessageEvent
from engines.contracts.roles import ROLE_INFOS, role_display_name
from engines.host_agent.schemas import SectionJudgement, SectionResult

_HOST_DISPLAY_NAME = ROLE_INFOS["host"].display_name


def build_agent_event(result: SectionResult) -> HostDiscussionMessageEvent:
    """构造 Agent(insight/media)章节发言事件。"""
    return HostDiscussionMessageEvent(
        type="agent",
        sender=role_display_name(result.source),
        content=result.body[:2000],
        source=result.source,
        section_key=result.section_key,
        timestamp=_now_time(),
    )


def build_judgement_event(judgement: SectionJudgement) -> HostDiscussionMessageEvent:
    """构造主持人单维度阶段裁判事件。"""
    return HostDiscussionMessageEvent(
        type="host",
        sender=_HOST_DISPLAY_NAME,
        content=judgement.content,
        source="host",
        section_key=judgement.section_key,
        timestamp=_now_time(),
    )


def build_final_event(content: str) -> HostDiscussionMessageEvent:
    """构造主持人最终裁判事件(无维度归属,section_key 留空)。"""
    return HostDiscussionMessageEvent(
        type="host",
        sender=_HOST_DISPLAY_NAME,
        content=content,
        source="host",
        section_key="",
        timestamp=_now_time(),
    )


def append_event(
        outbox: list[HostDiscussionMessageEvent],
        event: HostDiscussionMessageEvent,
) -> list[HostDiscussionMessageEvent]:
    """返回追加了新事件的 outbox"""
    return [*outbox, event]


def _now_time() -> str:
    return datetime.now().strftime("%H:%M:%S")
