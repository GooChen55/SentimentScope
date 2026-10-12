"""公共基础设施模块：engines/common/io/report_io.py。"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import re
from uuid import uuid4


def save_md_report(output_dir: str, prefix: str, query: str, content: str, suffix: str = ".md") -> Path:
    """直接完成从命名到落盘的全流程"""
    safe_query = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(query))[:100].strip('. ') or "research"
    stem = f"{prefix.lower()}_{safe_query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"

    path = Path(output_dir) / f"{stem}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
