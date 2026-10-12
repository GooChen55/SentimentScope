import asyncio
import traceback
from typing import Callable
from loguru import logger
import time
from engines.common.nodes.base_node import ProgressUpdate
from engines.common.llm.llm_client import LLMClient
from engines.insight_agent.context import InsightContext
from engines.insight_agent.graph import build_graph


async def invoke_insight_agent(query: str,
                               role: str,
                               llm_client: LLMClient,
                               out_put_dir: str,
                               progress_callback: Callable[[ProgressUpdate], None] | None,
                               ):
    logger.info(f"Insight智能体开始研究: {query}")

    context = InsightContext(
        role=role,
        llm_client=llm_client,
        output_dir=out_put_dir,
        progress_callback=progress_callback,
    )
    graph = build_graph(context)
    print(graph.get_graph().draw_mermaid())  # 打印图结构
    # print(graph.get_graph().draw_ascii())  # 打印图结构

    initial_state = {"query": query, "role": role}

    await graph.ainvoke(initial_state)

    logger.info(f"Insight智能体研究完成")


if __name__ == "__main__":
    async def run_min_test():
        query = "NBA总决赛冠军是谁"
        role = "insight"
        from engines.contracts.config import get_settings
        output_dir = get_settings().INSIGHT_REPORT_DIR
        logger.info("开始测试私域智能体全链路执行...")

        client = LLMClient.from_role(role)
        try:
            start = time.time()
            await invoke_insight_agent(
                query=query,
                role=role,
                llm_client=client,
                out_put_dir=output_dir,
                progress_callback=None
            )
            elapsed = time.time() - start
            logger.info(f"测试私域智能体全链路成功, 耗时:{elapsed:.3f} 秒")
        except Exception as e:
            logger.error(f"测试私域智能体全链路失败 原因 {str(e)}")
            traceback.print_exc()


    asyncio.run(run_min_test())
