import json
from dataclasses import asdict
from engines.common.runtime.research_context import research_id, artifact_dir


def save_evidence(role, records):
    if not research_id.get():
        return
    folder = artifact_dir()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f'{role}_evidence.json').write_text(
        json.dumps([asdict(record) for record in records], ensure_ascii=False, default=str), encoding='utf-8')
