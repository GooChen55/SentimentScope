"""Run original agent graphs with stub external boundaries, never real API calls."""
import asyncio
from engines.contracts.config import get_settings
from engines.contracts.dimensions import DIMENSIONS
from engines.contracts.evidence.models import EvidenceRecord, RetrievalMeta
from engines.common.llm.llm_client import LLMClient
from engines.insight_agent.tools.retrival_service import InsightRetrivalService
from engines.media_agent.context import MediaContext
from app.services.managed_research import ManagedResearchService
from app.services.research_store import ResearchStore


class StubLLM:
    async def generate_object(self, system, user, output_model, **kwargs):
        sections = []
        for dim in DIMENSIONS.values():
            item = {'section_key': dim.key, 'title': dim.title, 'goal_analysis_points': ['明确证据边界']}
            if output_model.__name__ == 'MediaResearchPlan':
                item.update(search_tool='comprehensive_search', search_keywords=['公告'])
            sections.append(item)
        return output_model(sections=sections)

    async def generate_text(self, system, user, **kwargs):
        return '# 测试桩输出\n\n仅用于结构集成测试。[E1] [E2]'


def test_original_graphs_with_stub_providers(tmp_path, monkeypatch):
    import engines.common.runtime.research_context as context
    import app.services.managed_research as managed
    monkeypatch.setattr(context, 'DATA_ROOT', tmp_path / 'data')
    monkeypatch.setattr(managed, 'DATA_ROOT', tmp_path / 'data')
    monkeypatch.setattr(LLMClient, 'from_role', classmethod(lambda cls, role: StubLLM()))
    for key in ('INSIGHT_ENGINE_API_KEY', 'MEDIA_ENGINE_API_KEY', 'HOST_API_KEY', 'HOST_MODEL_NAME', 'TAVILY_API_KEY'):
        monkeypatch.setenv(key, 'stub-only')
    monkeypatch.setenv('SEARCH_SWITCH', 'TavilyAPI')
    monkeypatch.setenv('INSIGHT_CLUSTERING_ENABLED', 'false')
    get_settings.cache_clear()

    async def private_evidence(self, query):
        return [EvidenceRecord('E1', 'weibo', 'weibo_note', query, '高考背景讨论', '2026-01-01',
            retrieval=RetrievalMeta([query], ['keyword_recall'], {'keyword_recall': .5}))]

    async def public_evidence(self, tool, query):
        return [EvidenceRecord('E2', 'test', 'public', query, '合成公告样本', '2026-01-01')]

    monkeypatch.setattr(InsightRetrivalService, 'retrival_evidence', private_evidence)
    monkeypatch.setattr(MediaContext, 'execute_search', public_evidence)

    async def scenario():
        service = ManagedResearchService(ResearchStore(tmp_path / 'tasks.sqlite3'))
        result = service.start_research('测试桩集成', 'live')
        await service.workers[result['research_id']]
        task = service.store.get(result['research_id'])
        await service.close()
        assert task['status'] == 'completed', task['error']
        assert set(task['results']) == {'insight', 'media', 'host'}
        assert len([event for event in service.store.events(result['research_id']) if event['event'] == 'section_ready']) == 10
    try:
        asyncio.run(scenario())
    finally:
        get_settings.cache_clear()
