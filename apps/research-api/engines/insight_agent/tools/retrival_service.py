import asyncio
from datetime import datetime, timedelta

import jieba.analyse
from dataclasses import dataclass
from typing import Literal, Optional
from loguru import logger

from engines.contracts.evidence.models  import EvidenceRecord, Engagement, RetrievalMeta
from engines.insight_agent.tools.db_search.repository import DatabaseSearchRepository
from engines.insight_agent.tools.vector_search.search_results import SearchHit
from engines.insight_agent.tools.db_search.search_results import SearchResponse, SearchRecord

RetrievalChannel = Literal["keyword_recall", "comment_recall", "hot_recall"]


@dataclass(slots=True)
class RetrievalQueryTask:
    channel: RetrievalChannel  # 查询通道
    limit: int  # 通道返回的查询结果
    channel_score: float
    query: str = ""  # 查询的词


def build_retrieval_tasks(query: str) -> list[RetrievalQueryTask]:
    """
    本质：query：去三通道检索  分词：两个通道检索
    原始查询：query: hot_recall通道检索
    分后词+原始的query：kw1:二通道检索 kw2:二通道检索 query:二通道检索
    :param query:
    :return:
    """

    final_query = []
    final_query.append(query)
    for extract_kw in _extract_keywords(query):
        if extract_kw not in final_query:
            final_query.append(extract_kw)
    retrieval_tasks: list[RetrievalQueryTask] = []
    for keyword in final_query:
        retrieval_tasks.append(RetrievalQueryTask(channel="keyword_recall", limit=10, channel_score=0.5, query=keyword))
        retrieval_tasks.append(RetrievalQueryTask(channel="comment_recall", limit=5, channel_score=0.4, query=keyword))

    retrieval_tasks.append(RetrievalQueryTask(channel="hot_recall", channel_score=0.3, limit=5, query=query))

    return retrieval_tasks


def _extract_keywords(query: str) -> list[str]:
    return [keyword for keyword in jieba.analyse.extract_tags(query, 2) if 2 <= len(keyword) <= 4]


from engines.contracts.config import get_settings


class InsightRetrivalService:
    """
    调用MySQL以及Vector的搜索结果（搜索结果的转换以及最终返回）
    去重、排序、聚类.. 后续节点单独做
    """

    def __init__(self):
        self._db_repo = DatabaseSearchRepository()
        self._vec_repo = None

    async def retrival_evidence(self, query: str) -> list[EvidenceRecord]:
        # 1. 查询(调用MySQL[keyword_recall/comment_recall/hot_recall]/Vector)
        retrival_db_tasks = build_retrieval_tasks(query)

        # 2. '并发'查询MySQL以及Vector 且‘等’二路查询都返回最后的结果EvidenceRecord
        db_evidences, vec_evidences = await asyncio.gather(self._retrival_db_evidence(retrival_db_tasks),
                                                           self._retrival_vec_evidence(query))

        # 3. 返回
        return [*db_evidences, *vec_evidences]

    async def _retrival_vec_evidence(self, query) -> list[EvidenceRecord]:
        # 1. 是否启用Vector检索
        if not get_settings().INSIGHT_VECTOR_ENABLED:
            return []
        if self._vec_repo is None:
            from engines.insight_agent.tools.vector_search.repository import VectorSearchRepository
            self._vec_repo = VectorSearchRepository()

        # 2.异步线程执行查询Vector
        try:
            search_results = await  asyncio.to_thread(self._vec_repo.search, query=query, limit=10,
                                                      filter_expr=self.filter_expr())
        except Exception as e:
            logger.error(f"Vector检索失败,查询={query} 原因={str(e)}")
            return []  # 保证db路检索正常

        # 3. 返回EvidenceRecord对象列表
        return map_vector_record(query, search_results)

    def filter_expr(self) -> str:
        days = get_settings().INSIGHT_VECTOR_FILTER_DAYS
        start_ts = int((datetime.now() - timedelta(days=days)).timestamp())
        return f"published_at >= {start_ts}"

    async def _retrival_db_evidence(self, retrival_db_tasks: list[RetrievalQueryTask]) -> list[EvidenceRecord]:

        # 1. 各个通道都查询完(后的所有结果[1.SearchResponse() 2.SearchResponse()....])
        task_responses = await asyncio.gather(*[self._run_retrival_db_evidence(task) for task in retrival_db_tasks])

        # 2. 封装各个通道的检索结果
        final_search_results: list[EvidenceRecord] = []
        for retrival_task, response in zip(retrival_db_tasks, task_responses):
            final_search_results.extend(map_db_record(retrival_task, response))
        # 3. 解析各个通道的结果返回
        return final_search_results

    async def _run_retrival_db_evidence(self, task: RetrievalQueryTask) -> Optional[SearchResponse]:
        db_repo = self._db_repo
        match task.channel:
            case "keyword_recall":
                return await db_repo.keyword_recall(task.query, limit=task.limit)
            case "comment_recall":
                return await db_repo.comment_recall(task.query, limit=task.limit)
            case "hot_recall":
                return await db_repo.hot_recall(time_period="year", limit=task.limit)
            case _:
                logger.error(f"通道 {task.channel} 未知...")
                return None


