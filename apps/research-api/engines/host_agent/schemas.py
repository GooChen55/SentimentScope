"""HostAgent 纯领域数据契约。仅承载不可变数据结构 + 事件载荷解析"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SectionResult:
    """单个 Agent 对某维度的章节研究结果(section_ready 事件载荷的领域投影)。"""

    source: str
    section_key: str
    title: str
    body: str
    query: str = ""
    hit_count: int = 0
    strength: str = ""

    @classmethod
    def from_event(cls, data: dict[str, Any]) -> "SectionResult":
        """从 section_ready 事件载荷构造"""
        metadata = data.get("section_metadata", {})
        return cls(
            source=data["source"],
            section_key=data["section_key"],
            title=data["title"],
            body=data["body"],
            query=data["query"],
            hit_count=metadata.get("hit_count"),
            strength=metadata.get("strength"),
        )


@dataclass(frozen=True)
class SectionPair:
    """同一维度 insight + media 的配对,供主持人研判。"""

    section_key: str
    title: str
    insight: SectionResult
    media: SectionResult


@dataclass(frozen=True)
class SectionJudgement:
    """主持人对单个维度的研判发言;content 承载完整 Markdown,是唯一信息字段。"""

    section_key: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {"section_key": self.section_key, "content": self.content}
