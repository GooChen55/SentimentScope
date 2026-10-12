
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse
from app.schemas.report_schema import ReportStatusResponse, GenerateReportRequest, GenerateReportResponse
from app.dependencies import ReportServiceDep
from app.services.report.task_store import  ReportTaskStatus

router = APIRouter(prefix="/api/report", tags=["报告路由"])

@router.get("/status", response_model=ReportStatusResponse, description="获取报告状态")
def get_report_status_endpoint(service: ReportServiceDep, query: str | None = None, research_id: str | None = None):
    try:
        report_status = service.get_report_status(query, research_id)
        return ReportStatusResponse(**report_status)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate", response_model=GenerateReportResponse, description="开始生成报告")
async def generate_report_endpoint(payload: GenerateReportRequest, service: ReportServiceDep):
    try:
        task = service.start_generate_report_task(payload.query, payload.research_id)
        return GenerateReportResponse(task_id=task.task_id)
    except KeyError:
        raise HTTPException(404, '研究任务不存在')
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{task_id}", description="获取报告生成结果")
def get_generate_result_endpoint(task_id: str, service: ReportServiceDep):
    try:
        task = service.get_generate_report_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="报告任务不存在")
    if task.status == ReportTaskStatus.ERROR:
        raise HTTPException(status_code=500, detail=task.error or "报告生成失败")
    if task.status !=ReportTaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="报告尚未完成")
    return Response(content=task.html_content, media_type="text/html")


@router.get("/task/{task_id}", description="查询报告任务状态")
def get_report_task_endpoint(task_id: str, service: ReportServiceDep):
    try:
        task = service.get_generate_report_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="报告任务不存在")
    return {"task_id": task.task_id, "status": task.status, "error": task.error}




@router.get("/download/{task_id}/{file_type}",description="下载HTML/MD格式报告")
def download_report_endpoint(task_id: str, file_type: str, service: ReportServiceDep):
    try:
        file_info = service.get_download_file(task_id, file_type)
        return FileResponse(
            file_info["file_path"],
            media_type=file_info["media_type"],
            filename=file_info["file_name"],
        )
    except (KeyError, FileNotFoundError):
        raise HTTPException(status_code=404, detail="报告任务或文件不存在")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
