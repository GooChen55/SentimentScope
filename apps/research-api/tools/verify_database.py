import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text
from engines.insight_agent.tools.connection import get_async_engine, close_async_engine
from engines.insight_agent.tools.retrival_service import InsightRetrivalService


async def main():
    async with get_async_engine().connect() as connection:
        counts = {}
        for table in ('douyin_aweme', 'douyin_aweme_comment', 'weibo_note', 'weibo_note_comment'):
            counts[table] = (await connection.execute(text(f'SELECT COUNT(*) FROM {table}'))).scalar_one()
    records = await InsightRetrivalService().retrival_evidence('高考')
    result = {'table_counts': counts, 'retrieved_count': len(records), 'platforms': sorted({r.platform for r in records})}
    print(json.dumps(result, ensure_ascii=True))
    await close_async_engine()

asyncio.run(main())
