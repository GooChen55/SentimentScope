"""InsightAgent 聚类节点：实现语义优先、规则兜底的舆情数据簇化处理。"""

from collections import defaultdict
from functools import lru_cache
from typing import Any

import numpy as np
from loguru import logger
from engines.common.nodes.base_node import BaseNode, ResearchNodeContext
from engines.contracts.config import get_settings
from engines.contracts.dimensions import dimension_for_key, get_insight_cluster_rules
from engines.insight_agent.evidence_processor import EvidenceCluster, EvidenceRecord
from engines.insight_agent.state import InsightState


@lru_cache(maxsize=1)
def _get_embedding_model():
    """获取语义向量模型 (全局单例)"""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(str(get_settings().INSIGHT_CLUSTER_MODEL))


@lru_cache(maxsize=1)
def _get_dimension_vector():
    """计算五大维度的标准向量(用于语义路由)"""
    rules = get_insight_cluster_rules()

    # 组合维度标题与关键词
    dimension_texts = [
        f"{dimension_for_key(dim_key).title}: {' '.join(keywords)}"
        for dim_key, keywords in rules.items()
    ]

    dimension_keys = list(rules.keys())
    dimension_embeddings = _get_embedding_model().encode(
        dimension_texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )
    return dimension_keys, dimension_embeddings


class ClusterNode(BaseNode):
    """负责将证据池中的记录归类为语义簇或维度簇。"""

    def __init__(self, context: ResearchNodeContext) -> None:
        super().__init__(context)

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        logger.info("开始进行证据记录的聚类...")

        pool = state["evidence_pool"]
        pool.clusters = self._cluster_evidence(pool.records)

        cluster_summary = ", ".join(f"{cluster.id}: {cluster.size}条" for cluster in pool.clusters)
        logger.info(f"聚类完成，共生成 {len(pool.clusters)} 个簇，分布情况: {cluster_summary}")

        return {"evidence_pool": pool}

    def _cluster_evidence(self, records: list[EvidenceRecord]) -> list[EvidenceCluster]:
        """执行聚类分区：根据配置选择语义聚类或规则聚类"""
        if self._is_semantic_enabled(records):
            return self._cluster_by_semantics(records)
        return self._cluster_by_rules(records)

    def _is_semantic_enabled(self, records: list[EvidenceRecord]) -> bool:
        settings = get_settings()
        return (
                settings.INSIGHT_CLUSTERING_ENABLED
                and bool(settings.INSIGHT_CLUSTER_MODEL)
                and len(records) >= settings.INSIGHT_CLUSTER_MIN_CLUSTER_SIZE
        )

    # 策略 1: 基于关键词匹配的规则聚类
    def _cluster_by_rules(self, records: list[EvidenceRecord]) -> list[EvidenceCluster]:
        cluster_data: dict[str, list[EvidenceRecord]] = defaultdict(list)

        for record in records:
            cluster_id = self._match_rule_key(record)
            record.cluster_id = cluster_id
            cluster_data[cluster_id].append(record)

        return self._assemble_clusters(cluster_data)

    def _match_rule_key(self, record: EvidenceRecord) -> str:
        text = f"{record.source_keyword} {record.content}"
        for dim_key, keywords in get_insight_cluster_rules().items():
            if any(k in text for k in keywords):
                return f"cluster_{dim_key}"   # cluster_background_overview
        return "cluster_other"

    # 策略 2: 基于 K-Means 的语义聚类
    def _cluster_by_semantics(self, records: list[EvidenceRecord]) -> list[EvidenceCluster]:
        settings = get_settings()
        sampled = records[:settings.INSIGHT_CLUSTER_MAX_RECORDS]
        contents = [f"{r.source_keyword} {r.content}".strip() for r in sampled]

        # 1. 向量化与 K-Means 计算
        embeddings = _get_embedding_model().encode(contents, normalize_embeddings=True, show_progress_bar=False)
        assignments = self._calculate_kmeans_labels(embeddings, len(sampled))

        # 2. 临时分组
        temp_groups: dict[int, list[EvidenceRecord]] = defaultdict(list)
        for record, label in zip(sampled, assignments):
            temp_groups[label].append(record)

        # 3. 语义路由：将自由簇对齐到标准维度
        cluster_data: dict[str, list[EvidenceRecord]] = defaultdict(list)
        for cluster_records in temp_groups.values():
            dim_key = self._route_to_dimension(cluster_records)
            cluster_id = f"cluster_{dim_key}"
            for record in cluster_records:
                record.cluster_id = cluster_id
                cluster_data[cluster_id].append(record)

        return self._assemble_clusters(cluster_data)

    def _calculate_kmeans_labels(self, embeddings: Any, count: int) -> list[int]:
        from sklearn.cluster import KMeans
        # k>=5(k固定是5 或者count//桶的最小数：INSIGHT_CLUSTER_MIN_CLUSTER_SIZE>5)
        k = self._determine_optimal_k(count)
        # doc1    doc2   doc3   doc4  doc5
        # [向量值  向量值  向量值  向量值 向量值]
        # [0,      1,    0,      2,   1]
        return [int(l) for l in KMeans(n_clusters=5, n_init="auto", random_state=42).fit_predict(embeddings)]

    def _determine_optimal_k(self, count: int) -> int:
        settings = get_settings()
        # 理论值：理论桶数多少
        k = count // settings.INSIGHT_CLUSTER_MIN_CLUSTER_SIZE
        return max(2, min(settings.INSIGHT_CLUSTER_MAX_CLUSTERS, k, count))

    def _route_to_dimension(self, records: list[EvidenceRecord]) -> str:
        """计算簇中心与预置维度向量的余弦相似度，执行语义投递"""
        sample = " ".join(r.content[:30] for r in records[:10])
        emb = _get_embedding_model().encode([sample], normalize_embeddings=True, show_progress_bar=False)

        keys, dimension_embs = _get_dimension_vector()
        # 1. 计算当前文本向量与五大维度向量的相似度
        similarities = np.dot(emb, dimension_embs.T)[0]
        # 2. 选择相似度最高的维度 key
        return keys[int(np.argmax(similarities))]

    # 实体组装
    def _assemble_clusters(self, data: dict[str, list[EvidenceRecord]]) -> list[EvidenceCluster]:
        """将分区数据转换为领域实体 EvidenceCluster"""
        result: list[EvidenceCluster] = []
        for cluster_id, cluster_records in data.items():
            section_key = cluster_id.removeprefix("cluster_")
            dimension = dimension_for_key(section_key)
            label = dimension.title if dimension else "其他相关讨论"

            result.append(EvidenceCluster(
                id=cluster_id,
                label=label,
                summary=f"{label}相关讨论，共 {len(cluster_records)} 条证据。",
                member_record_ids=[r.id for r in cluster_records],
                representative_ids=[r.id for r in cluster_records[:5]],
                size=len(cluster_records),
            ))

        return sorted(result, key=lambda c: c.size, reverse=True)


