import asyncio
from pydantic.dataclasses import dataclass
from functools import wraps
from typing import Any, Callable
from loguru import logger


@dataclass
class RetryConfig:
    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0

    def delay_for(self, attempt: int) -> float:
        return min(self.initial_delay * (self.backoff_factor ** attempt), self.max_delay)


RETRY_CONFIG = RetryConfig(
    max_retries=4,
    initial_delay=15.0,
    backoff_factor=2.0,
    max_delay=120.0,
)


def _is_non_retryable(exc: Exception) -> bool:
    """4xx 客户端错误(限流 429 除外)重试无意义,立即失败。"""
    status = getattr(exc, "status_code", None)
    if status is None:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
    return isinstance(status, int) and 400 <= status < 500 and status != 429


def _evaluate_failure(name: str, attempt: int, exc: Exception, config: RetryConfig) -> float | None:
    """返回重试延迟秒数;None 表示放弃。"""
    exhausted = attempt >= config.max_retries
    non_retryable = _is_non_retryable(exc)

    if non_retryable or exhausted:
        return None
    delay = config.delay_for(attempt)
    logger.warning(f"函数 {name} 第 {attempt + 1} 次尝试失败: {exc}")
    logger.info(f"将在 {delay:.1f} 秒后进行第 {attempt + 2} 次尝试...")
    return delay


def with_retry(func: Callable) -> Callable:
    """刚性重试：重试失败或遇到致命错误时向上抛异常。"""
    if not asyncio.iscoroutinefunction(func):
        raise TypeError(f"重试装饰器只能装饰 async 函数,得到的是同步函数 {func.__name__}")

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        cfg = RETRY_CONFIG
        for attempt in range(cfg.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                delay = _evaluate_failure(func.__name__, attempt, e, cfg)
                if delay is None:
                    raise
                await asyncio.sleep(delay)

    return wrapper


def with_graceful_retry(func: Callable) -> Callable:
    """柔性重试：失败时不抛异常,返回实例的 retry_default_return 属性(无则 None)。"""
    if not asyncio.iscoroutinefunction(func):
        raise TypeError(f"重试装饰器只能装饰 async 函数,得到的是同步函数 {func.__name__}")

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        cfg = RETRY_CONFIG
        default_return = getattr(args[0], "retry_default_return", None) if args else None
        for attempt in range(cfg.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                delay = _evaluate_failure(func.__name__, attempt, e, cfg)
                if delay is None:
                    return default_return
                await asyncio.sleep(delay)
        return default_return

    return wrapper
