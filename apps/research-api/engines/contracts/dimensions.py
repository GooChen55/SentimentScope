"""五维研究框架契约。"""

from dataclasses import dataclass




@dataclass(frozen=True)
class ResearchDimension:
    key: str
    title: str
    insight_goal: str
    media_goal: str
    insight_cluster_rule: tuple[str, ...] | None = None


# 直接定义为字典，Key 就是 section_key，Value 是 ResearchDimension 对象
DIMENSIONS: dict[str, ResearchDimension] = {
    "background_overview": ResearchDimension(
        key="background_overview",
        title="事件背景与概览",
        insight_goal="说明事件主线、库内可见讨论范围、关键时间点和基础事实。",
        media_goal="梳理媒体侧基础报道、首发信息、权威信源和事实框架。",
        insight_cluster_rule=("通报", "回应", "发布", "声明", "官方", "现场", "视频", "消息", "事件", "起因"),
    ),
    "heat_and_spread": ResearchDimension(
        key="heat_and_spread",
        title="舆情热度与传播",
        insight_goal="分析高热内容、传播节奏、互动特征和平台热度差异。",
        media_goal="分析报道热度、扩散节点、传播节奏和关键媒体/平台来源。",
        insight_cluster_rule=("热搜", "传播", "转发", "评论", "点赞", "爆料", "关注", "刷屏", "扩散", "趋势"),
    ),
    "sentiment_and_opinion": ResearchDimension(
        key="sentiment_and_opinion",
        title="公众情感与观点",
        insight_goal="提炼主要情绪倾向、观点类型、代表性用户声音和共识/分歧。",
        media_goal="分析公开报道和评论反馈中的情绪倾向、观点阵营和意见领袖表达。",
        insight_cluster_rule=("支持", "反对", "质疑", "吐槽", "愤怒", "担心", "理解", "争议", "态度", "看法"),
    ),
    "platform_and_group_diff": ResearchDimension(
        key="platform_and_group_diff",
        title="平台与群体差异",
        insight_goal="比较微博/抖音、帖子/评论之间的讨论重点、表达风格和人群侧重。",
        media_goal="比较官方媒体、市场化媒体、自媒体及不同平台渠道的叙事差异。",
        insight_cluster_rule=("微博", "抖音", "小红书", "快手", "网友", "专家", "媒体", "大V", "粉丝", "网民", "自媒体")
    ),
    "deep_causes_and_impact": ResearchDimension(
        key="deep_causes_and_impact",
        title="深层原因与影响",
        insight_goal="分析社会心理、争议成因、潜在影响和后续舆情风险。",
        media_goal="分析媒体议程设置、社会背景、争议成因、外溢影响和传播风险。",
        insight_cluster_rule=(
            "原因", "影响", "风险", "后续", "舆论", "危机", "信任", "社会", "背后", "监管", "处罚", "问责")
    ),
}


def dimension_for_key(key: str) -> ResearchDimension:
    return DIMENSIONS.get(key)


def get_insight_dimensions() -> list[dict[str, str]]:
    """获取 InsightAgent (私有舆情库) 专属的维度及分析目标。"""
    return [
        {
            "section_key": dimension.key,
            "title": dimension.title,
            "analysis_goal": dimension.insight_goal,
        }
        for dimension in DIMENSIONS.values()
    ]


def get_media_dimensions() -> list[dict[str, str]]:
    """获取 MediaAgent (公开媒体库) 专属的维度及分析目标。"""
    return [
        {
            "section_key": dimension.key,
            "title": dimension.title,
            "analysis_goal": dimension.media_goal,
        }
        for dimension in DIMENSIONS.values()
    ]


def get_insight_cluster_rules() -> dict[str, tuple[str, ...]]:
    """提取所有配置了 insight_cluster_rule 的维度规则。"""
    return {
        dimension.key: dimension.insight_cluster_rule
        for dimension in DIMENSIONS.values()
        if dimension.insight_cluster_rule is not None
    }
