from pydantic import BaseModel, Field, field_validator
class GenerateReportRequest(BaseModel):
    research_id: str | None = None
    query: str = Field("智能舆情分析报告", description="报告主题")

    @field_validator("query")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("报告主题不能为空")
        return v

class ReportStatusResponse(BaseModel):
    inputs_ready: bool = False
    files_found: list[str] = Field(default_factory=list)

class GenerateReportResponse(BaseModel):
    task_id: str = ""
