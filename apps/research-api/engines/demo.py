"""Explicit synthetic simulation: exercises orchestration, not model quality."""
import asyncio
from engines.contracts.dimensions import DIMENSIONS
from engines.common.eventing.event import EventType
from engines.common.eventing.bus import publish
from engines.common.io.report_io import save_md_report
from engines.common.runtime.research_context import artifact_dir
from engines.host_agent.schemas import SectionJudgement

DEMO_EVIDENCE = [
    {"id": "E1", "source": "模拟微博帖子", "text": "示例品牌宣布调整配送服务，部分用户关注送达时间。", "synthetic": True},
    {"id": "E2", "source": "模拟抖音评论", "text": "有用户反馈配送延迟，也有用户表示订单正常送达。", "synthetic": True},
    {"id": "E3", "source": "模拟公开公告", "text": "示例品牌公告称配送规则调整正在试行，尚未公布全面评估结果。", "synthetic": True},
]


class DemoJudge:
    async def judge_section(self, pair, previous):
        return SectionJudgement(section_key=pair.section_key, content=(
            f"### {pair.title}\n\n【模拟模式：无模型调用】\n\n"
            "私域反馈与公告属于不同来源，不能由少量评论推断总体比例。[E1] [E2] [E3]\n\n"
            "证据缺口：缺少完整订单样本、时间序列和独立核验。"))

    async def generate_final_report(self, results):
        return "# 模拟综合研判\n\n本报告用于验证应用流程，内容为合成样例，不代表真实事件或模型分析。\n\n" + "\n\n".join(r.content for r in results)


async def run_demo(query):
    if query != "示例品牌配送调整":
        raise ValueError("模拟模式仅支持主题：示例品牌配送调整；真实主题请选择真实分析模式")
    for role, name in (("insight", "Insight Engine"), ("media", "Media Engine")):
        sections = []
        for index, dimension in enumerate(DIMENSIONS.values()):
            publish(EventType.ROLE_PROGRESS, {"role": role, "status": "running", "message": f"模拟：{dimension.title}", "progress_pct": (index + 1) * 20})
            records = DEMO_EVIDENCE[:2] if role == "insight" else DEMO_EVIDENCE[2:]
            body = "【模拟模式：合成证据，无模型调用】\n\n" + "\n\n".join(f"[{r['id']}] {r['source']}：{r['text']}" for r in records)
            sections.append(f"## {dimension.title}\n\n{body}")
            publish(EventType.SECTION_READY, {"source": role, "agent_name": name, "section_key": dimension.key,
                    "section_index": index, "title": dimension.title, "query": query, "body": body,
                    "section_metadata": {"hit_count": len(records), "strength": "weak"}})
            await asyncio.sleep(0.04)
        save_md_report(str(artifact_dir() / role), role, query, "# 模拟研究报告\n\n" + "\n\n".join(sections))
        publish(EventType.ROLE_RESULT, {"role": role})
