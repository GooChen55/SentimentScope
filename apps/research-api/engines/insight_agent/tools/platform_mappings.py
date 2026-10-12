from typing import Any, Mapping
from dataclasses import dataclass


@dataclass
class ContentTableMapping:
    """
    "内容表" 映射
    """
    # 表名
    table_name: str
    # 内容
    text_col: str
    # 发布时间
    published_at_col: str
    # 搜索关键词
    source_keyword_col: str
    # 互动
    engagement_cols: Mapping[str, str]

    # 搜索字段
    search_fields: tuple[str, ...]


@dataclass
class CommentTableMapping:
    """
    "评论表" 映射
    """
    # 表名
    table_name: str
    # 内容
    text_col: str
    # 发布时间
    published_at_col: str
    # 互动
    engagement_cols: Mapping[str, str]   # 只读

    # 搜索字段
    search_fields: tuple[str, ...]


@dataclass
class PlatformSearchMapping:
    """
    平台搜索表映射
    """
    # 平台名字
    platform_name: str
    # 内容表
    content_mapping: ContentTableMapping
    # 评论表
    comment_mapping: CommentTableMapping


PLATFORM_MAPPING: dict[str, Any] = {

    "douyin": PlatformSearchMapping(
        platform_name="douyin",
        content_mapping=ContentTableMapping(
            table_name="douyin_aweme",
            text_col="title",
            published_at_col="create_time",
            source_keyword_col="source_keyword",
            engagement_cols={
                "likes": "liked_count",
                "comments": "comment_count",
                "shares": "share_count",
                "collects": "collected_count",
            },
            search_fields=("title", "source_keyword"),
        ),
        comment_mapping=CommentTableMapping(
            table_name="douyin_aweme_comment",
            text_col="content",
            published_at_col="create_time",
            engagement_cols={
                "likes": "like_count",
                "replies": "sub_comment_count",
            },
            search_fields=("content",)
        )
    ),
    "weibo": PlatformSearchMapping(
        platform_name="weibo",
        content_mapping=ContentTableMapping(
            table_name="weibo_note",
            text_col="content",
            published_at_col="create_time",
            source_keyword_col="source_keyword",
            engagement_cols={
                "likes": "liked_count",
                "comments": "comments_count",
                "shares": "shared_count",
            },
            search_fields=("content", "source_keyword")
        ),
        comment_mapping=CommentTableMapping(
            table_name="weibo_note_comment",
            text_col="content",
            published_at_col="create_time",
            engagement_cols={
                "likes": "comment_like_count",
                "replies": "sub_comment_count",
            },
            search_fields=("content",)
        )
    )

}