def map_db_record(retrival_task: RetrievalQueryTask,
                  response: SearchResponse) -> list[EvidenceRecord]:
    return [_map_to_db_record(retrival_task, record) for record in response.search_results]


def _map_to_db_record(retrival_task: RetrievalQueryTask, record: SearchRecord) -> EvidenceRecord:
    return EvidenceRecord(
        id=record.mysql_pk,  # 唯一（平台名+表名+主键）
        platform=record.platform,
        source_table=record.source_table,
        source_keyword=record.source_keyword,
        content=record.title_or_content,
        published_at=record.published_at.strftime("%Y-%m-%d %H:%M:%S"),
        hotness_score=record.hotness_score,
        engagement=Engagement(
            likes=record.engagement.get("likes", 0),
            comments=record.engagement.get("comments", 0),
            shares=record.engagement.get("shares", 0),
            collects=record.engagement.get("collects", 0),
            replies=record.engagement.get("replies", 0),
        ),
        retrieval=RetrievalMeta(
            matched_queries=[retrival_task.query],
            retrieval_channels=[retrival_task.channel],
            retrieval_scores={retrival_task.channel: retrival_task.channel_score}
        )

    )


def map_vector_record(query: str, search_results: list[SearchHit]) -> list[EvidenceRecord]:
    return [_map_to_vector_record(query, result) for result in search_results]


def _map_to_vector_record(query: str, result: SearchHit) -> EvidenceRecord:
    doc = result.retrieval_doc
    return EvidenceRecord(
        id=doc.doc_id,
        platform=doc.platform,
        source_table=doc.source_table,
        source_keyword=doc.source_keyword,
        content=doc.content,
        published_at=doc.published_at.strftime("%Y-%m-%d %H:%M:%S"),
        hotness_score=doc.hotness_score,
        engagement=Engagement(
            likes=doc.likes,
            comments=doc.comments,
            shares=doc.shares,
            collects=doc.collects,
            replies=doc.replies
        ),
        retrieval=RetrievalMeta(
            matched_queries=[query],
            retrieval_channels=[result.retrieval_channel],
            retrieval_scores={result.retrieval_channel: result.retrieval_score}  # {"semantic_recall":[0.2]}
        )
    )


if __name__ == '__main__':

    async def main_test():
        retriever = InsightRetrivalService()
        test_query = "高考难吗"

        logger.info(f"测试3 整体编排召回, Query: '{test_query}'")
        all_results = await retriever.retrival_evidence(test_query)
        logger.info(f"整体召回完成，总计汇总证据: {len(all_results)} 条")

        # 各个通道的分布情况
        channel_counts = {}
        for r in all_results:
            ch = r.retrieval.retrieval_channels[0]
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

        logger.info(f"通道分布统计: {channel_counts}")

        # tasks = build_retrieval_tasks(test_query)
        # logger.info(f"生成了 {len(tasks)} 个 DB 召回任务: {[t.channel for t in tasks]}")
        #
        #
        # # 获取所有检索结果
        # db_results = await retriever._retrival_db_evidence(tasks)
        #
        # logger.info(f"DB召回完成，共获取证据: {len(db_results)} 条")
        # grouped_results = defaultdict(list)
        # for record in db_results:
        #     query = record.retrieval.matched_queries[0]
        #     channel = record.retrieval.retrieval_channels[0]
        #     grouped_results[(query, channel)].append(record)
        #
        # print("词、通道检索结果统计：")
        #
        # for (query, channel), records in grouped_results.items():
        #     # 打印每个分类的汇总数量
        #     print(f"检索词: 【{query}】 | 通道: 【{channel}】 | 记录数: {len(records)} 条")
        #     for idx, record in enumerate(records, 1):
        #         short_content = record.content[:50] + '...'
        #         print(f"   [{idx}] ID: {record.id} | 表: {record.source_table} | 内容: {short_content}")
        #
        #     print("-" * 60)


    asyncio.run(main_test())
