import re

def sanitize_markdown(text: str) -> str:
    """
    清洗 LLM 输出：
    1. 剥离 Markdown 代码块包装 (```markdown ... ```)
    2. 压缩多余空行 (>=3 个换行符压缩为 2 个)
    3. 移除首尾的引号、空白及干扰字符
    """
    if not text:
        return ""

    # 1. 剥离 Markdown 代码块标记
    match = re.search(r"```[A-Za-z0-9_-]*\s*\n(.*?)```", text, flags=re.DOTALL)
    cleaned = match.group(1).strip() if match else text.strip()

    # 2. 压缩 3 个以上的连续换行为 2 个（维持 Markdown 段落间距）
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # 3. 剔除首尾的空白字符以及各种中英文引号
    return cleaned.strip(" \n\r\t\"'“”‘’")


# Keep the legacy node import compatible with the shared sanitizer.
clean_markdown_text = sanitize_markdown
