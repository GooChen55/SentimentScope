"""Adapter to shopkeeper_brain branch 0119; explicit judge and embeddings."""
import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engines.contracts.paths import WORKSPACE_ROOT, DATA_ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('samples', type=Path)
    parser.add_argument('--output', type=Path, default=DATA_ROOT / 'evaluation/ragas_result.csv')
    args = parser.parse_args()
    records = json.loads(args.samples.read_text(encoding='utf-8'))
    if any(not record.get('ground_truth') or not record.get('contexts') for record in records):
        raise ValueError('Every sample needs evidence contexts and a reviewed reference answer')
    required = ['EVAL_API_KEY', 'EVAL_MODEL', 'EVAL_EMBEDDING_MODEL']
    if any(not os.getenv(name) for name in required):
        raise ValueError('Set EVAL_API_KEY, EVAL_MODEL and EVAL_EMBEDDING_MODEL first')
    source = WORKSPACE_ROOT / 'references/evaluation/eval/eval.py'
    spec = importlib.util.spec_from_file_location('reference_eval', source)
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    llm = ChatOpenAI(api_key=os.environ['EVAL_API_KEY'], base_url=os.getenv('EVAL_BASE_URL'), model=os.environ['EVAL_MODEL'])
    embeddings = OpenAIEmbeddings(api_key=os.getenv('EVAL_EMBEDDING_API_KEY', os.environ['EVAL_API_KEY']),
        base_url=os.getenv('EVAL_EMBEDDING_BASE_URL', os.getenv('EVAL_BASE_URL')),
        model=os.environ['EVAL_EMBEDDING_MODEL'])
    rows = evaluator.step_4_evaluate_with_ragas(records, llm, embeddings)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    evaluator.step_5_write_result(rows, args.output)
    failed = any(any(row.get(metric, '') == '' for metric in evaluator.METRIC_COLUMN_MAP.values()) for row in rows)
    print('Saved', args.output, 'incomplete_metrics=' + str(failed))
    if failed:
        raise SystemExit(2)

if __name__ == '__main__':
    main()
