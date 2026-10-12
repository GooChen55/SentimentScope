import asyncio
from typing import Callable
from loguru import logger
from engines.media_agent.context import MediaContext
from engines.common.nodes.base_node import ProgressUpdate
from engines.common.llm.llm_client import LLMClient
from engines.media_agent.graph import build_graph


async def invoke_media_agent(
        query: str,
        role: str,
        llm_client: LLMClient,
        output_dir: str,
        progress_callback: Callable[[ProgressUpdate], None] | None = None,
) -> None:
    logger.info(f"Media智能体开始研究: {query}")

    context = MediaContext(
        role=role,
        llm_client=llm_client,
        output_dir=output_dir,
        progress_callback=progress_callback
    )

    graph = build_graph(context)
    print(graph.get_graph().draw_mermaid())  # 打印图结构

    initial_state = {"query": query, "role": role}

    await graph.ainvoke(initial_state)

    logger.info("Media智能体研究完成")


if __name__ == "__main__":


    async def run_min_test():
        query = "高考难不难"
        role = "media"
        from engines.contracts.config import get_settings
        output_dir = get_settings().MEDIA_REPORT_DIR

        # 初始化客户端
        client = LLMClient.from_role(role)

        try:
            await invoke_media_agent(
                query=query,
                role=role,
                llm_client=client,
                output_dir=output_dir,
                progress_callback=None
            )
            print("测试执行成功")
        except Exception as e:
            print(f"测试执行失败: {e}")
            import traceback
            traceback.print_exc()


    asyncio.run(run_min_test())
