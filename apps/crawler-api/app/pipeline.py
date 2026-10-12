#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫流水线编排器 — BroadTopicExtraction → DeepSentimentCrawling → 内容表。
"""

import asyncio
from datetime import date, datetime
from typing import List, Dict, Optional
from loguru import logger

from app.broad_topic.news import NewsCollector
from app.broad_topic.topic import TopicExtractor
from app.db.repository.topic_repository import TopicRepository
from app.db.session import get_session
from app.deep_sentiment.keyword_manager import KeywordManager
from app.deep_sentiment.platform_crawler import PlatformCrawler
from app.config import DEFAULT_MAX_KEYWORDS, DEFAULT_MAX_NOTES, SUPPORTED_PLATFORMS


class CrawlerPipeline:
    """爬虫流水线 — 话题提取 → 关键词 → 多平台爬取"""

    def __init__(self):
        self.news_collector = NewsCollector()
        self.topic_extractor = TopicExtractor()
        self.keyword_manager = KeywordManager()
        self.platform_crawler = PlatformCrawler()
        self._topic_repository = TopicRepository(get_session)

    async def run_broad_topic(
            self,
            news_sources: Optional[List[str]] = None,
            max_keywords: int = None,
    ) -> Dict:
        """
        运行话题提取流程。

        Returns:
            包含 news_collection、topic_extraction、database_save 结果的字典
        """
        if max_keywords is None:
            max_keywords = DEFAULT_MAX_KEYWORDS

        logger.info(f"=== 话题提取开始 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")

        result = {
            "success": False,
            "extraction_date": date.today().isoformat(),
            "start_time": datetime.now().isoformat(),
            "news_collection": {},
            "topic_extraction": {},
            "database_save": {},
            "error": None,
        }

        try:
            logger.info("【步骤1】收集并保存热点新闻...")
            news_result = await self.news_collector.fetch_and_save_daily_news(sources=news_sources)
            result["news_collection"] = {
                "success": news_result["success"],
                "total_news": news_result.get("total_news", 0),
                "successful_sources": news_result.get("successful_sources", 0),
                "total_sources": news_result.get("total_sources", 0),
            }

            if not news_result["success"] or not news_result.get("news_item_list"):
                raise Exception("新闻收集失败或没有获取到新闻")

            logger.info("【步骤2】提取关键词和生成总结...")
            keywords, summary = await self.topic_extractor.extract_keywords_and_summary(
                news_result["news_item_list"], max_keywords=max_keywords
            )
            result["topic_extraction"] = {
                "success": len(keywords) > 0,
                "keywords_count": len(keywords),
                "keywords": keywords,
                "summary": summary,
            }

            if not keywords:
                logger.warning("没有提取到有效关键词")

            logger.info("【步骤3】保存分析结果到数据库...")
            save_success = await self._topic_repository.save_daily_topics(
                keywords, summary, date.today()
            )
            result["database_save"] = {"success": save_success}

            result["success"] = True
            result["end_time"] = datetime.now().isoformat()
            logger.info(f"话题提取完成: {len(keywords)} 个关键词")

            return result

        except Exception as e:
            logger.exception(f"话题提取流程失败: {e}")
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
            return result

    async def run_deep_sentiment(
            self,
            target_date: date = None,
            platforms: List[str] = None,
            max_keywords: int = None,
            max_notes: int = None,
            login_type: str = None,
            keywords: List[str] = None,
    ) -> Dict:
        """
        运行深度情感爬取流程。

        从 daily_topics 表读取关键词，然后在指定平台上执行爬取。
        """
        if target_date is None:
            target_date = date.today()
        if platforms is None:
            platforms = SUPPORTED_PLATFORMS
        if max_keywords is None:
            max_keywords = DEFAULT_MAX_KEYWORDS
        if max_notes is None:
            max_notes = DEFAULT_MAX_NOTES

        logger.info(f"=== 深度情感爬取开始 ({target_date}) ===")

        keywords = keywords[:max_keywords] if keywords else await self.keyword_manager.get_latest_keywords(target_date, max_keywords)
        if not keywords:
            logger.warning("没有找到关键词，无法进行爬取")
            return {"success": False, "error": "没有关键词"}

        logger.info(f"获取到 {len(keywords)} 个关键词，将在 {len(platforms)} 个平台上爬取")

        crawl_results = await self.platform_crawler.run_multi_platform_crawl_by_keywords(
            keywords, platforms, login_type, max_notes
        )

        final_report = {
            "date": target_date.isoformat(),
            "keywords_count": len(keywords),
            "platforms": platforms,
            "crawl_results": crawl_results,
            "success": crawl_results["failed_tasks"] == 0 and crawl_results["successful_tasks"] > 0,
            "partial_success": crawl_results["successful_tasks"] > 0 and crawl_results["failed_tasks"] > 0,
            "error": "部分或全部平台采集失败，请查看各平台结果" if crawl_results["failed_tasks"] else None,
        }

        logger.info(
            f"深度情感爬取完成: {crawl_results['successful_tasks']}/"
            f"{crawl_results['total_tasks']} 任务成功"
        )
        return final_report

    def run_full_pipeline(
            self,
            target_date: date = None,
            news_sources: Optional[List[str]] = None,
            platforms: List[str] = None,
            max_keywords: int = None,
            max_notes: int = None,
            login_type: str = None,
    ) -> Dict:
        """
        运行完整流水线: BroadTopicExtraction → DeepSentimentCrawling。
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"=== 完整爬虫流水线开始 ({target_date}) ===")

        async def _run_broad():
            try:
                return await self.run_broad_topic(news_sources, max_keywords)
            finally:
                from app.db.session import dispose_engine
                await dispose_engine()

        topic_result = asyncio.run(_run_broad())

        if not topic_result["success"]:
            logger.error("话题提取失败，终止流水线")
            return {"success": False, "error": "话题提取失败", "topic_result": topic_result}

        async def _run_deep():
            try:
                return await self.run_deep_sentiment(target_date, platforms, max_keywords, max_notes, login_type)
            finally:
                from app.db.session import dispose_engine
                await dispose_engine()

        crawl_result = asyncio.run(_run_deep())

        return {
            "success": crawl_result.get("success", False),
            "date": target_date.isoformat(),
            "topic_result": topic_result,
            "crawl_result": crawl_result,
        }

    async def list_available_topics(self, days: int = 7):
        """列出最近可用的话题"""
        logger.info(f"最近 {days} 天的话题数据:")
        recent_topics = await self._topic_repository.get_recent_topics(days)

        if not recent_topics:
            logger.info("  暂无话题数据")
            return

        for topic in recent_topics:
            extract_date = topic["extract_date"]
            keywords_count = len(topic.get("keywords", []))
            summary = topic.get("summary", topic.get("topic_description", ""))
            summary_preview = (summary[:100] + "...") if len(summary) > 100 else summary
            logger.info(f"  {extract_date}: {keywords_count} 个关键词")
            logger.info(f"      摘要: {summary_preview}")

    def show_platform_guide(self):
        """显示平台使用指南"""
        platform_info = {
            "xhs": "小红书 - 美妆、生活、时尚内容为主",
            "dy": "抖音 - 短视频、娱乐、生活内容",
            "ks": "快手 - 生活、娱乐、农村题材内容",
            "bili": "B站 - 科技、学习、游戏、动漫内容",
            "wb": "微博 - 热点新闻、明星、社会话题",
            "tieba": "百度贴吧 - 兴趣讨论、游戏、学习",
            "zhihu": "知乎 - 知识问答、深度讨论",
        }
        logger.info("支持的平台:")
        for platform, desc in platform_info.items():
            logger.info(f"  {platform}: {desc}")
