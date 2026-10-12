from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class VectorDocument:
    doc_id: str
    platform: str
    source_table: str
    mysql_pk: int
    content: str

    published_at: int | datetime
    source_keyword: str

    likes: float = 0.0
    comments: float = 0.0
    shares: float = 0.0
    collects: float = 0.0
    replies: float = 0.0
    hotness_score: float = 0.0

    def to_milvus_record(
            self,
            dense_vector: list[float],
            sparse_vector: dict[int, float],
    ) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "source_table": self.source_table,
            "doc_id": self.doc_id,
            "mysql_pk": self.mysql_pk,
            "content": self.content,
            "published_at": self.published_at,
            "source_keyword": self.source_keyword,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "collects": self.collects,
            "replies": self.replies,
            "hotness_score": self.hotness_score,
            "dense_vector": dense_vector,
            "sparse_vector": sparse_vector,
        }


@dataclass(frozen=True)
class SearchHit:
    """向量检索命中结果。"""
    retrieval_score: float
    retrieval_channel: str
    retrieval_doc: VectorDocument
