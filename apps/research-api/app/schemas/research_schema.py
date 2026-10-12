from pydantic import BaseModel, Field, field_validator
from typing import Literal
class ResearchRequest(BaseModel):
    query: str = Field(..., description="研究主题")
    mode: Literal["live", "demo"] = "live"

    @field_validator("query")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("研究主题不能为空")
        return value

class ResearchResponse(BaseModel):
    started: bool = True
    research_id: str = ""
    mode: str = "live"

class ResearchRoleResult(BaseModel):
    final_report: str = ""
    report_file: str = ""

class ResearchResultsResponse(BaseModel):
    results: dict[str, ResearchRoleResult] = Field(default_factory=dict)
