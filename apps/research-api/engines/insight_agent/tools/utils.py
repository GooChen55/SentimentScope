from typing import Any
from datetime import datetime

from engines.insight_agent.tools.platform_mappings import CommentTableMapping, ContentTableMapping


def to_unique_id(platform_name: str, table_name: str, id: str)->str:
    return f"{platform_name}:{table_name}:{id}"


def to_datetime(timestamp: str) -> datetime:
    timestamp = float(timestamp)
    return datetime.fromtimestamp(
        timestamp / 1000 if timestamp > 1_000_000_000_000 else timestamp
    )


def extract_engagement(
        result_row: dict[str, Any],
        table_mapping: ContentTableMapping | CommentTableMapping
) -> dict[str, Any]:
    extracted_metrics: dict[str, float] = {}
    for metric_name in table_mapping.engagement_cols.keys():
        aliased_column_name = f"eng_{metric_name}"
        raw_value = result_row.get(aliased_column_name)
        extracted_metrics[metric_name] = raw_value
    return extracted_metrics
