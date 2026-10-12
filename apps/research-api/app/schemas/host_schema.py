from pydantic import BaseModel, Field

class HostStateResponse(BaseModel):
    host_running: bool

class HostDiscussionRecord(BaseModel):
    speaker_name: str = ""   # "insight" "media"  "host"
    message_text: str = ""
    sent_at: str = ""
    dimension_key: str = ""

class HostDiscussionRecordsResponse(BaseModel):
    discussion_records: list[HostDiscussionRecord] = Field(default_factory=list)

class ResearchDimensionRecord(BaseModel):
    key: str
    title: str
    index: str

class ResearchDimensionRecordsResponse(BaseModel):
    dimensions: list[ResearchDimensionRecord]
