# -*- coding: utf-8 -*-
"""WebSocket 路由 — 实时推送爬虫进度事件"""

import asyncio
import json
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.web.services.task_manager import TaskManager

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """管理 WebSocket 连接，处理订阅/取消订阅。"""

    def __init__(self):
        self._active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, task_id: str, ws: WebSocket) -> None:
        await ws.accept()
        if task_id not in self._active_connections:
            self._active_connections[task_id] = []
        self._active_connections[task_id].append(ws)

    def disconnect(self, task_id: str, ws: WebSocket) -> None:
        conns = self._active_connections.get(task_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, task_id: str, event: dict) -> None:
        """向所有订阅该任务的 WebSocket 客户端推送事件。"""
        conns = self._active_connections.get(task_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            conns.remove(ws)


_ws_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    return _ws_manager


@router.websocket("/crawl/{task_id}")
async def crawl_progress(ws: WebSocket, task_id: str):
    tm = TaskManager()
    await _ws_manager.connect(task_id, ws)

    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    tm.subscribe(task_id, queue)

    async def _forward_events():
        """从 TaskManager 的 asyncio.Queue 读取事件并推送到 WebSocket。"""
        while True:
            try:
                event = await queue.get() # 从队列获取 阻塞
                await ws.send_json(event) # 仅发送给自身订阅，避免多窗口重复广播
            except asyncio.CancelledError:
                break
            except Exception:
                break

    forward_task = asyncio.create_task(_forward_events())

    try:
        while True:
            raw = await ws.receive_text()  # 负责监听前端发来的指令
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("action") == "stop":
                tm.stop_task(task_id)
                await ws.send_json({"type": "ack", "action": "stop", "message": "停止信号已发送"})
            elif msg.get("action") == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        forward_task.cancel()   # 取消任务
        try:
            await forward_task
        except (asyncio.CancelledError, Exception):
            pass
        tm.unsubscribe(task_id, queue)   # 移除订阅者
        _ws_manager.disconnect(task_id, ws)  # 移除ws连接
