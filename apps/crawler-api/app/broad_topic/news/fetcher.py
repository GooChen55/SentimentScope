"""
新闻 API 客户端 — 从新闻 API 获取热点新闻数据。
"""

import asyncio
import httpx
from datetime import datetime
from typing import List, Any, Dict
from loguru import logger

BASE_URL = "https://newsnow.busiyi.world"

SOURCE_NAMES = {
    "weibo": "微博热搜",
    "zhihu": "知乎热榜",
    "bilibili-hot-search": "B站热搜",
    "toutiao": "今日头条",
    "douyin": "抖音热榜",
    "github-trending-today": "GitHub趋势",
    "coolapk": "酷安热榜",
    "tieba": "百度贴吧",
    "wallstreetcn": "华尔街见闻",
    "thepaper": "澎湃新闻",
    "cls-hot": "财联社",
    "xueqiu": "雪球热榜",
}


class NewApiFetcher:
    async def fetch_popular_news(self, sources: List[str] = None) -> List[dict]:
        """获取热门新闻"""
        if sources is None:
            sources = list(SOURCE_NAMES.keys())

        logger.info(f"将从 {len(sources)} 个新闻源收集数据")

        sources_results = []
        for source in sources:
            source_name = SOURCE_NAMES.get(source)
            logger.info(f"正在获取 {source_name} 的新闻...")
            fetch_result = await self._fetch_news(source)
            sources_results.append(fetch_result)

            if fetch_result["status"] == "success":
                data = fetch_result["data"]
                if "items" in data and isinstance(data["items"], list):
                    count = len(data["items"])
                    logger.info(f"{source_name}: 获取成功，共 {count} 条新闻")
                else:
                    logger.info(f"{source_name}: 获取成功")
            else:
                logger.error(f"{source_name}: {fetch_result.get('error')}")
            await asyncio.sleep(0.5)
        return sources_results

    async def _fetch_news(self, source: str) -> Dict[str, Any]:
        """从指定源获取最新新闻"""
        url = f"{BASE_URL}/api/s?id={source}&latest"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": BASE_URL,
            "Connection": "keep-alive",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return {
                    "source": source,
                    "status": "success",
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            return {
                "source": source,
                "status": "error",
                "error": f"未知错误: {source}) - {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }


if __name__ == '__main__':
    print(datetime.now().isoformat())
