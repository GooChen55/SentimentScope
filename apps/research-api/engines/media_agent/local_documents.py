"""Public documents collected by Sentinel share the research database."""
from sqlalchemy import text
from engines.insight_agent.tools.connection import get_async_engine
from engines.contracts.evidence.models import EvidenceRecord

async def search_local_documents(topic):
    if not topic.strip():
        return []
    engine = get_async_engine()
    async with engine.connect() as conn:
        exists = (await conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'crawler_document'"))).scalar()
        if not exists:
            return []
        rows = await conn.execute(text("SELECT id, url, title, content, topic, published_at FROM crawler_document WHERE topic = :topic ORDER BY collected_at DESC LIMIT 10"), {"topic": topic.strip()})
        return [EvidenceRecord(id="web:" + row["id"], platform="web", source_table="crawler_document",
                source_keyword=row["topic"], content=row["title"] + "\n" + row["content"][:8000] + ("\n[研判输入已截断，完整内容见来源网页]" if len(row["content"]) > 8000 else ""),
                published_at=row["published_at"] or "", url=row["url"]) for row in rows.mappings()]
