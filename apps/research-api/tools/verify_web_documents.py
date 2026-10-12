"""Read the real shared database; never calls a model or writes synthetic evidence."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engines.media_agent.local_documents import search_local_documents
from engines.insight_agent.tools.connection import close_async_engine

async def main():
    try:
        records = await search_local_documents("Python 3.12 发布")
        assert len(records) == 1
        assert records[0].url == "https://docs.python.org/3.12/whatsnew/3.12.html"
        assert len(records[0].content) > 80 and records[0].id.startswith("web:")
        assert await search_local_documents("unrelated_topic_no_match") == []
        print("PASS: real webpage document recalled by Media Agent, unrelated topic excluded")
    finally:
        await close_async_engine()

if __name__ == "__main__":
    asyncio.run(main())
