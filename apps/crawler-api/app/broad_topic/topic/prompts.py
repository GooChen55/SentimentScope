"""
话题分析 Prompt 模板。
"""

SYSTEM_PROMPT = "你是一个专业的新闻分析师，擅长从热点新闻中提取关键词和撰写分析总结。"


def format_news_list(news_list: list[dict]) -> str:
    """将新闻列表格式化为 LLM 输入文本"""
    items = []
    for i, news in enumerate(news_list, 1):
        title = news.get("title", "无标题")
        source = news.get("source", "未知")
        rank = news.get('rank', 0)
        items.append(f"{i}. 【{source}】{title} 【排名: {rank}】")
    return "\n".join(items)


def build_analysis_prompt(news_text: str, max_keywords: int, format_instructions: str) -> str:
    """构建话题分析 prompt"""
    news_count = len(news_text.split("\n"))
    return f"""
请分析以下{news_count}条今日热点新闻，完成两个任务：

新闻列表：
{news_text}

任务1：提取关键词（最多{max_keywords}个）
- 提取能代表今日热点话题的关键词
- 每个独立话题只提取 1-3 个关键词，严禁为同一话题生成多个变体
- 严禁列举同话题的衍生词
- 关键词应适合用于社交媒体平台搜索
- 优先选择热度高、讨论量大的话题
- 避免过于宽泛或过于具体的词汇

任务2：撰写新闻分析总结（150-300字）
- 简要概括今日热点新闻的主要内容
- 指出当前社会关注的重点话题方向
- 分析这些热点反映的社会现象或趋势
- 语言简洁明了，客观中性

{format_instructions}
"""
