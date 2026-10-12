import pytest
from evaluation.export_samples import build_sample
from app.services.evaluation_service import evaluate_task


def test_demo_cannot_claim_ragas_quality():
    with pytest.raises(ValueError, match='Synthetic'):
        build_sample({'status': 'completed', 'mode': 'demo'}, 'reference')


def test_checks_do_not_invent_semantic_scores(monkeypatch):
    import app.services.evaluation_service as module
    monkeypatch.setattr(module, 'get_evidence', lambda task: [{'id': 'E1'}, {'id': 'E2'}])
    result = evaluate_task({'research_id': 'test', 'mode': 'live', 'status': 'completed',
        'results': {'host': {'final_report': '事件背景与概览 [E1] [E999]'}}})
    assert result['citation_validity'] == .5
    assert result['unknown_citations'] == ['E999']
    assert result['semantic_quality'] is None
    unknown_web_id = 'f' * 32
    result = evaluate_task({'research_id': 'test', 'mode': 'live', 'status': 'completed',
        'results': {'host': {'final_report': f'[E1] [{unknown_web_id}]'}}})
    assert result['unknown_citations'] == [unknown_web_id]
    assert result['citation_validity'] == .5
