import json
import sys
import time
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from engines.contracts.paths import DATA_ROOT


def main():
    with httpx.Client(base_url='http://127.0.0.1:5001', trust_env=False, timeout=15) as client:
        assert client.get('/health').json()['status'] == 'ok'
        start = client.post('/api/research', json={'query': '示例品牌配送调整', 'mode': 'demo'})
        start.raise_for_status()
        task_id = start.json()['research_id']
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            task = client.get(f'/api/research/tasks/{task_id}').json()
            if task['status'] not in ('queued', 'running'):
                break
            time.sleep(.1)
        assert task['status'] == 'completed', task.get('error')
        assert set(task['results']) == {'insight', 'media', 'host'}
        discussion = client.get('/api/host/discussion', params={'research_id': task_id}).json()['discussion_records']
        assert len(discussion) == 16
        assert {m['speaker_name'] for m in discussion} == {'Insight Engine', 'Media Engine', 'Host Agent'}
        evaluation = client.get(f'/api/research/tasks/{task_id}/evaluation').json()
        assert evaluation['evidence_count'] == 3
        assert evaluation['citation_validity'] == 1
        assert evaluation['dimension_coverage'] == 1
        assert evaluation['semantic_quality'] is None
        response = client.post('/api/report/generate', json={'query': '模拟联调验证报告', 'research_id': task_id})
        response.raise_for_status()
        report_id = response.json()['task_id']
        for _ in range(100):
            status = client.get(f'/api/report/task/{report_id}').json()
            if status['status'] != 'running':
                break
            time.sleep(.05)
        assert status['status'] == 'completed', status
        for file_type in ('md', 'html'):
            download = client.get(f'/api/report/download/{report_id}/{file_type}')
            assert download.status_code == 200
            assert '模拟' in download.text
        assert client.get('/api/research/tasks/missing').status_code == 404
        config = client.get('/api/config').json()['config']
        for key, value in config.items():
            if key.endswith('API_KEY') or key == 'DB_PASSWORD':
                assert value in ('', '********')
        replayed = []
        with client.stream('GET', '/api/events/stream', params={'research_id': task_id}) as stream:
            for line in stream.iter_lines():
                if line.startswith('data: '):
                    event = json.loads(line[6:])
                    if 'id' in event:
                        assert event['data']['research_id'] == task_id
                        replayed.append(event)
                        if event['event'] == 'role_progress' and event['data'].get('status') == 'completed':
                            break
        assert len([e for e in replayed if e['event'] == 'section_ready']) == 10
    crawler = httpx.get('http://127.0.0.1:9000/api/health', trust_env=False).json()
    assert crawler['db_connected'] is True
    result = {'research_id': task_id, 'report_id': report_id, 'status': 'passed', 'mode': 'synthetic_demo',
        'host_messages': len(discussion), 'sse_replayed_events': len(replayed), 'evaluation': evaluation,
        'crawler_health': crawler, 'real_model_validation': 'not_passed'}
    target = DATA_ROOT / 'integration_verification.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
