import asyncio
import sys
from pathlib import Path
project = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project))
from app.db.session import create_db_engine
from app.db.models import Base as CrawlerBase
from app.db.content_schema import Base as MediaCrawlerBase


async def main():
    engine = create_db_engine()
    async with engine.begin() as conn:
        await conn.run_sync(CrawlerBase.metadata.create_all)
        await conn.run_sync(MediaCrawlerBase.metadata.create_all)
    print('Crawler and MediaCrawler tables ready; existing rows preserved.')
    await engine.dispose()

asyncio.run(main())
