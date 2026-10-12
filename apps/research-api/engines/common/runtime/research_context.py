from contextvars import ContextVar
from pathlib import Path
from engines.contracts.paths import DATA_ROOT

research_id: ContextVar[str] = ContextVar("research_id", default="")


def artifact_dir() -> Path:
    run = research_id.get()
    return DATA_ROOT / "runs" / run if run else DATA_ROOT / "report"
