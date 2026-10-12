"""
话题提取器 — 使用 LangChain LLM 从新闻标题中提取关键词和生成总结。
"""

import re
from typing import List, Dict, Tuple

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from app.config import (
    CRAWLER_LLM_API_KEY,
    CRAWLER_LLM_BASE_URL,
    CRAWLER_LLM_MODEL_NAME,
)
from app.broad_topic.topic.prompts import (
    SYSTEM_PROMPT,
    format_news_list,
    build_analysis_prompt,
)
from app.broad_topic.topic.parser import parse_result, get_format_instructions
from app.db.repository.topic_repository import TopicRepository
from app.db.session import get_session

_llm = ChatOpenAI(
    api_key=CRAWLER_LLM_API_KEY,
    base_url=CRAWLER_LLM_BASE_URL,
    model=CRAWLER_LLM_MODEL_NAME,
    max_tokens=1500,
    temperature=0.3,
)


class TopicExtractor:
    """话题提取器"""

    async def extract_keywords_and_summary(
            self, news_list: List[Dict], max_keywords: int = 100
    ) -> Tuple[List[str], str]:
        """从新闻列表中提取关键词和生成总结"""
        if not news_list:
            return [], "今日暂无热点新闻"

        news_text = format_news_list(news_list)

        prompt = build_analysis_prompt(news_text, max_keywords, get_format_instructions())

        try:
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
            response = await _llm.ainvoke(messages)
            keywords, summary = parse_result(response.content)

            logger.info(f"成功提取 {len(keywords)} 个关键词并生成新闻总结")
            return keywords[:max_keywords], summary

        except Exception as e:
            logger.exception(f"话题提取失败: {e}")
            fallback_keywords = _extract_simple_keywords(news_list)
            fallback_summary = f"今日共收集到 {len(news_list)} 条热点新闻，涵盖多个平台的热门话题。"
            return fallback_keywords[:max_keywords], fallback_summary


_STOP_WORDS = {"的", "了", "在", "和", "与", "或", "但", "是", "有", "被", "将", "已", "正在"}


def _extract_simple_keywords(news_list: List[Dict]) -> List[str]:
    """简单关键词提取（LLM 失败时的回退方案）"""
    keywords: List[str] = []
    for news in news_list:
        title = news.get("title", "")
        title_clean = re.sub(r"[#@【】\[\]()（）]", " ", title)
        for word in title_clean.split():
            word = word.strip()
            if len(word) > 1 and word not in _STOP_WORDS and word not in keywords:
                keywords.append(word)
    return keywords[:10]


from app.broad_topic.news.collector import NewsCollector
import asyncio

if __name__ == '__main__':
    async def main():
        news_collector = NewsCollector()

        fetched_news_result = await news_collector.fetch_and_save_daily_news()

        topic_extractor = TopicExtractor()

        extractor_key_worlds, summary = await topic_extractor.extract_keywords_and_summary(
            fetched_news_result['news_item_list'])

        topic_repository = TopicRepository(get_session)

        await topic_repository.save_daily_topics(extractor_key_worlds, summary)


    asyncio.run(main())
