from typing import Callable, Any
from loguru import logger
from engines.common.runtime.research_context import research_id
from engines.common.eventing.event import (
    EventType
)

EventCallback = Callable[[EventType, dict[str, Any]], None]
_subscribers: dict[EventType, set[EventCallback]] = {}


def subscribe(event_type: EventType, callback: EventCallback):
    _subscribers.setdefault(event_type, set()).add(callback)


def publish(event_type: EventType, data: dict[str, Any]) -> None:
    data = {**data, "research_id": data.get("research_id") or research_id.get()}
    for callback in list(_subscribers.get(event_type, ())):
        try:
            callback(event_type, data)
        except Exception as exc:
            logger.error(f"订阅者订阅失败原因：{str(exc)}")


def unsubscribe(callback: EventCallback) -> None:
    for subs in _subscribers.values():
        subs.discard(callback)


def clear():
    """
    取消所有的事件类型以及对应的订阅者
    :return:
    """
    _subscribers.clear()
