import asyncio
import pytest
from app.services.managed_research import ManagedResearchService
from app.services.research_store import ResearchStore


def test_demo_completes_and_persists(tmp_path):
    async def scenario():
        service = ManagedResearchService(ResearchStore(tmp_path / 'tasks.sqlite3'))
        result = service.start_research('示例品牌配送调整', 'demo')
        await service.workers[result['research_id']]
        task = service.store.get(result['research_id'])
        assert task['status'] == 'completed', task['error']
        assert set(task['results']) == {'insight', 'media', 'host'}
        events = service.store.events(result['research_id'])
        assert len([e for e in events if e['event'] == 'section_ready']) == 10
        assert all(e['data']['research_id'] == result['research_id'] for e in events)
        await service.close()
        assert ResearchStore(tmp_path / 'tasks.sqlite3').get(result['research_id'])['status'] == 'completed'
    asyncio.run(scenario())


def test_cancel_and_restart(tmp_path):
    async def scenario():
        service = ManagedResearchService(ResearchStore(tmp_path / 'tasks.sqlite3'))
        result = service.start_research('示例品牌配送调整', 'demo')
        with pytest.raises(RuntimeError):
            service.start_research('示例品牌配送调整', 'demo')
        await asyncio.sleep(.02)
        assert (await service.cancel(result['research_id']))['status'] == 'cancelled'
        await service.close()
        pending = service.store.create('old task', 'live')
        restarted = ManagedResearchService(service.store)
        restarted.activate()
        assert restarted.store.get(pending['research_id'])['status'] == 'interrupted'
        await restarted.close()
    asyncio.run(scenario())


def test_demo_rejects_real_topics(tmp_path):
    service = ManagedResearchService(ResearchStore(tmp_path / 'tasks.sqlite3'))
    with pytest.raises(ValueError, match='模拟模式'):
        service.start_research('联想', 'demo')
    asyncio.run(service.close())
