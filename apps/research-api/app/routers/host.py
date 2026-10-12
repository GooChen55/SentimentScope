
from fastapi import APIRouter, HTTPException
from app.dependencies import HostServiceDep
from app.schemas.host_schema import HostStateResponse, HostDiscussionRecordsResponse, ResearchDimensionRecordsResponse

router = APIRouter(prefix="/api/host", tags=["主持人 Agent"])


@router.get("/start", response_model=HostStateResponse, description="开始主持人讨论接口")
def start_host_endpoint(service: HostServiceDep):
    try:
        return HostStateResponse(host_running=service.start_host())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
@router.get("/stop", response_model=HostStateResponse, description="停止主持人讨论接口")
def stop_host_endpoint(service: HostServiceDep):
    try:
        service.stop_host()
        return HostStateResponse(host_running=False)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/discussion", response_model=HostDiscussionRecordsResponse,description=" 获取讨论区里收集到的发言记录")
def get_host_discussion_records_endpoint(service: HostServiceDep, research_id: str | None = None):
    try:
        discussion_records = service.get_discussion_records(research_id)
        return HostDiscussionRecordsResponse(**discussion_records)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))



@router.get("/dimensions", response_model=ResearchDimensionRecordsResponse,description="获取两个Agent的发言记录")
def get_host_research_dimensions_endpoint(service: HostServiceDep) -> ResearchDimensionRecordsResponse:
    try:
        research_dimension_records = service.get_research_dimensions()
        return ResearchDimensionRecordsResponse(dimensions=research_dimension_records)
    except  Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
