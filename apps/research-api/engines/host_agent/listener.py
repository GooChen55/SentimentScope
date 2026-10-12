"""HostAgent 运行时:事件监听。

- SectionReadyListener:SectionReady 事件入口,asyncio.Queue + 长跑 worker 串行处理
- 持有 judge / session / graph,
- worker 循环内函数驱动 LangGraph;start/stop 幂等。
"""

import asyncio
from typing import Any

from loguru import logger

from engines.common.eventing.event import EventType

from engines.common.eventing.publishers import publish_host_discussion_message
from engines.common.eventing.bus import subscribe, unsubscribe
from engines.host_agent.graph import build_graph
from engines.host_agent.judge import Judge
from engines.host_agent.state import Session
from engines.common.runtime.research_context import research_id


class SectionReadyListener:
    """监听 section_ready 事件,asyncio.Queue + 长跑 worker 串行处理章节发现"""

    def __init__(self, judge=None) -> None:
        judge = judge or Judge()
        self.session = Session()
        self.graph = build_graph(judge)
        self._queue: asyncio.Queue[dict[str, Any]] | None = None
        self._worker: asyncio.Task | None = None
        self.error: str = ""
        self.research_id = research_id.get()

    def start(self) -> None:
        """启动事件订阅 + worker;幂等(已激活时 no-op)。"""
        if self._worker is not None:
            return
        self._queue = asyncio.Queue()
        subscribe(EventType.SECTION_READY, self._on_callback)
        self._worker = asyncio.create_task(self._run())   # 创建两个
        # self._worker = asyncio.create_task(self._run())   # 在创建一个有问题，但是start有迷瞪
        logger.info("SectionReadyListener: 已启动, 按 section_key 进行主持人研判")

    def stop(self) -> None:
        """停止事件订阅 + 取消 worker
        """
        if self._worker is None:
            return
        unsubscribe(self._on_callback)
        self._worker.cancel()
        self._worker = None
        self._queue = None
        self.session.clear()
        logger.info("SectionReadyListener: 已停止")

    def _on_callback(self, _event_type: EventType, payload_data: dict) -> None:
        """事件回调"""
        if payload_data.get("research_id", "") != self.research_id:
            return
        self._queue.put_nowait(payload_data)

    async def wait_complete(self):
        await self._queue.join()
        if self.error:
            raise RuntimeError(self.error)
        if not self.session.pair_store.all_done():
            raise RuntimeError("主持人未收到完整的五维研究结果")

    async def _run(self) -> None:
        """worker自旋 消费queue+函数式驱动graph"""
        queue = self._queue
        while True:
            section_pack = await queue.get()
            try:
                state = self.session.to_state(section_pack)   # 共享session安全
                final_state = await self.graph.ainvoke(state)   # await期间并发安全
                self.session.apply_state(final_state)
                messages = final_state.get("outbox", [])
            except Exception as exc:
                logger.exception(f"SectionReadyListener: 章节发现处理失败: {exc}")
                self.error = str(exc)
                continue
            finally:
                queue.task_done()
            for message in messages:
                publish_host_discussion_message(message)
