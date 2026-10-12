"""HostAgent LangGraph 图节点:纯状态流转 。

职责:
- 纯函数节点(parse/accumulate/find/record_*)只做状态流转与校验,不依赖任何外部服务。
- 副节点 judge/final 通过闭包工厂注入 Judge;save_report 为普通节点
"""

from typing import Any, Callable

from loguru import logger

from engines.contracts.config import get_settings
from engines.contracts.dimensions import DIMENSIONS
from engines.host_agent.mappers import (
    append_event,
    build_agent_event,
    build_final_event,
    build_judgement_event,
)
from engines.host_agent.schemas import SectionResult
from engines.host_agent.judge import Judge
from engines.host_agent.state import State
from engines.common.io.report_io import save_md_report
from engines.common.runtime.research_context import artifact_dir


def parse_section(state: State) -> State:
    """解析 section_ready 事件:source ∈ {insight,media} 且 section_key ∈ 五维。"""
    result = SectionResult.from_event(state.get("incoming", {}))
    valid = result.source in {"insight", "media"} and result.section_key in DIMENSIONS
    if not valid:
        logger.warning(
            f"HostAgent: dropped SECTION_READY, source={result.source!r} section_key={result.section_key!r}"
        )
    return {"section_result": result, "valid": valid}


def accumulate_section(state: State) -> State:
    """章节结果入队配对存储;被接受时发 agent 发言消息。pair_store 原地 mutate,无需 return。"""
    result = state["section_result"]
    pair_store = state["pair_store"]
    if not pair_store.add(result):
        return {"query": result.query}
    return {
        "query": result.query,
        "outbox": append_event(state.get("outbox", []), build_agent_event(result)),
    }


def find_ready_pairs(state: State) -> State:
    """找出 insight+media 都到齐且未研判的维度配对。"""
    return {"ready_pairs": state["pair_store"].ready_pairs()}


def record_judgement(state: State) -> State:
    """标记已研判;追加 judgement;发 host 章节消息。计算 all_done 供路由读取。"""
    pair = state["current_pair"]
    judgement = state.get("current_judgement")
    pair_store = state["pair_store"]
    pair_store.mark_done(pair.section_key)
    updates = {
        "all_done": pair_store.all_done(),
    }
    if judgement:
        updates["judgements"] = [*state.get("judgements", []), judgement]
        updates["outbox"] = append_event(state.get("outbox", []), build_judgement_event(judgement))
    return updates


def build_judge_section(judge: "Judge") -> Callable[[State], Any]:
    """LLM 研判首个就绪配对;judgement 为 None 表示 LLM 不可用降级。"""

    async def judge_section(state: State) -> State:
        pair = state["ready_pairs"][0]
        logger.info(f"HostAgent: generating section judgement, section_key={pair.section_key}")
        judgement = await judge.judge_section(pair, list(state.get("judgements", [])))
        if judgement is None:
            raise RuntimeError("主持人章节研判失败，不能生成完整裁判报告")
        return {"current_pair": pair, "current_judgement": judgement}

    return judge_section


def build_generate_final_report(judge: "Judge") -> Callable[[State], Any]:
    """LLM 生成最终裁判报告;发 host 最终事件。"""

    async def generate_final_report(state: State) -> State:
        report = await judge.generate_final_report(list(state.get("judgements", [])))
        if not report:
            raise RuntimeError("主持人最终报告生成失败")
        return {
            "final_report": report,
            "outbox": append_event(state.get("outbox", []), build_final_event(report)),
        }

    return generate_final_report


def save_report(state: State) -> State:
    """最终报告 .md 落盘"""
    report = state.get("final_report")
    if not report:
        return {}
    output_dir = str(artifact_dir() / "host")
    md_path = save_md_report(output_dir, "host", state['query'], report)
    logger.info(f"HostAgent: 最终报告已落盘 {md_path}")
    return {}


def build_nodes(judge: "Judge") -> dict[str, Callable[..., Any]]:
    """返回 LangGraph add_node 用的 {node_name: callable} 注册表;Judge 直接注入。"""
    return {
        "parse_section": parse_section,
        "accumulate_section": accumulate_section,
        "find_ready_pairs": find_ready_pairs,
        "judge_section": build_judge_section(judge),
        "record_judgement": record_judgement,
        "generate_final_report": build_generate_final_report(judge),
        "save_report": save_report,
    }
