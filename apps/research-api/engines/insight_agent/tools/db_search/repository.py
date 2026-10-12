import asyncio
from typing import Any, Callable
from loguru import logger

from sqlalchemy import column, desc, union_all

from engines.insight_agent.tools.db_search.search_results import SearchResponse, SearchRecord
from engines.insight_agent.tools.platform_mappings import PLATFORM_MAPPING
from engines.insight_agent.tools.db_search.queries.builder import (
    build_content_search_query,
    build_comment_search_query,
    build_hotness_query
)
from engines.insight_agent.tools.connection import get_async_engine
from engines.insight_agent.tools.db_search.record_mapper import db_row_to_search_record
from engines.insight_agent.tools.hotness import HotRecallPeriod

RecordMapper = Callable[[dict[str, Any]], SearchRecord]


class DatabaseSearchRepository:

    async def hot_recall(
            self,
            time_period: HotRecallPeriod = 'week',
            limit: int = 20
    ) -> SearchResponse:

        select_queries = [
            build_hotness_query(platform_mapping, time_period, limit)
            for platform_mapping in PLATFORM_MAPPING.values()
        ]

        statement = union_all(*select_queries).order_by(desc(column("hotness_score"))).limit(limit)

        return await self._execute_search(
            channel="hot_recall",
            statement=statement,
            record_mapper=db_row_to_search_record,
        )

    async def keyword_recall(self, topic_keyword: str, limit: int = 20) -> SearchResponse:

        # 1. 构造 SQL 模糊查询所需的关键词格式 (例如: "%高考%")
        search_term = f"%{topic_keyword}%"

        # 2. 构建跨平台搜索语句
        select_queries = [
            build_content_search_query(platform_mapping, search_term, limit)
            for platform_mapping in PLATFORM_MAPPING.values()
        ]

        # 3. 构建两张表关联查询语句
        statement = union_all(*select_queries).order_by(desc(column("published_at")))

        # 4. 数据库执行联合 SQL，并将每行数据映射为标准对象，返回搜索结果对象
        return await self._execute_search(
            channel="keyword_recall",
            statement=statement,
            record_mapper=db_row_to_search_record,
        )

    async def comment_recall(self, comment_keyword: str, limit: int = 60) -> SearchResponse:
        """
        两个平台的评论表召回 专门为了保障评论/情绪/观点类证据覆盖
        """

        # 1.构建搜索关键字条目
        search_term = f"%{comment_keyword}%"

        # 2. 构建跨平台搜索SELECT语句
        select_queries = [
            build_comment_search_query(adapter, search_term, limit)
            for adapter in PLATFORM_MAPPING.values()
        ]

        # 3. 构建两张表关联查询语句
        statement = union_all(*select_queries).order_by(desc(column("published_at"))).limit(limit)

        # 4. 执行查询
        return await self._execute_search(
            channel="comment_recall",
            statement=statement,
            record_mapper=db_row_to_search_record,
        )

    async def _execute_search(
            self,
            *,
            channel: str,
            statement: Any,
            record_mapper: RecordMapper,
    ) -> SearchResponse:

        # 1. 获取查询记录
        rows = []
        error_message = None
        try:
            rows = await self._fetch_rows(statement)
        except Exception as e:
            error_message = str(e)
            logger.exception(f"数据库查询时发生错误: {e}")

        # 2. 结果映射InsightSearchRecord
        records = self._map_rows(rows, record_mapper)

        # 3. 封装查询响应
        return SearchResponse(
            retrieval_channel=channel,
            search_results=records,
            search_results_count=len(records),
            search_error_message=error_message,
        )

    @staticmethod
    async def _fetch_rows(select_statement) -> list[dict[str, Any]]:
        """执行 SQL 并返回字典列表"""
        engine = get_async_engine()
        async with engine.connect() as conn:
            result = await conn.execute(select_statement)
            rows = result.mappings().all()
            return [dict(row) for row in rows]

    @staticmethod
    def _map_rows(rows: list[dict[str, Any]], row_mapper: RecordMapper) -> list[SearchRecord]:
        records: list[SearchRecord] = []
        for row in rows:
            records.append(row_mapper(row))
        return records

async def main_test():
    from engines.insight_agent.tools.connection import close_async_engine
    repo =DatabaseSearchRepository()

    # 1. 测试内容表关键词召回 (keyword_recall)
    print("=" * 50)
    print("测试 1: 开始跨平台【内容】召回测试")
    print("=" * 50)

    keyword = "高考"

    keyword_response = await repo.keyword_recall(topic_keyword=keyword, limit=20)

    print(f"召回渠道: {keyword_response.retrieval_channel}")
    print(f"召回总数: {keyword_response.search_results_count} 条")
    for i, record in enumerate(keyword_response.search_results, 1):
        content_preview = record.title_or_content[:20]
        print(f"  [{i}] 平台: {record.platform:<8} | 表: {record.source_table:<20} | 热度分: {record.hotness_score:<6}| 内容: {content_preview}...")

    # 2. 测试评论表召回 (comment_recall)
    print("=" * 50)
    print("测试 2: 开始跨平台【评论】召回测试")
    print("=" * 50)

    comment_kw = "太难了"

    comment_response = await repo.comment_recall(comment_keyword=comment_kw, limit=5)

    print(f"召回渠道: {comment_response.retrieval_channel}")
    print(f"召回总数: {comment_response.search_results_count} 条")
    for i, record in enumerate(comment_response.search_results, 1):
        content_preview = record.title_or_content[:20]
        print(f"  [{i}] 平台: {record.platform:<8} | 表: {record.source_table:<20}  | 热度分: {record.hotness_score:<6}  | 评论: {content_preview}...")

    print("\n 所有测试执行完毕！")

    # print("=" * 50)
    # print("测试 3: 开始跨平台【热门/高赞】召回测试")
    # print("=" * 50)
    #
    # hot_response = await repo.hot_recall(time_period='year', limit=10)
    #
    # print(f"召回渠道: {hot_response.retrieval_channel}")
    # print(f"召回总数: {hot_response.search_results_count} 条")

    # for i, record in enumerate(hot_response.search_results, 1):
    #     content_preview = record.title_or_content[:20]
    #     hot_score = getattr(record, 'hotness_score')
    #     print(
    #         f"  [{i}] 平台: {record.platform:<8} | 表: {record.source_table:<20} | 热度分: {hot_score:<6} | ID: {record.mysql_pk} | 内容: {content_preview}...")

    await close_async_engine()


if __name__ == "__main__":
    asyncio.run(main_test())
