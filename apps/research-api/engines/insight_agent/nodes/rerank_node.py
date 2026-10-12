from collections import defaultdict
from typing import Any
from engines.insight_agent.state import InsightState
from engines.common.nodes.base_node import BaseNode, ResearchNodeContext
from engines.contracts.evidence.models import EvidenceRecord, RetrievalMeta

_CHANNEL_WEIGHTS = {
    "semantic_recall": 0.5,
    "keyword_recall": 0.4,
    "comment_recall": 0.4,
    "hot_recall": 0.20,
}

SOURCE_QUOTAS = {
    "keyword_recall": 10,
    "semantic_recall": 10,
    "comment_recall": 20,
    "hot_recall": 10,
}

MAX_EVIDENCE_RECORDS = 50


class RerankNode(BaseNode):

    def __init__(self, context: ResearchNodeContext) -> None:
        super().__init__(context)

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        # 1. 获取evidence_pool
        evidence_pool = state['evidence_pool']

        # 2. 获取records
        records = evidence_pool.records

        # 3. 去重、合并
        merged_records = _dedupe_and_merge(records)

        # 4. 打分、排序
        sorted_records = _score_and_sort(merged_records)

        # 5. 根据通道选择指定的证据记录对象列表【通道配额筛选】
        evidence_records = _apply_channel_quotas(sorted_records)

        # 4. 更新state的证据池中的证据记录
        evidence_pool.records = evidence_records

        # 5. 返回
        return {"evidence_pool": evidence_pool}


def _dedupe_and_merge(records: list[EvidenceRecord]) -> list[EvidenceRecord]:
    # 1. 判断是否有证据记录
    if not records:
        return []

    # 2. 遍历(去除重复的：MySQL三个通道的检索会不会重复？有可能：query:分词:【分词1.分词2】---分词1，分词2都获取到了同一条数据  Milvus中返回的查询记录可也可能和MySQL中查询某张表记录重复)
    # 2.1 基于ID即可

    records_by_id: dict[str, EvidenceRecord] = {}
    for record in records:

        # 1. 获取记录ID
        record_id = record.id

        # 2. 判断当前记录ID是否已经存在
        if record_id not in records_by_id:
            records_by_id[record_id] = record
            continue

        # 3. 当前记录已经存在(不是剔除掉重复的记录，而是利用重复的记录)
        # 3.1 更新当前记录的热度值(找同一条记录中最大热度值的那一个)
        # 3.2 更新当前记录的检索元数据（更新检索元数据的查询【字符串相加】、更新检索元数据的通道【字符串相加】 更新元数据的检索分数:复杂一点）

        base_record = records_by_id[record_id]
        base_record.retrieval = _merge_retrieval_meta(base_record, record)
        base_record.hotness_score = max(base_record.hotness_score,
                                        record.hotness_score)  # 两套规则计算热度值（多源数据:Milvus中的数据和MySQL中一致）

    # 4. 重复记录（利用起来）
    return list(records_by_id.values())


def _merge_retrieval_meta(base_record: EvidenceRecord,
                          new_record: EvidenceRecord) -> RetrievalMeta:
    # base_record:retrieval_scores==dict[str,float]  {"sematic_recall":0.35}
    # new_record:retrieval_scores==dict[str,float]  {"keyword":0.7}

    base_record.retrieval.retrieval_scores.update(new_record.retrieval.retrieval_scores)
    return RetrievalMeta(
        matched_queries=sorted(set(base_record.retrieval.matched_queries + new_record.retrieval.matched_queries)),
        retrieval_channels=sorted(
            set((base_record.retrieval.retrieval_channels + new_record.retrieval.retrieval_channels))),
        retrieval_scores=base_record.retrieval.retrieval_scores,
    )


def _retrival_score(merged_record: EvidenceRecord) -> float:
    # merged_record:  retrieval_channels:["sematic_recall","hot_recall"] retrieval_scores:{"sematic_recall":0.6,"hot_recall":0.4}
    meta = merged_record.retrieval
    return min(sum(meta.retrieval_scores[channel] * _CHANNEL_WEIGHTS[channel] for channel in meta.retrieval_channels),
               1.0)


