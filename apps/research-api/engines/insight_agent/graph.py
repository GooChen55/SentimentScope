from typing import Any
from langgraph.graph import END, START, StateGraph
from engines.insight_agent.context import InsightContext
from engines.insight_agent.state import InsightState
from engines.insight_agent.nodes.retrieval_node import RetrievalNode
from engines.insight_agent.nodes.cluster_node import ClusterNode
from engines.insight_agent.nodes.rerank_node import RerankNode
from engines.insight_agent.nodes.section_plan_node import SectionPlanNode
from engines.insight_agent.nodes.section_allocation_node import SectionAllocationNode
from engines.insight_agent.nodes.section_summary_node import SectionSummarizeNode
from engines.common.nodes.format_node import FormatReportNode
from engines.common.nodes.save_report_node import SaveReportNode


def _route_after_summarize(state: InsightState) -> str:
    cursor = state.get("cursor", 0)
    return "next_section" if cursor < len(state.get("sections", [])) else "all_done"


def build_graph(ctx: InsightContext) -> Any:
    graph = StateGraph(InsightState)

    graph.add_node("retrieval", RetrievalNode(ctx))
    graph.add_node("rank", RerankNode(ctx))
    graph.add_node("cluster", ClusterNode(ctx))
    graph.add_node("plan", SectionPlanNode(ctx))
    graph.add_node("section_allocation", SectionAllocationNode(ctx))
    graph.add_node("summarize", SectionSummarizeNode(ctx))
    graph.add_node("format_report", FormatReportNode(ctx))
    graph.add_node("persist_report", SaveReportNode(ctx))

    graph.add_edge(START, "retrieval")
    graph.add_edge("retrieval", "rank")
    graph.add_edge("rank", "cluster")
    graph.add_edge("cluster", "plan")
    graph.add_edge("plan", "section_allocation")
    graph.add_edge("section_allocation", "summarize")
    graph.add_conditional_edges(
        "summarize", _route_after_summarize,
        {"next_section": "summarize", "all_done": "format_report"},
    )
    graph.add_edge("format_report", "persist_report")
    graph.add_edge("persist_report", END)

    return graph.compile()
