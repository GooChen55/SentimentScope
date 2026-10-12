from typing import Annotated

from fastapi import Depends
from app.services.config_service import ConfigService
from app.services.managed_research import ManagedResearchService as ResearchService
from functools import lru_cache
from app.services.host_service import HostService
from app.services.report.report_service import ReportService
from app.services.report.task_store import ReportTaskStore
from engines.contracts.paths import DATA_ROOT


def get_config_service():
    return ConfigService()


ConfigServiceDep = Annotated[ConfigService, Depends(get_config_service)]


@lru_cache(maxsize=1)
def get_research_service():
    return ResearchService()


ResearchServiceDep = Annotated[ResearchService, Depends(get_research_service)]


@lru_cache(maxsize=1)
def get_host_service():
    """
    获取主持人服务
    :return:
    """
    return HostService(get_research_service())


HostServiceDep = Annotated[HostService, Depends(get_host_service)]

_report_service = ReportService(task_store=ReportTaskStore(DATA_ROOT / 'report_tasks.json'))

def get_report_service():
    """
    获取报告服务(共享)
    :return:
    """
    return _report_service


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