if __name__ == "__main__":
    import asyncio
    import traceback
    from engines.insight_agent.evidence_processor  import EvidencePool, EvidenceRecord, Engagement, RetrievalMeta


    async def main():
        test_records = [
            EvidenceRecord(
                id="rec_1", platform="douyin", source_table="douyin_aweme", source_keyword="高考",
                content="6月7日全国卷高考数学考试正式开考，引发全网关注。", published_at="2026-06-07 12:00:00",
                hotness_score=95.0, final_score=95.0, cluster_id="",
                engagement=Engagement(likes=1000, comments=200),
                retrieval=RetrievalMeta(matched_queries=["高考难不难"], retrieval_channels=["keyword_recall"])
            ),
            EvidenceRecord(
                id="rec_2", platform="douyin", source_table="douyin_aweme", source_keyword="数学考试",
                content="2026年高考第一天结束，关于数学考试的背景讨论成为全网焦点。", published_at="2026-06-07 17:30:00",
                hotness_score=88.5, final_score=88.5, cluster_id="",
                engagement=Engagement(likes=5000, comments=1200),
                retrieval=RetrievalMeta(matched_queries=["高考难不难"], retrieval_channels=["keyword_recall"])
            ),
            EvidenceRecord(
                id="rec_3", platform="douyin", source_table="douyin_aweme", source_keyword="热度",
                content="抖音爆款视频播放量突破千万，单条点赞超200万，传播数据惊人。", published_at="2026-06-07 20:00:00",
                hotness_score=99.9, final_score=99.9, cluster_id="",
                engagement=Engagement(likes=2000000, comments=240000),
                retrieval=RetrievalMeta(matched_queries=["高考难不难"], retrieval_channels=["hot_recall"])
            ),
            EvidenceRecord(
                id="rec_4", platform="douyin", source_table="douyin_aweme", source_keyword="爆量",
                content="关于高考数学的应援视频获得极高传播热度分，转发量已经过十万。",
                published_at="2026-06-07 10:15:00",
                hotness_score=76.2, final_score=76.2, cluster_id="",
                engagement=Engagement(likes=3500, comments=450),
                retrieval=RetrievalMeta(matched_queries=["高考难不难"], retrieval_channels=["hot_recall"])
            ),
            EvidenceRecord(
                id="rec_5", platform="weibo", source_table="weibo_note", source_keyword="心态",
                content="题目真的太难了，写到手抖笔都握不住，考生的焦虑感拉满，都在疯狂吐槽。",
                published_at="2026-06-07 18:00:00",
                hotness_score=91.0, final_score=91.0, cluster_id="",
                engagement=Engagement(likes=800, comments=350),
                retrieval=RetrievalMeta(matched_queries=["高考难不难"], retrieval_channels=["keyword_recall"])
            ),
            EvidenceRecord(
                id="rec_6", platform="weibo", source_table="weibo_note", source_keyword="吐槽",
                content="出卷人是不是刚考完研啊，今年到底难么？简直让人心态炸了，网友纷纷自嘲。",
                published_at="2026-06-07 19:22:00",
                hotness_score=84.0, final_score=84.0, cluster_id="",
                engagement=Engagement(likes=1200, comments=580),
                retrieval=RetrievalMeta(matched_queries=["高考难不难"], retrieval_channels=["comment_recall"])
            ),

            EvidenceRecord(
                id="rec_7", platform="weibo", source_table="weibo_note", source_keyword="跨平台",
                content="跨平台数据显示，抖音以情感应援为主，小红书和微博则集中在事实性标签速报。",
                published_at="2026-06-08 09:00:00",
                hotness_score=62.0, final_score=62.0, cluster_id="",
                engagement=Engagement(likes=150, comments=45),
                retrieval=RetrievalMeta(matched_queries=["高考难不难"], retrieval_channels=["keyword_recall"])
            ),
            EvidenceRecord(
                id="rec_8", platform="weibo", source_table="weibo_note_comment", source_keyword="微博",
                content="不同群体在知乎上的讨论深度明显不同，微博端相关舆情声量微弱且存在明显差异。",
                published_at="2026-06-08 11:30:00",
                hotness_score=55.0, final_score=55.0, cluster_id="",
                engagement=Engagement(likes=90, comments=22),
                retrieval=RetrievalMeta(matched_queries=["高考难不难"], retrieval_channels=["comment_recall"])
            ),
            EvidenceRecord(
                id="rec_9", platform="weibo", source_table="weibo_note_comment", source_keyword="内卷",
                content="高考难度争议的深层原因本质上是教育代际竞争和内卷压力的具象投射。",
                published_at="2026-06-08 14:00:00",
                hotness_score=89.0, final_score=89.0, cluster_id="",
                engagement=Engagement(likes=4500, comments=890),
                retrieval=RetrievalMeta(matched_queries=["高考难不难"], retrieval_channels=["keyword_recall"])
            ),
            EvidenceRecord(
                id="rec_10", platform="weibo", source_table="weibo_note_comment", source_keyword="阶层",
                content="很多家长将高考选拔机制视为子女阶层跃迁的最后确定性通道，产生了深远的社会影响。",
                published_at="2026-06-08 16:45:00",
                hotness_score=93.4, final_score=93.4, cluster_id="",
                engagement=Engagement(likes=6200, comments=1100),
                retrieval=RetrievalMeta(matched_queries=["高考难不难"], retrieval_channels=["keyword_recall"])
            )
        ]

        # 2. 构建全局状态
        pool = EvidencePool(query="高考难不难", records=test_records, clusters=[])
        state: InsightState = {
            "query": "高考难不难",
            "role": "insight",
            "evidence_pool": pool
        }

        # 3. 模拟上下文
        class DummyContext:
            output_dir = "./output_test"
            llm_client = None

        node = ClusterNode(DummyContext())

        # 4. 压测
        try:
            output = await node(state)
            print("\n--- 测试执行成功，验证真实产出的聚类实体 ---")
            processed_pool = output["evidence_pool"]

            for cluster in processed_pool.clusters:
                print(f"[{cluster.label}] ID: {cluster.id} | 包含数据: {cluster.size}条")
                print(f"摘要描述: {cluster.summary}")
                print(f"核心代表记录(Top3): {cluster.representative_ids[:3]}")
                print("-" * 50)

        except Exception as e:
            print(f"测试运行失败 原因{str(e)}")
            traceback.print_exc()


    asyncio.run(main())
