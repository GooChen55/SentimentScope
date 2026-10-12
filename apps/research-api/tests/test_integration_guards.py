import asyncio
import pytest
from app.services.config_service import ConfigService
from engines.contracts.config import get_settings
from app.services.report.task_store import ReportTaskStore, ReportTaskStatus
from app.services.research_store import ResearchStore
from app.services.report.report_service import ReportService
import app.services.report.report_service as report_module


def test_secrets_masked_and_unknown_fields_rejected(monkeypatch):
    monkeypatch.setenv('HOST_API_KEY', 'test-secret-only')
    get_settings.cache_clear()
    try:
        assert ConfigService().read_config_info()['HOST_API_KEY'] == '********'
        with pytest.raises(ValueError):
            ConfigService().update_config_info({'PATH': 'untrusted'})
    finally:
        get_settings.cache_clear()


def test_config_update_uses_central_config_file(tmp_path, monkeypatch):
    import app.services.config_service as config_module
    env_file = tmp_path / 'config' / 'research.env'
    env_file.parent.mkdir()
    env_file.write_text('', encoding='utf-8')
    monkeypatch.setattr(config_module, 'ENV_FILE', str(env_file))
    monkeypatch.setenv('HOST_MODEL_NAME', 'before-update')
    get_settings.cache_clear()
    try:
        updated = ConfigService().update_config_info({'HOST_MODEL_NAME': 'after-update'})
        assert updated['HOST_MODEL_NAME'] == 'after-update'
        assert 'after-update' in env_file.read_text(encoding='utf-8')
    finally:
        get_settings.cache_clear()


def test_same_topic_tasks_do_not_mix_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(report_module, 'DATA_ROOT', tmp_path / 'data')
    store = ResearchStore(tmp_path / 'tasks.sqlite3')
    ids = []
    for text in ('first-round', 'second-round'):
        task = store.create('same query', 'demo')
        task['status'] = 'completed'
        store.save(task)
        ids.append(task['research_id'])
        for role in ('insight', 'media', 'host'):
            directory = tmp_path / 'data' / 'runs' / task['research_id'] / role
            directory.mkdir(parents=True)
            (directory / f'{role}_same query_20260101_120000_abcdef12.md').write_text(text, encoding='utf-8')
    async def scenario():
        registry = ReportTaskStore(tmp_path / 'reports.json')
        service = ReportService(registry, output_dir=tmp_path / 'combined', research_store=store)
        task = service.start_generate_report_task('Custom report title', ids[0])
        await asyncio.gather(*service._workers)
        assert task.status == ReportTaskStatus.COMPLETED
        assert 'first-round' in task.html_content
        assert 'second-round' not in task.html_content
        restored = ReportTaskStore(tmp_path / 'reports.json').get_generate_task(task.task_id)
        assert restored.status == ReportTaskStatus.COMPLETED
        assert restored.html_content == task.html_content
    asyncio.run(scenario())
