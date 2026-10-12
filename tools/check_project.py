"""Read-only smoke checks for the running local platform; no model or crawling requests."""
import json
import sqlite3
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def get(url):
    with urlopen(url, timeout=20) as response:
        return json.load(response)


def main():
    research_health = get('http://127.0.0.1:5001/health')
    crawler_health = get('http://127.0.0.1:9000/api/health')
    assert research_health['status'] == 'ok' and crawler_health['db_connected']
    engine = get('http://127.0.0.1:9000/api/crawl/engine')
    assert engine['ready'], 'Crawler engine revision or environment mismatch'
    research = get('http://127.0.0.1:5001/api/research/tasks')['tasks']
    crawler = get('http://127.0.0.1:9000/api/crawl/tasks')['recent']
    baseline = ROOT / 'var/runtime/migration-baseline.json'
    if baseline.is_file():
        previous = json.loads(baseline.read_text(encoding='utf-8-sig'))
        assert set(previous['research_ids']) <= {task['research_id'] for task in research}, 'Missing research history'
        assert set(previous['crawler_ids']) <= {task['task_id'] for task in crawler}, 'Missing crawler history'
    with sqlite3.connect(ROOT / 'var/research/tasks.sqlite3') as database:
        assert database.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    registry = ROOT / 'var/research/report_tasks.json'
    reports = json.loads(registry.read_text(encoding='utf-8')) if registry.exists() else []
    downloads = 0
    for report in reports:
        if report['status'] != 'completed':
            continue
        for file_type, field in (('html', 'report_file_path'), ('md', 'markdown_file_path')):
            path = Path(report[field])
            assert path.is_relative_to(ROOT / 'var/research') and path.is_file(), 'Invalid persisted report path'
            with urlopen(f"http://127.0.0.1:5001/api/report/download/{report['task_id']}/{file_type}", timeout=20) as response:
                assert response.read() == path.read_bytes(), 'Report download differs from stored artifact'
            downloads += 1
    for port in (3000, 5173):
        with urlopen(f'http://127.0.0.1:{port}/', timeout=20) as response:
            assert response.status == 200
    result = {'status': 'passed', 'research_tasks': len(research), 'crawler_tasks': len(crawler),
              'report_downloads': downloads, 'sqlite_integrity': 'ok',
              'engine_revision': engine['installed_revision'], 'database_connected': True}
    output = ROOT / 'var/runtime/project-check.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
