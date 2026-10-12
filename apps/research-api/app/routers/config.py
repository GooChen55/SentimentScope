from typing import Any
from fastapi import APIRouter, HTTPException
from app.schemas.config_schema import ConfigResponse, ConfigUpdateRequest
from app.dependencies import ConfigServiceDep

router = APIRouter(prefix="/api/config", tags=["应用配置路由"])

"""
response_model: 自动映射、序列化、类型校验以及转换、过滤字段
"""


@router.get("", response_model=ConfigResponse)
def get_config_endpoint(service: ConfigServiceDep):
    try:
        config: dict[str, Any] = service.read_config_info()
        return ConfigResponse(config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ConfigResponse)
def get_config_endpoint(request: ConfigUpdateRequest, service: ConfigServiceDep):
    try:
        return ConfigResponse(config=service.update_config_info(request.root))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
