from typing import Mapping, cast

from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy import DECIMAL, cast as sa_cast, column, func, literal, literal_column

from engines.insight_agent.tools.platform_mappings import PlatformSearchMapping, ContentTableMapping, \
    CommentTableMapping
from engines.insight_agent.tools.hotness import HotScoreWeights
from engines.insight_agent.tools.hotness import ENGAGEMENT_METRICS


def content_search_columns(platform_mapping: PlatformSearchMapping) -> list[ColumnElement]:
    # 1. 获取平台内容表映射
    content_mapping = platform_mapping.content_mapping

    # 2. 返回列对象列表
    return [
        literal(platform_mapping.platform_name).label("platform"),
        literal(content_mapping.table_name).label("source_table"),
        column("id").label("mysql_pk"),
        column(content_mapping.text_col).label("title"),
        column(content_mapping.published_at_col).label("published_at"),
        column(content_mapping.source_keyword_col).label("source_keyword"),
    ]


def comment_search_columns(platform_mapping: PlatformSearchMapping) -> list[ColumnElement]:
    """
    评论表列投影
    """
    comment_mapping = platform_mapping.comment_mapping
    return [
        literal(platform_mapping.platform_name).label("platform"),
        literal(comment_mapping.table_name).label("source_table"),
        column("id").label("mysql_pk"),
        column(comment_mapping.text_col).label("title"),
        column(comment_mapping.published_at_col).label("published_at"),
        literal_column("NULL").label("source_keyword"),
    ]


def engagement_metric_columns(engagement_column_map: Mapping[str, str]) -> list[ColumnElement]:
    result_columns = []
    # 1. 遍历所有的参与度指标
    for engagement_metric in ENGAGEMENT_METRICS:

        # 2. 判断当前指标是否在映射字典中
        if engagement_metric in engagement_column_map:
            # 如果在字典中：获取对应的列名，并 处理safe_number_column
            mapped_column = engagement_column_map[engagement_metric]
            base_column = safe_number_column(mapped_column)
        else:
            # 如果不在字典中：提供一个默认的 0 列
            base_column = literal_column("0")

        # 3. 统一给该列加上 AS 别名 (label)
        labeled_column = base_column.label(f"eng_{engagement_metric}")

        result_columns.append(labeled_column)

    # 4. 返回最终的列表
    return result_columns


def hot_score_metric_column(
        table_mapping: ContentTableMapping | CommentTableMapping,
) -> ColumnElement:
    """基于平台各互动指标及对应权重，动态生成热度计算的 SQL 表达式。"""
    hotness_expression = None

    metric_weights = HotScoreWeights()
    for metric_key, db_column_name in table_mapping.engagement_cols.items():

        current_weight = getattr(metric_weights, metric_key)

        weighted_metric_term = safe_number_column(db_column_name) * current_weight

        if hotness_expression is None:
            hotness_expression = weighted_metric_term
        else:
            hotness_expression = hotness_expression + weighted_metric_term

    return cast(ColumnElement, hotness_expression).label("hotness_score")


def safe_number_column(col_name: str) -> ColumnElement:
    return func.coalesce(sa_cast(column(col_name), DECIMAL), 0.0)
