import argparse
import asyncio

from loguru import logger

from engines.insight_agent.tools.vector_search.repository import VectorSearchRepository
from engines.insight_agent.tools.vector_search.source.reader import SourceDocumentReader


async def sync_data(drop_existing: bool = True) -> int:
    milvus_repository = VectorSearchRepository()
    source_reader = SourceDocumentReader()

    milvus_repository.ensure_collection(drop_existing=drop_existing)

    all_docs = await source_reader.get_all_documents()
    count = milvus_repository.upsert_documents(all_docs)

    logger.info(f"Milvus 同步完成 总计={count}")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="同步MySQL数据到Milvus")
    parser.add_argument("--drop-existing", action="store_true", help="删除重建集合.")
    args = parser.parse_args()
    asyncio.run(sync_data(drop_existing=args.drop_existing))
