"""Structural checks; scores do not establish semantic truth or RAGAS quality."""
import json
import re
from engines.contracts.paths import DATA_ROOT
from engines.contracts.dimensions import DIMENSIONS


def get_evidence(task):
    folder = DATA_ROOT / 'runs' / task['research_id']
    records = []
    for name in ('evidence.json', 'insight_evidence.json', 'media_evidence.json'):
        path = folder / name
        if path.is_file():
            records.extend(json.loads(path.read_text(encoding='utf-8')))
    return list({str(record['id']): record for record in records}.values())


def evaluate_task(task):
    records = get_evidence(task)
    ids = {str(record['id']) for record in records}
    body = task.get('results', {}).get('host', {}).get('final_report', '')
    # Only bracket tokens that are evidence IDs (demo E1 or live platform:kind:id).
    citations = set(re.findall(r'\[((?:E\d+)|(?:[a-f0-9]{32})|(?:[\w-]+:[^\]\s]+))\]', body))
    citations.update(item for item in re.findall(r'\[([^\]\s]+)\]', body) if item in ids)
    covered = [dim.title for dim in DIMENSIONS.values() if dim.title in body]
    unknown = sorted(citations - ids)
    return {'research_id': task['research_id'], 'mode': task['mode'], 'status': task['status'],
        'kind': 'structural_checks', 'evidence_count': len(records),
        'cited_evidence_count': len(citations), 'unknown_citations': unknown,
        'citation_validity': len(citations & ids) / len(citations) if citations else None,
        'dimension_coverage': len(covered) / len(DIMENSIONS), 'covered_dimensions': covered,
        'elapsed_seconds': task.get('metrics', {}).get('elapsed_seconds'),
        'semantic_quality': None,
        'note': '仅检查引用存在性与章节覆盖，不评价事实支持、模型质量或真实性；模拟任务使用合成证据。'}
