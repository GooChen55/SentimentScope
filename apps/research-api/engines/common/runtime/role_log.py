from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from loguru import logger
from engines.contracts.paths import LOG_DIR
_LOG_DIR = LOG_DIR


@contextmanager
def route_logs_by_role(role: str) -> Iterator[None]:
    handler_id = None

    # 1. 给日志贴上上下文信息
    with logger.contextualize(role=role):
        try:
            _LOG_DIR.mkdir(parents=True, exist_ok=True)
            handler_id = logger.add(
                str(_LOG_DIR / f"{role}.log"),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | [{extra[role]}] {name} - {message}",
                level="INFO",   # >= INFO大小级别的能进入
                encoding="utf-8",
                rotation="1 MB",
                filter=lambda record: record["extra"].get("role") == role,  # 过滤表达式
            )
            # 2. 让出控制权 真正执行业务代码
            yield
        except Exception as exc:
            raise exc

        finally:
            # 3. 移除日志对象
            if handler_id is not None:
                logger.remove(handler_id)

def do_something():
    # logger.debug(f"debug hello world")  # 进不去
    # logger.info(f"hello world")         # 进去了
    logger.warning(f"hello world")        # 进去了
    logger.error(f"hello world")          # 进去了

    # 日志大小的排序  debug(10) < info(20) <warning(30)< error(40)

if __name__ == '__main__':
    with route_logs_by_role("test") as r:
        do_something()
