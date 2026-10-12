"""Keep test research artifacts and task state out of the user's workspace data."""
import pytest


@pytest.fixture(autouse=True)
def isolated_research_data(tmp_path, monkeypatch):
    from engines.common.runtime import research_context
    from app.services import managed_research, research_store, evaluation_service
    from app.services.report import report_service
    for module in (research_context, managed_research, research_store, evaluation_service, report_service):
        monkeypatch.setattr(module, 'DATA_ROOT', tmp_path / 'data')
