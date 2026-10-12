"""Bounded public HTML collection and article extraction; no model or login needed."""
import asyncio
import hashlib
import ipaddress
import json
import socket
import time
from lxml import html as html_parser
from urllib.parse import urlsplit, urlunsplit, urljoin
from urllib.robotparser import RobotFileParser
import httpx
import trafilatura
from sqlalchemy import select
from app.db.models import Base, WebDocument
from app.db.session import create_db_engine

AGENT = "SentimentResearchBot/1.0"

def explicit_publish_date(html):
    tree = html_parser.fromstring(html)
    values = tree.xpath('//meta[@property="article:published_time" or @itemprop="datePublished" or @name="pubdate"]/@content')
    def dates(obj):
        if isinstance(obj, dict):
            if isinstance(obj.get("datePublished"), str):
                yield obj["datePublished"]
            for value in obj.values():
                yield from dates(value)
        elif isinstance(obj, list):
            for value in obj:
                yield from dates(value)
    for raw in tree.xpath('//script[@type="application/ld+json"]/text()'):
        try:
            values.extend(dates(json.loads(raw)))
        except ValueError:
            pass
    from datetime import datetime
    for value in values:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if 1900 <= dt.year <= datetime.now().year:
                return value[:64]
        except ValueError:
            pass
    return None

def validate_url(url):
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
        raise ValueError("只支持公开 HTTP/HTTPS 网址")
    if parts.port not in (None, 80, 443):
        raise ValueError("只支持标准网页端口")
    addresses = socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == "https" else 80))
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("不支持本机、内网或保留地址")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))

async def fetch_html(client, url, limit=2_000_000):
    for _ in range(6):
        url = await asyncio.to_thread(validate_url, url)
        async with client.stream("GET", url) as response:
            if response.is_redirect:
                url = urljoin(url, response.headers["location"])
                continue
            response.raise_for_status()
            chunks, size = [], 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > limit:
                    raise ValueError("网页超过大小限制")
                chunks.append(chunk)
            return b"".join(chunks), url, response.headers.get("content-type", "")
    raise ValueError("重定向过多")

async def extract_page(client, url, redirects=0):
    if redirects > 5:
        raise ValueError("网页跳转过多")
    url = await asyncio.to_thread(validate_url, url)
    parts = urlsplit(url)
    robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
    try:
        robots, final_robots, _ = await fetch_html(client, robots_url, limit=500_000)
        rules = RobotFileParser(final_robots)
        rules.parse(robots.decode("utf-8", errors="replace").splitlines())
        if not rules.can_fetch(AGENT, url):
            raise ValueError("目标站点 robots.txt 禁止采集此网址")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code not in (404, 410):
            raise
    html, final_url, content_type = await fetch_html(client, url)
    if content_type and "html" not in content_type.lower():
        raise ValueError("只支持 HTML 网页")
    # Re-check robots for redirects to another origin/path before extracting.
    if final_url != url:
        return await extract_page(client, final_url, redirects + 1)
    raw = await asyncio.to_thread(trafilatura.extract, html, url=final_url,
                                 output_format="json", with_metadata=True, include_comments=False)
    if not raw:
        raise ValueError("没有提取到正文，可能需要登录或浏览器渲染")
    article = json.loads(raw)
    content = article.get("text", "").strip()
    if len(content.encode("utf-8")) > 60_000:
        content = content.encode("utf-8")[:60_000].decode("utf-8", errors="ignore") + "\n[正文过长，已截断]"
    if len(content) < 80:
        raise ValueError("正文过短，未作为有效证据入库")
    return {"id": hashlib.sha256(final_url.encode()).hexdigest(), "url": final_url,
            "title": article.get("title") or parts.hostname, "content": content,
            "source": parts.hostname, "published_at": explicit_publish_date(html),
            "collected_at": int(time.time() * 1000), "content_hash": hashlib.sha256(content.encode()).hexdigest()}

async def save_document(document, engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        table = WebDocument.__table__
        old = (await conn.execute(select(table.c.content_hash).where(table.c.id == document["id"]))).scalar_one_or_none()
        if old is None:
            await conn.execute(table.insert().values(**document))
            return "new"
        await conn.execute(table.update().where(table.c.id == document["id"]).values(**document))
        return "duplicate" if old == document["content_hash"] else "updated"

async def collect_pages(urls, topic):
    from app.web.services.crawl_worker import _emit
    documents, failures = [], []
    engine = create_db_engine()
    try:
        async with httpx.AsyncClient(timeout=25, headers={"User-Agent": AGENT}, follow_redirects=False) as client:
            for url in dict.fromkeys(urls):
                _emit({"type": "stage", "stage": "web_page", "message": "正在提取公开网页正文"})
                try:
                    article = await extract_page(client, url)
                    article["topic"] = topic
                    status = await save_document(article, engine)
                    documents.append({k: v for k, v in article.items() if k != "content"} | {"characters": len(article["content"]), "ingest_status": status})
                except Exception as exc:
                    error = str(exc) if isinstance(exc, ValueError) else f"网页采集失败：{type(exc).__name__}"
                    failures.append({"url": url, "error": error})
                _emit({"type": "progress", "notes": len(documents), "keywords_total": len(set(urls)), "keywords_done": len(documents) + len(failures)})
                await asyncio.sleep(1)
    finally:
        await engine.dispose()
    return {"success": bool(documents) and not failures, "documents": documents, "failures": failures,
            "partial_success": bool(documents) and bool(failures),
            "error": "部分或全部网页采集失败，请查看失败详情" if failures else None}

async def list_documents():
    engine = create_db_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            t = WebDocument.__table__
            rows = await conn.execute(select(t.c.id, t.c.title, t.c.url, t.c.topic, t.c.source,
                                            t.c.published_at, t.c.collected_at).order_by(t.c.collected_at.desc()).limit(50))
            return [dict(row) for row in rows.mappings()]
    finally:
        await engine.dispose()
