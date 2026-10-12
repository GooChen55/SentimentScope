"""HostAgent LangGraph 图编排:节点拓扑 + 条件路由。

不含 State/Session(见 state.py)与事件监听(见 listener.py);本模块仅承载图结构。
build_graph(judge) 编译并返回 LangGraph 可执行图。
"""
from typing import Any

from langgraph.graph import END, START, StateGraph

from engines.host_agent.nodes import build_nodes
from engines.host_agent.state import State


def _route_after_parse(state: State) -> str:
    return "valid" if state.get("valid") else "invalid"


def _route_after_find(state: State) -> str:
    return "judge" if state.get("ready_pairs") else "done"


def _route_after_record(state: State) -> str:
    """基于 record_judgement 的产出决定下一步是最终报告还是等待。"""
    if state.get("all_done"):
        return "final"
    return "done"


def build_graph(judge: "Judge") -> Any:
    """编译研判图:注册节点 + 条件路由,返回 LangGraph 可执行图。"""
    graph = StateGraph(State)
    for name, node in build_nodes(judge).items():
        graph.add_node(name, node)

    graph.add_edge(START, "parse_section")
    graph.add_conditional_edges(
        "parse_section", _route_after_parse,
        {"valid": "accumulate_section", "invalid": END},
    )
    graph.add_edge("accumulate_section", "find_ready_pairs")
    graph.add_conditional_edges(
        "find_ready_pairs", _route_after_find,
        {"judge": "judge_section", "done": END}
    )
    graph.add_edge("judge_section", "record_judgement")
    graph.add_conditional_edges(
        "record_judgement", _route_after_record,
        {"final": "generate_final_report", "done": END},
    )
    graph.add_edge("generate_final_report", "save_report")
    graph.add_edge("save_report", END)
    return graph.compile()
