"""共享证据契约:核心记录实体 + 强度评分。

本模块只保留跨域共享的证据数据模型:
- EvidenceRecord:insight 双通道召回与 media 网页搜索召回的统一数据载体,及其内嵌值对象 Engagement / RetrievalMeta(media 留空即可)。
- 证据强度类型

insight 私有的聚合根(EvidenceCluster / EvidencePool / SectionEvidencePack)回归 engines.insight_agent.evidence_processor,不再托管全局契约。
media 私有的 SectionEvidencePack 位于 engines.media_agent.evidence_processor。
"""



from dataclasses import dataclass, field
from typing import Optional,Literal

EvidenceStrength = Literal["missing", "weak", "medium", "strong"]

# ===== 证据核心实体 =====

@dataclass(slots=True)
class Engagement:
    """互动数据(点赞/评论/转发/收藏/回复)。media 网页证据通常没有该数据,保留默认零值即可。"""
    likes: float = 0.0
    comments: float = 0.0
    shares: float = 0.0
    collects: float = 0.0
    replies: float = 0.0


@dataclass(slots=True)
class RetrievalMeta:
    """召回过程元数据(命中的查询词/通道/各通道分数)。media 单通道召回时同样适用。"""

    matched_queries: list[str] = field(default_factory=list)
    retrieval_channels: list[str] = field(default_factory=list)
    retrieval_scores: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class EvidenceRecord:
    """证据记录:insight 双通道 DB/向量召回与 media 网页搜索召回的统一数据载体。"""

    # 溯源身份标识
    id: str
    platform: str
    source_table: str
    source_keyword: Optional[str]

    # 核心业务内容
    content: str
    published_at: str

    # 打分状态
    hotness_score: float = 0.0
    final_score: float = 0.0

    # 拓扑对象
    cluster_id: str = ""
    engagement: Engagement = field(default_factory=Engagement)
    retrieval: RetrievalMeta = field(default_factory=RetrievalMeta)

    # media 网页证据专属字段(insight DB/向量证据留空即可,不参与其排序/聚类逻辑)
    url: str = ""
