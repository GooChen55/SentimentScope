"""Transactional JSONL import using actual table columns, preserving existing data."""
import hashlib
import json
import time
from pathlib import Path
from sqlalchemy import MetaData, Table, select, insert, update, Integer, BigInteger
from app.db.session import create_db_engine
from app.db.models import Base, CrawlRecord

TABLES = {
    "dy": (("douyin_aweme", "aweme_id"), ("douyin_aweme_comment", "comment_id")),
    "wb": (("weibo_note", "note_id"), ("weibo_note_comment", "comment_id")),
    "xhs": (("xhs_note", "note_id"), ("xhs_note_comment", "comment_id")),
    "ks": (("kuaishou_video", "video_id"), ("kuaishou_video_comment", "comment_id")),
    "bili": (("bilibili_video", "video_id"), ("bilibili_video_comment", "comment_id")),
    "tieba": (("tieba_note", "note_id"), ("tieba_comment", "comment_id")),
    "zhihu": (("zhihu_content", "content_id"), ("zhihu_comment", "comment_id")),
}

def read_records(path: Path, platform: str):
    for file in sorted(path.rglob("*.jsonl")):
        if "contents_" in file.name:
            kind, mapping = "content", TABLES[platform][0]
        elif "comments_" in file.name:
            kind, mapping = "comment", TABLES[platform][1]
        else:
            continue
        for line in file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            remote_id = str(payload.get(mapping[1]) or "").strip()
            if not remote_id:
                raise ValueError(f"采集记录缺少 {mapping[1]}")
            key = hashlib.sha256(f"{platform}:{kind}:{remote_id}".encode()).hexdigest()
            yield kind, mapping, key, payload

async def ingest_records(path: Path, platform: str, engine=None):
    own_engine = engine is None
    engine = engine or create_db_engine()
    counts = {"notes_count": 0, "comments_count": 0, "new_notes": 0,
              "new_comments": 0, "updated_records": 0, "duplicate_records": 0}
    seen, tables = set(), {}
    ledger = CrawlRecord.__table__
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            for kind, (name, id_column), key, payload in read_records(path, platform):
                if key in seen:
                    counts["duplicate_records"] += 1
                    continue
                seen.add(key)
                if name not in tables:
                    tables[name] = await conn.run_sync(lambda c, n=name: Table(n, MetaData(), autoload_with=c))
                table = tables[name]
                values = {k: v for k, v in payload.items() if k in table.c and k != "id"}
                for k, v in list(values.items()):
                    if isinstance(table.c[k].type, (Integer, BigInteger)) and v is not None:
                        try:
                            values[k] = int(v)
                        except (ValueError, TypeError):
                            raise ValueError(f"{name}.{k} 与当前表结构不兼容") from None
                now = int(time.time() * 1000)
                if "last_modify_ts" in table.c:
                    values["last_modify_ts"] = now
                existing = (await conn.execute(select(table.c.id).where(table.c[id_column] == values[id_column]).limit(1))).scalar_one_or_none()
                bucket = "notes" if kind == "content" else "comments"
                if existing is None:
                    if "add_ts" in table.c:
                        values["add_ts"] = now
                    await conn.execute(insert(table).values(**values))
                    counts[f"new_{bucket}"] += 1
                else:
                    await conn.execute(update(table).where(table.c.id == existing).values(**values))
                    counts["updated_records"] += 1
                counts["notes_count" if kind == "content" else "comments_count"] += 1
                record = {"record_key": key, "platform": platform, "kind": kind,
                          "remote_id": str(payload[id_column]), "source_table": name,
                          "payload": json.dumps(payload, ensure_ascii=False),
                          "last_run": path.name, "collected_at": now}
                found = (await conn.execute(select(ledger.c.record_key).where(ledger.c.record_key == key))).scalar_one_or_none()
                if found:
                    await conn.execute(update(ledger).where(ledger.c.record_key == key).values(**record))
                else:
                    await conn.execute(insert(ledger).values(**record))
    finally:
        if own_engine:
            await engine.dispose()
    return counts
