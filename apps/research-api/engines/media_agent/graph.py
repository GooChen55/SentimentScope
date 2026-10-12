"""MediaAgent 全网媒体研究模块：engines/media_agent/graph.py。"""

from typing import Any

from engines.common.nodes.format_node import FormatReportNode
from engines.common.nodes.save_report_node import SaveReportNode
from engines.media_agent.context import MediaContext
from engines.media_agent.nodes import (
    PlanNode,
    SearchNode,
    SectionSummarizeNode,
)
from engines.media_agent.state import MediaState

from langgraph.graph import END, START, StateGraph


def _route_after_summarize(state: MediaState) -> str:
    cursor = state.get("cursor", 0)
    return "next_section" if cursor < len(state.get("sections", [])) else "all_done"

def build_graph(ctx: MediaContext) -> Any:
    graph = StateGraph(MediaState)

    graph.add_node("plan", PlanNode(ctx))
    graph.add_node("search", SearchNode(ctx))
    graph.add_node("summarize", SectionSummarizeNode(ctx))
    graph.add_node("format_report", FormatReportNode(ctx))
    graph.add_node("persist_report", SaveReportNode(ctx))

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "search")
    graph.add_edge("search", "summarize")
    graph.add_conditional_edges(
        "summarize", _route_after_summarize,
        {"next_section": "summarize", "all_done": "format_report"},
    )
    graph.add_edge("format_report", "persist_report")
    graph.add_edge("persist_report", END)

    return graph.compile()
