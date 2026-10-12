from fastapi import APIRouter, HTTPException
from app.schemas.research_schema import ResearchRequest, ResearchResponse, ResearchResultsResponse
from app.dependencies import ResearchServiceDep

router = APIRouter(prefix="/api/research", tags=["研究路由"])


@router.post("", response_model=ResearchResponse, description="开始研究接口")
async def start_research_endpoint(payload: ResearchRequest, service: ResearchServiceDep):
    try:
        return service.start_research(payload.query, payload.mode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest", response_model=ResearchResultsResponse, description="获取研究结果接口")
def get_research_result_endpoint(service: ResearchServiceDep, research_id: str | None = None):
    try:
        research_result = service.get_research_result(research_id)
        return ResearchResultsResponse(results=research_result)
    except KeyError:
        raise HTTPException(404, '研究任务不存在')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
def list_tasks(service: ResearchServiceDep):
    return {"tasks": [{key: value for key, value in task.items() if key != 'results'} for task in service.store.list()]}


@router.get("/tasks/{task_id}")
def get_task(task_id: str, service: ResearchServiceDep):
    try:
        return service.store.get(task_id)
    except KeyError:
        raise HTTPException(404, "研究任务不存在")


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, service: ResearchServiceDep):
    try:
        return await service.cancel(task_id)
    except KeyError:
        raise HTTPException(404, "研究任务不存在")


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str, service: ResearchServiceDep):
    try:
        task = service.store.get(task_id)
        return service.start_research(task["query"], task["mode"])
    except KeyError:
        raise HTTPException(404, "研究任务不存在")
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except RuntimeError as exc:
        raise HTTPException(409, str(exc))


@router.get('/tasks/{task_id}/evidence')
def evidence(task_id: str, service: ResearchServiceDep):
    from app.services.evaluation_service import get_evidence
    try:
        task = service.store.get(task_id)
        return {'research_id': task_id, 'mode': task['mode'], 'records': get_evidence(task)}
    except KeyError:
        raise HTTPException(404, '研究任务不存在')


@router.get('/tasks/{task_id}/evaluation')
def evaluation(task_id: str, service: ResearchServiceDep):
    from app.services.evaluation_service import evaluate_task
    try:
        return evaluate_task(service.store.get(task_id))
    except KeyError:
        raise HTTPException(404, '研究任务不存在')
