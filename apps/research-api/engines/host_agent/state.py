"""HostAgent 状态契约:LangGraph 运行时 State vs 跨事件 Session。

边界说明:
- State:LangGraph 单次 ainvoke 的运行时 state(TypedDict),每次 process_finding
  由 Session.to_state 生成,ainvoke 结束后由 Session.apply_state 回收。
- Session:跨多次 SectionReady 事件的累积会话状态(@dataclass),内部自管 pair_store
  (default_factory 实例化)与历史 judgements;是图执行间唯一持久化的内存状态。
  query 不在此累积——每次 invoke 由 accumulate_section 从 result.query 写入 state,save_report 同 invoke 读取。
  图拓扑由 record_judgement 产出的 all_done 状态驱动最终报告生成，天然阻止重复生成。
"""

from dataclasses import dataclass, field
from typing import Any, TypedDict

from engines.common.eventing.event import HostDiscussionMessageEvent
from engines.host_agent.pair_store import PairStore
from engines.host_agent.schemas import SectionJudgement, SectionPair, SectionResult


class State(TypedDict, total=False):
    """LangGraph 运行时状态契约;字段在图节点间流转,部分由 Session 注入。"""

    incoming: dict[str, Any]  # 本次 section_ready 事件原始载荷
    section_result: SectionResult  # parse_section 解析出的 SectionResult
    valid: bool  # 入口校验结果,驱动 _route_after_parse
    query: str  # 研究主题(accumulate_section 从 result.query 写入,save_report 读取)
    pair_store: PairStore  # 配对存储(Session 共享引用)
    ready_pairs: list[SectionPair]  # find_ready_pairs 计算的就绪配对
    current_pair: SectionPair  # 正在研判的 SectionPair
    current_judgement: SectionJudgement | None  # judge_section 产出的 SectionJudgement | None
    judgements: list[SectionJudgement]  # 本轮图执行累积的维度研判列表 (在 invoke 结束时会覆盖回 Session)
    all_done: bool  # record_judgement 产出的五维是否全完成
    final_report: str | None  # generate_final_report 产出的最终报告
    outbox: list[HostDiscussionMessageEvent]  # 本次 invoke 产出的讨论消息


@dataclass(slots=True)
class Session:
    """跨 SectionReady 事件的研判会话状态;to/apply_state 是与图运行的唯一桥梁"""

    pair_store: PairStore = field(default_factory=PairStore)  # 跨事件长存的维度配对存储
    judgements: list[SectionJudgement] = field(default_factory=list)  # 跨事件长存的阶段性研判历史

    def clear(self) -> None:
        self.pair_store.clear()
        self.judgements.clear()

    def to_state(self, incoming: dict[str, Any]) -> State:
        """由 SectionReadyListener 在每次执行langgraph 前调用,注入跨事件状态。"""
        return {
            "incoming": incoming,
            "pair_store": self.pair_store,
            "judgements": list(self.judgements),
            "outbox": [],
        }

    def apply_state(self, state: State) -> None:
        """由 SectionReadyListener 在每次 process_finding 后调用,回收跨事件状态。"""
        self.judgements = list(state.get("judgements", []))