def _score_and_sort(merged_records: list[EvidenceRecord]) -> list[EvidenceRecord]:
    if not merged_records:
        return []
    # EvidenceRecord对象的检索元数据的通道就有可能是多个["keyword_recall","sematic_recall"]
    max_hot_score = max([merged_record.hotness_score for merged_record in merged_records]) or 1.0
    for merged_record in merged_records:
        # 总得分（二因子）检索相关得分*0.6+热度值*0.4
        final_score = (_retrival_score(merged_record) * 0.6 + ((merged_record.hotness_score / max_hot_score) * 0.4))
        merged_record.final_score = final_score

    return sorted(merged_records, key=lambda record: record.final_score, reverse=True)


def _apply_channel_quotas(sorted_records: list[EvidenceRecord]) -> list[EvidenceRecord]:
    selected_records = []
    channel_count: dict[str, int] = defaultdict(int)
    for record in sorted_records:
        channel = _SOURCE_QUOTAS(record)
        if channel_count[channel] < SOURCE_QUOTAS[channel]:
            selected_records.append(record)
            channel_count[channel] += 1

    if len(selected_records) < MAX_EVIDENCE_RECORDS:
        selected_ids = [r.id for r in selected_records]
        remainders = [r for r in sorted_records if r.id not in selected_ids]
        selected_records.extend(remainders[:(MAX_EVIDENCE_RECORDS - len(selected_ids))])

    return sorted(selected_records, key=lambda record: record.final_score, reverse=True)


def _SOURCE_QUOTAS(record: EvidenceRecord) -> str:
    record_channels = record.retrieval.retrieval_channels
    # record:retrieval_channels ["hot_recall","comment_recall"]
    for channel in SOURCE_QUOTAS:
        if channel in record_channels:
            return channel

    return "other"


if __name__ == "__main__":
    import asyncio
    from dataclasses import dataclass, field


    @dataclass
    class EvidenceRecord:
        id: str
        content: str
        hotness_score: float
        retrieval: RetrievalMeta
        final_score: float = 0.0


    @dataclass
    class EvidencePool:
        records: list[EvidenceRecord]


    async def run_test():
        print("=== 开始初始化 RankNode 测试 ===")

        # 构造测试数据
        mock_records = [
            # 这两条 ID 相同，用来测试去重合并 (多路召回了同一条帖子)
            EvidenceRecord(
                id="doc_1", content="高考数学太难了！", hotness_score=100.0,
                retrieval=RetrievalMeta(["高考"], ["keyword_recall"], {"keyword_recall": 0.5})
            ),
            EvidenceRecord(
                id="doc_1", content="高考数学太难了！", hotness_score=150.0,  # 模拟热度更新
                retrieval=RetrievalMeta(["高考难"], ["semantic_recall"], {"semantic_recall": 0.35})
            ),

            # 其他通道的数据
            EvidenceRecord(
                id="doc_2", content="大家放平心态，加油！", hotness_score=500.0,
                retrieval=RetrievalMeta(["高考"], ["hot_recall"], {"hot_recall": 0.4})
            ),
            EvidenceRecord(
                id="doc_3", content="评论区也是一片哀嚎...", hotness_score=20.0,
                retrieval=RetrievalMeta(["高考"], ["comment_recall"], {"comment_recall": 0.2})
            ),
        ]

        state = {
            "evidence_pool": EvidencePool(records=mock_records)
        }

        # 执行节点 (绕过 __init__ 传 ctx 的强制要求)
        node = RerankNode(context=None)
        result_state = await node(state)

        # 验证结果
        final_records = result_state["evidence_pool"].records
        print(f"\n排序节点执行完毕！")
        print(f"原始记录数: {len(mock_records)} -> 最终记录数: {len(final_records)} (成功去重并分配)")
        print("-" * 60)

        for i, record in enumerate(final_records, 1):
            print(f"[{i}] ID: {record.id} | 最终得分: {record.final_score:.4f} | 热度: {record.hotness_score}")
            print(f"    包含渠道: {record.retrieval.retrieval_channels}")
            print(f"    原始分数: {record.retrieval.retrieval_scores}")
            print("-" * 60)


    # 启动测试
    asyncio.run(run_test())
