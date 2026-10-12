"""Export completed live research into the evaluation repository's sample schema."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.research_store import ResearchStore
from app.services.evaluation_service import get_evidence, evaluate_task
from engines.contracts.paths import DATA_ROOT


def build_sample(task, reference):
    if task['status'] != 'completed':
        raise ValueError('Only completed tasks can be evaluated')
    if task['mode'] != 'live':
        raise ValueError('Synthetic demos cannot be used to claim model quality')
    if not reference.strip():
        raise ValueError('A human-reviewed reference answer is required')
    records = get_evidence(task)
    return {'question': task['query'], 'answer': task['results']['host']['final_report'],
            'contexts': [record['content'] for record in records if record.get('content')],
            'ground_truth': reference, 'research_id': task['research_id'],
            'structural_checks': evaluate_task(task)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('research_id')
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=DATA_ROOT / 'evaluation/samples.json')
    args = parser.parse_args()
    sample = build_sample(ResearchStore().get(args.research_id), args.reference.read_text(encoding='utf-8'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([sample], ensure_ascii=False, indent=2), encoding='utf-8')
    print('Exported', args.output)

if __name__ == '__main__':
    main()
