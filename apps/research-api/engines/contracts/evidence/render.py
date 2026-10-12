"""公共证据文本格式化工具:insight/media 共用的 EvidenceRecord → LLM 证据文本渲染器"""

from engines.contracts.evidence.models import EvidenceRecord, Engagement
from typing import Literal


EvidenceStrength = Literal["missing", "weak", "medium", "strong"]



_ENGAGEMENT_LABELS = {
    "likes": "点赞",
    "comments": "评论",
    "shares": "转发",
    "collects": "收藏",
    "replies": "回复",
}


def evaluate_evidence_strength(hit_count: int) -> EvidenceStrength:
    """证据强度领域规则"""
    if hit_count >= 10:
        return "strong"
    if hit_count >= 5:
        return "medium"
    if hit_count > 0:
        return "weak"
    return "missing"


def render_evidence_records(records: list[EvidenceRecord]) -> list[str]:
    """将证据记录渲染为 LLM 写作用的文本块"""
    return [_render_single_record(record) for record in records]


def _render_single_record(record: EvidenceRecord) -> str:
    # 1. 标题
    lines = [f"证据引用编号: [{record.id}]", f"标题: {record.content[:30]}"]
    # 2. 平台
    lines.append(f"平台: {record.platform}")
    # 3. 来源
    lines.append(f"来源表/工具: {record.source_table}")
    # 4. 搜索关键词
    lines.append(f"来源关键词: {record.source_keyword}")
    # 5. 内容
    lines.append(f"内容: {_limit_content(record.content)}")
    # 6. 时间
    lines.append(f"发布时间/抓取时间: {record.published_at}")

    # 7. 热度值分数
    if record.hotness_score:
        lines.append(f"热度分: {record.hotness_score}")

    # 8. 最终得分
    if record.final_score:
        lines.append(f"综合分: {record.final_score}")

    # 9. 互动数据
    if record.engagement:
        lines.append(f"互动数据: { _format_engagement(record.engagement)}")

    # 10. url
    if record.url:
        lines.append(f"链接: {record.url}")

    return "\n".join(lines)



def _limit_content(content: str, max_length: int = 3000) -> str:
    if len(content) <= max_length:
        return content
    truncated = content[:max_length]
    return truncated + "..."

def _format_engagement(engagement: Engagement) -> str:
    parts = [
        f"{label} {value}"
        for key, label in _ENGAGEMENT_LABELS.items()
        if (value := getattr(engagement, key))
    ]
    return " / ".join(parts)
