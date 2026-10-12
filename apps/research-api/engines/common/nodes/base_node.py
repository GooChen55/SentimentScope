from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable
from engines.common.llm.llm_client import LLMClient


@dataclass(frozen=True)
class ProgressUpdate:
    status: str
    message: str
    progress_pct: int


@runtime_checkable
class ResearchNodeContext(Protocol):
    """Insight / Media 研究角色节点所依赖的运行时上下文协议。具体实现InsightContext / MediaContext。"""
    llm_client: LLMClient

    output_dir: str


class BaseNode(ABC):
    def __init__(self, context: ResearchNodeContext) -> None:
        self.context = context

    @abstractmethod
    async def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        pass
