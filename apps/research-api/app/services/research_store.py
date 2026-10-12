import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from engines.contracts.paths import DATA_ROOT


class ResearchStore:
    def __init__(self, path: Path | None = None):
        self.path = path or DATA_ROOT / "tasks.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, body TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, body TEXT)")
            db.execute("CREATE INDEX IF NOT EXISTS event_task ON events(task_id)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def create(self, query, mode):
        task = {"research_id": uuid4().hex, "query": query, "mode": mode, "status": "queued",
                "created_at": datetime.now(timezone.utc).isoformat(), "error": "", "results": {}, "metrics": {}}
        self.save(task)
        return task

    def save(self, task):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?)", (task["research_id"], json.dumps(task, ensure_ascii=False)))

    def get(self, task_id):
        with self.connect() as db:
            row = db.execute("SELECT body FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise KeyError("研究任务不存在")
        return json.loads(row[0])

    def list(self):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM tasks ORDER BY rowid DESC LIMIT 100").fetchall()
        return [json.loads(row[0]) for row in rows]

    def append_event(self, event):
        with self.connect() as db:
            cursor = db.execute("INSERT INTO events(task_id,body) VALUES (?,?)", (event["data"].get("research_id", ""), json.dumps(event, ensure_ascii=False)))
            return cursor.lastrowid

    def events(self, task_id, after=0):
        with self.connect() as db:
            rows = db.execute("SELECT seq,body FROM events WHERE task_id=? AND seq>? ORDER BY seq", (task_id, after)).fetchall()
        return [{"id": row[0], **json.loads(row[1])} for row in rows]
