import asyncio
from loguru import logger
from typing import Callable, Awaitable
from engines.common.llm.llm_client import LLMClient
from engines.common.nodes.base_node import ProgressUpdate
from engines.insight_agent.agent import invoke_insight_agent
from engines.media_agent.agent import invoke_media_agent
from engines.common.runtime.role_log import route_logs_by_role
from engines.common.eventing.publishers import pub_role_result, pub_role_error, pub_role_progress
from engines.common.eventing.event import RoleResultEvent, RoleErrorEvent, RoleProgressEvent
from engines.contracts.config import PROJECT_ROOT, get_settings
from pathlib import Path
from engines.common.runtime.research_context import artifact_dir

ProgressCallback = Callable[[ProgressUpdate], None]
AgentInvoker = Callable[[str, str, LLMClient, str, ProgressCallback], Awaitable[None]]

_RESEARCH_INVOKER: dict[str, AgentInvoker] = {
    "insight": invoke_insight_agent,
    "media": invoke_media_agent,

}


async def run_research(query: str):
    """
    职责：运行两个维度查询的Agent(面向私域数据检索的insight_agent 面向公域数据检索的media_agent)
    执行两个Agent【invoke_insight_agent、invoke_media_agent】的时候都需要以下几个参数
    param1: query:str   "高考"
    param2: role: str   "insight" "media"
    param3: llm_client:  LLMClient
    param4: out_dir:  str
    param5: process_callback:  Callable[[进度更新对象],None]

    :return:
    """

    tasks = [asyncio.create_task(_run_research_role_task(role, query)) for role in _RESEARCH_INVOKER]
    try:
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def _run_research_role_task(role: str, query: str):
    """
    启动两个角色Agent的运行的后台任务
    :param role:
    :param query:
    :return:
    """
    with route_logs_by_role(role):
        # 1. 发布启动研究任务事件
        _publish_role_progress(role=role,update=ProgressUpdate(status="starting",message="开始执行研究",progress_pct=0))
        # 2. 执行指定角色的研究Agent
        try:
            await _execute_research_flow(role, query)
            # 3.  发布研究结果事件
            pub_role_result(RoleResultEvent(role=role))

        except Exception as e:
            logger.error(f"{role} 研究智能体执行期间出现了异常: {str(e)}")
            # 4.  发布研究失败事件
            pub_role_error(RoleErrorEvent(role=role, error=str(e)))
            raise


async def _execute_research_flow(role: str, query: str):
    # 1. 获取指定角色Agent的LLM配置信息的客户端对象
    llm_client = LLMClient.from_role(role)

    # 2. 获取指定角色Agent的报告落盘目录
    output_dir = str(artifact_dir() / role)

    # 3. 运行指定角色的Agent[INSIGHT]
    await _RESEARCH_INVOKER[role](
        query,
        role,
        llm_client,
        output_dir,
        lambda update: _publish_role_progress(role, update)
    )

def _publish_role_progress(role: str, update: ProgressUpdate):
    pub_role_progress(RoleProgressEvent(role=role,
                                        status= update.status,
                                        message= update.message,
                                        progress_pct=update.progress_pct
                                        ))
