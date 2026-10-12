from pydantic import BaseModel, Field,field_validator,RootModel
from typing import Any

class ConfigUpdateRequest(RootModel[dict[str, Any]]):
    @field_validator("root")
    @classmethod
    def not_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            raise ValueError("请求体不能为空")
        return v




class ConfigResponse(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict, description="当前配置")
