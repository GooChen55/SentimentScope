"""
LLM 响应解析 — 使用 LangChain JsonOutputParser。
"""

from langchain_core.output_parsers import JsonOutputParser
from loguru import logger

from pydantic import BaseModel, Field


class TopicAnalysisResult(BaseModel):
    """LLM 话题分析输出结构"""
    keywords: list[str] = Field(description="热点话题关键词列表，适合用于社交媒体平台搜索")
    summary: str = Field(description="今日新闻分析总结，150-300字")


_parser = JsonOutputParser(pydantic_object=TopicAnalysisResult)


def get_format_instructions() -> str:
    """获取输出格式说明，嵌入 prompt 中"""
    return _parser.get_format_instructions()


def parse_result(text: str) -> tuple[list[str], str]:
    """解析 LLM 响应，返回 (关键词列表, 总结文本)"""
    try:
        data = _parser.parse(text)
    except Exception as e:
        logger.warning(f"JsonOutputParser 解析失败: {e}")
        return [], "分析结果解析失败，请稍后重试。"

    keywords = [str(kw).strip() for kw in data.get("keywords", []) if kw and len(str(kw).strip()) > 1]
    summary = data.get("summary", "").strip()
    if not summary or len(summary) < 10:
        summary = "今日热点新闻涵盖多个领域，反映了当前社会的多元化关注点。"
    return keywords, summary
